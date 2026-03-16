"""
Schemas for report sharing
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class ShareReportRequest(BaseModel):
    """Request to create a shareable link"""
    job_id: UUID
    expires_in_days: Optional[int] = Field(None, ge=1, le=365, description="Link expires in N days (None = never)")
    requires_password: bool = False
    password: Optional[str] = Field(None, min_length=4, description="Password for accessing shared link")
    description: Optional[str] = Field(None, max_length=500)
    access_level: str = "view"  # "view" or "comment"


class ShareReportResponse(BaseModel):
    """Response with shareable link"""
    share_id: UUID
    share_token: str
    share_url: str
    expires_at: Optional[datetime]
    created_at: datetime
    access_count: int
    is_active: bool
    requires_password: bool
    description: Optional[str] = None


class SharedReportInfo(BaseModel):
    """Information about a shared report (for viewing)"""
    share_id: UUID
    job_id: UUID
    job_title: Optional[str]
    shared_by: str  # Email or name
    created_at: datetime
    expires_at: Optional[datetime]
    access_count: int
    description: Optional[str]
    requires_password: bool


class AccessSharedReportRequest(BaseModel):
    """Request to access a shared report"""
    password: Optional[str] = None


class SharedReportListResponse(BaseModel):
    """List of shared reports for a user"""
    shares: list[ShareReportResponse]
    total: int

