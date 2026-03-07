"""
Report Management Schemas
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserStatsResponse(BaseModel):
    """User statistics response"""
    user_id: int
    email: str
    storage_used: int  # bytes
    storage_limit: int  # bytes
    storage_used_percent: float  # percentage
    reports_generated: int
    reports_completed: int
    reports_failed: int
    reports_processing: int
    reports_queued: int
    total_reports: int
    created_at: datetime
    last_login: Optional[datetime] = None


class JobTitleUpdate(BaseModel):
    """Schema for updating job title"""
    title: str


class DeleteResponse(BaseModel):
    """Response for delete operations"""
    success: bool
    message: str
    job_id: str

