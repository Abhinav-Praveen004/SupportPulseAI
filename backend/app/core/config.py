"""Application Configuration Settings."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application runtime settings."""

    APP_NAME: str = "SupportPulse AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # Security
    SECRET_KEY: str = "supportpulse-local-dev-secret-key-2026-safe-for-local"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    MODELS_DIR: Path = BASE_DIR / "models"
    REPORTS_DIR: Path = BASE_DIR / "reports"

    # Database
    DATABASE_URL: str = "sqlite:///./data/supportpulse.db"

    # ML Defaults
    ACTIVE_MODEL_VERSION: str = "v1.0.0"
    HUMAN_TRIAGE_CONFIDENCE_THRESHOLD: float = 0.65
    SLA_ALERT_DEFAULT_RECALL: float = 0.80

    # SLA Target Hours
    SLA_TARGET_P1_HOURS: float = 4.0
    SLA_TARGET_P2_HOURS: float = 8.0
    SLA_TARGET_P3_HOURS: float = 24.0
    SLA_TARGET_P4_HOURS: float = 72.0

    # Scheduler
    SCHEDULER_INTERVAL_MINUTES: int = 5
    ENABLE_SCHEDULER: bool = True

    # Notification integrations (disabled by default)
    WEBHOOK_URL: str = ""
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
