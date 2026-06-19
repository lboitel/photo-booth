from PIL import Image, ImageEnhance
from escpos.printer import File


def print_image(
    device: str,
    image: Image.Image,
    width_px: int = 384,
    rotate: int = 0,
    brightness: float = 1.0,
) -> None:
    if image.mode != "RGB":
        image = image.convert("RGB")

    if rotate:
        image = image.rotate(rotate, expand=True)

    scale = width_px / image.width
    new_height = max(1, round(image.height * scale))
    image = image.resize((width_px, new_height))

    if brightness != 1.0:
        image = image.convert("L")
        image = ImageEnhance.Brightness(image).enhance(brightness)

    p = File(device)
    p.image(image, impl="bitImageRaster")
    p.ln(4)
