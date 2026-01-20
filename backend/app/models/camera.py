from sqlalchemy import Column, String, Text
from app.models.base import BaseModel


class Camera(BaseModel):
    __tablename__ = "cameras"

    camera_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    rtsp_url = Column(Text, nullable=True)

    def __repr__(self):
        return f"<Camera {self.camera_id}: {self.name}>"
