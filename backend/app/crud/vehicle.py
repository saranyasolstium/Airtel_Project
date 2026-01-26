
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import date
from sqlalchemy import func


from app.models.vehicle import VehicleLog
from app.models.vehicle_whitelist import VehicleWhitelist
from app.utils.vehicle_helpers import compute_dwell, normalize_image_base64


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
    # entry_time stored like "2026-01-26T07:22:00"
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
    """
    Adds runtime attribute: row.whitelist_status
    values: approved / blocked / expired / not_found
    """
    plates = sorted({str(x.plate_text or "").strip().upper() for x in items if x.plate_text})

    # default for all
    for row in items:
        row.whitelist_status = "not_found"

    if not plates:
        return

    # ✅ TRIM+UPPER on DB side to avoid space/case mismatch
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
    if "type" in data and "event_type" not in data:
        data["event_type"] = data.pop("type")

    plate = (data.get("plate_text") or "").strip()
    if not plate:
        raise ValueError("plate_text is required")
    plate = plate.upper()

    entry_time = _clean_time(data.get("entry_time"))
    exit_time = _clean_time(data.get("exit_time"))

    location = data.get("location")
    entry_camera_name = data.get("entry_camera_name")
    exit_camera_name = data.get("exit_camera_name")
    event_type = data.get("event_type")
    object_classification = data.get("object_classification")

    entry_img = data.get("capture_image_entry")
    if entry_img:
        entry_img = normalize_image_base64(entry_img)

    exit_img = data.get("capture_image_exit")
    if exit_img:
        exit_img = normalize_image_base64(exit_img)

    has_exit = exit_time is not None

    if has_exit:
        open_row = (
            db.query(VehicleLog)
            .filter(VehicleLog.plate_text == plate)
            .filter(or_(VehicleLog.exit_time.is_(None), VehicleLog.exit_time == ""))
            .order_by(VehicleLog.id.desc())
            .first()
        )

        if open_row:
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
                dwell_seconds, dwell_str, _ = compute_dwell(open_row.entry_time, open_row.exit_time)
                open_row.dwell_seconds = dwell_seconds
                open_row.dwell_time = dwell_str

            db.commit()
            db.refresh(open_row)
            return open_row

        obj = VehicleLog(
            plate_text=plate,
            entry_time=entry_time,
            exit_time=exit_time,
            location=location,
            status="exited",
            exit_camera_name=exit_camera_name,
            event_type=event_type,
            object_classification=object_classification,
            capture_image_exit=exit_img,
        )
        if entry_time and exit_time:
            dwell_seconds, dwell_str, _ = compute_dwell(entry_time, exit_time)
            obj.dwell_seconds = dwell_seconds
            obj.dwell_time = dwell_str

        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

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
        dwell_seconds=None,
        dwell_time=None,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_vehicle_logs(db: Session, search=None, date_from=None, date_to=None, limit=200, offset=0):
    q = db.query(VehicleLog)
    if search:
        q = _apply_search(q, search)
    q = _apply_date_range(q, date_from, date_to)

    items = q.order_by(VehicleLog.id.desc()).offset(offset).limit(limit).all()

    for row in items:
        if row.entry_time and not row.exit_time:
            dwell_seconds, dwell_str, _ = compute_dwell(row.entry_time, None)
            row.dwell_seconds = dwell_seconds
            row.dwell_time = dwell_str
            row.status = "on_site"
        elif row.exit_time:
            row.status = "exited"

    _attach_whitelist_status(db, items)
    return items


def count_vehicle_logs(db: Session, search=None, date_from=None, date_to=None) -> int:
    q = db.query(VehicleLog)
    if search:
        q = _apply_search(q, search)
    q = _apply_date_range(q, date_from, date_to)
    return q.count()

# from sqlalchemy.orm import Session
# from sqlalchemy import or_
# from datetime import date

# from app.models.vehicle import VehicleLog
# from app.models.vehicle_whitelist import VehicleWhitelist
# from app.utils.vehicle_helpers import compute_dwell, normalize_image_base64


# def _apply_search(q, search: str):
#     like = f"%{search}%"
#     return q.filter(
#         or_(
#             VehicleLog.plate_text.ilike(like),
#             VehicleLog.location.ilike(like),
#             VehicleLog.status.ilike(like),
#             VehicleLog.entry_camera_name.ilike(like),
#             VehicleLog.exit_camera_name.ilike(like),
#             VehicleLog.event_type.ilike(like),
#             VehicleLog.object_classification.ilike(like),
#         )
#     )


# def _apply_date_range(q, date_from: str | None, date_to: str | None):
#     if date_from:
#         q = q.filter(VehicleLog.entry_time >= f"{date_from}T00:00:00")
#     if date_to:
#         q = q.filter(VehicleLog.entry_time <= f"{date_to}T23:59:59")
#     return q


# def _clean_time(v: str | None) -> str | None:
#     if v is None:
#         return None
#     s = str(v).strip()
#     return s if s else None


# def _parse_entry_date(entry_time: str | None) -> date | None:
#     # entry_time stored like: "2026-01-26T07:22:00"
#     if not entry_time:
#         return None
#     s = str(entry_time).strip()
#     if len(s) < 10:
#         return None
#     try:
#         y, m, d = s[:10].split("-")
#         return date(int(y), int(m), int(d))
#     except Exception:
#         return None


# def _attach_whitelist_status(db: Session, items: list[VehicleLog]) -> None:
#     """
#     Adds runtime attribute: row.whitelist_status
#     values: approved / blacklisted / expired / not_found
#     """
#     plates = sorted(
#         {str(x.plate_text or "").strip().upper() for x in items if x.plate_text}
#     )
#     if not plates:
#         for row in items:
#             row.whitelist_status = "not_found"
#         return

#     wl_rows = (
#         db.query(VehicleWhitelist)
#         .filter(VehicleWhitelist.vehicle_number.in_(plates))
#         .all()
#     )

#     wl_map: dict[str, list[VehicleWhitelist]] = {}
#     for w in wl_rows:
#         k = str(w.vehicle_number or "").strip().upper()
#         wl_map.setdefault(k, []).append(w)

#     for row in items:
#         plate = str(row.plate_text or "").strip().upper()
#         entry_d = _parse_entry_date(row.entry_time)

#         row.whitelist_status = "not_found"
#         candidates = wl_map.get(plate, [])

#         if not candidates or not entry_d:
#             continue

#         matched = None
#         for w in candidates:
#             if w.from_date and w.to_date and (w.from_date <= entry_d <= w.to_date):
#                 matched = w
#                 break

#         if not matched:
#             row.whitelist_status = "expired"
#         else:
#             s = str(matched.status or "").lower()
#             row.whitelist_status = "approved" if s == "approved" else "blacklisted"


# def upsert_vehicle_log_by_plate(db: Session, data: dict) -> VehicleLog:
#     """
#     SAME POST for entry & exit:

#     ENTRY:
#       - send entry_time, no exit_time
#       - stores capture_image_entry + entry_camera_name
#       - creates new row

#     EXIT:
#       - send exit_time (same plate)
#       - updates latest open row (exit_time is NULL or "")
#       - stores capture_image_exit + exit_camera_name
#       - computes dwell & sets status exited
#     """

#     # map payload "type" -> event_type
#     if "type" in data and "event_type" not in data:
#         data["event_type"] = data.pop("type")

#     plate = (data.get("plate_text") or "").strip()
#     if not plate:
#         raise ValueError("plate_text is required")

#     plate = plate.upper()

#     entry_time = _clean_time(data.get("entry_time"))
#     exit_time = _clean_time(data.get("exit_time"))

#     location = data.get("location")
#     entry_camera_name = data.get("entry_camera_name")
#     exit_camera_name = data.get("exit_camera_name")

#     event_type = data.get("event_type")
#     object_classification = data.get("object_classification")

#     entry_img = data.get("capture_image_entry")
#     if entry_img:
#         entry_img = normalize_image_base64(entry_img)

#     exit_img = data.get("capture_image_exit")
#     if exit_img:
#         exit_img = normalize_image_base64(exit_img)

#     has_exit = exit_time is not None

#     # -------------------------
#     # EXIT -> UPDATE OPEN ROW
#     # -------------------------
#     if has_exit:
#         open_row = (
#             db.query(VehicleLog)
#             .filter(VehicleLog.plate_text == plate)
#             .filter(or_(VehicleLog.exit_time.is_(None), VehicleLog.exit_time == ""))
#             .order_by(VehicleLog.id.desc())
#             .first()
#         )

#         if open_row:
#             open_row.exit_time = exit_time
#             open_row.status = "exited"

#             if location is not None:
#                 open_row.location = location
#             if exit_camera_name is not None:
#                 open_row.exit_camera_name = exit_camera_name
#             if event_type is not None:
#                 open_row.event_type = event_type
#             if object_classification is not None:
#                 open_row.object_classification = object_classification

#             if exit_img:
#                 open_row.capture_image_exit = exit_img

#             if open_row.entry_time and open_row.exit_time:
#                 dwell_seconds, dwell_str, _ = compute_dwell(
#                     open_row.entry_time, open_row.exit_time
#                 )
#                 open_row.dwell_seconds = dwell_seconds
#                 open_row.dwell_time = dwell_str

#             db.commit()
#             db.refresh(open_row)
#             return open_row

#         # if no open row exists -> create exit-only row
#         obj = VehicleLog(
#             plate_text=plate,
#             entry_time=entry_time,
#             exit_time=exit_time,
#             location=location,
#             status="exited",
#             exit_camera_name=exit_camera_name,
#             event_type=event_type,
#             object_classification=object_classification,
#             capture_image_exit=exit_img,
#         )

#         if entry_time and exit_time:
#             dwell_seconds, dwell_str, _ = compute_dwell(entry_time, exit_time)
#             obj.dwell_seconds = dwell_seconds
#             obj.dwell_time = dwell_str

#         db.add(obj)
#         db.commit()
#         db.refresh(obj)
#         return obj

#     # -------------------------
#     # ENTRY -> CREATE ROW
#     # -------------------------
#     obj = VehicleLog(
#         plate_text=plate,
#         entry_time=entry_time,
#         exit_time=None,
#         location=location,
#         status="on_site",
#         entry_camera_name=entry_camera_name,
#         event_type=event_type,
#         object_classification=object_classification,
#         capture_image_entry=entry_img,
#         dwell_seconds=None,
#         dwell_time=None,
#     )

#     db.add(obj)
#     db.commit()
#     db.refresh(obj)
#     return obj


# def list_vehicle_logs(
#     db: Session,
#     search: str | None = None,
#     date_from: str | None = None,
#     date_to: str | None = None,
#     limit: int = 200,
#     offset: int = 0,
# ):
#     q = db.query(VehicleLog)

#     if search:
#         q = _apply_search(q, search)

#     q = _apply_date_range(q, date_from, date_to)

#     items = q.order_by(VehicleLog.id.desc()).offset(offset).limit(limit).all()

#     # ✅ dynamic dwell + statuses
#     for row in items:
#         if row.entry_time and not row.exit_time:
#             dwell_seconds, dwell_str, _ = compute_dwell(row.entry_time, None)
#             row.dwell_seconds = dwell_seconds
#             row.dwell_time = dwell_str
#             row.status = "on_site"
#         elif row.exit_time:
#             row.status = "exited"

#     # ✅ attach whitelist info
#     _attach_whitelist_status(db, items)

#     return items


# def count_vehicle_logs(
#     db: Session,
#     search: str | None = None,
#     date_from: str | None = None,
#     date_to: str | None = None,
# ) -> int:
#     q = db.query(VehicleLog)
#     if search:
#         q = _apply_search(q, search)
#     q = _apply_date_range(q, date_from, date_to)
#     return q.count()


