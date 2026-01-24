from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.dialects.mysql import LONGTEXT
from app.database import Base


class IncidentAlert(Base):
    __tablename__ = "incident_alerts"  # ✅ one table for all incidents

    alert_id = Column(Integer, primary_key=True, index=True)

    # crowd / unauthorized
    incident_type = Column(String(30), nullable=False, default="crowd")

    zone_name = Column(String(100), nullable=False)
    camera_name = Column(String(100), nullable=False)

    # ✅ optional values (only for crowd)
    person_count = Column(Integer, nullable=True)
    max_count = Column(Integer, nullable=True)

    timestamp = Column(DateTime(timezone=True),
                       server_default=func.now(), nullable=False)

    image_base64 = Column(LONGTEXT, nullable=False)

    message = Column(String(255), nullable=False)
