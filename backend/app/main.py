from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import settings
from app.database import engine, Base

from app.routes import cameras_router, vehicle_logs_router, hls_router, traffic_flow_router, auth_router, incidents_router,vehicle_whitelist_router


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router, prefix="/api")
app.include_router(cameras_router, prefix="/api")
app.include_router(vehicle_logs_router, prefix="/api")
app.include_router(hls_router, prefix="/api")
app.include_router(traffic_flow_router, prefix="/api")
app.include_router(incidents_router, prefix="/api")
app.include_router(vehicle_whitelist_router, prefix="/api")



@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")


@app.get("/")
def root():
    return {"message": "Security Platform API", "version": settings.APP_VERSION, "docs": "/api/docs"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
