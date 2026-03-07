"""
Reports Router - User Statistics and Report Management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import User, Job, JobStatus
from app.dependencies.auth import get_current_active_user
from app.schemas.reports import UserStatsResponse
from app.config import settings

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/stats",
            summary="Get User Statistics",
            description="Get statistics for the authenticated user including storage usage and report counts.",
            response_model=UserStatsResponse,
            responses={
                200: {"description": "Statistics retrieved successfully"},
                401: {"description": "Authentication required"}
            })
async def get_user_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get statistics for the authenticated user"""
    user_id = current_user.id
    
    # Get report counts by status
    stats = db.query(
        func.count(Job.id).filter(Job.status == JobStatus.COMPLETED).label('completed'),
        func.count(Job.id).filter(Job.status == JobStatus.FAILED).label('failed'),
        func.count(Job.id).filter(Job.status == JobStatus.PROCESSING).label('processing'),
        func.count(Job.id).filter(Job.status == JobStatus.QUEUED).label('queued'),
        func.count(Job.id).label('total')
    ).filter(Job.user_id == user_id).first()
    
    # Calculate storage usage percentage
    storage_limit = settings.DEFAULT_STORAGE_LIMIT
    storage_used = current_user.storage_used
    storage_used_percent = (storage_used / storage_limit * 100) if storage_limit > 0 else 0
    
    return UserStatsResponse(
        user_id=user_id,
        email=current_user.email,
        storage_used=storage_used,
        storage_limit=storage_limit,
        storage_used_percent=round(storage_used_percent, 2),
        reports_generated=current_user.reports_generated,
        reports_completed=stats.completed or 0,
        reports_failed=stats.failed or 0,
        reports_processing=stats.processing or 0,
        reports_queued=stats.queued or 0,
        total_reports=stats.total or 0,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )

