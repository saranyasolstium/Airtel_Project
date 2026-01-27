from __future__ import annotations

import base64
import re
from datetime import datetime
from typing import Optional, Tuple

_DATA_URL_RE = re.compile(
    r"^data:image\/[a-zA-Z0-9.+-]+;base64,", re.IGNORECASE)


def parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    s = value.strip()

    # ISO 8601
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        pass

    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass

    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            t = datetime.strptime(s, fmt).time()
            now = datetime.now()
            return datetime(now.year, now.month, now.day, t.hour, t.minute, t.second)
        except Exception:
            pass

    return None


def format_dwell(seconds: int) -> str:
    if seconds < 0:
        seconds = 0
    mins = seconds // 60
    hrs = mins // 60
    mins = mins % 60
    if hrs > 0:
        return f"{hrs}h {mins}m"
    return f"{mins} min"


def normalize_image_base64(value: Optional[str]) -> Optional[str]:
    """
    Keep URL as-is.
    If base64 -> remove data prefix, remove whitespace/newlines, auto-pad, and validate.
    """
    if not value:
        return None

    s = str(value).strip()

    if s.startswith("http://") or s.startswith("https://"):
        return s

    # remove data-url header if present
    s = _DATA_URL_RE.sub("", s)

    # remove whitespace/newlines
    s = re.sub(r"\s+", "", s)

    # add missing padding if needed
    pad = (-len(s)) % 4
    if pad:
        s += "=" * pad

    try:
        # lenient decode for common base64 variants
        base64.b64decode(s, validate=False)
    except Exception:
        raise ValueError("Invalid image. Must be base64 string or URL")

    return s


def compute_dwell(
    entry_time: Optional[str],
    exit_time: Optional[str],
) -> Tuple[Optional[int], Optional[str], Optional[str]]:
    """
    Always returns:
    (dwell_seconds, dwell_time_str, exit_time_used_str)

    - If entry_time missing => (None, None, None)
    - If exit_time missing => use current time as exit_time_used_str
    """
    en = parse_dt(entry_time)
    if not en:
        return None, None, None

    ex = parse_dt(exit_time)
    if ex:
        seconds = int((ex - en).total_seconds())
        if seconds < 0:
            seconds = 0
        return seconds, format_dwell(seconds), exit_time
    else:
        now = datetime.now()
        seconds = int((now - en).total_seconds())
        if seconds < 0:
            seconds = 0
        return seconds, format_dwell(seconds), now.isoformat(timespec="seconds")
