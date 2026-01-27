from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.vehicle_whitelist import (
    WhitelistCreate,
    WhitelistUpdate,
    WhitelistOut,
)
from app.crud.vehicle_whitelist import (
    create_whitelist,
    list_whitelist,
    update_whitelist,
    toggle_status,
    delete_whitelist,
)

router = APIRouter(
    prefix="/vehicle-whitelist",
    tags=["Vehicle Whitelist"],
)


@router.post("/", response_model=WhitelistOut)
def add_vehicle(payload: WhitelistCreate, db: Session = Depends(get_db)):
    try:
        return create_whitelist(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/", response_model=list[WhitelistOut])
def get_all(db: Session = Depends(get_db)):
    return list_whitelist(db)


@router.put("/{row_id}", response_model=WhitelistOut)
def update_vehicle(
    row_id: int,
    payload: WhitelistUpdate,
    db: Session = Depends(get_db),
):
    try:
        obj = update_whitelist(db, row_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    if not obj:
        raise HTTPException(404, "Vehicle not found")

    return obj


@router.put("/{row_id}/status/{status}", response_model=WhitelistOut)
def change_status(row_id: int, status: str, db: Session = Depends(get_db)):
    if status not in ("approved", "blocked", "expired"):
        raise HTTPException(400, "Invalid status")

    try:
        obj = toggle_status(db, row_id, status)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    if not obj:
        raise HTTPException(404, "Vehicle not found")

    return obj


@router.delete("/{row_id}")
def delete_vehicle(row_id: int, db: Session = Depends(get_db)):
    ok = delete_whitelist(db, row_id)
    if not ok:
        raise HTTPException(404, "Vehicle not found")

    return {"ok": True, "message": "Deleted successfully"}
