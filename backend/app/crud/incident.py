from __future__ import annotations

from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.models.incident import IncidentAlert


def _auto_resolve_previous_crowd(db: Session, camera_name: str, zone_name: str):
    # resolve all previous ACTIVE crowd alerts for same camera + zone
    (
        db.query(IncidentAlert)
        .filter(IncidentAlert.incident_type == "crowd")
        .filter(IncidentAlert.camera_name == camera_name)
        .filter(IncidentAlert.zone_name == zone_name)
        .filter(IncidentAlert.alert_status == "active")
        .update(
            {
                IncidentAlert.alert_status: "resolved",
                IncidentAlert.resolved_at: datetime.utcnow(),
            },
            synchronize_session=False,
        )
    )


def create_incident_alert(
    db: Session,
    incident_type: str,
    zone_name: str,
    camera_name: str,
    image_base64: str,
    person_count: int | None = None,
    max_count: int | None = None,
    object_type: str | None = None,
):
    incident_type = (incident_type or "crowd").strip().lower()
    zone_name = (zone_name or "").strip()
    camera_name = (camera_name or "").strip()

    # ✅ crowd = people only
    if incident_type == "crowd":
        _auto_resolve_previous_crowd(
            db, camera_name=camera_name, zone_name=zone_name)

        mc = max_count if max_count is not None else 20
        pc = person_count if person_count is not None else 0

        if pc > mc:
            message = f"Crowd density exceeds limit ({mc} people) in {zone_name}"
        else:
            message = f"Crowd count normal in {zone_name}"

        row = IncidentAlert(
            incident_type="crowd",
            object_type="people",  # ✅ force people
            zone_name=zone_name,
            camera_name=camera_name,
            person_count=pc,
            max_count=mc,
            image_base64=image_base64,
            message=message,
            alert_status="active",
            resolved_at=None,
        )

    else:
        # ✅ non-crowd = no person_count/max_count
        if incident_type == "unauthorized":
            msg = f"Unauthorized entry detected in {zone_name}"
        elif incident_type == "door_open":
            msg = f"Door opened in {zone_name}"
        elif incident_type == "door_close":
            msg = f"Door closed in {zone_name}"
        elif incident_type == "vehicle_unauthorized":
            msg = f"Unauthorized vehicle detected in {zone_name}"
        else:
            msg = f"Incident detected in {zone_name}"

        row = IncidentAlert(
            incident_type=incident_type,
            object_type=object_type,  # optional
            zone_name=zone_name,
            camera_name=camera_name,
            person_count=None,
            max_count=None,
            image_base64=image_base64,
            message=msg,
            alert_status="active",
            resolved_at=None,
        )

    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_incident_alerts(
    db: Session,
    incident_type: str = "all",
    status: str = "all",
    camera_name: str | None = None,
    object_type: str | None = None,
    limit: int = 500,
):
    q = db.query(IncidentAlert).order_by(IncidentAlert.timestamp.desc())

    if incident_type and incident_type != "all":
        q = q.filter(IncidentAlert.incident_type == incident_type)

    if status and status != "all":
        q = q.filter(IncidentAlert.alert_status == status)

    if camera_name:
        q = q.filter(IncidentAlert.camera_name == camera_name)

    if object_type:
        q = q.filter(IncidentAlert.object_type == object_type)

    return q.limit(limit).all()


def resolve_incident_alert(db: Session, alert_id: int):
    row = db.query(IncidentAlert).filter(
        IncidentAlert.alert_id == alert_id).first()
    if not row:
        return None

    row.alert_status = "resolved"
    row.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(row)
    return row


def get_incident_filters(db: Session):
    cameras = [
        r[0]
        for r in db.query(IncidentAlert.camera_name)
        .distinct()
        .order_by(IncidentAlert.camera_name)
        .all()
        if r and r[0]
    ]

    incident_types = [
        r[0]
        for r in db.query(IncidentAlert.incident_type)
        .distinct()
        .order_by(IncidentAlert.incident_type)
        .all()
        if r and r[0]
    ]

    object_types = [
        r[0]
        for r in db.query(IncidentAlert.object_type)
        .distinct()
        .order_by(IncidentAlert.object_type)
        .all()
        if r and r[0]
    ]

    return {"cameras": cameras, "incident_types": incident_types, "object_types": object_types}


# ✅ NEW: STATS COUNTS (by date, optional filters)
def get_alert_counts(
    db: Session,
    incident_type: str = "all",
    camera_name: str | None = None,
    object_type: str | None = None,
    target_date: date | None = None,
):
    """
    Returns counts for ONE DAY.

    If target_date = None → today.
    If incident_type=all → combined (all incident types)
    If incident_type=crowd → only crowd counts
    """

    if target_date is None:
        target_date = datetime.utcnow().date()

    base = db.query(IncidentAlert)

    # ✅ filter by date (DATE(timestamp)=target_date)
    base = base.filter(func.date(IncidentAlert.timestamp) == target_date)

    if camera_name:
        base = base.filter(IncidentAlert.camera_name == camera_name)

    if object_type:
        base = base.filter(IncidentAlert.object_type == object_type)

    if incident_type and incident_type != "all":
        base = base.filter(IncidentAlert.incident_type == incident_type)

    # ✅ summary
    summary_row = base.with_entities(
        func.count(IncidentAlert.alert_id).label("total"),
        func.sum(case((IncidentAlert.alert_status == "active", 1), else_=0)).label(
            "active"),
        func.sum(case((IncidentAlert.alert_status == "resolved", 1), else_=0)).label(
            "resolved"),
    ).first()

    summary = {
        "total": int(summary_row.total or 0),
        "active": int(summary_row.active or 0),
        "resolved": int(summary_row.resolved or 0),
    }

    # ✅ breakdown by type (even if incident_type filter is used, it will return only that type)
    by_type_q = base.with_entities(
        IncidentAlert.incident_type.label("incident_type"),
        func.count(IncidentAlert.alert_id).label("total"),
        func.sum(case((IncidentAlert.alert_status == "active", 1), else_=0)).label(
            "active"),
        func.sum(case((IncidentAlert.alert_status == "resolved", 1), else_=0)).label(
            "resolved"),
    ).group_by(IncidentAlert.incident_type)

    by_type = {}
    for r in by_type_q.all():
        key = (r.incident_type or "unknown").strip().lower()
        by_type[key] = {
            "total": int(r.total or 0),
            "active": int(r.active or 0),
            "resolved": int(r.resolved or 0),
        }

    return {
        "date": str(target_date),
        "filters": {
            "incident_type": incident_type,
            "camera_name": camera_name,
            "object_type": object_type,
        },
        "summary": summary,
        "by_type": by_type,
    }


# from sqlalchemy.orm import Session
# from datetime import datetime
# from app.models.incident import IncidentAlert


# def _auto_resolve_previous_crowd(db: Session, camera_name: str, zone_name: str):
#     # resolve all previous ACTIVE crowd alerts for same camera + zone
#     (
#         db.query(IncidentAlert)
#         .filter(IncidentAlert.incident_type == "crowd")
#         .filter(IncidentAlert.camera_name == camera_name)
#         .filter(IncidentAlert.zone_name == zone_name)
#         .filter(IncidentAlert.alert_status == "active")
#         .update(
#             {
#                 IncidentAlert.alert_status: "resolved",
#                 IncidentAlert.resolved_at: datetime.utcnow(),
#             },
#             synchronize_session=False,
#         )
#     )


# def create_incident_alert(
#     db: Session,
#     incident_type: str,
#     zone_name: str,
#     camera_name: str,
#     image_base64: str,
#     person_count: int | None = None,
#     max_count: int | None = None,
#     object_type: str | None = None,
# ):
#     incident_type = (incident_type or "crowd").strip().lower()
#     zone_name = (zone_name or "").strip()
#     camera_name = (camera_name or "").strip()

#     # ✅ crowd = people only
#     if incident_type == "crowd":
#         _auto_resolve_previous_crowd(
#             db, camera_name=camera_name, zone_name=zone_name)

#         mc = max_count if max_count is not None else 20
#         pc = person_count if person_count is not None else 0

#         if pc > mc:
#             message = f"Crowd density exceeds limit ({mc} people) in {zone_name}"
#         else:
#             message = f"Crowd count normal in {zone_name}"

#         row = IncidentAlert(
#             incident_type="crowd",
#             object_type="people",  # ✅ force people
#             zone_name=zone_name,
#             camera_name=camera_name,
#             person_count=pc,
#             max_count=mc,
#             image_base64=image_base64,
#             message=message,
#             alert_status="active",
#             resolved_at=None,
#         )

#     else:
#         # ✅ non-crowd = no person_count/max_count
#         if incident_type == "unauthorized":
#             msg = f"Unauthorized entry detected in {zone_name}"
#         elif incident_type == "door_open":
#             msg = f"Door opened in {zone_name}"
#         elif incident_type == "door_close":
#             msg = f"Door closed in {zone_name}"
#         elif incident_type == "vehicle_unauthorized":
#             msg = f"Unauthorized vehicle detected in {zone_name}"
#         else:
#             msg = f"Incident detected in {zone_name}"

#         row = IncidentAlert(
#             incident_type=incident_type,
#             object_type=object_type,  # optional
#             zone_name=zone_name,
#             camera_name=camera_name,
#             person_count=None,
#             max_count=None,
#             image_base64=image_base64,
#             message=msg,
#             alert_status="active",
#             resolved_at=None,
#         )

#     db.add(row)
#     db.commit()
#     db.refresh(row)
#     return row


# def list_incident_alerts(
#     db: Session,
#     incident_type: str = "all",
#     status: str = "all",
#     camera_name: str | None = None,
#     object_type: str | None = None,
#     limit: int = 500,
# ):
#     q = db.query(IncidentAlert).order_by(IncidentAlert.timestamp.desc())

#     if incident_type and incident_type != "all":
#         q = q.filter(IncidentAlert.incident_type == incident_type)

#     if status and status != "all":
#         q = q.filter(IncidentAlert.alert_status == status)

#     if camera_name:
#         q = q.filter(IncidentAlert.camera_name == camera_name)

#     if object_type:
#         q = q.filter(IncidentAlert.object_type == object_type)

#     return q.limit(limit).all()


# def resolve_incident_alert(db: Session, alert_id: int):
#     row = db.query(IncidentAlert).filter(
#         IncidentAlert.alert_id == alert_id).first()
#     if not row:
#         return None

#     row.alert_status = "resolved"
#     row.resolved_at = datetime.utcnow()
#     db.commit()
#     db.refresh(row)
#     return row


# def get_incident_filters(db: Session):
#     cameras = [
#         r[0] for r in db.query(IncidentAlert.camera_name).distinct().order_by(IncidentAlert.camera_name).all()
#         if r and r[0]
#     ]
#     incident_types = [
#         r[0] for r in db.query(IncidentAlert.incident_type).distinct().order_by(IncidentAlert.incident_type).all()
#         if r and r[0]
#     ]
#     object_types = [
#         r[0] for r in db.query(IncidentAlert.object_type).distinct().order_by(IncidentAlert.object_type).all()
#         if r and r[0]
#     ]
#     return {"cameras": cameras, "incident_types": incident_types, "object_types": object_types}
