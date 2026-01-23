from pydantic import BaseModel, Field
from datetime import datetime


class CrowdAlertCreate(BaseModel):
    zone_name: str
    camera_name: str

    person_count: int = Field(..., ge=0)

    # REQUIRED
    image_base64: str

    # optional override; default 20
    max_count: int | None = None


class CrowdAlertOut(BaseModel):
    alert_id: int
    zone_name: str
    camera_name: str
    person_count: int
    max_count: int
    timestamp: datetime
    image_base64: str
    message: str

    class Config:
        from_attributes = True
