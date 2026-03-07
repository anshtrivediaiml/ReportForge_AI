"""
Utility script to clear stuck Celery tasks from Redis queue
Run this if Celery is continuously processing old tasks
"""
import redis
from app.config import settings

def clear_celery_queue():
    """Clear all tasks from Celery queue"""
    try:
        # Connect to Redis
        r = redis.from_url(settings.CELERY_BROKER_URL)
        
        # Get all queue names
        queue_name = 'celery'  # Default Celery queue
        
        # Clear the queue
        deleted = r.delete(queue_name)
        
        # Also try to clear any other Celery-related keys
        pattern = 'celery*'
        keys = r.keys(pattern)
        if keys:
            deleted += r.delete(*keys)
        
        print(f"✅ Cleared {deleted} items from Celery queue")
        print("✅ Celery worker should now be idle")
        print("\n⚠️  Restart Celery worker after clearing:")
        print("   celery -A app.core.celery_app worker --loglevel=info --pool=solo")
        
    except Exception as e:
        print(f"❌ Error clearing queue: {e}")
        print("\nMake sure Redis is running:")
        print("   redis-cli ping")

if __name__ == "__main__":
    clear_celery_queue()

