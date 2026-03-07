"""
Configuration settings for the application
Uses pydantic-settings to load from environment variables
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    DATABASE_URL: str = "sqlite:///./reportforge.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:5173"
    
    # File Upload Settings
    MAX_FILE_SIZE: int = 104857600  # 100MB in bytes
    MAX_UPLOAD_SIZE: int = 104857600  # 100MB in bytes (alias)
    UPLOAD_DIR: str = "../inputs"
    OUTPUT_DIR: str = "../outputs"
    
    # Application Info
    APP_NAME: str = "ReportForge AI"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # CORS Settings
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000", "http://localhost:8080"]
    
    # Celery Settings
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None
    
    # JWT Settings
    JWT_SECRET_KEY: str = "dev-secret-key-change-in-production-use-openssl-rand-hex-32"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # OAuth Settings (GitHub disabled per user preference)
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    # GITHUB_CLIENT_ID: Optional[str] = None  # Disabled
    # GITHUB_CLIENT_SECRET: Optional[str] = None  # Disabled
    
    # Storage Limits
    DEFAULT_STORAGE_LIMIT: int = 5 * 1024 * 1024 * 1024  # 5GB per user
    FREE_TIER_REPORTS_LIMIT: int = 10  # Max reports for free users
    
    # File Size Limits (in bytes)
    MAX_PDF_SIZE: int = 100 * 1024 * 1024  # 100MB
    MAX_ZIP_SIZE: int = 500 * 1024 * 1024  # 500MB
    MAX_TOTAL_UPLOAD: int = 600 * 1024 * 1024  # 600MB combined
    
    # Session
    SESSION_SECRET_KEY: str = "dev-session-secret-change-in-production"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # This allows extra fields without errors
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Use Redis URL for Celery if not explicitly set
        if self.CELERY_BROKER_URL is None:
            self.CELERY_BROKER_URL = self.REDIS_URL
        if self.CELERY_RESULT_BACKEND is None:
            self.CELERY_RESULT_BACKEND = self.REDIS_URL
        
        # Ensure directories exist
        Path(self.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
        Path(self.OUTPUT_DIR).mkdir(parents=True, exist_ok=True)


# Create global settings instance
settings = Settings()