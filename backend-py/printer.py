from PIL import Image, ImageEnhance

ESC = b"\x1b"
GS = b"\x1d"


def image_to_escpos(
    image: Image.Image,
    printer_width_px: int = 384,
    rotate: int = 0,
    brightness: float = 1.0,
) -> bytes:
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
            if pixels[x, y] == 0:
                data[row_offset + (x // 8)] |= 0x80 >> (x % 8)

    header = (
        ESC + b"@"
        + GS + b"v0" + b"\x00"
        + bytes([bytes_per_row & 0xFF, (bytes_per_row >> 8) & 0xFF])
        + bytes([height & 0xFF, (height >> 8) & 0xFF])
    )

    return header + bytes(data)


def send_to_printer(device: str, payload: bytes) -> None:
    with open(device, "wb") as f:
        f.write(payload)
        f.write(b"\n\n\n\n")
        f.flush()
