"""
Job Service - CRUD operations, artifact cleanup, and storage accounting
"""
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models import Job, JobStatus, User
from app.schemas.job import JobCreate, JobUpdate
from app.services.storage_service import storage_service
from app.utils.time_utils import get_accurate_utc_time


def create_job(
    db: Session,
    job_data: JobCreate,
    guidelines_path: str,
    project_path: str,
    user_id: Optional[int] = None,
    title: Optional[str] = None,
    original_filename: Optional[str] = None,
    file_size: Optional[int] = None,
) -> Job:
    """Create a new job with optional user association."""
    job = Job(
        guidelines_filename=job_data.guidelines_filename,
        project_filename=job_data.project_filename,
        guidelines_path=guidelines_path,
        project_path=project_path,
        status=JobStatus.QUEUED,
        user_id=user_id,
        title=title,
        original_filename=original_filename,
        file_size=file_size,
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


def get_job(db: Session, job_id: UUID, user_id: Optional[int] = None) -> Optional[Job]:
    """Get a job by ID, filtered by user_id for security."""
    query = db.query(Job).filter(Job.id == job_id)
    if user_id is not None:
        query = query.filter(Job.user_id == user_id)
    return query.first()


def update_job(db: Session, job_id: UUID, update_data: JobUpdate, user_id: Optional[int] = None) -> Optional[Job]:
    """Update a job, optionally checking user ownership."""
    job = get_job(db, job_id, user_id=user_id)
    if not job:
        return None

    update_dict = update_data.model_dump(exclude_unset=True)

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
    """Convenience wrapper for update_job."""
    return update_job(db, job_id, update_data)


def list_jobs(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    status: Optional[JobStatus] = None,
    user_id: Optional[int] = None,
) -> tuple[List[Job], int]:
    """List jobs with pagination and user filtering."""
    query = db.query(Job)

    if user_id is None:
        return [], 0

    query = query.filter(Job.user_id == user_id)

    if status:
        query = query.filter(Job.status == status)

    total = query.count()
    jobs = query.order_by(desc(Job.created_at)).offset(skip).limit(limit).all()

    return jobs, total


def get_job_artifact_paths(job: Job) -> list[Path]:
    """Return all filesystem roots associated with a job."""
    job_id = str(job.id)
    paths: list[Path] = []

    if job.user_id is not None:
        paths.append(storage_service.get_job_upload_dir(job.user_id, job_id))

    paths.extend(
        [
            storage_service.get_job_intermediate_dir(job_id),
            storage_service.get_job_final_dir(job_id),
            storage_service.get_job_extract_dir(job_id),
        ]
    )

    if job.output_path:
        output_path = Path(job.output_path)
        final_dir = storage_service.get_job_final_dir(job_id)
        try:
            is_inside_final_dir = output_path.resolve(strict=False).is_relative_to(final_dir.resolve(strict=False))
        except AttributeError:
            output_str = str(output_path.resolve(strict=False))
            final_dir_str = str(final_dir.resolve(strict=False))
            is_inside_final_dir = output_str.startswith(final_dir_str)

        if not is_inside_final_dir:
            paths.append(output_path)

    return paths


def get_job_artifact_size(job: Job) -> int:
    """Return the size of all known artifacts for a job."""
    return storage_service.get_paths_size(get_job_artifact_paths(job))


def cleanup_job_artifacts(job: Job) -> list[str]:
    """Delete all known filesystem artifacts for a job and return failed paths."""
    return storage_service.remove_paths(get_job_artifact_paths(job))


def calculate_user_storage_usage(db: Session, user_id: int) -> int:
    """Calculate storage used by a user across uploads and job runtime artifacts."""
    total_size = storage_service.get_user_storage_size(user_id)
    user_jobs = db.query(Job).filter(Job.user_id == user_id).all()

    runtime_paths = []
    for job in user_jobs:
        runtime_paths.extend(
            [
                storage_service.get_job_intermediate_dir(str(job.id)),
                storage_service.get_job_final_dir(str(job.id)),
                storage_service.get_job_extract_dir(str(job.id)),
            ]
        )

        if job.output_path:
            output_path = Path(job.output_path)
            final_dir = storage_service.get_job_final_dir(str(job.id))
            try:
                is_inside_final_dir = output_path.resolve(strict=False).is_relative_to(final_dir.resolve(strict=False))
            except AttributeError:
                output_str = str(output_path.resolve(strict=False))
                final_dir_str = str(final_dir.resolve(strict=False))
                is_inside_final_dir = output_str.startswith(final_dir_str)

            if not is_inside_final_dir:
                runtime_paths.append(output_path)

    total_size += storage_service.get_paths_size(runtime_paths)
    return total_size


def sync_user_storage_usage(db: Session, user_id: int, commit: bool = True) -> int:
    """Persist the user's storage_used field from the filesystem source of truth."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return 0

    storage_used = calculate_user_storage_usage(db, user_id)
    user.storage_used = storage_used

    if commit:
        db.commit()
        db.refresh(user)

    return storage_used


def delete_job(db: Session, job_id: UUID, user_id: Optional[int] = None) -> bool:
    """Delete a job, clean its artifacts, and resync storage usage."""
    job = get_job(db, job_id, user_id=user_id)
    if not job:
        return False

    target_user_id = job.user_id
    cleanup_job_artifacts(job)

    db.delete(job)
    db.flush()

    if target_user_id is not None:
        sync_user_storage_usage(db, target_user_id, commit=False)

    db.commit()
    return True
