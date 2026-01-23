from sqlalchemy.orm import Session
from app.models.crowd import CrowdAlert


def create_crowd_alert(
    db: Session,
    zone_name: str,
    camera_name: str,
    person_count: int,
    max_count: int,
    image_base64: str,
):
    if person_count > max_count:
        message = f"Crowd density exceeds limit ({max_count} people) in {zone_name}"
    else:
        message = f"Crowd count normal in {zone_name}"

    row = CrowdAlert(
        zone_name=zone_name,
        camera_name=camera_name,
        person_count=person_count,
        max_count=max_count,
        image_base64=image_base64,
        message=message,
    )

    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_crowd_alerts(db: Session):
    # ✅ No limit param in API, but we keep safe default here (latest 200)
    return (
        db.query(CrowdAlert)
        .order_by(CrowdAlert.timestamp.desc())
        .limit(200)
        .all()
    )

    # If you REALLY want all rows, replace above with:
    # return db.query(CrowdAlert).order_by(CrowdAlert.timestamp.desc()).all()
