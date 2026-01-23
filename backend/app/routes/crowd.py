from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.crowd import CrowdAlertCreate, CrowdAlertOut
from app.crud.crowd import create_crowd_alert, list_crowd_alerts

router = APIRouter(prefix="/crowd", tags=["Crowd"])


@router.post("/alerts", response_model=CrowdAlertOut)
def create_alert(body: CrowdAlertCreate, db: Session = Depends(get_db)):
    max_count = body.max_count or 20

    return create_crowd_alert(
        db=db,
        zone_name=body.zone_name,
        camera_name=body.camera_name,
        person_count=body.person_count,
        max_count=max_count,
        image_base64=body.image_base64,
    )


@router.get("/alerts", response_model=list[CrowdAlertOut])
def get_alerts(db: Session = Depends(get_db)):
    # ✅ no limit query param
    return list_crowd_alerts(db=db)
