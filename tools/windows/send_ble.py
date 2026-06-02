import asyncio
import sys
from bleak import BleakScanner, BleakClient

DEVICE_NAME = "RaspberryBLE"
RX_CHAR = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"

async def main():
    if len(sys.argv) < 2:
        print('Uso:')
        print('  python send_ble.py "mensaje"')
        return

    message = sys.argv[1]

    print("Buscando RaspberryBLE...")

    device = None
    for intento in range(1, 4):
        print(f"Intento {intento}/3...")
        device = await BleakScanner.find_device_by_name(DEVICE_NAME, timeout=10.0)
        if device is not None:
            break

    if device is None:
        print("No encontré RaspberryBLE. Verifica que la Raspberry esté en modo BLE.")
        return

    print(f"Conectando a {device.name} / {device.address}...")

    async with BleakClient(device) as client:
        if not client.is_connected:
            print("No se pudo conectar.")
            return

        print("Conectado. Enviando mensaje...")
        await client.write_gatt_char(RX_CHAR, message.encode("utf-8"), response=True)
        print("Mensaje enviado.")

asyncio.run(main())
