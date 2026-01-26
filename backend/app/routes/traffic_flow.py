from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import date
from typing import Optional
import io
import csv

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


# ✅ NEW: Export CSV (Swagger will show this)
@router.get("/vehicles/export")
def traffic_flow_vehicles_export(
    date_selected: Optional[date] = Query(None, alias="date"),
    dwell_limit_seconds: int = Query(7200, ge=60),
    db: Session = Depends(get_db),
):
    # Export all rows for the day
    total, data = get_traffic_flow_vehicles(
        db=db,
        selected_date=date_selected,
        limit=50000,
        offset=0,
        dwell_limit_seconds=dwell_limit_seconds,
    )

    out = io.StringIO()
    writer = csv.writer(out)

    headers = [
        "id",
        "plate_text",
        "severity",
        "status",
        "location_text",
        "dwell_seconds",
        "dwell_text",
        "limit_seconds",
        "is_alert",
        "entry_time",
        "exit_time",
        "entry_camera_name",
        "exit_camera_name",
        "created_at",
    ]
    writer.writerow(headers)

    for r in data:
        writer.writerow([
            r.get("id"),
            r.get("plate_text"),
            r.get("severity"),
            r.get("status"),
            r.get("location_text"),
            r.get("dwell_seconds"),
            r.get("dwell_text"),
            r.get("limit_seconds"),
            r.get("is_alert"),
            r.get("entry_time"),
            r.get("exit_time"),
            r.get("entry_camera_name"),
            r.get("exit_camera_name"),
            r.get("created_at"),
        ])

    out.seek(0)

    file_date = str(date_selected or date.today())
    filename = f"traffic_flow_{file_date}.csv"

    return StreamingResponse(
        iter([out.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# from fastapi import APIRouter, Depends, Query
# from sqlalchemy.orm import Session
# from datetime import date
# from typing import Optional

# from app.database import get_db
# from app.schemas.traffic_flow import TrafficFlowVehiclesResponse
# from app.crud.traffic_flow import get_traffic_flow_vehicles

# router = APIRouter(prefix="/traffic-flow", tags=["Traffic Flow"])


# @router.get("/vehicles", response_model=TrafficFlowVehiclesResponse)
# def traffic_flow_vehicles(
#     date_selected: Optional[date] = Query(None, alias="date"),
#     limit: int = Query(20, ge=1, le=200),
#     offset: int = Query(0, ge=0),
#     dwell_limit_seconds: int = Query(7200, ge=60),
#     db: Session = Depends(get_db),
# ):
#     total, data = get_traffic_flow_vehicles(
#         db=db,
#         selected_date=date_selected,
#         limit=limit,
#         offset=offset,
#         dwell_limit_seconds=dwell_limit_seconds,
#     )

#     return {
#         "total": total,
#         "limit": limit,
#         "offset": offset,
#         "date": str(date_selected or date.today()),
#         "dwell_limit_seconds": dwell_limit_seconds,
#         "data": data,
#     }
