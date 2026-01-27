from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class IncidentAlertCreate(BaseModel):
    incident_type: str = "crowd"
    object_type: Optional[str] = None
    zone_name: str
    camera_name: str

    # only for crowd
    person_count: Optional[int] = Field(default=None, ge=0)
    max_count: Optional[int] = Field(default=None, ge=0)

    image_base64: str


class IncidentAlertOut(BaseModel):
    alert_id: int
    incident_type: str
    object_type: Optional[str] = None
    zone_name: str
    camera_name: str

    person_count: Optional[int] = None
    max_count: Optional[int] = None

    timestamp: datetime
    image_base64: str
    message: str

    alert_status: str
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True
