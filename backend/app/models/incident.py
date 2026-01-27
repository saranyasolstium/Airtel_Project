from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.dialects.mysql import LONGTEXT
from app.database import Base


class IncidentAlert(Base):
    __tablename__ = "incident_alerts"

    alert_id = Column(Integer, primary_key=True, index=True)

    # crowd / unauthorized / door_open / door_close / vehicle_unauthorized ...
    incident_type = Column(String(30), nullable=False, default="crowd")

    # optional extra label (people/door/vehicle etc)
    object_type = Column(String(30), nullable=True)

    zone_name = Column(String(100), nullable=False)
    camera_name = Column(String(100), nullable=False)

    # crowd only
    person_count = Column(Integer, nullable=True)
    max_count = Column(Integer, nullable=True)

    timestamp = Column(DateTime(timezone=True),
                       server_default=func.now(), nullable=False)

    image_base64 = Column(LONGTEXT, nullable=False)
    message = Column(String(255), nullable=False)

    # ✅ status
    alert_status = Column(String(20), nullable=False,
                          default="active")  # active/resolved
    resolved_at = Column(DateTime(timezone=True), nullable=True)
