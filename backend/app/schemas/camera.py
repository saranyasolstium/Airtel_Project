# app/schemas/camera.py
from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Literal

from pydantic import BaseModel, ConfigDict, Field


class CameraBase(BaseModel):
    name: str
    rtsp_url: Optional[str] = None


class CameraCreate(CameraBase):
    camera_id: str


class CameraUpdate(BaseModel):
    # ✅ allow editing camera_id also
    camera_id: Optional[str] = None
    name: Optional[str] = None
    rtsp_url: Optional[str] = None


class CameraOut(BaseModel):
    id: int
    camera_id: str
    name: str
    rtsp_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    location: Optional[str] = None
    status: Literal["online", "warning", "offline"] = "offline"
    health: int = Field(default=0, ge=0, le=100)

    model_config = ConfigDict(from_attributes=True)


class CameraListResponse(BaseModel):
    items: List[CameraOut]
    total: int
    page: int
    size: int
    pages: int
    has_more: bool
