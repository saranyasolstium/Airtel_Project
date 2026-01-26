from sqlalchemy.orm import Session
from datetime import date

from app.models.vehicle_whitelist import VehicleWhitelist
from app.schemas.vehicle_whitelist import WhitelistCreate, WhitelistUpdate


def create_whitelist(db: Session, data: WhitelistCreate):
    obj = VehicleWhitelist(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def list_whitelist(db: Session):
    return db.query(VehicleWhitelist).order_by(VehicleWhitelist.id.desc()).all()


def update_whitelist(db: Session, row_id: int, data: WhitelistUpdate):
    obj = db.query(VehicleWhitelist).filter(
        VehicleWhitelist.id == row_id
    ).first()

    if not obj:
        return None

    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)

    db.commit()
    db.refresh(obj)
    return obj


def toggle_status(db: Session, row_id: int, status: str):
    obj = db.query(VehicleWhitelist).filter(
        VehicleWhitelist.id == row_id
    ).first()

    if not obj:
        return None

    obj.status = status
    db.commit()
    db.refresh(obj)
    return obj


def get_active_for_vehicle(db: Session, vehicle_number: str, today: date):
    return (
        db.query(VehicleWhitelist)
        .filter(VehicleWhitelist.vehicle_number == vehicle_number)
        .filter(VehicleWhitelist.from_date <= today)
        .filter(VehicleWhitelist.to_date >= today)
        .filter(VehicleWhitelist.status == "approved")
        .first()
    )
