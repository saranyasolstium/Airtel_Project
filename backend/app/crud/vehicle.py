from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.models.vehicle import VehicleLog
from app.models.vehicle_whitelist import VehicleWhitelist
from app.utils.vehicle_helpers import compute_dwell, normalize_image_base64


UNKNOWN_PLATES = {"unknown", "unknow", "no plate", "noplate", "no_plate", "none", "null", "-"}


def _is_unknown_plate(plate: str | None) -> bool:
    if not plate:
        return True
    p = str(plate).strip().lower()
    return p in UNKNOWN_PLATES


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


# ✅ FIX: filter by ENTRY OR EXIT in selected date range
def _apply_date_range(q, date_from: str | None, date_to: str | None):
    if not date_from and not date_to:
        return q

    start = f"{date_from}T00:00:00" if date_from else None
    end = f"{date_to}T23:59:59" if date_to else None

    if start and end:
        return q.filter(
            or_(
                VehicleLog.entry_time.between(start, end),
                VehicleLog.exit_time.between(start, end),
            )
        )

    if start:
        return q.filter(
            or_(
                VehicleLog.entry_time >= start,
                VehicleLog.exit_time >= start,
            )
        )

    # end only
    return q.filter(
        or_(
            VehicleLog.entry_time <= end,
            VehicleLog.exit_time <= end,
        )
    )


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


def _today_from_payload(entry_time: str | None, exit_time: str | None) -> date | None:
    # use entry date if exists else exit date
    d = _parse_entry_date(entry_time)
    if d:
        return d
    return _parse_entry_date(exit_time)


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


def upsert_vehicle_log_by_plate(db: Session, data: dict) -> VehicleLog:
    """
    ✅ Rules implemented:

    Rule-1 (unknown/noplate/no plate):
      ENTRY -> insert new row
      EXIT  -> insert new row
      never update

    Rule-2 (real plate + same plate open entry TODAY):
      ENTRY -> insert new row
      EXIT  -> update latest open row only if entry_date == today

    Rule-3 (real plate but no open entry today):
      EXIT -> insert new row (do not update old rows)

    Also:
    ✅ accept `capture_image` into `capture_image_entry`
    ✅ never return None silently
    ✅ rollback on error
    ✅ `type` never null (default "car")
    """
    try:
        # accept payload key "type" and map into python attr event_type
        if "type" in data and "event_type" not in data:
            data["event_type"] = data.pop("type")

        # old payload compatibility
        if (not data.get("capture_image_entry")) and data.get("capture_image"):
            data["capture_image_entry"] = data.get("capture_image")

        plate_raw = (data.get("plate_text") or "").strip()
        if not plate_raw:
            raise ValueError("plate_text is required")

        plate = plate_raw.upper()
        is_unknown = _is_unknown_plate(plate_raw)

        entry_time = _clean_time(data.get("entry_time"))
        exit_time = _clean_time(data.get("exit_time"))

        location = data.get("location")
        entry_camera_name = data.get("entry_camera_name")
        exit_camera_name = data.get("exit_camera_name")
        event_type = (data.get("event_type") or "car")  # ✅ default non-null
        object_classification = data.get("object_classification")

        entry_img = data.get("capture_image_entry")
        if entry_img:
            entry_img = normalize_image_base64(entry_img)

        exit_img = data.get("capture_image_exit")
        if exit_img:
            exit_img = normalize_image_base64(exit_img)

        has_exit = exit_time is not None

        # ---------------------------
        # RULE-1: Unknown plates -> never update
        # ---------------------------
        if is_unknown:
            obj = VehicleLog(
                plate_text=plate,
                entry_time=entry_time,
                exit_time=exit_time if has_exit else None,
                location=location,
                status="exited" if has_exit else "on_site",
                entry_camera_name=entry_camera_name,
                exit_camera_name=exit_camera_name,
                event_type=event_type,
                object_classification=object_classification,
                capture_image_entry=entry_img if not has_exit else None,
                capture_image_exit=exit_img if has_exit else None,
            )
            if obj.entry_time and obj.exit_time:
                ds, dt, _ = compute_dwell(obj.entry_time, obj.exit_time)
                obj.dwell_seconds = ds
                obj.dwell_time = dt

            db.add(obj)
            db.commit()
            db.refresh(obj)
            return obj

        # ---------------------------
        # ENTRY (real plate) -> always insert
        # ---------------------------
        if not has_exit:
            obj = VehicleLog(
                plate_text=plate,
                entry_time=entry_time,
                exit_time=None,
                location=location,
                status="on_site",
                entry_camera_name=entry_camera_name,
                event_type=event_type,
                object_classification=object_classification,
                capture_image_entry=entry_img,
            )
            db.add(obj)
            db.commit()
            db.refresh(obj)
            return obj

        # ---------------------------
        # EXIT (real plate) -> update only open row from TODAY else insert
        # ---------------------------
        today_d = _today_from_payload(entry_time, exit_time)

        open_row = (
            db.query(VehicleLog)
            .filter(func.upper(func.trim(VehicleLog.plate_text)) == plate)
            .filter(or_(VehicleLog.exit_time.is_(None), VehicleLog.exit_time == ""))
            .order_by(VehicleLog.id.desc())
            .first()
        )

        # Rule-2: update only if open row entry_date == today_d
        if open_row and today_d and _parse_entry_date(open_row.entry_time) == today_d:
            open_row.exit_time = exit_time
            open_row.status = "exited"

            if location is not None:
                open_row.location = location
            if exit_camera_name is not None:
                open_row.exit_camera_name = exit_camera_name
            if event_type is not None:
                open_row.event_type = event_type
            if object_classification is not None:
                open_row.object_classification = object_classification
            if exit_img:
                open_row.capture_image_exit = exit_img

            if open_row.entry_time and open_row.exit_time:
                ds, dt, _ = compute_dwell(open_row.entry_time, open_row.exit_time)
                open_row.dwell_seconds = ds
                open_row.dwell_time = dt

            db.commit()
            db.refresh(open_row)
            return open_row

        # Rule-3: insert separate exited row
        obj = VehicleLog(
            plate_text=plate,
            entry_time=entry_time,
            exit_time=exit_time,
            location=location,
            status="exited",
            entry_camera_name=entry_camera_name,
            exit_camera_name=exit_camera_name,
            event_type=event_type,
            object_classification=object_classification,
            capture_image_exit=exit_img,
        )
        if entry_time and exit_time:
            ds, dt, _ = compute_dwell(entry_time, exit_time)
            obj.dwell_seconds = ds
            obj.dwell_time = dt

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
            ds, dt, _ = compute_dwell(row.entry_time, row.exit_time)
            row.dwell_seconds = ds
            row.dwell_time = dt

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
