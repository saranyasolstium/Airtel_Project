from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import date

from app.models.vehicle_whitelist import VehicleWhitelist
from app.schemas.vehicle_whitelist import WhitelistCreate, WhitelistUpdate


# --------------------------------------------------
# Auto-expire helper
# --------------------------------------------------
def mark_expired(db: Session, today: date) -> int:
    q = (
        db.query(VehicleWhitelist)
        .filter(VehicleWhitelist.to_date < today)
        .filter(VehicleWhitelist.status != "expired")
    )

    count = q.count()
    if count:
        q.update({VehicleWhitelist.status: "expired"},
                 synchronize_session=False)
        db.commit()

    return count


# --------------------------------------------------
# Date overlap checker
# --------------------------------------------------
def _has_overlap(
    db: Session,
    vehicle_number: str,
    from_date: date,
    to_date: date,
    exclude_id: int | None = None,
) -> bool:
    q = (
        db.query(VehicleWhitelist)
        .filter(VehicleWhitelist.vehicle_number == vehicle_number)
        .filter(VehicleWhitelist.status.in_(["approved", "blocked"]))
        .filter(
            and_(
                VehicleWhitelist.from_date <= to_date,
                VehicleWhitelist.to_date >= from_date,
            )
        )
    )

    if exclude_id:
        q = q.filter(VehicleWhitelist.id != exclude_id)

    return db.query(q.exists()).scalar()


# --------------------------------------------------
# CREATE
# --------------------------------------------------
def create_whitelist(db: Session, data: WhitelistCreate):
    today = date.today()
    mark_expired(db, today)

    if _has_overlap(db, data.vehicle_number, data.from_date, data.to_date):
        raise ValueError("Vehicle already exists for overlapping date range")

    obj = VehicleWhitelist(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


# --------------------------------------------------
# LIST
# --------------------------------------------------
def list_whitelist(db: Session):
    today = date.today()
    mark_expired(db, today)

    return db.query(VehicleWhitelist).order_by(VehicleWhitelist.id.desc()).all()


# --------------------------------------------------
# UPDATE (BLOCK if expired)
# --------------------------------------------------
def update_whitelist(db: Session, row_id: int, data: WhitelistUpdate):
    today = date.today()
    mark_expired(db, today)

    obj = db.query(VehicleWhitelist).filter(
        VehicleWhitelist.id == row_id).first()
    if not obj:
        return None

    if obj.status == "expired":
        raise ValueError(
            "Expired vehicles cannot be edited. Please add a new entry.")

    payload = data.model_dump(exclude_unset=True)

    new_vehicle_number = payload.get("vehicle_number", obj.vehicle_number)
    new_from = payload.get("from_date", obj.from_date)
    new_to = payload.get("to_date", obj.to_date)

    if new_to < new_from:
        raise ValueError("to_date cannot be before from_date")

    if _has_overlap(db, new_vehicle_number, new_from, new_to, exclude_id=obj.id):
        raise ValueError("Vehicle already exists for overlapping date range")

    for k, v in payload.items():
        setattr(obj, k, v)

    db.commit()
    db.refresh(obj)
    return obj


# --------------------------------------------------
# STATUS TOGGLE
# --------------------------------------------------
def toggle_status(db: Session, row_id: int, status: str):
    obj = db.query(VehicleWhitelist).filter(
        VehicleWhitelist.id == row_id).first()
    if not obj:
        return None

    if obj.status == "expired":
        raise ValueError(
            "Expired vehicles cannot be modified. Please add a new entry.")

    obj.status = status
    db.commit()
    db.refresh(obj)
    return obj


# --------------------------------------------------
# DELETE
# --------------------------------------------------
def delete_whitelist(db: Session, row_id: int) -> bool:
    obj = db.query(VehicleWhitelist).filter(
        VehicleWhitelist.id == row_id).first()
    if not obj:
        return False

    db.delete(obj)
    db.commit()
    return True


# --------------------------------------------------
# ACTIVE LOOKUP (used by analytics)
# --------------------------------------------------
def get_active_for_vehicle(db: Session, vehicle_number: str, today: date):
    mark_expired(db, today)

    return (
        db.query(VehicleWhitelist)
        .filter(VehicleWhitelist.vehicle_number == vehicle_number)
        .filter(VehicleWhitelist.from_date <= today)
        .filter(VehicleWhitelist.to_date >= today)
        .filter(VehicleWhitelist.status == "approved")
        .first()
    )
