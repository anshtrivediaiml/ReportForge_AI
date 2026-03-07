"""
Job Service - CRUD operations for jobs
"""
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional, List
from uuid import UUID
from datetime import datetime, timezone
from app.models import Job, JobStatus, Stage
from app.schemas.job import JobCreate, JobUpdate, JobResponse
from app.utils.time_utils import get_accurate_utc_time


def create_job(
    db: Session, 
    job_data: JobCreate, 
    guidelines_path: str, 
    project_path: str,
    user_id: Optional[int] = None,
    title: Optional[str] = None,
    original_filename: Optional[str] = None,
    file_size: Optional[int] = None
) -> Job:
    """Create a new job with optional user association"""
    job = Job(
        guidelines_filename=job_data.guidelines_filename,
        project_filename=job_data.project_filename,
        guidelines_path=guidelines_path,
        project_path=project_path,
        status=JobStatus.QUEUED,
        user_id=user_id,
        title=title,
        original_filename=original_filename,
        file_size=file_size
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: UUID, user_id: Optional[int] = None) -> Optional[Job]:
    """Get a job by ID, filtered by user_id for security.
    
    SECURITY: user_id should always be provided to prevent accessing other users' jobs.
    """
    query = db.query(Job).filter(Job.id == job_id)
    
    # SECURITY: Always filter by user_id if provided - mandatory for privacy
    if user_id is not None:
        query = query.filter(Job.user_id == user_id)
    # Note: If user_id is None, this could return any user's job - caller should ensure user_id is set
    
    return query.first()


def update_job(db: Session, job_id: UUID, update_data: JobUpdate, user_id: Optional[int] = None) -> Optional[Job]:
    """Update a job, optionally checking user ownership"""
    job = get_job(db, job_id, user_id=user_id)
    if not job:
        return None
    
    update_dict = update_data.model_dump(exclude_unset=True)
    
    # Handle status changes
    if "status" in update_dict:
        new_status = update_dict["status"]
        if new_status == JobStatus.PROCESSING and not job.started_at:
            update_dict["started_at"] = get_accurate_utc_time()
        elif new_status == JobStatus.COMPLETED and not job.completed_at:
            update_dict["completed_at"] = get_accurate_utc_time()
    
    for key, value in update_dict.items():
        setattr(job, key, value)
    
    db.commit()
    db.refresh(job)
    return job


def update_job_status(db: Session, job_id: UUID, update_data: JobUpdate) -> Optional[Job]:
    """
    Convenience wrapper for update_job
    Alias for backward compatibility
    """
    return update_job(db, job_id, update_data)


def list_jobs(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    status: Optional[JobStatus] = None,
    user_id: Optional[int] = None
) -> tuple[List[Job], int]:
    """List jobs with pagination and user filtering.
    
    SECURITY: user_id is REQUIRED - this function should never be called without a user_id
    to prevent exposing other users' jobs.
    """
    query = db.query(Job)
    
    # SECURITY: Always filter by user_id - this is mandatory for privacy
    if user_id is None:
        # This should never happen in production, but fail safely
        # Return empty list instead of raising error to avoid 500 errors
        # The caller should ensure user_id is provided
        return [], 0
    
    query = query.filter(Job.user_id == user_id)
    
    # Filter by status if provided
    if status:
        query = query.filter(Job.status == status)
    
    total = query.count()
    jobs = query.order_by(desc(Job.created_at)).offset(skip).limit(limit).all()
    
    return jobs, total


def delete_job(db: Session, job_id: UUID, user_id: Optional[int] = None) -> bool:
    """Delete a job, optionally checking user ownership"""
    job = get_job(db, job_id, user_id=user_id)
    if not job:
        return False
    
    db.delete(job)
    db.commit()
    return True

