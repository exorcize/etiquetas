import asyncio
from bleak import BleakScanner, BleakClient

NAME   = "MY-7779"
WRITE  = "00002af1-0000-1000-8000-00805f9b34fb"
NOTIFY = "00002af0-0000-1000-8000-00805f9b34fb"

# ---- chutes pra calibrar (50mm @ 8 dots/mm) ----
W = 384            # largura em dots (48mm uteis). Se a borda nao chegar na beira, aumenta.
H = 400            # altura de 1 etiqueta (50mm). Se sobrar/faltar, ajusta.
BYTES_W = W // 8   # bytes por linha

buf = bytearray(BYTES_W * H)

def setpx(x, y):
    if 0 <= x < W and 0 <= y < H:
        buf[y * BYTES_W + (x >> 3)] |= (0x80 >> (x & 7))

def hline(x0, x1, y):
    for x in range(x0, x1 + 1):
        setpx(x, y)

def vline(x, y0, y1):
    for y in range(y0, y1 + 1):
        setpx(x, y)

def rect(x0, y0, x1, y1):
    hline(x0, x1, y0); hline(x0, x1, y1)
    vline(x0, y0, y1); vline(x1, y0, y1)

# borda externa (2px pra ficar visivel)
rect(0, 0, W - 1, H - 1)
rect(1, 1, W - 2, H - 2)
# cruz central
vline(W // 2, 0, H - 1)
hline(0, W - 1, H // 2)
# regua: tick a cada 40 dots (5mm), maior a cada 80 dots (10mm)
for y in range(0, H, 40):
    hline(0, 20, y)
for y in range(0, H, 80):
    hline(0, 40, y)
for x in range(0, W, 40):
    vline(x, 0, 20)
for x in range(0, W, 80):
    vline(x, 0, 40)

def raster_cmd(band, rows):
    return bytes([0x1d, 0x76, 0x30, 0x00,
                  BYTES_W & 0xff, BYTES_W >> 8,
                  rows & 0xff, rows >> 8]) + band

def on_notify(_, data):
    print("NOTIFY <-", data.hex(" "))

async def send(client, data, chunk=180):
    for i in range(0, len(data), chunk):
        await client.write_gatt_char(WRITE, data[i:i+chunk], response=False)
        await asyncio.sleep(0.02)

async def main():
    print(f"Procurando '{NAME}'...  (alvo: {W}x{H} dots)")
    dev = await BleakScanner.find_device_by_name(NAME, timeout=10)
    if dev is None:
        print("Nao achei. Liga a impressora e fecha o Eleph-label.")
        return

    async with BleakClient(dev) as client:
        print("Conectado. Mandando calibracao...")
        try:
            await client.start_notify(NOTIFY, on_notify)
        except Exception as e:
            print("notify falhou (ok):", e)

        out = b"\x1b@"                       # init
        BAND = 128                           # manda o raster em faixas
        y = 0
        while y < H:
            rows = min(BAND, H - y)
            band = bytes(buf[y * BYTES_W:(y + rows) * BYTES_W])
            out += raster_cmd(band, rows)
            y += rows
        out += b"\n\n\n"                     # avanca pra arrancar

        await send(client, out)
        await asyncio.sleep(2)
        print("Pronto. Olha onde as bordas e a regua caem na etiqueta.")

asyncio.run(main())
