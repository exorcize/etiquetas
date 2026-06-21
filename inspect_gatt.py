import asyncio
from bleak import BleakScanner, BleakClient

NAME = "MY-7779"

async def main():
    print(f"Procurando '{NAME}'...")
    device = await BleakScanner.find_device_by_name(NAME, timeout=10)
    if device is None:
        print("Nao achei. Liga a impressora e fecha o Eleph-label (1 cliente BLE por vez).")
        return

    print(f"Achei: {device.name}  ->  {device.address}")
    print("Conectando...")

    async with BleakClient(device) as client:
        print(f"Conectado: {client.is_connected}\n")
        for s in client.services:
            print(f"[service] {s.uuid}")
            for c in s.characteristics:
                props = ",".join(c.properties)
                print(f"    char {c.uuid}  props=[{props}]")
                for d in c.descriptors:
                    print(f"        descr {d.uuid}")
        print("\nProcure a char com 'write' ou 'write-without-response' -> e a de envio.")

asyncio.run(main())
