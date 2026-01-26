from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.vehicle import VehicleLog
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


def upsert_vehicle_log_by_plate(db: Session, data: dict) -> VehicleLog:
    """
    SAME POST for entry & exit:

    ENTRY:
      - send entry_time, no exit_time
      - stores capture_image_entry + entry_camera_name
      - creates new row

    EXIT:
      - send exit_time (same plate)
      - updates latest open row (exit_time is NULL or "")
      - stores capture_image_exit + exit_camera_name
      - computes dwell & sets status exited
    """

    # map payload "type" -> event_type
    if "type" in data and "event_type" not in data:
        data["event_type"] = data.pop("type")

    plate = (data.get("plate_text") or "").strip()
    if not plate:
        raise ValueError("plate_text is required")

    entry_time = _clean_time(data.get("entry_time"))
    exit_time = _clean_time(data.get("exit_time"))

    location = data.get("location")
    entry_camera_name = data.get("entry_camera_name")
    exit_camera_name = data.get("exit_camera_name")

    event_type = data.get("event_type")
    object_classification = data.get("object_classification")

    # ✅ images (two fields)
    entry_img = data.get("capture_image_entry")
    if entry_img:
        entry_img = normalize_image_base64(entry_img)

    exit_img = data.get("capture_image_exit")
    if exit_img:
        exit_img = normalize_image_base64(exit_img)

    has_exit = exit_time is not None

    # -------------------------
    # EXIT -> UPDATE OPEN ROW
    # -------------------------
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

            # ✅ dwell must be computed if entry+exit exist
            if open_row.entry_time and open_row.exit_time:
                dwell_seconds, dwell_str, _ = compute_dwell(
                    open_row.entry_time, open_row.exit_time
                )
                open_row.dwell_seconds = dwell_seconds
                open_row.dwell_time = dwell_str

            db.commit()
            db.refresh(open_row)
            return open_row

        # if no open row exists -> create exit-only row
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

    # -------------------------
    # ENTRY -> CREATE ROW
    # -------------------------
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


def list_vehicle_logs(
    db: Session,
    search: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 200,
    offset: int = 0,
):
    q = db.query(VehicleLog)

    if search:
        q = _apply_search(q, search)

    q = _apply_date_range(q, date_from, date_to)

    items = q.order_by(VehicleLog.id.desc()).offset(offset).limit(limit).all()

    # ✅ dynamic dwell for on-site rows
    for row in items:
        if row.entry_time and not row.exit_time:
            dwell_seconds, dwell_str, _ = compute_dwell(row.entry_time, None)
            row.dwell_seconds = dwell_seconds
            row.dwell_time = dwell_str
            row.status = "on_site"
        elif row.exit_time:
            row.status = "exited"

    return items


def count_vehicle_logs(
    db: Session,
    search: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> int:
    q = db.query(VehicleLog)
    if search:
        q = _apply_search(q, search)
    q = _apply_date_range(q, date_from, date_to)
    return q.count()


# from sqlalchemy.orm import Session
# from sqlalchemy import or_

# from app.models.vehicle import VehicleLog
# from app.utils.vehicle_helpers import compute_dwell, normalize_image_base64


# def _apply_search(q, search: str):
#     like = f"%{search}%"
#     return q.filter(
#         or_(
#             VehicleLog.plate_text.ilike(like),
#             VehicleLog.location.ilike(like),
#             VehicleLog.status.ilike(like),
#             VehicleLog.camera_name.ilike(like),
#             VehicleLog.event_type.ilike(like),
#             VehicleLog.object_classification.ilike(like),
#         )
#     )


# def _apply_date_range(q, date_from: str | None, date_to: str | None):
#     # entry_time stored like "YYYY-MM-DDTHH:MM:SS" (string compare safe)
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


# # =========================
# # ENTRY -> CREATE NEW ROW
# # =========================
# def create_vehicle_entry(db: Session, data: dict) -> VehicleLog:
#     """
#     Creates a new entry row:
#       - exit_time must be empty/None
#       - capture_image -> capture_image_entry
#       - status -> on_site
#     """

#     # map payload "type" -> model field "event_type"
#     if "type" in data and "event_type" not in data:
#         data["event_type"] = data.pop("type")

#     plate = (data.get("plate_text") or "").strip()
#     if not plate:
#         raise ValueError("plate_text is required")

#     entry_time = _clean_time(data.get("entry_time"))
#     if not entry_time:
#         raise ValueError("entry_time is required for entry")

#     location = data.get("location")
#     camera_name = data.get("camera_name")
#     event_type = data.get("event_type")
#     object_classification = data.get("object_classification")

#     img = data.get("capture_image")
#     if img:
#         img = normalize_image_base64(img)

#     obj = VehicleLog(
#         plate_text=plate,
#         entry_time=entry_time,
#         exit_time=None,
#         location=location,
#         camera_name=camera_name,
#         event_type=event_type,
#         object_classification=object_classification,
#         status="on_site",
#         capture_image_entry=img,
#         dwell_seconds=None,
#         dwell_time=None,
#     )

#     db.add(obj)
#     db.commit()
#     db.refresh(obj)
#     return obj


# # =========================
# # EXIT -> UPDATE OPEN ROW
# # =========================
# def update_vehicle_exit_by_plate(db: Session, data: dict) -> VehicleLog:
#     """
#     Updates the latest open row for same plate:
#       - finds row where plate_text == plate AND (exit_time is NULL or "")
#       - updates exit_time, status, capture_image_exit
#       - computes dwell and stores it
#     """

#     # map payload "type" -> model field "event_type"
#     if "type" in data and "event_type" not in data:
#         data["event_type"] = data.pop("type")

#     plate = (data.get("plate_text") or "").strip()
#     if not plate:
#         raise ValueError("plate_text is required")

#     exit_time = _clean_time(data.get("exit_time"))
#     if not exit_time:
#         raise ValueError("exit_time is required for exit")

#     location = data.get("location")
#     camera_name = data.get("camera_name")
#     event_type = data.get("event_type")
#     object_classification = data.get("object_classification")

#     img = data.get("capture_image")
#     if img:
#         img = normalize_image_base64(img)

#     open_row = (
#         db.query(VehicleLog)
#         .filter(VehicleLog.plate_text == plate)
#         .filter(or_(VehicleLog.exit_time.is_(None), VehicleLog.exit_time == ""))
#         .order_by(VehicleLog.id.desc())
#         .first()
#     )

#     if not open_row:
#         # If you want STRICT behavior (recommended):
#         # raise ValueError("No open entry found for this plate to mark exit")

#         # If you want fallback behavior (create exit-only row), uncomment below:
#         obj = VehicleLog(
#             plate_text=plate,
#             entry_time=_clean_time(data.get("entry_time")),  # optional
#             exit_time=exit_time,
#             location=location,
#             camera_name=camera_name,
#             event_type=event_type,
#             object_classification=object_classification,
#             status="exited",
#             capture_image_exit=img,
#         )

#         if obj.entry_time and obj.exit_time:
#             dwell_seconds, dwell_str, _ = compute_dwell(obj.entry_time, obj.exit_time)
#             obj.dwell_seconds = dwell_seconds
#             obj.dwell_time = dwell_str

#         db.add(obj)
#         db.commit()
#         db.refresh(obj)
#         return obj

#     # update open row
#     open_row.exit_time = exit_time
#     open_row.status = "exited"

#     if location is not None:
#         open_row.location = location
#     if camera_name is not None:
#         open_row.camera_name = camera_name
#     if event_type is not None:
#         open_row.event_type = event_type
#     if object_classification is not None:
#         open_row.object_classification = object_classification

#     if img:
#         open_row.capture_image_exit = img

#     # ✅ compute dwell and store
#     if open_row.entry_time and open_row.exit_time:
#         dwell_seconds, dwell_str, _ = compute_dwell(open_row.entry_time, open_row.exit_time)
#         open_row.dwell_seconds = dwell_seconds
#         open_row.dwell_time = dwell_str

#     db.commit()
#     db.refresh(open_row)
#     return open_row


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

#     # recompute dwell dynamically for open rows (optional)
#     for row in items:
#         if row.entry_time and not row.exit_time:
#             dwell_seconds, dwell_str, _ = compute_dwell(row.entry_time, None)
#             row.dwell_seconds = dwell_seconds
#             row.dwell_time = dwell_str
#             row.status = "on_site"
#         elif row.exit_time:
#             row.status = "exited"

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
