from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.incident import IncidentAlertCreate, IncidentAlertOut
from app.crud.incident import create_incident_alert, list_incident_alerts

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
    )


@router.get("/alerts", response_model=list[IncidentAlertOut])
def get_alerts(
    db: Session = Depends(get_db),
    incident_type: str = Query(
        "all", description="all | crowd | unauthorized"),
):
    return list_incident_alerts(db=db, incident_type=incident_type)
