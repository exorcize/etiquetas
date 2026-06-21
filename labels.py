import sys, re, asyncio
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from bleak import BleakScanner, BleakClient

# ---------- impressora ----------
NAME   = "MY-7779"
WRITE  = "00002af1-0000-1000-8000-00805f9b34fb"
NOTIFY = "00002af0-0000-1000-8000-00805f9b34fb"

# ---------- etiqueta (calibrado) ----------
W, H      = 384, 400      # 1 etiqueta 5x5cm em dots
MARGIN    = 14            # respiro nas bordas (nao cortar/apagar)
OFF_X     = -12           # deslocamento: mais negativo = mais pra esquerda
OFF_Y     = 12            # deslocamento: mais positivo  = mais pra baixo
COLS      = 2
CAPTION   = "Data de fab:"
MODELS = {
    "fab":    {"rows": 5, "caption": True},   # 2x5: "Data de fab:" + data
    "simple": {"rows": 7, "caption": False},  # 2x7: so a data
}

AVENIR = "/System/Library/Fonts/Avenir Next.ttc"
F_DATE    = (AVENIR, 2)   # Demi Bold
F_CAPTION = (AVENIR, 0)   # Bold (mais forte)

def font(spec, size):
    return ImageFont.truetype(spec[0], size, index=spec[1])

def fit(draw, text, spec, max_w, start):
    """maior tamanho que cabe em max_w."""
    s = start
    while s > 8:
        f = font(spec, s)
        if draw.textlength(text, font=f) <= max_w:
            return f
        s -= 1
    return font(spec, 8)

def render(date_str, model="fab", rows=None):
    M = MODELS[model]
    rows = rows or M["rows"]
    img = Image.new("L", (W, H), 255)          # branco
    d = ImageDraw.Draw(img)

    # area do grid recuada pela margem, centralizada
    cw = (W - 2*MARGIN) // COLS
    ch = (H - 2*MARGIN) // rows
    ox = (W - cw*COLS) // 2 + OFF_X
    oy = (H - ch*rows) // 2 + OFF_Y
    pad = 8
    gap = 4

    date_f = fit(d, date_str, F_DATE, cw - 2*pad, 27)
    _, _, _, date_h = d.textbbox((0,0), date_str, font=date_f)
    if M["caption"]:
        cap_f = font(F_CAPTION, 19)
        _, _, _, cap_h = d.textbbox((0,0), CAPTION, font=cap_f)
        block = cap_h + gap + date_h
    else:
        cap_h, block = 0, date_h

    for r in range(rows):
        for c in range(COLS):
            x0, y0 = ox + c*cw, oy + r*ch
            # guia de corte (borda da celula)
            d.rectangle([x0, y0, x0+cw-1, y0+ch-1], outline=0, width=1)

            ty = y0 + (ch - block)//2
            if M["caption"]:
                cap_w = d.textlength(CAPTION, font=cap_f)
                d.text((x0+(cw-cap_w)//2, ty), CAPTION, font=cap_f, fill=0)
                ty += cap_h + gap
            date_w = d.textlength(date_str, font=date_f)
            d.text((x0+(cw-date_w)//2, ty), date_str, font=date_f, fill=0)

    return img

def pack(img):
    mono = img.point(lambda p: 0 if p < 128 else 255, mode="1")  # threshold, sem dither
    return bytes(b ^ 0xFF for b in mono.tobytes())               # 1 = preto

# ---------- BLE / ESC-POS ----------
def on_notify(_, data): print("NOTIFY <-", data.hex(" "))

async def send(client, data, chunk=180):
    for i in range(0, len(data), chunk):
        await client.write_gatt_char(WRITE, data[i:i+chunk], response=False)
        await asyncio.sleep(0.02)

async def do_print(buf):
    bw = W // 8
    print(f"Procurando '{NAME}'...")
    dev = await BleakScanner.find_device_by_name(NAME, timeout=10)
    if dev is None:
        print("Nao achei. Liga a impressora e fecha o Eleph-label."); return
    async with BleakClient(dev) as client:
        print("Conectado. Imprimindo...")
        try: await client.start_notify(NOTIFY, on_notify)
        except Exception as e: print("notify falhou (ok):", e)
        out = b"\x1b@"
        y = 0
        while y < H:                              # raster em faixas
            rows = min(128, H - y)
            band = buf[y*bw:(y+rows)*bw]
            out += bytes([0x1d,0x76,0x30,0x00, bw&0xff, bw>>8, rows&0xff, rows>>8]) + band
            y += rows
        out += b"\n\n\n"
        await send(client, out)
        await asyncio.sleep(2)
        print("Pronto.")

# ---------- main ----------
def main():
    args = sys.argv[1:]
    preview_only = "preview" in args
    model = "simple" if "simple" in args else "fab"
    rows = next((int(a) for a in args if a.isdigit()), None)   # ex: python3 labels.py preview simple 8
    m = next((a for a in args if re.fullmatch(r"\d{2}/\d{2}/\d{4}", a)), None)
    date_str = m or datetime.now().strftime("%d/%m/%Y")

    img = render(date_str, model, rows)
    img.save("preview.png")
    print(f"Data: {date_str}  modelo: {model}  linhas: {rows or MODELS[model]['rows']}  ->  preview.png salvo")

    if not preview_only:
        asyncio.run(do_print(pack(img)))
    else:
        print("(so preview, nao imprimiu)")

if __name__ == "__main__":
    main()
