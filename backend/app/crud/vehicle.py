from __future__ import annotations

import re
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.models.vehicle import VehicleLog
from app.models.vehicle_whitelist import VehicleWhitelist
from app.utils.vehicle_helpers import compute_dwell, normalize_image_base64


# ---------------------------
# Unknown plate detection (FIXED)
# ---------------------------

UNKNOWN_PLATE_SET = {
    "UNKNOWN",
    "UNKNOW",        # ✅ your current value
    "NO PLATE",
    "NOPLATE",
    "NO_PLATE",
    "NOT DETECTED",
    "NOTDETECTED",
    "NO NUMBER",
    "NONUMBER",
    "NA",
    "N/A",
    "-",
    "--",
    "NONE",
    "NULL",
    "0",
}

_UNKNOWN_NORM_SET = {re.sub(r"[\s\-_]", "", x) for x in UNKNOWN_PLATE_SET}


def is_unknown_plate(plate: str | None) -> bool:
    if not plate:
        return True

    p = str(plate).strip().upper()
    p = " ".join(p.split())

    if not p:
        return True

    if p in UNKNOWN_PLATE_SET:
        return True

    p2 = re.sub(r"[\s\-_]", "", p)
    if p2 in _UNKNOWN_NORM_SET:
        return True

    # common "unknown-like" patterns
    if p2.startswith("UNK"):  # UNK / UNKN / UNKNOW / UNKNOWN
        return True
    if "NOPLATE" in p2 or "NPLATE" in p2:
        return True

    return False


# ---------------------------
# Listing helpers
# ---------------------------

def _apply_search(q, search: str):
    like = f"%{search}%"
    return q.filter(
        or_(
            VehicleLog.plate_text.ilike(like),
            VehicleLog.location.ilike(like),
            VehicleLog.status.ilike(like),
            VehicleLog.entry_camera_name.ilike(like),
            VehicleLog.exit_camera_name.ilike(like),
            VehicleLog.event_type.ilike(like),
            VehicleLog.object_classification.ilike(like),
        )
    )


def _apply_date_range(q, date_from: str | None, date_to: str | None):
    if date_from:
        q = q.filter(VehicleLog.entry_time >= f"{date_from}T00:00:00")
    if date_to:
        q = q.filter(VehicleLog.entry_time <= f"{date_to}T23:59:59")
    return q


def _clean_time(v: str | None) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


def _parse_entry_date(entry_time: str | None) -> date | None:
    if not entry_time:
        return None
    s = str(entry_time).strip()
    if len(s) < 10:
        return None
    try:
        y, m, d = s[:10].split("-")
        return date(int(y), int(m), int(d))
    except Exception:
        return None


def _attach_whitelist_status(db: Session, items: list[VehicleLog]) -> None:
    plates = sorted({str(x.plate_text or "").strip().upper()
                    for x in items if x.plate_text})

    for row in items:
        row.whitelist_status = "not_found"

    if not plates:
        return

    wl_rows = (
        db.query(VehicleWhitelist)
        .filter(func.upper(func.trim(VehicleWhitelist.vehicle_number)).in_(plates))
        .all()
    )

    wl_map: dict[str, list[VehicleWhitelist]] = {}
    for w in wl_rows:
        k = str(w.vehicle_number or "").strip().upper()
        wl_map.setdefault(k, []).append(w)

    for row in items:
        plate = str(row.plate_text or "").strip().upper()
        entry_d = _parse_entry_date(row.entry_time)

        candidates = wl_map.get(plate, [])
        if not candidates or not entry_d:
            continue

        matched = None
        for w in candidates:
            if w.from_date and w.to_date and (w.from_date <= entry_d <= w.to_date):
                matched = w
                break

        if not matched:
            row.whitelist_status = "expired"
        else:
            s = str(matched.status or "").lower().strip()
            if s == "approved":
                row.whitelist_status = "approved"
            elif s == "blocked":
                row.whitelist_status = "blocked"
            else:
                row.whitelist_status = s


def _only_model_columns(payload: dict) -> dict:
    """
    ✅ Prevents: "invalid keyword argument for VehicleLog"
    Keeps only keys that exist as real DB columns on VehicleLog.
    """
    allowed = set(VehicleLog.__table__.columns.keys())
    return {k: v for k, v in payload.items() if k in allowed}


# ---------------------------
# Main CRUD (RULES)
# ---------------------------

def upsert_vehicle_log_by_plate(db: Session, data: dict) -> VehicleLog:
    """
    ✅ Rules:

    Rule-1 (unknown/noplate/no plate):
      ENTRY -> insert
      EXIT  -> insert
      never update

    Rule-2 (real plate + open entry today):
      ENTRY -> insert
      EXIT  -> update latest open row only if entry_date == today

    Rule-3 (real plate but no open entry today OR different plate):
      EXIT -> insert
      do not update older rows
    """
    try:
        # accept payload key "type" and map into python attr event_type
        if "type" in data and "event_type" not in data:
            data["event_type"] = data.pop("type")

        # ✅ allow NULL in DB, but still normalize if present
        if data.get("event_type") is not None:
            data["event_type"] = str(data["event_type"]).strip() or None

        # compatibility: old payload might send capture_image
        if (not data.get("capture_image_entry")) and data.get("capture_image"):
            data["capture_image_entry"] = data.get("capture_image")

        raw_plate = (data.get("plate_text") or "").strip()
        if not raw_plate:
            raise ValueError("plate_text is required")

        plate = " ".join(raw_plate.upper().split())

        entry_time = _clean_time(data.get("entry_time"))
        exit_time = _clean_time(data.get("exit_time"))
        has_exit = exit_time is not None

        # normalize images
        if data.get("capture_image_entry"):
            data["capture_image_entry"] = normalize_image_base64(
                data["capture_image_entry"])
        if data.get("capture_image_exit"):
            data["capture_image_exit"] = normalize_image_base64(
                data["capture_image_exit"])

        plate_unknown = is_unknown_plate(plate)
        today_d = date.today()

        # ---------------------------
        # EXIT event
        # ---------------------------
        if has_exit:
            # ✅ Rule-1: unknown -> always insert (never update)
            if plate_unknown:
                payload = {
                    "plate_text": plate,
                    "entry_time": entry_time,
                    "exit_time": exit_time,
                    "location": data.get("location"),
                    "status": "exited",
                    "entry_camera_name": data.get("entry_camera_name"),
                    "exit_camera_name": data.get("exit_camera_name"),
                    "event_type": data.get("event_type"),
                    "object_classification": data.get("object_classification"),
                    "capture_image_entry": data.get("capture_image_entry"),
                    "capture_image_exit": data.get("capture_image_exit"),
                }
                payload = _only_model_columns(payload)

                obj = VehicleLog(**payload)
                if entry_time and exit_time:
                    dwell_seconds, dwell_str, _ = compute_dwell(
                        entry_time, exit_time)
                    obj.dwell_seconds = dwell_seconds
                    obj.dwell_time = dwell_str

                db.add(obj)
                db.commit()
                db.refresh(obj)
                return obj

            # ✅ Rule-2: update only if same plate open entry is TODAY
            open_row = (
                db.query(VehicleLog)
                .filter(func.upper(func.trim(VehicleLog.plate_text)) == plate)
                .filter(or_(VehicleLog.exit_time.is_(None), VehicleLog.exit_time == ""))
                .order_by(VehicleLog.id.desc())
                .first()
            )

            if open_row:
                open_entry_d = _parse_entry_date(open_row.entry_time)
                if open_entry_d == today_d:
                    open_row.exit_time = exit_time
                    open_row.status = "exited"

                    if data.get("location") is not None:
                        open_row.location = data.get("location")
                    if data.get("exit_camera_name") is not None:
                        open_row.exit_camera_name = data.get(
                            "exit_camera_name")
                    if data.get("event_type") is not None:
                        open_row.event_type = data.get("event_type")
                    if data.get("object_classification") is not None:
                        open_row.object_classification = data.get(
                            "object_classification")
                    if data.get("capture_image_exit"):
                        open_row.capture_image_exit = data.get(
                            "capture_image_exit")

                    if open_row.entry_time and open_row.exit_time:
                        dwell_seconds, dwell_str, _ = compute_dwell(
                            open_row.entry_time, open_row.exit_time
                        )
                        open_row.dwell_seconds = dwell_seconds
                        open_row.dwell_time = dwell_str

                    db.commit()
                    db.refresh(open_row)
                    return open_row

            # ✅ Rule-3: no open today -> insert new EXIT row
            payload = {
                "plate_text": plate,
                "entry_time": entry_time,
                "exit_time": exit_time,
                "location": data.get("location"),
                "status": "exited",
                "entry_camera_name": data.get("entry_camera_name"),
                "exit_camera_name": data.get("exit_camera_name"),
                "event_type": data.get("event_type"),
                "object_classification": data.get("object_classification"),
                "capture_image_entry": data.get("capture_image_entry"),
                "capture_image_exit": data.get("capture_image_exit"),
            }
            payload = _only_model_columns(payload)

            obj = VehicleLog(**payload)
            if entry_time and exit_time:
                dwell_seconds, dwell_str, _ = compute_dwell(
                    entry_time, exit_time)
                obj.dwell_seconds = dwell_seconds
                obj.dwell_time = dwell_str

            db.add(obj)
            db.commit()
            db.refresh(obj)
            return obj

        # ---------------------------
        # ENTRY event -> always insert
        # ---------------------------
        payload = {
            "plate_text": plate,
            "entry_time": entry_time,
            "exit_time": None,
            "location": data.get("location"),
            "status": "on_site",
            "entry_camera_name": data.get("entry_camera_name"),
            "exit_camera_name": data.get("exit_camera_name"),
            "event_type": data.get("event_type"),
            "object_classification": data.get("object_classification"),
            "capture_image_entry": data.get("capture_image_entry"),
        }
        payload = _only_model_columns(payload)

        obj = VehicleLog(**payload)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    except Exception:
        db.rollback()
        raise


def list_vehicle_logs(
    db: Session,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
):
    q = db.query(VehicleLog)
    if search:
        q = _apply_search(q, search)
    q = _apply_date_range(q, date_from, date_to)

    items = q.order_by(VehicleLog.id.desc()).offset(offset).limit(limit).all()

    for row in items:
        if row.exit_time and str(row.exit_time).strip():
            row.status = "exited"
        else:
            row.status = "on_site"

        if row.entry_time and str(row.entry_time).strip():
            dwell_seconds, dwell_str, _ = compute_dwell(
                row.entry_time, row.exit_time)
            row.dwell_seconds = dwell_seconds
            row.dwell_time = dwell_str

    _attach_whitelist_status(db, items)
    return items


def count_vehicle_logs(
    db: Session,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> int:
    q = db.query(VehicleLog)
    if search:
        q = _apply_search(q, search)
    q = _apply_date_range(q, date_from, date_to)
    return q.count()
