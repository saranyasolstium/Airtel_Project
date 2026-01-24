from sqlalchemy.orm import Session
from app.models.incident import IncidentAlert


def create_incident_alert(
    db: Session,
    incident_type: str,
    zone_name: str,
    camera_name: str,
    image_base64: str,
    person_count: int | None = None,
    max_count: int | None = None,
):
    # message logic based on type
    if incident_type == "crowd":
        mc = max_count if max_count is not None else 20
        pc = person_count if person_count is not None else 0

        if pc > mc:
            message = f"Crowd density exceeds limit ({mc} people) in {zone_name}"
        else:
            message = f"Crowd count normal in {zone_name}"

        row = IncidentAlert(
            incident_type="crowd",
            zone_name=zone_name,
            camera_name=camera_name,
            person_count=pc,
            max_count=mc,
            image_base64=image_base64,
            message=message,
        )

    else:
        # unauthorized
        message = f"Unauthorized entry detected in {zone_name}"
        row = IncidentAlert(
            incident_type="unauthorized",
            zone_name=zone_name,
            camera_name=camera_name,
            person_count=None,
            max_count=None,
            image_base64=image_base64,
            message=message,
        )

    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_incident_alerts(db: Session, incident_type: str | None = None):
    q = db.query(IncidentAlert).order_by(IncidentAlert.timestamp.desc())

    if incident_type and incident_type != "all":
        q = q.filter(IncidentAlert.incident_type == incident_type)

    return q.limit(200).all()
