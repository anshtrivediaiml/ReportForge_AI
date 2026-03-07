"""
Database configuration and session management
Supports both SQLite (local dev) and PostgreSQL (production)
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Handle SQLite vs PostgreSQL connection args
connect_args = {}
if "sqlite" in settings.DATABASE_URL.lower():
    connect_args = {"check_same_thread": False}
    # SQLite doesn't need pool settings
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args=connect_args,
        echo=False  # Set to True for SQL debug logs
    )
else:
    # PostgreSQL connection with pooling
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


def get_db():
    """
    Dependency for FastAPI routes to get database session
    Usage: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database (create all tables)
    Called from setup_db.py
    """
    from app.models import Job, User  # Import all models
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")