from pydantic import BaseModel, field_validator
from typing import Optional, Literal
from datetime import date, datetime

WhitelistStatus = Literal["approved", "blocked", "expired"]


class WhitelistCreate(BaseModel):
    name: str
    vehicle_number: str
    vehicle_type: str
    purpose: Optional[str] = None
    from_date: date
    to_date: date
    status: WhitelistStatus = "approved"

    @field_validator("to_date")
    @classmethod
    def validate_date_range(cls, v, info):
        from_date = info.data.get("from_date")
        if from_date and v < from_date:
            raise ValueError("to_date cannot be before from_date")
        return v


class WhitelistUpdate(BaseModel):
    name: Optional[str] = None
    vehicle_number: Optional[str] = None
    vehicle_type: Optional[str] = None
    purpose: Optional[str] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    status: Optional[WhitelistStatus] = None

    @field_validator("to_date")
    @classmethod
    def validate_date_range(cls, v, info):
        from_date = info.data.get("from_date")
        if from_date and v and v < from_date:
            raise ValueError("to_date cannot be before from_date")
        return v


class WhitelistOut(BaseModel):
    id: int
    name: str
    vehicle_number: str
    vehicle_type: str
    purpose: Optional[str]
    from_date: date
    to_date: date
    status: WhitelistStatus
    created_at: datetime

    class Config:
        from_attributes = True
