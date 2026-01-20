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

    # Common formats
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            pass

    # Time only -> assume today
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
    If base64 -> remove data prefix and validate.
    """
    if not value:
        return None

    s = value.strip()

    if s.startswith("http://") or s.startswith("https://"):
        return s

    s = _DATA_URL_RE.sub("", s)

    try:
        base64.b64decode(s, validate=True)
    except Exception:
        raise ValueError("capture_image is not a valid base64 string or URL")

    return s


def compute_dwell(entry_time: Optional[str], exit_time: Optional[str]) -> Tuple[Optional[int], Optional[str], Optional[str]]:
    """
    ✅ Always returns 3 values:
    (dwell_seconds, dwell_time_str, exit_time_used_str)

    Rules:
    - If entry_time missing => (None, None, None)
    - If exit_time missing => use current time as exit_time_used_str
    """
    en = parse_dt(entry_time)
    if not en:
        return None, None, None

    ex = parse_dt(exit_time)
    if ex:
        seconds = int((ex - en).total_seconds())
        return seconds if seconds >= 0 else 0, format_dwell(seconds), exit_time
    else:
        now = datetime.now()
        seconds = int((now - en).total_seconds())
        if seconds < 0:
            seconds = 0
        return seconds, format_dwell(seconds), now.isoformat(timespec="seconds")


# from __future__ import annotations

# import base64
# import re
# from datetime import datetime
# from typing import Optional, Tuple

# _DATA_URL_RE = re.compile(
#     r"^data:image\/[a-zA-Z0-9.+-]+;base64,", re.IGNORECASE)


# def parse_dt(value: Optional[str]) -> Optional[datetime]:
#     """
#     Accepts:
#     - 2026-01-20T11:22:00
#     - 2026-01-20 11:22:00
#     - 2026/01/20 11:22:00
#     - 11:22:00 (today)
#     """
#     if not value:
#         return None

#     s = value.strip()
#     if not s:
#         return None

#     # ISO
#     try:
#         return datetime.fromisoformat(s.replace("Z", ""))
#     except Exception:
#         pass

#     # Common formats
#     for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S"):
#         try:
#             return datetime.strptime(s, fmt)
#         except Exception:
#             pass

#     # Time only -> today
#     for fmt in ("%H:%M:%S", "%H:%M"):
#         try:
#             t = datetime.strptime(s, fmt).time()
#             now = datetime.now()
#             return datetime(now.year, now.month, now.day, t.hour, t.minute, t.second)
#         except Exception:
#             pass

#     return None


# def format_dwell(seconds: int) -> str:
#     if seconds < 0:
#         seconds = 0

#     mins = seconds // 60
#     hrs = mins // 60
#     mins = mins % 60

#     if hrs > 0:
#         return f"{hrs}h {mins}m"
#     return f"{mins} min"


# def normalize_image_base64(value: Optional[str]) -> Optional[str]:
#     """
#     Returns:
#     - URL as is
#     - base64 stripped of data prefix
#     """
#     if not value:
#         return None

#     s = value.strip()
#     if not s:
#         return None

#     # URL allowed
#     if s.startswith("http://") or s.startswith("https://"):
#         return s

#     # Remove data-url prefix
#     s = _DATA_URL_RE.sub("", s)

#     # Validate base64
#     try:
#         base64.b64decode(s, validate=True)
#     except Exception:
#         raise ValueError("capture_image is not valid base64 or URL")

#     return s


# def compute_dwell(entry_time: Optional[str], exit_time: Optional[str]) -> Tuple[Optional[int], Optional[str]]:
#     """
#     ✅ MAIN RULE:
#     - exit_time exists  -> dwell = exit_time - entry_time
#     - exit_time is NULL -> dwell = now - entry_time
#     """
#     en = parse_dt(entry_time)
#     if not en:
#         return None, None

#     ex = parse_dt(exit_time) if exit_time else None
#     if not ex:
#         ex = datetime.now()

#     seconds = int((ex - en).total_seconds())
#     if seconds < 0:
#         seconds = 0

#     return seconds, format_dwell(seconds)
