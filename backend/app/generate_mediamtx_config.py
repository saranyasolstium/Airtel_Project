# app/generate_mediamtx_config.py
import os
import re
import yaml
import hashlib
from typing import Tuple, Dict, Any

# ✅ edit these if your locations differ
MTX_CONFIG_PATH = os.path.join("mediamtx", "mediamtx.yml")
HLS_BASE_URL = os.environ.get("HLS_BASE_URL", "http://localhost:8888")


def _safe_load_yaml(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data is None:
        data = {}

    # if "paths:" exists but empty => None
    if data.get("paths") is None:
        data["paths"] = {}

    return data


def _safe_write_yaml(path: str, data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            data,
            f,
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
        )


def _slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "cam"


def _make_path_name(rtsp_url: str) -> str:
    # stable path name per RTSP
    h = hashlib.sha1(rtsp_url.encode("utf-8")).hexdigest()[:10]
    return f"cam-{h}"


def generate_mediamtx_config(rtsp_url: str) -> Tuple[bool, str]:
    """
    Returns:
      needs_restart: bool   -> if config changed, restart MediaMTX
      hls_url: str          -> HLS m3u8 URL to play
    """
    config = _safe_load_yaml(MTX_CONFIG_PATH)

    # ✅ guarantee dict
    if config.get("paths") is None:
        config["paths"] = {}
    if not isinstance(config["paths"], dict):
        config["paths"] = {}

    path_name = _make_path_name(rtsp_url)

    # what we want to write into paths
    new_path_cfg = {
        "source": rtsp_url,
        "sourceOnDemand": False,
        # ✅ force TCP (reduces UDP/8000 issues)
        "rtspTransport": "tcp",
    }

    existing_path_cfg = config["paths"].get(path_name)
    needs_restart = existing_path_cfg != new_path_cfg

    if needs_restart:
        config["paths"][path_name] = new_path_cfg
        _safe_write_yaml(MTX_CONFIG_PATH, config)

    # MediaMTX HLS default format:
    # http://HOST:8888/<path>/index.m3u8
    hls_url = f"{HLS_BASE_URL}/{path_name}/index.m3u8"
    return needs_restart, hls_url
