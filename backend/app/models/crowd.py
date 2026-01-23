from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.dialects.mysql import LONGTEXT

from app.database import Base


class CrowdAlert(Base):
    __tablename__ = "crowd_alerts"

    alert_id = Column(Integer, primary_key=True, index=True)

    zone_name = Column(String(100), nullable=False)
    camera_name = Column(String(100), nullable=False)

    person_count = Column(Integer, nullable=False)

    # default max count (20)
    max_count = Column(Integer, nullable=False, default=20)

    timestamp = Column(DateTime(timezone=True),
                       server_default=func.now(), nullable=False)

    # MUST be LONGTEXT for large base64
    image_base64 = Column(LONGTEXT, nullable=False)

    message = Column(String(255), nullable=False)
