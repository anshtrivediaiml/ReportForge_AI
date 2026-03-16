"""
Storage Service - File management and runtime artifact cleanup
"""
import shutil
import time
import uuid
from pathlib import Path
from typing import Iterable, Optional
from app.config import settings


class StorageService:
    """Service for managing persisted and runtime storage paths."""

    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.output_dir = Path(settings.OUTPUT_DIR)
        self.intermediate_output_dir = self.output_dir / "intermediate"
        self.final_output_dir = self.output_dir / "final"
        self.temp_extract_dir = Path("temp_extract")

        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.intermediate_output_dir.mkdir(parents=True, exist_ok=True)
        self.final_output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_extract_dir.mkdir(parents=True, exist_ok=True)

    def get_user_upload_dir(self, user_id: Optional[int] = None) -> Path:
        """Get the upload directory for a user."""
        if user_id:
            user_dir = self.upload_dir / f"user_{user_id}"
            user_dir.mkdir(parents=True, exist_ok=True)
            return user_dir

        anonymous_dir = self.upload_dir / "anonymous"
        anonymous_dir.mkdir(parents=True, exist_ok=True)
        return anonymous_dir

    def get_job_upload_dir(self, user_id: Optional[int], job_id: str) -> Path:
        """Get the job-specific upload directory inside the user's upload root."""
        return self.get_user_upload_dir(user_id) / str(job_id)

    def get_job_intermediate_dir(self, job_id: str) -> Path:
        return self.intermediate_output_dir / f"job_{job_id}"

    def get_job_final_dir(self, job_id: str) -> Path:
        return self.final_output_dir / f"job_{job_id}"

    def get_job_extract_dir(self, job_id: str) -> Path:
        return self.temp_extract_dir / f"job_{job_id}"

    def save_file(
        self,
        file_content: bytes,
        filename: str,
        file_id: Optional[uuid.UUID] = None,
        user_id: Optional[int] = None,
    ) -> tuple[Path, uuid.UUID]:
        """Save a file to a user-specific directory and return its path and ID."""
        if file_id is None:
            file_id = uuid.uuid4()

        user_dir = self.get_user_upload_dir(user_id)
        file_path = user_dir / f"{file_id}_{filename}"

        with open(file_path, "wb") as f:
            f.write(file_content)

        return file_path, file_id

    def save_chunk(self, chunk_content: bytes, file_id: uuid.UUID, chunk_index: int, user_id: Optional[int] = None) -> Path:
        """Save a file chunk to a user-specific directory."""
        user_dir = self.get_user_upload_dir(user_id)
        chunk_path = user_dir / f"{file_id}_chunk_{chunk_index}"

        with open(chunk_path, "wb") as f:
            f.write(chunk_content)

        return chunk_path

    def assemble_chunks(self, file_id: uuid.UUID, total_chunks: int, filename: str, user_id: Optional[int] = None) -> tuple[Path, uuid.UUID]:
        """Assemble chunks into a complete file in a user-specific directory."""
        user_dir = self.get_user_upload_dir(user_id)
        final_path = user_dir / f"{file_id}_{filename}"

        with open(final_path, "wb") as f:
            for i in range(total_chunks):
                chunk_path = user_dir / f"{file_id}_chunk_{i}"
                if chunk_path.exists():
                    with open(chunk_path, "rb") as chunk_file:
                        shutil.copyfileobj(chunk_file, f)
                    chunk_path.unlink()

        return final_path, file_id

    def get_file_path(self, file_id: uuid.UUID, user_id: Optional[int] = None) -> Optional[Path]:
        """Get file path by ID, searching in the user directory first, then globally."""
        if user_id:
            user_dir = self.get_user_upload_dir(user_id)
            for file_path in user_dir.glob(f"{file_id}_*"):
                if "_chunk_" not in file_path.name:
                    return file_path

        for file_path in self.upload_dir.rglob(f"{file_id}_*"):
            if "_chunk_" not in file_path.name:
                return file_path
        return None

    def delete_file(self, file_id: uuid.UUID, user_id: Optional[int] = None) -> bool:
        """Delete a file by ID from the user directory."""
        file_path = self.get_file_path(file_id, user_id)
        if file_path and file_path.exists():
            file_path.unlink()
            return True
        return False

    def get_path_size(self, path: Path) -> int:
        """Return the recursive size of a file or directory."""
        if not path.exists():
            return 0

        if path.is_file():
            try:
                return path.stat().st_size
            except OSError:
                return 0

        total_size = 0
        for item in path.rglob("*"):
            if item.is_file():
                try:
                    total_size += item.stat().st_size
                except OSError:
                    continue
        return total_size

    def get_paths_size(self, paths: Iterable[Path]) -> int:
        """Return the total size of unique filesystem roots."""
        unique_paths: list[Path] = []
        seen = set()

        for path in paths:
            normalized = str(path.resolve(strict=False))
            if normalized in seen:
                continue
            seen.add(normalized)
            unique_paths.append(path)

        return sum(self.get_path_size(path) for path in unique_paths)

    def remove_path(self, path: Path) -> bool:
        """Remove a file or directory if it exists."""
        if not path.exists():
            return True

        try:
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=False)
            else:
                path.unlink(missing_ok=True)
            return True
        except Exception as exc:
            print(f"Warning: failed to remove {path}: {exc}")
            return False

    def remove_paths(self, paths: Iterable[Path]) -> list[str]:
        """Remove multiple filesystem paths and return any failures."""
        failures: list[str] = []
        seen = set()

        for path in paths:
            normalized = str(path.resolve(strict=False))
            if normalized in seen:
                continue
            seen.add(normalized)

            if not self.remove_path(path):
                failures.append(str(path))

        return failures

    def get_user_storage_size(self, user_id: int) -> int:
        """Calculate storage used in the user's upload directory."""
        return self.get_path_size(self.get_user_upload_dir(user_id))

    def cleanup_old_files(self, days: int = 7):
        """Backward-compatible wrapper for stale runtime cleanup."""
        self.cleanup_stale_runtime_artifacts(days=days)

    def cleanup_stale_runtime_artifacts(self, days: int = 7) -> list[str]:
        """Clean runtime artifacts older than the given age and return removed roots."""
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        removed: list[str] = []

        runtime_roots = [
            self.intermediate_output_dir,
            self.temp_extract_dir,
        ]

        for runtime_root in runtime_roots:
            if not runtime_root.exists():
                continue

            for path in runtime_root.iterdir():
                try:
                    modified_time = path.stat().st_mtime
                except OSError:
                    continue

                if modified_time < cutoff_time and self.remove_path(path):
                    removed.append(str(path))

        return removed

    def delete_user_directory(self, user_id: int) -> bool:
        """Delete the entire user upload directory."""
        user_dir = self.get_user_upload_dir(user_id)
        if user_dir.exists():
            return self.remove_path(user_dir)
        return True


storage_service = StorageService()
