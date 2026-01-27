from sqlalchemy import Column, Integer, String, Date, Enum, DateTime
from sqlalchemy.sql import func

from app.models.base import Base


class VehicleWhitelist(Base):
    __tablename__ = "vehicle_whitelist"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(120), nullable=False)

    # NOT unique — expired or future entries allowed
    vehicle_number = Column(String(40), nullable=False, index=True)

    vehicle_type = Column(String(40), nullable=False)
    purpose = Column(String(255), nullable=True)

    from_date = Column(Date, nullable=False)
    to_date = Column(Date, nullable=False)

    status = Column(
        Enum("approved", "blocked", "expired",
             name="vehicle_whitelist_status"),
        nullable=False,
        default="approved",
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
