import asyncio

from bleak import BleakClient
from PIL import Image, ImageEnhance

ESC = b"\x1b"
GS = b"\x1d"


def image_to_escpos(
    image: Image.Image,
    printer_width_px: int = 384,
    rotate: int = 0,
    brightness: float = 1.0,
) -> bytes:
    """Convert a PIL image to ESC/POS raster bitmap commands (GS v 0).

    rotate: degrees to rotate the image before printing (e.g. 90 for a
        landscape photo on a narrow receipt).
    brightness: >1.0 lightens the image before dithering, producing a
        less "inky" print.
    """
    if image.mode != "RGB":
        image = image.convert("RGB")

    if rotate:
        image = image.rotate(rotate, expand=True)

    scale = printer_width_px / image.width
    new_height = max(1, round(image.height * scale))
    image = image.resize((printer_width_px, new_height))

    image = image.convert("L")
    if brightness != 1.0:
        image = ImageEnhance.Brightness(image).enhance(brightness)
    image = image.convert("1", dither=Image.FLOYDSTEINBERG)

    width, height = image.size
    bytes_per_row = (width + 7) // 8
    pixels = image.load()

    data = bytearray(bytes_per_row * height)
    for y in range(height):
        row_offset = y * bytes_per_row
        for x in range(width):
            if pixels[x, y] == 0:  # 0 = black in mode "1"
                data[row_offset + (x // 8)] |= 0x80 >> (x % 8)

    header = (
        ESC + b"@"  # initialize printer
        + GS + b"v0" + b"\x00"
        + bytes([bytes_per_row & 0xFF, (bytes_per_row >> 8) & 0xFF])
        + bytes([height & 0xFF, (height >> 8) & 0xFF])
    )

    return header + bytes(data)


async def send_to_printer(
    address: str,
    char_uuid: str,
    payload: bytes,
    chunk_size: int = 180,
    delay: float = 0.02,
) -> None:
    """Connect over BLE and stream the ESC/POS payload to the printer."""
    async with BleakClient(address) as client:
        for i in range(0, len(payload), chunk_size):
            chunk = payload[i : i + chunk_size]
            await client.write_gatt_char(char_uuid, chunk, response=False)
            await asyncio.sleep(delay)

        # Feed paper so the photo clears the cutter
        await client.write_gatt_char(char_uuid, b"\n\n\n\n", response=False)

        # Give the printer's internal buffer time to finish printing
        # before the BLE connection is closed, otherwise the tail end
        # of the image gets dropped.
        # print(f"Waiting {max(2.0, len(payload) / 2000):.1f}s for printer to finish...")
        await asyncio.sleep(5.0)
