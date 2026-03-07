"""
Simple database initialization script
Run this to create database tables without using Alembic

Usage:
    python setup_db.py
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import init_db, engine, settings
from app.models import Job


def setup_database():
    """Create all database tables"""
    print("=" * 60)
    print("Database Setup")
    print("=" * 60)
    print(f"Database URL: {settings.DATABASE_URL}")
    print(f"Database Type: {'SQLite' if 'sqlite' in settings.DATABASE_URL.lower() else 'PostgreSQL'}")
    print()
    
    print("Creating tables...")
    try:
        init_db()
        print()
        print("✅ Setup complete!")
        print()
        print("Tables created:")
        print("  - jobs (for tracking report generation)")
        print()
        print("You can now start the API server:")
        print("  uvicorn app.main:app --reload")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
        print("Troubleshooting:")
        print("1. Make sure .env file exists with DATABASE_URL")
        print("2. Check if database file/server is accessible")
        print("3. Verify all models are imported in database.py")
        return False
    
    return True


if __name__ == "__main__":
    success = setup_database()
    sys.exit(0 if success else 1)