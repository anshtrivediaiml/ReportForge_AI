"""
Jobs Router - Report Management with User Authentication
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from pathlib import Path
from datetime import datetime, timezone
from app.database import get_db
from app.models import JobStatus, User
from app.dependencies.auth import get_current_active_user, get_current_user_optional
from app.schemas.job import JobResponse, JobListResponse, JobUpdate
from app.schemas.reports import DeleteResponse, JobTitleUpdate
from typing import List
from app.services.job_service import get_job, list_jobs, update_job, delete_job

router = APIRouter(prefix="/jobs", tags=["jobs"])


def serialize_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Serialize datetime to ISO format with UTC timezone indicator"""
    if dt is None:
        return None
    # If timezone-naive, assume it's UTC and add 'Z' suffix
    if dt.tzinfo is None:
        return dt.isoformat() + 'Z'
    # If timezone-aware, convert to UTC and add 'Z'
    return dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')


@router.get("/{job_id}",
            summary="Get Job by ID",
            description="Get a job by ID. If authenticated, only returns jobs owned by the user.",
            responses={
                200: {"description": "Job found"},
                404: {"description": "Job not found"},
                403: {"description": "Access denied - job belongs to another user"}
            })
async def get_job_endpoint(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get a job by ID with file size. Requires authentication and ownership."""
    
    # SECURITY: Require authentication - users can only access their own jobs
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to access jobs"
        )
    
    # SECURITY: Always filter by authenticated user's ID - never show other users' jobs
    user_id = current_user.id
    job = get_job(db, job_id, user_id=user_id)
    
    if not job:
        # Return 404 instead of revealing if job exists but belongs to another user
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # SECURITY: Double-check ownership before returning
    if job.user_id != current_user.id:
        # This should never happen due to query filtering, but extra safety check
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied - this job belongs to another user"
        )
    
    # Build job response
    job_dict = {
        "id": str(job.id),
        "title": job.title,
        "user_id": job.user_id,
        "guidelines_filename": job.guidelines_filename,
        "project_filename": job.project_filename,
        "status": job.status.value if hasattr(job.status, 'value') else str(job.status),
        "current_stage": job.current_stage.value if job.current_stage and hasattr(job.current_stage, 'value') else (str(job.current_stage) if job.current_stage else None),
        "progress": job.progress,
        "created_at": serialize_datetime(job.created_at),
        "started_at": serialize_datetime(job.started_at),
        "completed_at": serialize_datetime(job.completed_at),
        "files_analyzed": job.files_analyzed,
        "chapters_created": job.chapters_created,
        "sections_written": job.sections_written,
        "total_sections": job.total_sections,
        "pages_generated": job.pages_generated,
        "output_path": job.output_path,
        "output_filename": job.output_filename,
        "error_message": job.error_message,
    }
    
    # Calculate file size if output file exists
    if job.output_path:
        try:
            output_file = Path(job.output_path)
            if output_file.exists():
                job_dict["output_file_size"] = output_file.stat().st_size
            else:
                job_dict["output_file_size"] = None
        except Exception as e:
            print(f"Error calculating file size: {e}")
            job_dict["output_file_size"] = None
    else:
        job_dict["output_file_size"] = None
    
    return JSONResponse(content={"success": True, "data": job_dict})


@router.get("",
            summary="List Jobs (History)",
            description="List jobs with pagination. If authenticated, only returns user's jobs.",
            response_model=JobListResponse)
async def list_jobs_endpoint(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    job_status: Optional[JobStatus] = Query(None, description="Filter by status", alias="status"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """List jobs with pagination. Authenticated users only see their own jobs."""
    # SECURITY: Require authentication - users can only see their own jobs
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to view jobs"
        )
    
    skip = (page - 1) * page_size
    
    # SECURITY: Always filter by authenticated user's ID - never show other users' jobs
    user_id = current_user.id
    jobs, total = list_jobs(db, skip=skip, limit=page_size, status=job_status, user_id=user_id)
    
    # Convert jobs to response format
    job_responses = []
    for job in jobs:
        # SECURITY: Double-check ownership before including in response
        if job.user_id != current_user.id:
            # This should never happen due to query filtering, but extra safety check
            continue
            
        # Calculate file size if output file exists
        output_file_size = None
        if job.output_path:
            try:
                output_file = Path(job.output_path)
                if output_file.exists():
                    output_file_size = output_file.stat().st_size
            except Exception:
                pass
        
        # Create JobResponse directly from job object - Pydantic will handle datetime serialization
        # using the json_encoders we configured in the schema
        job_responses.append(JobResponse(
            id=job.id,
            title=job.title,
            user_id=job.user_id,
            guidelines_filename=job.guidelines_filename,
            project_filename=job.project_filename,
            status=job.status,
            current_stage=job.current_stage,
            progress=job.progress,
            created_at=job.created_at,  # Pass datetime object, Pydantic will serialize it
            started_at=job.started_at,
            completed_at=job.completed_at,
            files_analyzed=job.files_analyzed,
            chapters_created=job.chapters_created,
            sections_written=job.sections_written,
            total_sections=job.total_sections,
            pages_generated=job.pages_generated,
            output_path=job.output_path,
            output_filename=job.output_filename,
            error_message=job.error_message,
            output_file_size=output_file_size
        ))
    
    return JobListResponse(
        jobs=job_responses,
        total=total,
        page=page,
        page_size=page_size
    )


@router.patch("/{job_id}",
              summary="Update Job Title",
              description="Update the title of a job. Requires authentication and ownership.",
              responses={
                  200: {"description": "Job title updated successfully"},
                  404: {"description": "Job not found"},
                  403: {"description": "Access denied - job belongs to another user"}
              })
async def update_job_title(
    job_id: UUID,
    update_data: JobTitleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update the title of a job. Only the owner can update it."""
    user_id = current_user.id
    
    # Check if job exists and belongs to user
    job = get_job(db, job_id, user_id=user_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found or you don't have permission to access it"
        )
    
    # Update title
    update_payload = JobUpdate(title=update_data.title)
    updated_job = update_job(db, job_id, update_payload, user_id=user_id)
    
    if not updated_job:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update job"
        )
    
    return JSONResponse(content={
        "success": True,
        "message": "Job title updated successfully",
        "data": {
            "id": str(updated_job.id),
            "title": updated_job.title
        }
    })


@router.delete("/{job_id}",
               summary="Delete Job",
               description="Delete a job. Requires authentication and ownership.",
               response_model=DeleteResponse,
               responses={
                   200: {"description": "Job deleted successfully"},
                   404: {"description": "Job not found"},
                   403: {"description": "Access denied - job belongs to another user"}
               })
async def delete_job_endpoint(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a job. Only the owner can delete it."""
    user_id = current_user.id
    
    # Check if job exists and belongs to user
    job = get_job(db, job_id, user_id=user_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found or you don't have permission to delete it"
        )
    
    # Delete the job
    success = delete_job(db, job_id, user_id=user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete job"
        )
    
    return DeleteResponse(
        success=True,
        message="Job deleted successfully",
        job_id=str(job_id)
    )


@router.post("/bulk-delete",
             summary="Bulk Delete Jobs",
             description="Delete multiple jobs at once. Requires authentication and ownership.",
             response_model=dict,
             responses={
                 200: {"description": "Jobs deleted successfully"},
                 400: {"description": "Invalid request"}
             })
async def bulk_delete_jobs(
    job_ids: List[UUID],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete multiple jobs. Only the owner can delete them."""
    if not job_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No job IDs provided"
        )
    
    user_id = current_user.id
    deleted_count = 0
    failed_ids = []
    
    for job_id in job_ids:
        job = get_job(db, job_id, user_id=user_id)
        if job:
            if delete_job(db, job_id, user_id=user_id):
                deleted_count += 1
            else:
                failed_ids.append(str(job_id))
        else:
            failed_ids.append(str(job_id))
    
    return {
        "success": True,
        "message": f"Deleted {deleted_count} of {len(job_ids)} jobs",
        "deleted_count": deleted_count,
        "failed_ids": failed_ids
    }

