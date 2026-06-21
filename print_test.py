import asyncio
from bleak import BleakScanner, BleakClient

NAME   = "MY-7779"
WRITE  = "00002af1-0000-1000-8000-00805f9b34fb"   # service 18f0 (aposta principal)
NOTIFY = "00002af0-0000-1000-8000-00805f9b34fb"

def on_notify(_, data):
    print("NOTIFY <-", data.hex(" "))

async def send(client, data, chunk=180):
    for i in range(0, len(data), chunk):
        await client.write_gatt_char(WRITE, data[i:i+chunk], response=False)
        await asyncio.sleep(0.02)

async def main():
    print(f"Procurando '{NAME}'...")
    dev = await BleakScanner.find_device_by_name(NAME, timeout=10)
    if dev is None:
        print("Nao achei. Liga a impressora e fecha o Eleph-label.")
        return

    async with BleakClient(dev) as client:
        print("Conectado. Mandando teste ESC/POS...")
        try:
            await client.start_notify(NOTIFY, on_notify)
        except Exception as e:
            print("notify falhou (ok, segue):", e)

        ESC = b"\x1b"
        data  = ESC + b"@"                  # init
        data += b"MY-7779 TESTE\n"
        data += b"FAB: 20/06/2026\n"
        data += b"abcdefghij 0123456789\n"
        data += b"\n\n\n\n"                  # avanca papel

        await send(client, data)
        await asyncio.sleep(2)              # deixa esvaziar o buffer
        print("Pronto. Saiu papel com texto?")

asyncio.run(main())
