"""Helper script to find your Bluetooth printer's address and write characteristic.

Run it with your printer powered on:

    python scan_printer.py

It lists nearby BLE devices, then lets you pick one to inspect its services and
characteristics so you can fill in PRINTER_ADDRESS and PRINTER_CHAR_UUID in .env.
"""

import asyncio

from bleak import BleakClient, BleakScanner


async def main() -> None:
    print("Scanning for BLE devices (6s)...")
    devices = await BleakScanner.discover(timeout=6.0)

    if not devices:
        print("No BLE devices found. Make sure the printer is on and in range.")
        return

    for i, device in enumerate(devices):
        print(f"[{i}] {device.name or 'Unknown'} - {device.address}")

    choice = input("\nEnter the index of your printer to inspect it: ").strip()
    try:
        device = devices[int(choice)]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return

    print(f"\nConnecting to {device.address}...")
    async with BleakClient(device.address) as client:
        print(f"Connected. Address to use as PRINTER_ADDRESS: {device.address}\n")
        for service in client.services:
            print(f"Service {service.uuid}")
            for char in service.characteristics:
                print(f"  Characteristic {char.uuid} - properties: {char.properties}")

    print(
        "\nLook for a characteristic with 'write' or 'write-without-response' in its "
        "properties - that's the one to use as PRINTER_CHAR_UUID."
    )


if __name__ == "__main__":
    asyncio.run(main())
