from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional

from app.database import get_db
from app.schemas.traffic_flow import TrafficFlowVehiclesResponse
from app.crud.traffic_flow import get_traffic_flow_vehicles

router = APIRouter(prefix="/traffic-flow", tags=["Traffic Flow"])


@router.get("/vehicles", response_model=TrafficFlowVehiclesResponse)
def traffic_flow_vehicles(
    date_selected: Optional[date] = Query(None, alias="date"),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    dwell_limit_seconds: int = Query(7200, ge=60),
    db: Session = Depends(get_db),
):
    total, data = get_traffic_flow_vehicles(
        db=db,
        selected_date=date_selected,
        limit=limit,
        offset=offset,
        dwell_limit_seconds=dwell_limit_seconds,
    )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "date": str(date_selected or date.today()),
        "dwell_limit_seconds": dwell_limit_seconds,
        "data": data,
    }
