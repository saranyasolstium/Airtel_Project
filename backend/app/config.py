from pydantic_settings import BaseSettings
from typing import List
from dotenv import load_dotenv
import os
from urllib.parse import quote_plus

# Load environment variables from .env file
load_dotenv()

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY", "CHANGE_THIS_TO_A_LONG_RANDOM_SECRET")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))


class Settings(BaseSettings):
    # MySQL Individual Components
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT: int = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "Saranya@30!")
    MYSQL_DB: str = os.getenv("MYSQL_DB", "Airtel")

    # Construct DATABASE_URL
    @property
    def DATABASE_URL(self) -> str:
        # URL encode the password (important for special characters like @)
        encoded_password = quote_plus(self.MYSQL_PASSWORD)
        return f"mysql+pymysql://{self.MYSQL_USER}:{encoded_password}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DB}"

    # App
    APP_NAME: str = os.getenv("APP_NAME", "Airtel Platform API")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # CORS
    ALLOWED_ORIGINS: List[str] = os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

# Print database URL for debugging (remove in production)
print(f"Database URL: {settings.DATABASE_URL}")
