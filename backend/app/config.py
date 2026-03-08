from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Core
    APP_NAME: str = "report-checker-backend"
    ENV: Literal["dev", "prod", "test"] = "dev"
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://report_checker:report_checker@postgres:5432/report_checker"

    # S3 / MinIO
    S3_ENDPOINT_URL: str = "http://minio:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "report-checker-documents"
    S3_REGION: str = "us-east-1"

    # Auth
    AUTH_MODE: Literal["itmo_id", "dev"] = "dev"

    ITMO_ID_CLIENT_ID: str | None = None
    ITMO_ID_CLIENT_SECRET: str | None = None
    ITMO_ID_REDIRECT_URI: str | None = None

    JWT_SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # Documents
    MAX_FILE_SIZE_MB: int = 50
    DOCUMENT_RETENTION_DAYS: int = 365


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
