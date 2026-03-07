"""
Analytics Service - Track usage metrics, performance, and errors
"""
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models import User, Job, JobStatus
import logging

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for tracking and retrieving analytics data"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def log_error(self, error: Exception, context: Optional[Dict] = None):
        """Log an error with context"""
        error_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "context": context or {}
        }
        logger.error(f"Analytics Error: {error_data}")
        # In production, send to error tracking service (Sentry, etc.)
    
    def get_user_metrics(self, db: Session, user_id: int, days: int = 30) -> Dict:
        """Get user-specific metrics"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Total reports
        total_reports = db.query(Job).filter(
            and_(Job.user_id == user_id, Job.created_at >= cutoff_date)
        ).count()
        
        # Reports by status
        reports_by_status = db.query(
            Job.status,
            func.count(Job.id).label('count')
        ).filter(
            and_(Job.user_id == user_id, Job.created_at >= cutoff_date)
        ).group_by(Job.status).all()
        
        status_dict = {status: 0 for status in ['queued', 'processing', 'completed', 'failed']}
        for status, count in reports_by_status:
            status_dict[status] = count
        
        # Processing time statistics
        processing_times = db.query(Job.processing_time).filter(
            and_(
                Job.user_id == user_id,
                Job.status == JobStatus.COMPLETED,
                Job.processing_time.isnot(None),
                Job.created_at >= cutoff_date
            )
        ).all()
        
        processing_time_values = [pt[0] for pt in processing_times if pt[0] is not None]
        
        avg_processing_time = sum(processing_time_values) / len(processing_time_values) if processing_time_values else 0
        min_processing_time = min(processing_time_values) if processing_time_values else None
        max_processing_time = max(processing_time_values) if processing_time_values else None
        
        # Storage usage
        user = db.query(User).filter(User.id == user_id).first()
        storage_used = user.storage_used if user else 0
        
        # Get completed jobs for detailed metrics
        completed_jobs = db.query(Job).filter(
            and_(
                Job.user_id == user_id,
                Job.status == JobStatus.COMPLETED,
                Job.created_at >= cutoff_date
            )
        ).all()
        
        # Calculate additional metrics
        total_pages = sum(job.pages_generated or 0 for job in completed_jobs)
        total_sections = sum(job.sections_written or 0 for job in completed_jobs)
        total_chapters = sum(job.chapters_created or 0 for job in completed_jobs)
        avg_pages_per_report = total_pages / len(completed_jobs) if completed_jobs else 0
        avg_sections_per_report = total_sections / len(completed_jobs) if completed_jobs else 0
        
        # Calculate growth metrics (compare with previous period)
        previous_cutoff = datetime.now(timezone.utc) - timedelta(days=days * 2)
        previous_period_reports = db.query(Job).filter(
            and_(
                Job.user_id == user_id,
                Job.created_at >= previous_cutoff,
                Job.created_at < cutoff_date
            )
        ).count()
        
        growth_rate = 0
        if previous_period_reports > 0:
            growth_rate = ((total_reports - previous_period_reports) / previous_period_reports) * 100
        
        # Calculate success rate
        success_rate = (status_dict['completed'] / total_reports * 100) if total_reports > 0 else 0
        
        # Calculate reports per day
        reports_per_day = total_reports / days if days > 0 else 0
        
        # Calculate average storage per report
        avg_storage_per_report = storage_used / total_reports if total_reports > 0 else 0
        
        return {
            "total_reports": total_reports,
            "reports_by_status": status_dict,
            "avg_processing_time_seconds": float(avg_processing_time) if avg_processing_time else 0,
            "min_processing_time_seconds": float(min_processing_time) if min_processing_time is not None else None,
            "max_processing_time_seconds": float(max_processing_time) if max_processing_time is not None else None,
            "storage_used_bytes": storage_used,
            "period_days": days,
            # New analytics metrics
            "growth_rate_percent": round(growth_rate, 1),
            "success_rate_percent": round(success_rate, 1),
            "reports_per_day": round(reports_per_day, 2),
            "avg_pages_per_report": round(avg_pages_per_report, 1),
            "avg_sections_per_report": round(avg_sections_per_report, 1),
            "total_pages_generated": total_pages,
            "total_sections_written": total_sections,
            "total_chapters_created": total_chapters,
            "avg_storage_per_report_bytes": round(avg_storage_per_report, 0)
        }
    
    def get_system_metrics(self, db: Session, days: int = 30) -> Dict:
        """Get system-wide metrics (admin only)"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        # Total users
        total_users = db.query(User).count()
        active_users = db.query(User).filter(
            User.last_login >= cutoff_date
        ).count()
        
        # Total reports
        total_reports = db.query(Job).filter(
            Job.created_at >= cutoff_date
        ).count()
        
        # Reports by status
        reports_by_status = db.query(
            Job.status,
            func.count(Job.id).label('count')
        ).filter(
            Job.created_at >= cutoff_date
        ).group_by(Job.status).all()
        
        status_dict = {status: 0 for status in ['queued', 'processing', 'completed', 'failed']}
        for status, count in reports_by_status:
            status_dict[status] = count
        
        # Average processing time
        avg_processing_time = db.query(
            func.avg(Job.processing_time)
        ).filter(
            and_(
                Job.status == JobStatus.COMPLETED,
                Job.processing_time.isnot(None),
                Job.created_at >= cutoff_date
            )
        ).scalar() or 0
        
        # Daily report generation (last 7 days)
        daily_reports = []
        for i in range(7):
            day_start = datetime.now(timezone.utc) - timedelta(days=i+1)
            day_end = datetime.now(timezone.utc) - timedelta(days=i)
            count = db.query(Job).filter(
                and_(
                    Job.created_at >= day_start,
                    Job.created_at < day_end
                )
            ).count()
            daily_reports.append({
                "date": day_start.date().isoformat(),
                "count": count
            })
        daily_reports.reverse()
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "total_reports": total_reports,
            "reports_by_status": status_dict,
            "avg_processing_time_seconds": float(avg_processing_time) if avg_processing_time else 0,
            "daily_reports": daily_reports,
            "period_days": days
        }


# Create global analytics service instance
analytics_service = AnalyticsService()

