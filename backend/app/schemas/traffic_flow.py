from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TrafficFlowVehicleItem(BaseModel):
    id: int
    plate_text: str

    title_text: str
    location_text: str
    dwell_text: str

    dwell_seconds: int
    limit_seconds: int
    is_alert: bool
    severity: str
    status: str

    # ✅ NEW (if you have these in DB/model)
    entry_camera_name: Optional[str] = None
    exit_camera_name: Optional[str] = None

    # keep for compatibility
    camera_name: Optional[str] = None

    object_classification: Optional[str] = None
    entry_time: Optional[str] = None
    exit_time: Optional[str] = None
    created_at: Optional[datetime] = None


class TrafficFlowVehiclesResponse(BaseModel):
    total: int
    limit: int
    offset: int
    date: str
    dwell_limit_seconds: int
    data: List[TrafficFlowVehicleItem]


# from pydantic import BaseModel
# from typing import Optional, List
# from datetime import datetime


# class TrafficFlowVehicleItem(BaseModel):
#     id: int
#     plate_text: str

#     title_text: str
#     location_text: str
#     dwell_text: str

#     dwell_seconds: int
#     limit_seconds: int
#     is_alert: bool
#     severity: str
#     status: str

#     camera_name: Optional[str] = None
#     object_classification: Optional[str] = None
#     entry_time: Optional[str] = None
#     exit_time: Optional[str] = None
#     created_at: Optional[datetime] = None


# class TrafficFlowVehiclesResponse(BaseModel):
#     total: int
#     limit: int
#     offset: int
#     date: str
#     dwell_limit_seconds: int
#     data: List[TrafficFlowVehicleItem]
