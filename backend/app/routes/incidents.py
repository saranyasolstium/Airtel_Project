from __future__ import annotations

from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.incident import IncidentAlertCreate, IncidentAlertOut
from app.crud.incident import (
    create_incident_alert,
    list_incident_alerts,
    resolve_incident_alert,
    get_incident_filters,
    get_alert_counts,
)

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.post("/alerts", response_model=IncidentAlertOut)
def create_alert(body: IncidentAlertCreate, db: Session = Depends(get_db)):
    return create_incident_alert(
        db=db,
        incident_type=body.incident_type,
        zone_name=body.zone_name,
        camera_name=body.camera_name,
        image_base64=body.image_base64,
        person_count=body.person_count,
        max_count=body.max_count,
        object_type=body.object_type,
    )


@router.get("/alerts", response_model=list[IncidentAlertOut])
def get_alerts(
    db: Session = Depends(get_db),
    incident_type: str = Query("all"),
    status: str = Query("active"),  # default ONLY active
    camera_name: str = Query("", description="optional"),
    object_type: str = Query("", description="optional"),
):
    return list_incident_alerts(
        db=db,
        incident_type=incident_type,
        status=status,
        camera_name=camera_name or None,
        object_type=object_type or None,
    )


@router.get("/alerts/filters")
def filters(db: Session = Depends(get_db)):
    return get_incident_filters(db)


@router.put("/alerts/{alert_id}/resolve", response_model=IncidentAlertOut)
def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
    row = resolve_incident_alert(db, alert_id)
    if not row:
        raise HTTPException(404, "Alert not found")
    return row


# ✅ NEW: STATS
@router.get("/alerts/stats")
def alerts_stats(
    db: Session = Depends(get_db),
    incident_type: str = Query("all"),
    camera_name: str = Query(""),
    object_type: str = Query(""),
    date: date | None = Query(
        None, description="YYYY-MM-DD. If not passed → today"),
):
    return get_alert_counts(
        db=db,
        incident_type=incident_type,
        camera_name=camera_name or None,
        object_type=object_type or None,
        target_date=date,
    )


# from fastapi import APIRouter, Depends, Query, HTTPException
# from sqlalchemy.orm import Session

# from app.database import get_db
# from app.schemas.incident import IncidentAlertCreate, IncidentAlertOut
# from app.crud.incident import (
#     create_incident_alert,
#     list_incident_alerts,
#     resolve_incident_alert,
#     get_incident_filters,
# )

# router = APIRouter(prefix="/incidents", tags=["Incidents"])


# @router.post("/alerts", response_model=IncidentAlertOut)
# def create_alert(body: IncidentAlertCreate, db: Session = Depends(get_db)):
#     return create_incident_alert(
#         db=db,
#         incident_type=body.incident_type,
#         zone_name=body.zone_name,
#         camera_name=body.camera_name,
#         image_base64=body.image_base64,
#         person_count=body.person_count,
#         max_count=body.max_count,
#         object_type=body.object_type,
#     )


# @router.get("/alerts", response_model=list[IncidentAlertOut])
# def get_alerts(
#     db: Session = Depends(get_db),
#     incident_type: str = Query("all"),
#     status: str = Query("active"),  # default ONLY active
#     camera_name: str = Query("", description="optional"),
#     object_type: str = Query("", description="optional"),
# ):
#     return list_incident_alerts(
#         db=db,
#         incident_type=incident_type,
#         status=status,
#         camera_name=camera_name or None,
#         object_type=object_type or None,
#     )


# @router.get("/alerts/filters")
# def filters(db: Session = Depends(get_db)):
#     return get_incident_filters(db)


# @router.put("/alerts/{alert_id}/resolve", response_model=IncidentAlertOut)
# def resolve_alert(alert_id: int, db: Session = Depends(get_db)):
#     row = resolve_incident_alert(db, alert_id)
#     if not row:
#         raise HTTPException(404, "Alert not found")
#     return row
