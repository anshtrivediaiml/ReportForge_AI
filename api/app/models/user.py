"""
User Model for Authentication
"""
from sqlalchemy import Column, String, Integer, Boolean, BigInteger, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database import Base


class AuthProvider(str, enum.Enum):
    """Authentication provider types"""
    EMAIL = "email"
    GOOGLE = "google"
    GITHUB = "github"


class User(Base):
    """User model for authentication and user management"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=True, index=True)
    hashed_password = Column(String(255), nullable=True)  # NULL for OAuth users
    full_name = Column(String(200), nullable=True)
    profile_picture = Column(String(500), nullable=True)  # URL to avatar
    
    # Authentication
    auth_provider = Column(SQLEnum(AuthProvider), default=AuthProvider.EMAIL, nullable=False)
    oauth_id = Column(String(100), nullable=True)  # Google/GitHub user ID
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String(100), nullable=True)
    password_reset_token = Column(String(100), nullable=True)
    password_reset_expires = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Storage and usage
    storage_used = Column(BigInteger, default=0, nullable=False)  # bytes
    reports_generated = Column(Integer, default=0, nullable=False)
    
    # Relationship to jobs (reports)
    jobs = relationship("Job", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, provider={self.auth_provider})>"

