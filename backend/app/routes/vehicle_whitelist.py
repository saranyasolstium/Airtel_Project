from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date

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
)

router = APIRouter(
    prefix="/vehicle-whitelist",
    tags=["Vehicle Whitelist"],
)


@router.post("/", response_model=WhitelistOut)
def add_vehicle(payload: WhitelistCreate, db: Session = Depends(get_db)):
    return create_whitelist(db, payload)


@router.get("/", response_model=list[WhitelistOut])
def get_all(db: Session = Depends(get_db)):
    return list_whitelist(db)


@router.put("/{row_id}", response_model=WhitelistOut)
def update_vehicle(
    row_id: int,
    payload: WhitelistUpdate,
    db: Session = Depends(get_db),
):
    obj = update_whitelist(db, row_id, payload)
    if not obj:
        raise HTTPException(404, "Vehicle not found")
    return obj


@router.put("/{row_id}/status/{status}", response_model=WhitelistOut)
def change_status(
    row_id: int,
    status: str,
    db: Session = Depends(get_db),
):
    if status not in ("approved", "blocked"):
        raise HTTPException(400, "Invalid status")

    obj = toggle_status(db, row_id, status)
    if not obj:
        raise HTTPException(404, "Vehicle not found")

    return obj
