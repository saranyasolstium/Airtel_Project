
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.models.base import Base


class VehicleLog(Base):
    __tablename__ = "vehicle_logs"

    id = Column(Integer, primary_key=True, index=True)

    plate_text = Column(String(64), nullable=False, index=True)

    entry_time = Column(String(32), nullable=True)
    exit_time = Column(String(32), nullable=True)

    dwell_time = Column(String(32), nullable=True)
    dwell_seconds = Column(Integer, nullable=True)

    location = Column(String(128), nullable=True)

    status = Column(String(32), nullable=True, default="on_site")

    # ✅ updated columns
    capture_image_entry = Column(Text, nullable=True)  # LONGTEXT in MySQL
    capture_image_exit = Column(Text, nullable=True)   # LONGTEXT in MySQL

    # ✅ entry/exit camera columns
    entry_camera_name = Column(String(120), nullable=True)
    exit_camera_name = Column(String(120), nullable=True)

    # DB column name is `type` but python attribute is event_type
    event_type = Column("type", String(50), nullable=True)

    object_classification = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


# from sqlalchemy import Column, Integer, String, Text, DateTime
# from sqlalchemy.sql import func
# from app.models.base import Base


# class VehicleLog(Base):
#     __tablename__ = "vehicle_logs"

#     id = Column(Integer, primary_key=True, index=True)

#     plate_text = Column(String(64), nullable=False, index=True)

#     entry_time = Column(String(32), nullable=True)
#     exit_time = Column(String(32), nullable=True)

#     dwell_time = Column(String(32), nullable=True)
#     dwell_seconds = Column(Integer, nullable=True)

#     location = Column(String(128), nullable=True)

#     # status will be set automatically in CRUD based on exit_time
#     status = Column(String(32), nullable=True, default="on_site")

#     # IMPORTANT: in MySQL set this column to LONGTEXT if storing big base64
#     capture_image = Column(Text, nullable=True)

#     camera_name = Column(String(120), nullable=True)

#     # DB column name is `type` but python attribute is event_type
#     event_type = Column("type", String(50), nullable=True)

#     object_classification = Column(String(255), nullable=True)

#     created_at = Column(DateTime(timezone=True), server_default=func.now())
