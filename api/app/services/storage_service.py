"""
Storage Service - File management with user-specific directories
"""
import os
import shutil
import uuid
from pathlib import Path
from typing import Optional, BinaryIO
from app.config import settings


class StorageService:
    """Service for managing file storage with user-specific directories"""
    
    def __init__(self):
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def get_user_upload_dir(self, user_id: Optional[int] = None) -> Path:
        """Get user-specific upload directory"""
        if user_id:
            user_dir = self.upload_dir / f"user_{user_id}"
            user_dir.mkdir(parents=True, exist_ok=True)
            return user_dir
        # For backward compatibility, use a shared directory for anonymous users
        anonymous_dir = self.upload_dir / "anonymous"
        anonymous_dir.mkdir(parents=True, exist_ok=True)
        return anonymous_dir
    
    def save_file(self, file_content: bytes, filename: str, file_id: Optional[uuid.UUID] = None, user_id: Optional[int] = None) -> tuple[Path, uuid.UUID]:
        """Save a file to user-specific directory and return its path and ID"""
        if file_id is None:
            file_id = uuid.uuid4()
        
        user_dir = self.get_user_upload_dir(user_id)
        file_path = user_dir / f"{file_id}_{filename}"
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        return file_path, file_id
    
    def save_chunk(self, chunk_content: bytes, file_id: uuid.UUID, chunk_index: int, user_id: Optional[int] = None) -> Path:
        """Save a file chunk to user-specific directory"""
        user_dir = self.get_user_upload_dir(user_id)
        chunk_path = user_dir / f"{file_id}_chunk_{chunk_index}"
        
        with open(chunk_path, "wb") as f:
            f.write(chunk_content)
        
        return chunk_path
    
    def assemble_chunks(self, file_id: uuid.UUID, total_chunks: int, filename: str, user_id: Optional[int] = None) -> tuple[Path, uuid.UUID]:
        """Assemble chunks into a complete file in user-specific directory"""
        user_dir = self.get_user_upload_dir(user_id)
        final_path = user_dir / f"{file_id}_{filename}"
        
        with open(final_path, "wb") as f:
            for i in range(total_chunks):
                chunk_path = user_dir / f"{file_id}_chunk_{i}"
                if chunk_path.exists():
                    with open(chunk_path, "rb") as chunk_file:
                        shutil.copyfileobj(chunk_file, f)
                    # Clean up chunk
                    chunk_path.unlink()
        
        return final_path, file_id
    
    def get_file_path(self, file_id: uuid.UUID, user_id: Optional[int] = None) -> Optional[Path]:
        """Get file path by ID, searching in user directory first, then globally"""
        # First try user-specific directory
        if user_id:
            user_dir = self.get_user_upload_dir(user_id)
            for file_path in user_dir.glob(f"{file_id}_*"):
                if not "_chunk_" in file_path.name:
                    return file_path
        
        # Fallback: search in all directories (for backward compatibility)
        for file_path in self.upload_dir.rglob(f"{file_id}_*"):
            if not "_chunk_" in file_path.name:
                return file_path
        return None
    
    def delete_file(self, file_id: uuid.UUID, user_id: Optional[int] = None) -> bool:
        """Delete a file by ID from user directory"""
        file_path = self.get_file_path(file_id, user_id)
        if file_path and file_path.exists():
            file_path.unlink()
            return True
        return False
    
    def get_user_storage_size(self, user_id: int) -> int:
        """Calculate total storage used by a specific user"""
        user_dir = self.get_user_upload_dir(user_id)
        total_size = 0
        if user_dir.exists():
            for item in user_dir.rglob("*"):
                if item.is_file():
                    total_size += item.stat().st_size
        return total_size
    
    def cleanup_old_files(self, days: int = 7):
        """Clean up files older than specified days"""
        import time
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        
        for file_path in self.upload_dir.iterdir():
            if file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
    
    def delete_user_directory(self, user_id: int) -> bool:
        """Delete entire user directory and all its contents"""
        user_dir = self.get_user_upload_dir(user_id)
        if user_dir.exists():
            try:
                shutil.rmtree(user_dir)
                return True
            except Exception as e:
                print(f"Error deleting user directory {user_dir}: {e}")
                return False
        return True  # Directory doesn't exist, consider it deleted


storage_service = StorageService()

