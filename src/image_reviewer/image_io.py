import base64
import mimetypes
from pathlib import Path

SUPPORTED_MIME_TYPES = {"image/png", "image/jpeg", "image/gif", "image/webp"}


def detect_mime_type(path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(str(path))
    if mime_type not in SUPPORTED_MIME_TYPES:
        raise ValueError(f"Unsupported image format: {path.suffix}")
    return mime_type


def encode_image_to_data_url(path: Path) -> str:
    mime_type = detect_mime_type(path)
    image_bytes = path.read_bytes()
    b64 = base64.b64encode(image_bytes).decode()
    return f"data:{mime_type};base64,{b64}"


def save_annotated_image(base64_data: str, output_path: Path) -> None:
    if base64_data.startswith("data:"):
        base64_data = base64_data.split(",", 1)[1]
    image_bytes = base64.b64decode(base64_data)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(image_bytes)
