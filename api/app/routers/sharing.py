"""
Report Sharing Router - Share reports with shareable links
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from starlette.requests import Request
from typing import Optional, Annotated
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
import secrets
from uuid import UUID

from app.database import get_db
from app.models import User, Job, SharedReport, ShareAccess
from app.dependencies.auth import get_current_active_user, get_current_user_optional
from app.schemas.sharing import (
    ShareReportRequest,
    ShareReportResponse,
    SharedReportInfo,
    AccessSharedReportRequest,
    SharedReportListResponse
)
from app.core.auth import get_password_hash, verify_password
from app.config import settings

router = APIRouter(prefix="/api/v1/sharing", tags=["sharing"])


def generate_share_token() -> str:
    """Generate a secure share token"""
    return secrets.token_urlsafe(32)


@router.post("/create",
             summary="Create Shareable Link",
             description="Create a shareable link for a report",
             response_model=ShareReportResponse)
async def create_share_link(
    share_data: ShareReportRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    """Create a shareable link for a report"""
    # SECURITY: Verify job exists and belongs to user - use get_job with user_id filter
    from app.services.job_service import get_job
    job = get_job(db, share_data.job_id, user_id=current_user.id)
    if not job:
        # Return 404 instead of revealing if job exists but belongs to another user
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found"
        )
    
    # SECURITY: Double-check ownership
    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied - this report belongs to another user"
        )
    
    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to share this report"
        )
    
    # Check if job is completed
    if job.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only completed reports can be shared"
        )
    
    # Generate share token
    share_token = generate_share_token()
    
    # Calculate expiration
    expires_at = None
    if share_data.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=share_data.expires_in_days)
    
    # Hash password if required
    password_hash = None
    if share_data.requires_password and share_data.password:
        password_hash = get_password_hash(share_data.password)
    
    # Create shared report
    shared_report = SharedReport(
        job_id=share_data.job_id,
        shared_by_user_id=current_user.id,
        share_token=share_token,
        access_level=share_data.access_level,
        requires_password=share_data.requires_password,
        password_hash=password_hash,
        expires_at=expires_at,
        description=share_data.description
    )
    
    db.add(shared_report)
    db.commit()
    db.refresh(shared_report)
    
    share_url = f"{settings.FRONTEND_URL}/shared/{share_token}"
    
    return ShareReportResponse(
        share_id=shared_report.id,
        share_token=shared_report.share_token,
        share_url=share_url,
        expires_at=shared_report.expires_at,
        created_at=shared_report.created_at,
        access_count=shared_report.access_count,
        is_active=shared_report.is_active,
        requires_password=shared_report.requires_password,
        description=shared_report.description
    )


@router.get("/list",
            summary="List My Shared Reports",
            description="Get all shareable links created by the current user",
            response_model=SharedReportListResponse)
async def list_shared_reports(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    """List all shared reports created by the user"""
    shares = db.query(SharedReport).filter(
        SharedReport.shared_by_user_id == current_user.id
    ).order_by(SharedReport.created_at.desc()).all()
    
    share_responses = []
    for share in shares:
        share_url = f"{settings.FRONTEND_URL}/shared/{share.share_token}"
        share_responses.append(ShareReportResponse(
            share_id=share.id,
            share_token=share.share_token,
            share_url=share_url,
            expires_at=share.expires_at,
            created_at=share.created_at,
            access_count=share.access_count,
            is_active=share.is_active,
            requires_password=share.requires_password,
            description=share.description
        ))
    
    return SharedReportListResponse(
        shares=share_responses,
        total=len(share_responses)
    )


@router.get("/{share_token}",
            summary="Get Shared Report Info",
            description="Get information about a shared report (public endpoint)",
            response_model=SharedReportInfo)
async def get_shared_report_info(
    share_token: str,
    db: Session = Depends(get_db)
):
    """Get information about a shared report (public endpoint - no auth required)"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Getting shared report info for token: {share_token[:10]}...")
    
    # Get shared report by token
    shared_report = db.query(SharedReport).filter(
        SharedReport.share_token == share_token
    ).first()
    
    if not shared_report:
        logger.warning(f"Shared report not found for token: {share_token[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared link not found"
        )
    
    logger.info(f"Found shared report {shared_report.id} for job {shared_report.job_id}")
    
    if not shared_report.is_valid():
        logger.warning(f"Shared report {shared_report.id} is invalid (expired or deactivated)")
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This shared link has expired or been deactivated"
        )
    
    # SECURITY: For shared reports, we need to access jobs that belong to other users
    # This is intentional - shared links allow access to jobs across users
    # Direct query without user_id filter is correct here
    job = db.query(Job).filter(Job.id == shared_report.job_id).first()
    if not job:
        logger.error(f"Shared report {shared_report.id} references job {shared_report.job_id} which does not exist")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found. The shared link references a report that no longer exists."
        )
    
    logger.info(f"Found job {job.id} for shared report")
    
    # Get user info
    user = db.query(User).filter(User.id == shared_report.shared_by_user_id).first()
    shared_by = user.email if user else "Unknown"
    
    return SharedReportInfo(
        share_id=shared_report.id,
        job_id=shared_report.job_id,
        job_title=job.title or job.output_filename,
        shared_by=shared_by,
        created_at=shared_report.created_at,
        expires_at=shared_report.expires_at,
        access_count=shared_report.access_count,
        description=shared_report.description,
        requires_password=shared_report.requires_password
    )


@router.post("/{share_token}/access",
             summary="Access Shared Report",
             description="Verify password and get download access to shared report")
async def access_shared_report(
    share_token: str,
    access_data: AccessSharedReportRequest,
    db: Session = Depends(get_db)
):
    """Verify password and grant access to shared report"""
    shared_report = db.query(SharedReport).filter(
        SharedReport.share_token == share_token
    ).first()
    
    if not shared_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared link not found"
        )
    
    if not shared_report.is_valid():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This shared link has expired or been deactivated"
        )
    
    # Verify password if required
    if shared_report.requires_password:
        if not access_data.password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password required"
            )
        
        if not shared_report.password_hash or not verify_password(access_data.password, shared_report.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password"
            )
    
    # Update access stats
    shared_report.access_count += 1
    shared_report.last_accessed_at = datetime.now(timezone.utc)
    db.commit()
    
    # Return job ID for download
    return {
        "job_id": str(shared_report.job_id),
        "access_granted": True
    }


@router.get("/{share_token}/view",
            summary="Get Document View URL",
            description="Get a viewable URL for the shared document (public endpoint)")
async def get_shared_report_view_url(
    share_token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get a viewable URL for the shared document"""
    from app.config import settings
    from pathlib import Path
    
    # Get shared report
    shared_report = db.query(SharedReport).filter(
        SharedReport.share_token == share_token
    ).first()
    
    if not shared_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared link not found"
        )
    
    if not shared_report.is_valid():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This shared link has expired or been deactivated"
        )
    
    # Get job
    job = db.query(Job).filter(Job.id == shared_report.job_id).first()
    if not job or job.status != "completed" or not job.output_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found or not ready"
        )
    
    output_file = Path(job.output_path)
    if not output_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file does not exist"
        )
    
    # Create a viewable URL using the API endpoint
    # Use the request URL base to construct the full URL
    base_url = str(request.base_url).rstrip('/')
    file_url = f"{base_url}/api/v1/sharing/{share_token}/file"
    
    # URL encode the file URL for use in viewer services
    from urllib.parse import quote_plus
    encoded_file_url = quote_plus(file_url)
    
    # Create Google Docs Viewer URL (free service, works with public HTTPS URLs)
    # Note: Google Docs Viewer requires the file to be publicly accessible via HTTPS
    # For localhost development, it will show "No preview available"
    # In production with HTTPS, it will work perfectly
    google_docs_viewer_url = f"https://docs.google.com/viewer?url={encoded_file_url}&embedded=true"
    
    # Also create Microsoft Office Online Viewer URL as alternative
    office_viewer_url = f"https://view.officeapps.live.com/op/embed.aspx?src={encoded_file_url}"
    
    return {
        "view_url": file_url,  # Direct file URL
        "google_docs_viewer_url": google_docs_viewer_url,  # Google Docs Viewer URL
        "office_viewer_url": office_viewer_url,  # Office Online Viewer URL
        "download_url": f"{base_url}/api/v1/sharing/{share_token}/file?download=true",
        "filename": job.output_filename or output_file.name
    }


@router.get("/{share_token}/file",
            summary="Serve Shared Report File",
            description="Serve the shared report file for viewing or downloading (public endpoint)")
async def serve_shared_report_file(
    share_token: str,
    download: bool = False,
    db: Session = Depends(get_db)
):
    """Serve the shared report file for viewing or downloading"""
    from fastapi.responses import FileResponse, Response
    from pathlib import Path
    import os
    
    # Get shared report
    shared_report = db.query(SharedReport).filter(
        SharedReport.share_token == share_token
    ).first()
    
    if not shared_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared link not found"
        )
    
    if not shared_report.is_valid():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="This shared link has expired or been deactivated"
        )
    
    # Get job
    job = db.query(Job).filter(Job.id == shared_report.job_id).first()
    if not job or job.status != "completed" or not job.output_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found or not ready"
        )
    
    output_file = Path(job.output_path)
    if not output_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file does not exist"
        )
    
    # Update access stats
    shared_report.access_count += 1
    shared_report.last_accessed_at = datetime.now(timezone.utc)
    db.commit()
    
    # Read file content
    with open(output_file, 'rb') as f:
        file_content = f.read()
    
    # Return file with proper CORS headers for external viewers
    headers = {
        "Content-Disposition": f'{"attachment" if download else "inline"}; filename="{job.output_filename or output_file.name}"',
        "Content-Type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "Access-Control-Allow-Origin": "*",  # Allow external viewers
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "*",
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "public, max-age=3600"  # Cache for 1 hour
    }
    
    return Response(
        content=file_content,
        headers=headers,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


@router.delete("/{share_id}",
               summary="Delete Share Link",
               description="Deactivate a shareable link")
async def delete_share_link(
    share_id: UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    """Delete (deactivate) a shareable link"""
    shared_report = db.query(SharedReport).filter(
        SharedReport.id == share_id
    ).first()
    
    if not shared_report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share link not found"
        )
    
    if shared_report.shared_by_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this share link"
        )
    
    # Deactivate instead of deleting (for audit trail)
    shared_report.is_active = False
    db.commit()
    
    return {"message": "Share link deactivated successfully"}

