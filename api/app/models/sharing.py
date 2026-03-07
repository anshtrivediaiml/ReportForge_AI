"""
Report Sharing Model - Shareable links with expiration
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime, timezone
from app.database import Base
import enum


class ShareAccess(str, enum.Enum):
    """Access level for shared reports"""
    VIEW = "view"  # Can only view/download
    COMMENT = "comment"  # Can view and comment (future feature)


class SharedReport(Base):
    """Model for shared reports with shareable links"""
    __tablename__ = "shared_reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Relationship to job (report)
    job_id = Column(UUID(as_uuid=True), ForeignKey('jobs.id', ondelete='CASCADE'), nullable=False, index=True)
    job = relationship("Job", backref="shared_links")
    
    # Relationship to user who shared
    shared_by_user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    shared_by_user = relationship("User", foreign_keys=[shared_by_user_id])
    
    # Shareable link token (unique, used in URL)
    share_token = Column(String(64), unique=True, nullable=False, index=True)
    
    # Access control
    access_level = Column(String(20), default=ShareAccess.VIEW.value, nullable=False)
    requires_password = Column(Boolean, default=False, nullable=False)
    password_hash = Column(String(255), nullable=True)  # Hashed password if required
    
    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=True)  # None = never expires
    is_active = Column(Boolean, default=True, nullable=False)  # Can be deactivated
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    access_count = Column(Integer, default=0, nullable=False)
    
    # Optional description/note
    description = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<SharedReport(id={self.id}, job_id={self.job_id}, token={self.share_token[:8]}...)>"
    
    def is_expired(self) -> bool:
        """Check if the share link has expired"""
        if not self.expires_at:
            return False
        # Ensure both datetimes are timezone-aware for comparison
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            # If expires_at is timezone-naive, assume it's UTC
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) > expires_at
    
    def is_valid(self) -> bool:
        """Check if the share link is valid (active and not expired)"""
        return self.is_active and not self.is_expired()

