import asyncio
import base64
import os
import time
from io import BytesIO
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from PIL import Image

from printer import image_to_escpos, send_to_printer

load_dotenv()

app = Flask(__name__)
CORS(app)

BASE_DIR = Path(__file__).resolve().parent
TEMP_DIR = BASE_DIR / "temp"
TEMP_DIR.mkdir(exist_ok=True)

PRINTER_ADDRESS = os.environ.get("PRINTER_ADDRESS")
PRINTER_CHAR_UUID = os.environ.get("PRINTER_CHAR_UUID")
PRINTER_WIDTH_PX = int(os.environ.get("PRINTER_WIDTH_PX", "384"))
PRINTER_ROTATE = int(os.environ.get("PRINTER_ROTATE", "90"))
PRINTER_BRIGHTNESS = float(os.environ.get("PRINTER_BRIGHTNESS", "1.4"))


def decode_photo(data_url: str) -> bytes:
    _, _, b64data = data_url.partition(",")
    if not b64data:
        b64data = data_url
    return base64.b64decode(b64data)


@app.post("/api/save-photo")
def save_photo():
    body = request.get_json(force=True) or {}
    photo = body.get("photo")
    if not photo:
        return jsonify({"error": "No photo provided"}), 400

    try:
        image_bytes = decode_photo(photo)
    except Exception:
        return jsonify({"error": "Invalid photo data"}), 400

    timestamp = int(time.time() * 1000)
    filename = f"photo-{timestamp}.png"
    filepath = TEMP_DIR / filename
    filepath.write_bytes(image_bytes)

    return jsonify({"success": True, "filename": filename, "path": str(filepath)})


@app.post("/api/print-photo")
def print_photo():
    if not PRINTER_ADDRESS or not PRINTER_CHAR_UUID:
        return jsonify(
            {"error": "Printer not configured. Set PRINTER_ADDRESS and PRINTER_CHAR_UUID in .env"}
        ), 500

    body = request.get_json(force=True) or {}
    photo = body.get("photo")
    if not photo:
        return jsonify({"error": "No photo provided"}), 400

    try:
        image_bytes = decode_photo(photo)
        image = Image.open(BytesIO(image_bytes))
        payload = image_to_escpos(
            image,
            PRINTER_WIDTH_PX,
            rotate=PRINTER_ROTATE,
            brightness=PRINTER_BRIGHTNESS,
        )
    except Exception as exc:
        return jsonify({"error": f"Failed to process photo: {exc}"}), 400

    try:
        asyncio.run(send_to_printer(PRINTER_ADDRESS, PRINTER_CHAR_UUID, payload))
    except Exception as exc:
        return jsonify({"error": f"Printing failed: {exc}"}), 500

    return jsonify({"success": True})


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(port=3001)
