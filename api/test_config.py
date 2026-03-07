"""
Test configuration loading
Run this to verify all settings are loaded correctly

Usage:
    python test_config.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.config import settings
from app.database import engine


def test_config():
    """Test that configuration loads correctly"""
    print("=" * 60)
    print("Configuration Test")
    print("=" * 60)
    
    print("\n📋 Loaded Settings:")
    print(f"  DATABASE_URL: {settings.DATABASE_URL}")
    print(f"  REDIS_URL: {settings.REDIS_URL}")
    print(f"  API_HOST: {settings.API_HOST}")
    print(f"  API_PORT: {settings.API_PORT}")
    print(f"  FRONTEND_URL: {settings.FRONTEND_URL}")
    print(f"  MAX_FILE_SIZE: {settings.MAX_FILE_SIZE} bytes ({settings.MAX_FILE_SIZE / 1024 / 1024:.1f} MB)")
    print(f"  UPLOAD_DIR: {settings.UPLOAD_DIR}")
    print(f"  OUTPUT_DIR: {settings.OUTPUT_DIR}")
    
    print("\n🔌 Testing Database Connection:")
    try:
        # Try to connect
        with engine.connect() as conn:
            print("  ✅ Database connection successful!")
    except Exception as e:
        print(f"  ❌ Database connection failed: {e}")
        return False
    
    print("\n✅ All tests passed!")
    return True


if __name__ == "__main__":
    success = test_config()
    sys.exit(0 if success else 1)