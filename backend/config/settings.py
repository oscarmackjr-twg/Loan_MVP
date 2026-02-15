"""Application configuration and settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Pydantic v2 settings config:
    # - Ignore extra env vars (e.g. AWS_PROFILE in dev/containers)
    # - Still load from .env when present
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        env_ignore_empty=True,
        extra="ignore",
    )
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/loan_engine"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # File Storage
    STORAGE_TYPE: str = "local"  # "local" or "s3"
    INPUT_DIR: str = "./data/inputs"
    OUTPUT_DIR: str = "./data/outputs"
    OUTPUT_SHARE_DIR: str = "./data/output_share"
    ARCHIVE_DIR: str = "./data/archive"  # Per-run archive: archive/{run_id}/input, archive/{run_id}/output
    
    # S3 Configuration (required when STORAGE_TYPE=s3)
    S3_BUCKET_NAME: Optional[str] = None
    S3_REGION: Optional[str] = None
    S3_ACCESS_KEY_ID: Optional[str] = None
    S3_SECRET_ACCESS_KEY: Optional[str] = None
    S3_BASE_PREFIX: Optional[str] = None  # Optional prefix for all S3 paths (e.g., "test/" or "prod/")
    
    # Pipeline
    IRR_TARGET: float = 8.05
    DEFAULT_PDATE: Optional[str] = None
    
    # Scheduler
    ENABLE_SCHEDULER: bool = True
    DAILY_RUN_TIME: str = "02:00"  # 2 AM
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = None
    
# Load settings
# Note: If .env file has parsing errors, pydantic-settings will show a warning
# but the application will still start using defaults and environment variables
settings = Settings()
