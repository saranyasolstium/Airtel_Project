from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.vehicle import VehicleLog
from app.utils.vehicle_helpers import compute_dwell, normalize_image_base64


def create_vehicle_log(db: Session, data: dict) -> VehicleLog:
    # map payload "type" -> model field "event_type"
    if "type" in data and "event_type" not in data:
        data["event_type"] = data.pop("type")

    # normalize base64/url
    if data.get("capture_image"):
        data["capture_image"] = normalize_image_base64(data["capture_image"])

    # status
    data["status"] = "exited" if data.get("exit_time") else "on_site"

    # ✅ initial create: only compute dwell if exit_time exists
    if data.get("entry_time") and data.get("exit_time"):
        dwell_seconds, dwell_str, _ = compute_dwell(
            data.get("entry_time"), data.get("exit_time"))
        data["dwell_seconds"] = dwell_seconds
        data["dwell_time"] = dwell_str
    else:
        data["dwell_seconds"] = None
        data["dwell_time"] = None

    obj = VehicleLog(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def _apply_search(q, search: str):
    like = f"%{search}%"
    return q.filter(or_(
        VehicleLog.plate_text.ilike(like),
        VehicleLog.location.ilike(like),
        VehicleLog.status.ilike(like),
        VehicleLog.camera_name.ilike(like),
        VehicleLog.event_type.ilike(like),
        VehicleLog.object_classification.ilike(like),
    ))


def _apply_date_range(q, date_from: str | None, date_to: str | None):
    # entry_time stored like "YYYY-MM-DDTHH:MM:SS"
    # range will be string compare safe
    if date_from:
        q = q.filter(VehicleLog.entry_time >= f"{date_from}T00:00:00")
    if date_to:
        q = q.filter(VehicleLog.entry_time <= f"{date_to}T23:59:59")
    return q


def list_vehicle_logs(
    db: Session,
    search: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 200,
    offset: int = 0
):
    q = db.query(VehicleLog)

    if search:
        q = _apply_search(q, search)

    q = _apply_date_range(q, date_from, date_to)

    items = q.order_by(VehicleLog.id.desc()).offset(offset).limit(limit).all()

    # ✅ compute dwell dynamically for on_site rows (exit_time is null)
    for row in items:
        if row.entry_time and not row.exit_time:
            dwell_seconds, dwell_str, _ = compute_dwell(row.entry_time, None)
            row.dwell_seconds = dwell_seconds
            row.dwell_time = dwell_str
            row.status = "on_site"
        elif row.exit_time:
            row.status = "exited"

    return items


def count_vehicle_logs(db: Session, search: str | None = None, date_from: str | None = None, date_to: str | None = None) -> int:
    q = db.query(VehicleLog)
    if search:
        q = _apply_search(q, search)
    q = _apply_date_range(q, date_from, date_to)
    return q.count()


def get_vehicle_log(db: Session, log_id: int):
    obj = db.query(VehicleLog).filter(VehicleLog.id == log_id).first()
    if not obj:
        return None

    # ✅ compute dwell dynamically if needed
    if obj.entry_time and not obj.exit_time:
        dwell_seconds, dwell_str, _ = compute_dwell(obj.entry_time, None)
        obj.dwell_seconds = dwell_seconds
        obj.dwell_time = dwell_str
        obj.status = "on_site"
    elif obj.exit_time:
        obj.status = "exited"

    return obj


def delete_vehicle_log(db: Session, log_id: int) -> bool:
    obj = db.query(VehicleLog).filter(VehicleLog.id == log_id).first()
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


def update_vehicle_exit(db: Session, log_id: int, exit_time: str):
    obj = db.query(VehicleLog).filter(VehicleLog.id == log_id).first()
    if not obj:
        return None

    obj.exit_time = exit_time

    dwell_seconds, dwell_str, _ = compute_dwell(obj.entry_time, obj.exit_time)
    obj.dwell_seconds = dwell_seconds
    obj.dwell_time = dwell_str
    obj.status = "exited"

    db.commit()
    db.refresh(obj)
    return obj


# from __future__ import annotations

# from typing import Optional
# from sqlalchemy.orm import Session
# from sqlalchemy import or_

# from app.models.vehicle import VehicleLog
# from app.utils.vehicle_helpers import compute_dwell, normalize_image_base64


# def _map_payload_keys(data: dict) -> dict:
#     """
#     Incoming JSON uses "type"
#     SQLAlchemy model uses "event_type" (DB column is `type`)
#     """
#     if not data:
#         return {}

#     data = dict(data)

#     if "type" in data and "event_type" not in data:
#         data["event_type"] = data.pop("type")

#     return data


# def create_vehicle_log(db: Session, data: dict) -> VehicleLog:
#     """
#     POST:
#     - store base fields
#     - status auto set
#     - DO NOT store dwell for on_site (exit_time missing)
#     """
#     data = _map_payload_keys(data)

#     # normalize base64 / URL
#     if data.get("capture_image"):
#         data["capture_image"] = normalize_image_base64(data["capture_image"])

#     # status auto
#     if data.get("exit_time"):
#         data["status"] = "exited"
#     else:
#         data["status"] = "on_site"

#     # IMPORTANT: keep dwell NULL in DB when on_site
#     if not data.get("exit_time"):
#         data["dwell_seconds"] = None
#         data["dwell_time"] = None
#     else:
#         # if exit_time present, you can store dwell in DB (optional)
#         ds, dt = compute_dwell(data.get("entry_time"), data.get("exit_time"))
#         data["dwell_seconds"] = ds
#         data["dwell_time"] = dt

#     obj = VehicleLog(**data)

#     try:
#         db.add(obj)
#         db.commit()
#         db.refresh(obj)
#         return obj
#     except Exception:
#         db.rollback()
#         raise


# def list_vehicle_logs(
#     db: Session,
#     search: Optional[str] = None,
#     limit: int = 200,
#     offset: int = 0
# ):
#     """
#     GET:
#     ✅ ALWAYS compute dwell dynamically
#     - if exit_time NULL => now - entry_time
#     - else => exit_time - entry_time
#     """
#     q = db.query(VehicleLog)

#     if search:
#         like = f"%{search}%"
#         q = q.filter(or_(
#             VehicleLog.plate_text.ilike(like),
#             VehicleLog.location.ilike(like),
#             VehicleLog.status.ilike(like),
#             VehicleLog.camera_name.ilike(like),
#             VehicleLog.event_type.ilike(like),
#             VehicleLog.object_classification.ilike(like),
#         ))

#     logs = q.order_by(VehicleLog.id.desc()).offset(offset).limit(limit).all()

#     # ✅ FIX: compute dwell for response
#     for log in logs:
#         if log.entry_time:
#             ds, dt = compute_dwell(log.entry_time, log.exit_time)
#             log.dwell_seconds = ds
#             log.dwell_time = dt

#         # ✅ status auto
#         if log.exit_time:
#             log.status = "exited"
#         else:
#             log.status = "on_site"

#     return logs


# def get_vehicle_log(db: Session, log_id: int):
#     obj = db.query(VehicleLog).filter(VehicleLog.id == log_id).first()
#     if not obj:
#         return None

#     if obj.entry_time:
#         ds, dt = compute_dwell(obj.entry_time, obj.exit_time)
#         obj.dwell_seconds = ds
#         obj.dwell_time = dt

#     obj.status = "exited" if obj.exit_time else "on_site"
#     return obj


# def delete_vehicle_log(db: Session, log_id: int) -> bool:
#     obj = db.query(VehicleLog).filter(VehicleLog.id == log_id).first()
#     if not obj:
#         return False

#     try:
#         db.delete(obj)
#         db.commit()
#         return True
#     except Exception:
#         db.rollback()
#         raise


# def update_vehicle_exit(db: Session, log_id: int, exit_time: str):
#     """
#     PUT exit:
#     - set exit_time
#     - compute dwell using exit_time
#     - set status exited
#     """
#     obj = db.query(VehicleLog).filter(VehicleLog.id == log_id).first()
#     if not obj:
#         return None

#     obj.exit_time = exit_time
#     obj.status = "exited"

#     ds, dt = compute_dwell(obj.entry_time, obj.exit_time)
#     obj.dwell_seconds = ds
#     obj.dwell_time = dt

#     try:
#         db.commit()
#         db.refresh(obj)
#         return obj
#     except Exception:
#         db.rollback()
#         raise
