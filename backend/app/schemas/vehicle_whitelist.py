from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class WhitelistCreate(BaseModel):
    name: str
    vehicle_number: str
    vehicle_type: str
    purpose: Optional[str] = None
    from_date: date
    to_date: date
    status: str = "approved"


class WhitelistUpdate(BaseModel):
    name: Optional[str] = None
    vehicle_type: Optional[str] = None
    purpose: Optional[str] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    status: Optional[str] = None


class WhitelistOut(BaseModel):
    id: int
    name: str
    vehicle_number: str
    vehicle_type: str
    purpose: Optional[str]
    from_date: date
    to_date: date
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
