"""
WebSocket Message Schemas
"""
from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
from app.models import Stage


class ProgressUpdate(BaseModel):
    """Progress update message"""
    type: str = "progress"
    job_id: str
    stage: Stage
    progress: int  # 0-100
    message: str
    timestamp: datetime
    files_analyzed: Optional[int] = None
    chapters_created: Optional[int] = None
    sections_written: Optional[int] = None
    total_sections: Optional[int] = None
    pages_generated: Optional[int] = None
    estimated_time_remaining: Optional[str] = None
    details: Optional[dict[str, Any]] = None


class LogMessage(BaseModel):
    """Log message"""
    type: str = "log"
    job_id: str
    agent: str
    level: str = "info"  # info, warning, error, success
    message: str
    timestamp: datetime


class ErrorMessage(BaseModel):
    """Error message"""
    type: str = "error"
    job_id: str
    stage: Stage
    message: str
    error: Optional[str] = None
    timestamp: datetime


class ConnectedMessage(BaseModel):
    """Connection confirmation"""
    type: str = "connected"
    job_id: str
    message: str
    timestamp: datetime

