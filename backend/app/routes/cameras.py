from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.crud.camera import get_camera_crud
from app.schemas.camera import CameraCreate, CameraUpdate, CameraOut, CameraListResponse

router = APIRouter(prefix="/cameras", tags=["cameras"])


def compute_status_and_health(rtsp_url: Optional[str]) -> tuple[str, int]:
    """
    Dummy logic for now:
    - If rtsp_url exists => online with 95 health
    - Else => offline with 0 health
    You can replace later with real camera health checks.
    """
    if rtsp_url:
        return "online", 95
    return "offline", 0


@router.get("/", response_model=CameraListResponse)
def get_cameras(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    crud = get_camera_crud(db)

    if search:
        items, total = crud.search(search, skip=skip, limit=limit)
    else:
        items, total = crud.get_all(skip=skip, limit=limit)

    # ✅ Convert ORM -> CameraOut with extra UI fields
    out_items: list[CameraOut] = []
    for cam in items:
        status_val, health_val = compute_status_and_health(cam.rtsp_url)

        out_items.append(
            CameraOut(
                id=cam.id,
                camera_id=cam.camera_id,
                name=cam.name,
                rtsp_url=cam.rtsp_url,
                created_at=cam.created_at,
                updated_at=cam.updated_at,
                location="Unknown",     # TODO: replace later from DB
                status=status_val,
                health=health_val,
            )
        )

    pages = (total + limit - 1) // limit if limit > 0 else 0

    return {
        "items": out_items,
        "total": total,
        "page": (skip // limit) + 1 if limit > 0 else 1,
        "size": limit,
        "pages": pages,
        "has_more": (skip + limit) < total
    }


@router.get("/{camera_id}", response_model=CameraOut)
def get_camera(camera_id: str, db: Session = Depends(get_db)):
    crud = get_camera_crud(db)
    cam = crud.get(camera_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")

    status_val, health_val = compute_status_and_health(cam.rtsp_url)

    return CameraOut(
        id=cam.id,
        camera_id=cam.camera_id,
        name=cam.name,
        rtsp_url=cam.rtsp_url,
        created_at=cam.created_at,
        updated_at=cam.updated_at,
        location="Unknown",
        status=status_val,
        health=health_val,
    )


@router.post("/", response_model=CameraOut, status_code=status.HTTP_201_CREATED)
def create_camera(camera: CameraCreate, db: Session = Depends(get_db)):
    crud = get_camera_crud(db)
    cam = crud.create(camera)
    if not cam:
        raise HTTPException(status_code=400, detail="Camera already exists")

    status_val, health_val = compute_status_and_health(cam.rtsp_url)

    return CameraOut(
        id=cam.id,
        camera_id=cam.camera_id,
        name=cam.name,
        rtsp_url=cam.rtsp_url,
        created_at=cam.created_at,
        updated_at=cam.updated_at,
        location="Unknown",
        status=status_val,
        health=health_val,
    )


@router.put("/{camera_id}", response_model=CameraOut)
def update_camera(camera_id: str, camera_update: CameraUpdate, db: Session = Depends(get_db)):
    crud = get_camera_crud(db)
    cam = crud.update(camera_id, camera_update)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")

    status_val, health_val = compute_status_and_health(cam.rtsp_url)

    return CameraOut(
        id=cam.id,
        camera_id=cam.camera_id,
        name=cam.name,
        rtsp_url=cam.rtsp_url,
        created_at=cam.created_at,
        updated_at=cam.updated_at,
        location="Unknown",
        status=status_val,
        health=health_val,
    )

@router.delete("/{camera_id}", status_code=status.HTTP_200_OK)
def delete_camera(camera_id: str, db: Session = Depends(get_db)):
    crud = get_camera_crud(db)   # ✅ same pattern as others
    ok = crud.delete(camera_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Camera not found")
    return {"message": "Camera deleted successfully"}
