"""
Database Models
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Enum, Text, BigInteger, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, timezone
from app.database import Base
from app.utils.time_utils import get_accurate_utc_time
import enum


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Stage(str, enum.Enum):
    PARSER = "parser"
    PLANNER = "planner"
    WRITER = "writer"
    BUILDER = "builder"
    COMPLETE = "complete"


class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # User relationship (nullable for backward compatibility with existing data)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    user = relationship("User", back_populates="jobs")
    
    # Report metadata
    title = Column(String(200), nullable=True)  # User can name their report
    original_filename = Column(String(255), nullable=True)  # Combined filename for display
    file_size = Column(BigInteger, nullable=True)  # bytes (combined PDF + ZIP)
    
    # File information
    guidelines_filename = Column(String(255), nullable=False)
    project_filename = Column(String(255), nullable=False)
    guidelines_path = Column(String(500), nullable=False)
    project_path = Column(String(500), nullable=False)
    output_path = Column(String(500), nullable=True)
    output_filename = Column(String(255), nullable=True)
    
    # Status tracking
    status = Column(
        Enum(JobStatus),
        default=JobStatus.QUEUED,
        nullable=False,
        index=True
    )
    current_stage = Column(
        Enum(Stage),
        nullable=True
    )
    progress = Column(Integer, default=0)  # 0-100
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: get_accurate_utc_time(), nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    processing_time = Column(Float, nullable=True)  # seconds
    
    # Metrics
    files_analyzed = Column(Integer, default=0)
    chapters_created = Column(Integer, default=0)
    sections_written = Column(Integer, default=0)
    total_sections = Column(Integer, default=0)
    pages_generated = Column(Integer, default=0)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    error_traceback = Column(Text, nullable=True)
    
    # Additional metadata (renamed to avoid SQLAlchemy conflict)
    job_metadata = Column(JSON, default={})  # Store flexible data
    
    def __repr__(self):
        return f"<Job(id={self.id}, status={self.status}, progress={self.progress})>"

