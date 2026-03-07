"""
Analytics Router - Usage metrics and monitoring
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Annotated
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.dependencies.auth import get_current_active_user
from app.services.analytics_service import analytics_service

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/my-metrics",
            summary="Get My Metrics",
            description="Get usage metrics for the authenticated user")
async def get_my_metrics(
    current_user: Annotated[User, Depends(get_current_active_user)],
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get user-specific analytics metrics"""
    try:
        metrics = analytics_service.get_user_metrics(db, current_user.id, days)
        return {
            "success": True,
            "data": metrics
        }
    except Exception as e:
        analytics_service.log_error(e, {"user_id": current_user.id, "endpoint": "my-metrics"})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve metrics"
        )


@router.get("/system",
            summary="Get System Metrics",
            description="Get system-wide metrics (admin only - placeholder)")
async def get_system_metrics(
    current_user: Annotated[User, Depends(get_current_active_user)],
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """Get system-wide analytics metrics (admin only)"""
    # TODO: Add admin check
    # For now, allow any authenticated user (can restrict later)
    try:
        metrics = analytics_service.get_system_metrics(db, days)
        return {
            "success": True,
            "data": metrics
        }
    except Exception as e:
        analytics_service.log_error(e, {"user_id": current_user.id, "endpoint": "system-metrics"})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system metrics"
        )

