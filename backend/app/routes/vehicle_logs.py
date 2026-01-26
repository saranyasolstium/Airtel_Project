from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List

from app.database import get_db
from app.crud import vehicle as vehicle_crud

router = APIRouter(prefix="/vehicle-logs", tags=["Vehicle Logs"])


class VehicleLogCreate(BaseModel):
    plate_text: str = Field(..., min_length=1)

    entry_time: Optional[str] = None
    exit_time: Optional[str] = None

    location: Optional[str] = None

    # ✅ new fields (will show in Swagger)
    capture_image_entry: Optional[str] = None
    capture_image_exit: Optional[str] = None

    entry_camera_name: Optional[str] = None
    exit_camera_name: Optional[str] = None

    event_type: Optional[str] = Field(default=None, alias="type")
    object_classification: Optional[str] = None

    class Config:
        populate_by_name = True


class VehicleLogOut(BaseModel):
    id: int
    plate_text: str

    entry_time: Optional[str] = None
    exit_time: Optional[str] = None

    dwell_time: Optional[str] = None
    dwell_seconds: Optional[int] = None

    location: Optional[str] = None
    status: Optional[str] = None

    capture_image_entry: Optional[str] = None
    capture_image_exit: Optional[str] = None

    entry_camera_name: Optional[str] = None
    exit_camera_name: Optional[str] = None

    event_type: Optional[str] = Field(default=None, alias="type")
    object_classification: Optional[str] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class VehicleLogListOut(BaseModel):
    items: List[VehicleLogOut]
    total: int
    limit: int
    offset: int


@router.post("/", response_model=VehicleLogOut)
def push_vehicle_log(payload: VehicleLogCreate, db: Session = Depends(get_db)):
    try:
        obj = vehicle_crud.upsert_vehicle_log_by_plate(
            db, payload.model_dump(by_alias=True)
        )
        return obj
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=VehicleLogListOut)
def get_vehicle_logs(
    search: Optional[str] = Query(default=None),
    date_from: Optional[str] = Query(default=None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(default=None, description="YYYY-MM-DD"),
    limit: int = Query(default=200, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    # if only one date provided, treat it as same-day range
    if date_from and not date_to:
        date_to = date_from
    if date_to and not date_from:
        date_from = date_to

    items = vehicle_crud.list_vehicle_logs(
        db,
        search=search,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
    total = vehicle_crud.count_vehicle_logs(
        db, search=search, date_from=date_from, date_to=date_to
    )
    return {"items": items, "total": total, "limit": limit, "offset": offset}


# from fastapi import APIRouter, Depends, HTTPException, Query
# from sqlalchemy.orm import Session
# from pydantic import BaseModel, Field
# from typing import Optional, List

# from app.database import get_db
# from app.crud import vehicle as vehicle_crud

# router = APIRouter(prefix="/vehicle-logs", tags=["Vehicle Logs"])


# class VehicleEntryIn(BaseModel):
#     plate_text: str = Field(..., min_length=1)
#     entry_time: str = Field(..., min_length=5)

#     location: Optional[str] = None
#     camera_name: Optional[str] = None
#     event_type: Optional[str] = Field(default=None, alias="type")
#     object_classification: Optional[str] = None
#     capture_image: Optional[str] = None  # entry image

#     class Config:
#         populate_by_name = True


# class VehicleExitIn(BaseModel):
#     plate_text: str = Field(..., min_length=1)
#     exit_time: str = Field(..., min_length=5)

#     # optional: if you want fallback create exit-only row
#     entry_time: Optional[str] = None

#     location: Optional[str] = None
#     camera_name: Optional[str] = None
#     event_type: Optional[str] = Field(default=None, alias="type")
#     object_classification: Optional[str] = None
#     capture_image: Optional[str] = None  # exit image

#     class Config:
#         populate_by_name = True


# class VehicleLogOut(BaseModel):
#     id: int
#     plate_text: str
#     entry_time: Optional[str] = None
#     exit_time: Optional[str] = None
#     dwell_time: Optional[str] = None
#     dwell_seconds: Optional[int] = None
#     location: Optional[str] = None
#     status: Optional[str] = None

#     capture_image_entry: Optional[str] = None
#     capture_image_exit: Optional[str] = None

#     camera_name: Optional[str] = None
#     event_type: Optional[str] = Field(default=None, alias="type")
#     object_classification: Optional[str] = None

#     class Config:
#         from_attributes = True
#         populate_by_name = True


# class VehicleLogListOut(BaseModel):
#     items: List[VehicleLogOut]
#     total: int
#     limit: int
#     offset: int


# @router.post("/entry", response_model=VehicleLogOut)
# def post_entry(payload: VehicleEntryIn, db: Session = Depends(get_db)):
#     try:
#         return vehicle_crud.create_vehicle_entry(db, payload.model_dump(by_alias=True))
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))


# @router.post("/exit", response_model=VehicleLogOut)
# def post_exit(payload: VehicleExitIn, db: Session = Depends(get_db)):
#     try:
#         return vehicle_crud.update_vehicle_exit_by_plate(db, payload.model_dump(by_alias=True))
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))


# @router.get("/", response_model=VehicleLogListOut)
# def get_vehicle_logs(
#     search: Optional[str] = Query(default=None),
#     date_from: Optional[str] = Query(default=None, description="YYYY-MM-DD"),
#     date_to: Optional[str] = Query(default=None, description="YYYY-MM-DD"),
#     limit: int = Query(default=200, ge=1, le=1000),
#     offset: int = Query(default=0, ge=0),
#     db: Session = Depends(get_db),
# ):
#     # same-day helper
#     if date_from and not date_to:
#         date_to = date_from
#     if date_to and not date_from:
#         date_from = date_to

#     items = vehicle_crud.list_vehicle_logs(
#         db, search=search, date_from=date_from, date_to=date_to, limit=limit, offset=offset
#     )
#     total = vehicle_crud.count_vehicle_logs(db, search=search, date_from=date_from, date_to=date_to)

#     return {"items": items, "total": total, "limit": limit, "offset": offset}


# # from __future__ import annotations

# # from fastapi import APIRouter, Depends, HTTPException, Query
# # from sqlalchemy.orm import Session
# # from pydantic import BaseModel, Field
# # from typing import Optional, List

# # from app.database import get_db
# # from app.crud import vehicle as vehicle_crud

# # router = APIRouter(prefix="/vehicle-logs", tags=["Vehicle Logs"])


# # class VehicleLogCreate(BaseModel):
# #     plate_text: str = Field(..., min_length=1)

# #     entry_time: Optional[str] = None
# #     exit_time: Optional[str] = None

# #     location: Optional[str] = None

# #     # ✅ one field from AI, backend will store entry/exit separately
# #     capture_image: Optional[str] = None

# #     camera_name: Optional[str] = None
# #     event_type: Optional[str] = Field(default=None, alias="type")
# #     object_classification: Optional[str] = None

# #     class Config:
# #         populate_by_name = True


# # class VehicleLogOut(BaseModel):
# #     id: int
# #     plate_text: str
# #     entry_time: Optional[str] = None
# #     exit_time: Optional[str] = None
# #     dwell_time: Optional[str] = None
# #     dwell_seconds: Optional[int] = None
# #     location: Optional[str] = None
# #     status: Optional[str] = None

# #     capture_image_entry: Optional[str] = None
# #     capture_image_exit: Optional[str] = None

# #     camera_name: Optional[str] = None
# #     event_type: Optional[str] = Field(default=None, alias="type")
# #     object_classification: Optional[str] = None

# #     class Config:
# #         from_attributes = True
# #         populate_by_name = True


# # class VehicleLogListOut(BaseModel):
# #     items: List[VehicleLogOut]
# #     total: int
# #     limit: int
# #     offset: int


# # @router.post("/", response_model=VehicleLogOut)
# # def push_vehicle_log(payload: VehicleLogCreate, db: Session = Depends(get_db)):
# #     try:
# #         obj = vehicle_crud.upsert_vehicle_log_by_plate(
# #             db, payload.model_dump(by_alias=True)
# #         )
# #         return obj
# #     except ValueError as e:
# #         raise HTTPException(status_code=400, detail=str(e))
# #     except Exception as e:
# #         # ✅ see real error in response (remove in prod)
# #         raise HTTPException(status_code=500, detail=f"Server error: {e}")


# # @router.get("/", response_model=VehicleLogListOut)
# # def get_vehicle_logs(
# #     search: Optional[str] = Query(default=None),
# #     date_from: Optional[str] = Query(default=None, description="YYYY-MM-DD"),
# #     date_to: Optional[str] = Query(default=None, description="YYYY-MM-DD"),
# #     limit: int = Query(default=200, ge=1, le=1000),
# #     offset: int = Query(default=0, ge=0),
# #     db: Session = Depends(get_db),
# # ):
# #     # ✅ normalize search: search="" should behave like None
# #     if search is not None:
# #         search = search.strip() or None

# #     # if only one date provided, treat it as same-day range
# #     if date_from and not date_to:
# #         date_to = date_from
# #     if date_to and not date_from:
# #         date_from = date_to

# #     items = vehicle_crud.list_vehicle_logs(
# #         db,
# #         search=search,
# #         date_from=date_from,
# #         date_to=date_to,
# #         limit=limit,
# #         offset=offset,
# #     )
# #     total = vehicle_crud.count_vehicle_logs(
# #         db, search=search, date_from=date_from, date_to=date_to
# #     )

# #     return {"items": items, "total": total, "limit": limit, "offset": offset}



