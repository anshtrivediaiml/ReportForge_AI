"""
Download Router - Report Downloads with User Authentication
"""
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from uuid import UUID
from pathlib import Path
from typing import Optional
from app.database import get_db
from app.services.job_service import get_job
from app.models import JobStatus, User
from app.dependencies.auth import get_current_user_optional

router = APIRouter(prefix="/download", tags=["download"])


@router.get("/{job_id}",
            summary="Download Report",
            description="Download a generated report. If job has a user_id, authentication is required.",
            responses={
                200: {"description": "File download"},
                404: {"description": "Job or file not found"},
                400: {"description": "Report not ready"},
                401: {"description": "Authentication required"},
                403: {"description": "Access denied - job belongs to another user"}
            })
async def download_report(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Download generated report. Requires authentication and ownership."""
    
    # SECURITY: Require authentication - users can only download their own reports
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to download reports"
        )
    
    # SECURITY: Always filter by authenticated user's ID - never allow downloading other users' reports
    user_id = current_user.id
    job = get_job(db, job_id, user_id=user_id)
    
    if not job:
        # Return 404 instead of revealing if job exists but belongs to another user
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    # SECURITY: Double-check ownership before allowing download
    if job.user_id != current_user.id:
        # This should never happen due to query filtering, but extra safety check
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied - this report belongs to another user"
        )
    
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Report not ready. Current status: {job.status}"
        )
    
    if not job.output_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output file not found"
        )
    
    output_file = Path(job.output_path)
    if not output_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Output file does not exist on server"
        )
    
    return FileResponse(
        path=str(output_file),
        filename=job.output_filename or output_file.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
