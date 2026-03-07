"""
Job Schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
from uuid import UUID
from app.models import JobStatus, Stage
import json


class JobBase(BaseModel):
    """Base job schema"""
    guidelines_filename: str
    project_filename: str


class JobCreate(JobBase):
    """Schema for creating a job"""
    pass


class JobUpdate(BaseModel):
    """Schema for updating a job"""
    status: Optional[JobStatus] = None
    current_stage: Optional[Stage] = None
    progress: Optional[int] = Field(None, ge=0, le=100)
    title: Optional[str] = Field(None, max_length=200)  # Allow updating title
    files_analyzed: Optional[int] = None
    chapters_created: Optional[int] = None
    sections_written: Optional[int] = None
    total_sections: Optional[int] = None
    pages_generated: Optional[int] = None
    error_message: Optional[str] = None
    output_path: Optional[str] = None
    output_filename: Optional[str] = None


class JobResponse(JobBase):
    """Schema for job response"""
    id: UUID
    title: Optional[str] = None
    user_id: Optional[int] = None
    status: JobStatus
    current_stage: Optional[Stage]
    progress: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    files_analyzed: int
    chapters_created: int
    sections_written: int
    total_sections: int
    pages_generated: int
    output_path: Optional[str]
    output_filename: Optional[str]
    error_message: Optional[str]
    output_file_size: Optional[int] = None
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z' if v and v.tzinfo is None else (v.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z') if v else None)
        }


class JobListResponse(BaseModel):
    """Schema for job list response"""
    jobs: list[JobResponse]
    total: int
    page: int
    page_size: int

