from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
import logging
from app.models.base import Base

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={
        "check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")


# from app.models.base import Base
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, Session
# from app.config import settings
# import logging

# logger = logging.getLogger(__name__)

# # Create engine
# engine = create_engine(
#     settings.DATABASE_URL,
#     echo=settings.DEBUG,
#     pool_pre_ping=True,
#     pool_recycle=300,
#     connect_args={
#         "check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
# )

# # Create session factory
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# def get_db() -> Session:
#     """
#     Database dependency for FastAPI
#     """
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


# # Import all models to ensure they are registered with Base

# # Create tables (called from main.py on startup)

# def create_tables():
#     Base.metadata.create_all(bind=engine)
#     logger.info("Database tables created")
