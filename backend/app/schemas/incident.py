from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal, Optional

IncidentType = Literal["crowd", "unauthorized"]


class IncidentAlertCreate(BaseModel):
    incident_type: IncidentType = "crowd"
    zone_name: str
    camera_name: str

    # optional for unauthorized
    person_count: Optional[int] = Field(default=None, ge=0)
    max_count: Optional[int] = Field(default=None, ge=0)

    image_base64: str


class IncidentAlertOut(BaseModel):
    alert_id: int
    incident_type: IncidentType
    zone_name: str
    camera_name: str

    person_count: Optional[int]
    max_count: Optional[int]

    timestamp: datetime
    image_base64: str
    message: str

    class Config:
        from_attributes = True
