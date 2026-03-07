"""
Script to add password reset columns to users table
Run this once to migrate existing database: python api/add_password_reset_columns.py
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import SessionLocal, engine
from sqlalchemy import text
import sqlite3


def add_password_reset_columns():
    """Add password_reset_token and password_reset_expires columns to users table"""
    db = SessionLocal()
    
    try:
        # Check if columns already exist
        if 'sqlite' in str(engine.url):
            # SQLite - check pragma table_info
            result = db.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result]
            
            if 'password_reset_token' in columns and 'password_reset_expires' in columns:
                print("[OK] Password reset columns already exist. No migration needed.")
                return
            
            # Add columns if they don't exist
            print("Adding password_reset_token column...")
            try:
                db.execute(text("ALTER TABLE users ADD COLUMN password_reset_token VARCHAR(100)"))
                db.commit()
                print("[OK] Added password_reset_token column")
            except Exception as e:
                if "duplicate column" not in str(e).lower():
                    print(f"[WARNING] Error adding password_reset_token: {e}")
                else:
                    print("[OK] password_reset_token column already exists")
            
            print("Adding password_reset_expires column...")
            try:
                db.execute(text("ALTER TABLE users ADD COLUMN password_reset_expires DATETIME"))
                db.commit()
                print("[OK] Added password_reset_expires column")
            except Exception as e:
                if "duplicate column" not in str(e).lower():
                    print(f"[WARNING] Error adding password_reset_expires: {e}")
                else:
                    print("[OK] password_reset_expires column already exists")
        
        else:
            # PostgreSQL - use information_schema
            result = db.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name IN ('password_reset_token', 'password_reset_expires')
            """))
            existing_columns = [row[0] for row in result]
            
            if 'password_reset_token' not in existing_columns:
                print("Adding password_reset_token column...")
                db.execute(text("ALTER TABLE users ADD COLUMN password_reset_token VARCHAR(100)"))
                db.commit()
                print("[OK] Added password_reset_token column")
            else:
                print("[OK] password_reset_token column already exists")
            
            if 'password_reset_expires' not in existing_columns:
                print("Adding password_reset_expires column...")
                db.execute(text("ALTER TABLE users ADD COLUMN password_reset_expires TIMESTAMP WITH TIME ZONE"))
                db.commit()
                print("[OK] Added password_reset_expires column")
            else:
                print("[OK] password_reset_expires column already exists")
        
        print("\n" + "=" * 60)
        print("[SUCCESS] Database migration completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"[ERROR] Error during migration: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    add_password_reset_columns()

