from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional, Tuple
from app.models.camera import Camera
from app.schemas.camera import CameraCreate, CameraUpdate
import logging

logger = logging.getLogger(__name__)


class CameraCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get(self, camera_id: str) -> Optional[Camera]:
        return self.db.query(Camera).filter(Camera.camera_id == camera_id).first()

    def get_by_id(self, id: int) -> Optional[Camera]:
        return self.db.query(Camera).filter(Camera.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> Tuple[List[Camera], int]:
        query = self.db.query(Camera)
        total = query.count()
        items = query.order_by(desc(Camera.created_at)).offset(
            skip).limit(limit).all()
        return items, total

    def create(self, camera_in: CameraCreate) -> Optional[Camera]:
        if self.get(camera_in.camera_id):
            return None

        db_camera = Camera(
            camera_id=camera_in.camera_id,
            name=camera_in.name,
            rtsp_url=camera_in.rtsp_url
        )
        self.db.add(db_camera)
        self.db.commit()
        self.db.refresh(db_camera)
        logger.info(f"Created camera: {db_camera.camera_id}")
        return db_camera

    # ✅ FIXED: camera_id rename supported
    def update(self, camera_id: str, camera_in: CameraUpdate) -> Optional[Camera]:
        db_camera = self.get(camera_id)
        if not db_camera:
            return None

        update_data = camera_in.dict(exclude_unset=True)

        # ✅ handle camera_id change safely
        new_camera_id = update_data.get("camera_id")
        if new_camera_id and new_camera_id != camera_id:
            # check duplicate
            exists = self.get(new_camera_id)
            if exists:
                # return special marker by raising, or just None (router will map)
                raise ValueError("camera_id already exists")

            db_camera.camera_id = new_camera_id

        # update remaining fields
        if "name" in update_data:
            db_camera.name = update_data["name"]
        if "rtsp_url" in update_data:
            db_camera.rtsp_url = update_data["rtsp_url"]

        self.db.commit()
        self.db.refresh(db_camera)
        logger.info(f"Updated camera: {camera_id} -> {db_camera.camera_id}")
        return db_camera

    def delete(self, camera_id: str) -> bool:
        db_camera = self.get(camera_id)
        if not db_camera:
            return False

        self.db.delete(db_camera)
        self.db.commit()
        logger.info(f"Deleted camera: {camera_id}")
        return True

    def search(self, query: str, skip: int = 0, limit: int = 100) -> Tuple[List[Camera], int]:
        search_query = f"%{query}%"
        items = self.db.query(Camera).filter(
            (Camera.camera_id.ilike(search_query)) |
            (Camera.name.ilike(search_query))
        ).offset(skip).limit(limit).all()
        total = len(items)
        return items, total


def get_camera_crud(db: Session) -> CameraCRUD:
    return CameraCRUD(db)
