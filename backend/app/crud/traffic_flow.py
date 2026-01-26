from datetime import datetime, date, timedelta
from typing import Optional, Tuple, List, Dict

from sqlalchemy.orm import Session

from app.models.vehicle import VehicleLog


# ---------- helpers ----------

def _parse_dt(dt_str: Optional[str]) -> Optional[datetime]:
    if not dt_str:
        return None
    s = str(dt_str).strip().replace("Z", "")
    try:
        return datetime.fromisoformat(s)
    except Exception:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    return None


def _format_dwell(seconds: int) -> str:
    seconds = max(int(seconds or 0), 0)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}h {m}m {s}s"
    if m > 0:
        return f"{m}m {s}s"
    return f"{s}s"


def _format_limit(seconds: int) -> str:
    seconds = int(seconds or 0)
    if seconds <= 0:
        return "0s"
    if seconds % 3600 == 0:
        return f"{seconds // 3600}h"
    if seconds % 60 == 0:
        return f"{seconds // 60}m"
    return f"{seconds}s"


# ✅ NEW RULE (fixed thresholds)
# INFO <= 2h
# WARNING > 2h and <= 10h
# CRITICAL > 10h
def _severity(dwell_seconds: int) -> str:
    if dwell_seconds > 10 * 3600:
        return "CRITICAL"
    if dwell_seconds > 2 * 3600:
        return "WARNING"
    return "INFO"


def compute_status_and_dwell(row: VehicleLog) -> Tuple[str, int, str]:
    entry_dt = _parse_dt(row.entry_time)
    exit_dt = _parse_dt(row.exit_time)

    if not entry_dt:
        return "on_site", 0, "0s"

    end_dt = exit_dt if exit_dt else datetime.now()
    dwell_seconds = int((end_dt - entry_dt).total_seconds())
    dwell_seconds = max(dwell_seconds, 0)

    status = "exited" if exit_dt else "on_site"
    return status, dwell_seconds, _format_dwell(dwell_seconds)


# ---------- main function ----------

def get_traffic_flow_vehicles(
    db: Session,
    selected_date: Optional[date],
    limit: int,
    offset: int,
    dwell_limit_seconds: int,
) -> Tuple[int, List[Dict]]:

    if not selected_date:
        selected_date = date.today()

    start_dt = datetime.combine(selected_date, datetime.min.time())
    end_dt = start_dt + timedelta(days=1)

    base_query = (
        db.query(VehicleLog)
        .filter(VehicleLog.created_at >= start_dt)
        .filter(VehicleLog.created_at < end_dt)
    )

    total = base_query.count()

    rows = (
        base_query
        .order_by(VehicleLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    limit_label = _format_limit(dwell_limit_seconds)
    items: List[Dict] = []

    for r in rows:
        status, dwell_seconds, dwell_time = compute_status_and_dwell(r)

        # keep your existing "is_alert" based on dwell_limit_seconds
        is_alert = dwell_seconds > int(dwell_limit_seconds or 0)

        plate = r.plate_text or "UNKNOWN"
        location = r.location or "Unknown Location"

        title_text = (
            f"{plate} exceeded dwell time limit"
            if is_alert else
            f"{plate} in zone"
        )

        items.append({
            "id": r.id,
            "plate_text": plate,
            "title_text": title_text,
            "location_text": location,
            "dwell_text": f"{dwell_time} / Limit: {limit_label}",
            "dwell_seconds": dwell_seconds,
            "limit_seconds": int(dwell_limit_seconds or 0),
            "is_alert": is_alert,

            # ✅ NEW: severity based on 2h/10h rule
            "severity": _severity(dwell_seconds),

            "status": status,

            # ✅ If you renamed camera fields in DB, update these names accordingly
            # If your VehicleLog has entry_camera_name / exit_camera_name, return them:
            "entry_camera_name": getattr(r, "entry_camera_name", None),
            "exit_camera_name": getattr(r, "exit_camera_name", None),

            # keep old fields if still used elsewhere
            "camera_name": getattr(r, "camera_name", None),

            "object_classification": r.object_classification,
            "entry_time": r.entry_time,
            "exit_time": r.exit_time,
            "created_at": r.created_at,
        })

    return total, items



# from datetime import datetime, date, timedelta
# from typing import Optional, Tuple, List, Dict

# from sqlalchemy.orm import Session
# from sqlalchemy import text

# from app.models.vehicle import VehicleLog


# # ---------- helpers ----------

# def _parse_dt(dt_str: Optional[str]) -> Optional[datetime]:
#     if not dt_str:
#         return None
#     s = dt_str.strip().replace("Z", "")
#     try:
#         return datetime.fromisoformat(s)
#     except Exception:
#         pass
#     for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
#         try:
#             return datetime.strptime(s, fmt)
#         except Exception:
#             continue
#     return None


# def _format_dwell(seconds: int) -> str:
#     seconds = max(seconds, 0)
#     h = seconds // 3600
#     m = (seconds % 3600) // 60
#     s = seconds % 60
#     if h > 0:
#         return f"{h}h {m}m {s}s"
#     if m > 0:
#         return f"{m}m {s}s"
#     return f"{s}s"


# def _format_limit(seconds: int) -> str:
#     if seconds % 3600 == 0:
#         return f"{seconds // 3600}h"
#     if seconds % 60 == 0:
#         return f"{seconds // 60}m"
#     return f"{seconds}s"


# def _severity(dwell_seconds: int, limit_seconds: int) -> str:
#     if dwell_seconds >= limit_seconds * 2:
#         return "CRITICAL"
#     if dwell_seconds >= limit_seconds:
#         return "WARNING"
#     return "INFO"


# def compute_status_and_dwell(row: VehicleLog) -> Tuple[str, int, str]:
#     entry_dt = _parse_dt(row.entry_time)
#     exit_dt = _parse_dt(row.exit_time)

#     if not entry_dt:
#         return "on_site", 0, "0s"

#     end_dt = exit_dt if exit_dt else datetime.now()
#     dwell_seconds = int((end_dt - entry_dt).total_seconds())
#     dwell_seconds = max(dwell_seconds, 0)

#     status = "exited" if exit_dt else "on_site"
#     return status, dwell_seconds, _format_dwell(dwell_seconds)


# # ---------- main function ----------

# def get_traffic_flow_vehicles(
#     db: Session,
#     selected_date: Optional[date],
#     limit: int,
#     offset: int,
#     dwell_limit_seconds: int,
# ) -> Tuple[int, List[Dict]]:

#     # ✅ Default = today
#     if not selected_date:
#         selected_date = date.today()

#     start_dt = datetime.combine(selected_date, datetime.min.time())
#     end_dt = start_dt + timedelta(days=1)

#     base_query = (
#         db.query(VehicleLog)
#         .filter(VehicleLog.created_at >= start_dt)
#         .filter(VehicleLog.created_at < end_dt)
#     )

#     total = base_query.count()

#     rows = (
#         base_query
#         .order_by(VehicleLog.created_at.desc())
#         .offset(offset)
#         .limit(limit)
#         .all()
#     )

#     limit_label = _format_limit(dwell_limit_seconds)
#     items: List[Dict] = []

#     for r in rows:
#         status, dwell_seconds, dwell_time = compute_status_and_dwell(r)
#         is_alert = dwell_seconds > dwell_limit_seconds

#         plate = r.plate_text or "UNKNOWN"
#         location = r.location or "Unknown Location"

#         title_text = (
#             f"{plate} exceeded dwell time limit"
#             if is_alert else
#             f"{plate} in zone"
#         )

#         items.append({
#             "id": r.id,
#             "plate_text": plate,
#             "title_text": title_text,
#             "location_text": location,
#             "dwell_text": f"{dwell_time} / Limit: {limit_label}",
#             "dwell_seconds": dwell_seconds,
#             "limit_seconds": dwell_limit_seconds,
#             "is_alert": is_alert,
#             "severity": _severity(dwell_seconds, dwell_limit_seconds),
#             "status": status,
#             "camera_name": r.camera_name,
#             "object_classification": r.object_classification,
#             "entry_time": r.entry_time,
#             "exit_time": r.exit_time,
#             "created_at": r.created_at,
#         })

#     return total, items
