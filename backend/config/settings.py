"""Application configuration and settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from typing import Optional
import os
from pathlib import Path
from urllib.parse import quote_plus


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

    # Database: support either full DATABASE_URL or individual env vars (for Elastic Beanstalk, etc.)
    DATABASE_URL: Optional[str] = None
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: str = "5432"
    DATABASE_NAME: str = "loan_engine"
    DATABASE_USER: str = "postgres"
    DATABASE_PASSWORD: str = ""
    DATABASE_SSLMODE: Optional[str] = None  # e.g. "require" for RDS

    @model_validator(mode="after")
    def build_database_url(self) -> "Settings":
        if self.DATABASE_URL and self.DATABASE_URL.strip():
            return self
        # Build from components so EB/containers can set DATABASE_HOST, DATABASE_USER, etc.
        user = quote_plus(self.DATABASE_USER)
        password = quote_plus(self.DATABASE_PASSWORD) if self.DATABASE_PASSWORD else ""
        host = self.DATABASE_HOST
        port = self.DATABASE_PORT
        name = self.DATABASE_NAME
        if password:
            self.DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{name}"
        else:
            self.DATABASE_URL = f"postgresql://{user}@{host}:{port}/{name}"
        if self.DATABASE_SSLMODE:
            self.DATABASE_URL = f"{self.DATABASE_URL}?sslmode={self.DATABASE_SSLMODE}"
        return self
    
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
    S3_INPUTS_PREFIX: str = "input"  # S3 key prefix for inputs area; use "input" to match s3://bucket/input/...
    
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
