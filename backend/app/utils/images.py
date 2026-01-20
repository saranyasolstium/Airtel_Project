import os
import base64
import uuid
from typing import Optional

CAPTURE_DIR = os.path.join("storage", "vehicle_captures")


def ensure_dirs():
    os.makedirs(CAPTURE_DIR, exist_ok=True)


def _strip_data_url(b64: str) -> str:
    # supports "data:image/jpeg;base64,...."
    if "," in b64 and "base64" in b64.split(",")[0]:
        return b64.split(",", 1)[1]
    return b64


def save_base64_image(b64: Optional[str]) -> Optional[str]:
    if not b64:
        return None

    ensure_dirs()
    raw = _strip_data_url(b64)

    try:
        img_bytes = base64.b64decode(raw)
    except Exception:
        return None

    filename = f"{uuid.uuid4().hex}.jpg"
    path = os.path.join(CAPTURE_DIR, filename)

    with open(path, "wb") as f:
        f.write(img_bytes)

    # URL served by StaticFiles
    return f"/storage/vehicle_captures/{filename}"
