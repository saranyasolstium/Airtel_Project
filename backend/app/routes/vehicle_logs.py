from __future__ import annotations

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
    status: Optional[str] = None

    capture_image: Optional[str] = None

    camera_name: Optional[str] = None
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
    capture_image: Optional[str] = None

    camera_name: Optional[str] = None
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
        obj = vehicle_crud.create_vehicle_log(
            db, payload.model_dump(by_alias=True))
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
        db, search=search, date_from=date_from, date_to=date_to)

    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.get("/{log_id}", response_model=VehicleLogOut)
def get_one_vehicle_log(log_id: int, db: Session = Depends(get_db)):
    obj = vehicle_crud.get_vehicle_log(db, log_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Vehicle log not found")
    return obj


class VehicleExitUpdate(BaseModel):
    exit_time: str = Field(..., min_length=5)


@router.put("/{log_id}/exit", response_model=VehicleLogOut)
def mark_exit(log_id: int, payload: VehicleExitUpdate, db: Session = Depends(get_db)):
    obj = vehicle_crud.update_vehicle_exit(db, log_id, payload.exit_time)
    if not obj:
        raise HTTPException(status_code=404, detail="Vehicle log not found")
    return obj


@router.delete("/{log_id}")
def delete_vehicle_log(log_id: int, db: Session = Depends(get_db)):
    ok = vehicle_crud.delete_vehicle_log(db, log_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Vehicle log not found")
    return {"success": True}


# from __future__ import annotations

# from fastapi import APIRouter, Depends, HTTPException, Query
# from sqlalchemy.orm import Session
# from pydantic import BaseModel, Field
# from typing import Optional, List

# from app.database import get_db
# from app.crud import vehicle as vehicle_crud

# router = APIRouter(prefix="/vehicle-logs", tags=["Vehicle Logs"])


# class VehicleLogCreate(BaseModel):
#     plate_text: str = Field(..., min_length=1)

#     entry_time: Optional[str] = None
#     exit_time: Optional[str] = None

#     location: Optional[str] = None
#     capture_image: Optional[str] = None

#     camera_name: Optional[str] = None

#     # accept JSON "type"
#     event_type: Optional[str] = Field(default=None, alias="type")

#     object_classification: Optional[str] = None

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

#     capture_image: Optional[str] = None
#     camera_name: Optional[str] = None

#     event_type: Optional[str] = Field(default=None, alias="type")
#     object_classification: Optional[str] = None

#     class Config:
#         from_attributes = True
#         populate_by_name = True


# class VehicleLogListOut(BaseModel):
#     items: List[VehicleLogOut]
#     total: int


# @router.post("/", response_model=VehicleLogOut)
# def push_vehicle_log(payload: VehicleLogCreate, db: Session = Depends(get_db)):
#     try:
#         obj = vehicle_crud.create_vehicle_log(db, payload.dict(by_alias=True))
#         return obj
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))


# @router.get("/", response_model=VehicleLogListOut)
# def get_vehicle_logs(
#     search: Optional[str] = Query(default=None),
#     limit: int = Query(default=200, ge=1, le=1000),
#     offset: int = Query(default=0, ge=0),
#     db: Session = Depends(get_db),
# ):
#     items = vehicle_crud.list_vehicle_logs(
#         db, search=search, limit=limit, offset=offset)
#     return {"items": items, "total": len(items)}


# @router.get("/{log_id}", response_model=VehicleLogOut)
# def get_one_vehicle_log(log_id: int, db: Session = Depends(get_db)):
#     obj = vehicle_crud.get_vehicle_log(db, log_id)
#     if not obj:
#         raise HTTPException(status_code=404, detail="Vehicle log not found")
#     return obj


# class VehicleExitUpdate(BaseModel):
#     exit_time: str = Field(..., min_length=5)


# @router.put("/{log_id}/exit", response_model=VehicleLogOut)
# def mark_exit(log_id: int, payload: VehicleExitUpdate, db: Session = Depends(get_db)):
#     obj = vehicle_crud.update_vehicle_exit(db, log_id, payload.exit_time)
#     if not obj:
#         raise HTTPException(status_code=404, detail="Vehicle log not found")
#     return obj


# @router.delete("/{log_id}")
# def delete_vehicle_log(log_id: int, db: Session = Depends(get_db)):
#     ok = vehicle_crud.delete_vehicle_log(db, log_id)
#     if not ok:
#         raise HTTPException(status_code=404, detail="Vehicle log not found")
#     return {"success": True}
