"""
Upload Router - File upload with chunking support and user authentication
"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from typing import Optional, Annotated
from app.schemas.upload import UploadResponse, StartGenerationRequest, StartGenerationResponse
from app.services.job_service import create_job, calculate_user_storage_usage, sync_user_storage_usage
from app.schemas.job import JobCreate
from app.database import get_db
from app.models import JobStatus, User
from app.dependencies.auth import get_current_active_user
from sqlalchemy.orm import Session
from uuid import UUID
from pathlib import Path
import shutil
from app.config import settings
from app.tasks.report_tasks import generate_report_task

router = APIRouter(prefix="/upload", tags=["upload"])


def validate_file_type(filename: str, content: bytes) -> tuple[bool, str]:
    """Validate file type (PDF or ZIP)"""
    filename_lower = filename.lower()
    
    # Check extension
    if filename_lower.endswith('.pdf'):
        # Check MIME type
        if content.startswith(b'%PDF'):
            return True, "pdf"
        return False, "Invalid PDF file"
    
    if filename_lower.endswith('.zip'):
        # Check ZIP magic bytes
        if content.startswith(b'PK\x03\x04') or content.startswith(b'PK\x05\x06'):
            return True, "zip"
        return False, "Invalid ZIP file"
    
    return False, "File must be PDF or ZIP format"


@router.post("/file", 
             summary="Upload a file",
             description="Uploads a PDF or ZIP file. Authentication REQUIRED. "
                        "File is saved to user-specific directory: inputs/{user_id}/{file_id}/filename",
             responses={
                 200: {"description": "File uploaded successfully"},
                 401: {"description": "Authentication required"},
                 413: {"description": "File too large or storage limit exceeded"}
             })
async def upload_file(
    file: UploadFile = File(...),
    file_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload a complete file (for small files)
    
    **Authentication: REQUIRED**
    - File saved to `inputs/{user_id}/{file_id}/filename`
    - Storage limits enforced per user
    
    **To authenticate:**
    1. Click "Authorize" button in Swagger UI
    2. Enter email as username and password
    3. Click "Authorize" then "Close"
    """
    try:
        # Authentication is required - current_user is guaranteed by dependency
        user_id = current_user.id
        print(f"📤 Upload by user: {user_id}")
        
        # Read file content
        content = await file.read()
        
        # Get filename (handle None case)
        filename = file.filename or "unnamed_file"
        
        # Validate file type
        is_valid, file_type = validate_file_type(filename, content)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=file_type
            )
        
        # Check file size based on type
        max_size = settings.MAX_PDF_SIZE if file_type == "pdf" else settings.MAX_ZIP_SIZE
        if len(content) > max_size:
            max_mb = max_size / 1024 / 1024
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"{file_type.upper()} file size exceeds maximum of {max_mb}MB"
            )
        
        # Check user storage limit
        current_storage = calculate_user_storage_usage(db, user_id)
        if current_storage + len(content) > settings.DEFAULT_STORAGE_LIMIT:
            available_gb = (settings.DEFAULT_STORAGE_LIMIT - current_storage) / (1024 ** 3)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Storage limit exceeded. Available: {available_gb:.2f}GB"
            )
        
        # Generate file_id if not provided
        if file_id is None:
            import uuid
            file_id = uuid.uuid4()
        
        # Create user-specific directory structure: inputs/{user_id}/{file_id}/
        user_dir = Path(settings.UPLOAD_DIR) / f"user_{user_id}"
        file_dir = user_dir / str(file_id)
        file_dir.mkdir(parents=True, exist_ok=True)
        
        # Save file to user-specific directory
        file_path = file_dir / filename
        with open(file_path, "wb") as f:
            f.write(content)
        
        print(f"📁 Saved to: inputs/user_{user_id}/{file_id}/{filename}")
        
        # Update user storage
        current_user.storage_used = sync_user_storage_usage(db, user_id, commit=False)
        db.commit()
        
        response_data = UploadResponse(
            file_id=file_id,
            filename=filename,
            size=len(content),
            chunk_count=1,
            uploaded_chunks=1
        )
        
        return JSONResponse(content={
            "success": True,
            "data": response_data.model_dump(mode='json')
        })
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Upload error: {e}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"File upload failed: {str(e)}"
        )


@router.post("/chunk")
async def upload_chunk(
    chunk: UploadFile = File(...),
    file_id: UUID = Query(...),
    chunk_index: int = Query(...),
    total_chunks: int = Query(...),
    filename: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Upload a file chunk - Authentication REQUIRED"""
    user_id = current_user.id
    print(f"📤 Chunk upload by user: {user_id}, file_id: {file_id}")
    
    chunk_content = await chunk.read()
    
    # Save chunk to user-specific directory: inputs/{user_id}/{file_id}_chunk_{index}
    user_dir = Path(settings.UPLOAD_DIR) / f"user_{user_id}"
    user_dir.mkdir(parents=True, exist_ok=True)
    chunk_path = user_dir / f"{file_id}_chunk_{chunk_index}"
    
    with open(chunk_path, "wb") as f:
        f.write(chunk_content)
    
    return {
        "success": True,
        "file_id": str(file_id),
        "chunk_index": chunk_index,
        "chunk_size": len(chunk_content)
    }


@router.post("/chunks/assemble")
async def assemble_chunks(
    file_id: UUID,
    filename: str,
    total_chunks: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Assemble uploaded chunks into a complete file - Authentication REQUIRED"""
    user_id = current_user.id
    print(f"📤 Assemble chunks by user: {user_id}, file_id: {file_id}")
    # Create user-specific directory: inputs/{user_id}/{file_id}/
    user_dir = Path(settings.UPLOAD_DIR) / f"user_{user_id}"
    file_dir = user_dir / str(file_id)
    file_dir.mkdir(parents=True, exist_ok=True)
    
    # Assemble chunks into final file
    final_path = file_dir / filename
    with open(final_path, "wb") as f:
        for i in range(total_chunks):
            chunk_path = user_dir / f"{file_id}_chunk_{i}"
            if chunk_path.exists():
                with open(chunk_path, "rb") as chunk_file:
                    f.write(chunk_file.read())
                chunk_path.unlink()  # Clean up chunk
    
    file_size = final_path.stat().st_size
    print(f"📁 Assembled to: inputs/user_{user_id}/{file_id}/{filename}")
    
    # Update user storage
    current_user.storage_used = sync_user_storage_usage(db, user_id, commit=False)
    db.commit()
    
    response_data = UploadResponse(
        file_id=file_id,
        filename=filename,
        size=file_size,
        chunk_count=total_chunks,
        uploaded_chunks=total_chunks
    )
    
    return JSONResponse(content={
        "success": True,
        "data": response_data.model_dump(mode='json')
    })


@router.post("/generate")
async def start_generation(
    request: StartGenerationRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Start report generation - Authentication REQUIRED
    
    Files are organized in user-specific directories:
    - Guidelines: inputs/{user_id}/{guidelines_file_id}/guidelines.pdf
    - Project: inputs/{user_id}/{project_file_id}/project.zip
    - Job: inputs/{user_id}/{job_id}/ (files copied here for processing)
    """
    user_id = current_user.id
    print(f"🚀 Report generation requested by user: {user_id}")
    
    # Construct user-specific file paths
    user_dir = Path(settings.UPLOAD_DIR) / f"user_{user_id}"
    guidelines_file_dir = user_dir / str(request.guidelines_file_id)
    project_file_dir = user_dir / str(request.project_file_id)
    
    # Find guidelines file
    guidelines_path = None
    for file_path in guidelines_file_dir.glob("*"):
        if file_path.is_file() and not "_chunk_" in file_path.name:
            guidelines_path = file_path
            break
    
    # Find project file
    project_path = None
    for file_path in project_file_dir.glob("*"):
        if file_path.is_file() and not "_chunk_" in file_path.name:
            project_path = file_path
            break
    
    if not guidelines_path or not guidelines_path.exists():
        raise HTTPException(status_code=404, detail=f"Guidelines file not found in user_{user_id}/{request.guidelines_file_id}/")
    
    if not project_path or not project_path.exists():
        raise HTTPException(status_code=404, detail=f"Project file not found in user_{user_id}/{request.project_file_id}/")
    
    # Calculate total file size
    total_size = guidelines_path.stat().st_size + project_path.stat().st_size
    
    # Check total upload size limit
    if total_size > settings.MAX_TOTAL_UPLOAD:
        max_mb = settings.MAX_TOTAL_UPLOAD / 1024 / 1024
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Combined file size exceeds maximum of {max_mb}MB"
        )
    
    # Check storage limits
    current_storage = calculate_user_storage_usage(db, user_id)
    if current_storage > settings.DEFAULT_STORAGE_LIMIT:
        available_gb = (settings.DEFAULT_STORAGE_LIMIT - current_storage) / (1024 ** 3)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Storage limit exceeded. Available: {available_gb:.2f}GB"
        )
    
    # Generate job_id and create job directory
    import uuid
    job_id = uuid.uuid4()
    job_dir = user_dir / str(job_id)
    job_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy files to job directory
    job_guidelines_path = job_dir / "guidelines.pdf"
    job_project_path = job_dir / "project.zip"
    shutil.copy2(guidelines_path, job_guidelines_path)
    shutil.copy2(project_path, job_project_path)
    
    print(f"📁 Files copied to job directory: inputs/user_{user_id}/{job_id}/")
    
    # Create combined filename for display
    combined_filename = f"{guidelines_path.stem}_{project_path.stem}"
    
    # Create job with user association
    job = create_job(
        db,
        JobCreate(
            guidelines_filename=guidelines_path.name,
            project_filename=project_path.name
        ),
        str(job_guidelines_path),  # Use job directory path
        str(job_project_path),     # Use job directory path
        user_id=user_id,
        title=request.title if hasattr(request, 'title') and request.title else None,
        original_filename=combined_filename,
        file_size=total_size
    )

    # Remove the original upload folders after the job record exists.
    # The job-specific copies become the canonical inputs for processing.
    for source_dir in [guidelines_file_dir, project_file_dir]:
        if source_dir != job_dir and source_dir.exists():
            shutil.rmtree(source_dir, ignore_errors=True)
    
    # Update user statistics
    current_user.storage_used = sync_user_storage_usage(db, user_id, commit=False)
    current_user.reports_generated += 1
    db.commit()
    
    print(f"🚀 Job {job.id} created for user {user_id}")
    
    # Check if job is already processing (prevent duplicate tasks)
    if job.status == JobStatus.PROCESSING:
        raise HTTPException(
            status_code=400, 
            detail="Report generation is already in progress for this job"
        )
    
    # Start Celery task (only when user explicitly clicks generate)
    # Pass job_id, guidelines_path, project_path, and user_id to the task
    # user_id is required now (authentication is required), so always pass it
    generate_report_task.apply_async(
        args=[str(job.id), str(job_guidelines_path), str(job_project_path), user_id],
        countdown=0  # Execute immediately, but only when explicitly called
    )
    
    # Construct a deployment-safe WebSocket URL from the incoming request.
    forwarded_proto = http_request.headers.get('x-forwarded-proto', http_request.url.scheme)
    forwarded_host = http_request.headers.get('x-forwarded-host') or http_request.headers.get('host') or http_request.url.netloc
    ws_protocol = 'wss' if forwarded_proto == 'https' else 'ws'
    ws_host = forwarded_host or 'localhost:8000'
    ws_url = f"{ws_protocol}://{ws_host}/ws/{job.id}"
    
    response_data = StartGenerationResponse(
        job_id=job.id,
        ws_url=ws_url,
        status="queued"
    )
    
    return JSONResponse(content={
        "success": True,
        "data": response_data.model_dump(mode='json')
    })

