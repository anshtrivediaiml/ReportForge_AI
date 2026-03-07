"""
WebSocket Service - Real-time communication
"""
from fastapi import WebSocket
from typing import Dict, Set
import json
import asyncio
from datetime import datetime
from app.schemas.websocket import ProgressUpdate, LogMessage, ErrorMessage, ConnectedMessage


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, job_id: str):
        """Accept and register a WebSocket connection"""
        await websocket.accept()
        
        if job_id not in self.active_connections:
            self.active_connections[job_id] = set()
        
        self.active_connections[job_id].add(websocket)
        
        # Send connection confirmation
        await self.send_to_job(job_id, ConnectedMessage(
            job_id=job_id,
            message="Connected to live updates stream",
            timestamp=datetime.utcnow()
        ).model_dump())
    
    def disconnect(self, websocket: WebSocket, job_id: str):
        """Remove a WebSocket connection"""
        if job_id in self.active_connections:
            self.active_connections[job_id].discard(websocket)
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]
    
    async def send_to_job(self, job_id: str, message: dict):
        """Send message to all connections for a job"""
        if job_id not in self.active_connections:
            return
        
        disconnected = set()
        for connection in self.active_connections[job_id]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
        
        # Clean up disconnected connections
        for conn in disconnected:
            self.active_connections[job_id].discard(conn)
    
    async def broadcast_progress(self, job_id: str, update: ProgressUpdate):
        """Broadcast progress update"""
        await self.send_to_job(job_id, update.model_dump())
    
    async def broadcast_log(self, job_id: str, log: LogMessage):
        """Broadcast log message"""
        await self.send_to_job(job_id, log.model_dump())
    
    async def broadcast_error(self, job_id: str, error: ErrorMessage):
        """Broadcast error message"""
        await self.send_to_job(job_id, error.model_dump())


# Global connection manager
connection_manager = ConnectionManager()


def broadcast_progress_sync(job_id: str, data: dict):
    """
    Synchronous wrapper for broadcasting (used by Celery)
    Uses Redis pub/sub to send messages from Celery to FastAPI
    """
    import redis
    from app.config import settings
    from datetime import datetime
    
    try:
        # Ensure all datetime objects are serialized to strings
        def serialize_datetime(obj):
            """Recursively serialize datetime objects in dict"""
            if isinstance(obj, dict):
                return {k: serialize_datetime(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize_datetime(item) for item in obj]
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif hasattr(obj, 'value'):  # Handle Enum objects
                return obj.value
            else:
                return obj
        
        # Serialize any remaining datetime objects
        serialized_data = serialize_datetime(data)
        
        # Connect to Redis
        r = redis.from_url(settings.REDIS_URL, decode_responses=True)
        
        # Publish message to Redis channel
        channel = f"job_updates:{job_id}"
        message_str = json.dumps(serialized_data)
        subscribers = r.publish(channel, message_str)
        
        # Log for debugging (can remove later)
        if subscribers == 0:
            print(f"[WARNING] Published to {channel} but no subscribers (this is OK if WebSocket not connected yet)")
        else:
            print(f"[DEBUG] Published to {channel}, {subscribers} subscriber(s)")
        
        r.close()
        
    except Exception as e:
        # Fallback: just log the error
        import traceback
        print(f"[ERROR] Failed to broadcast via Redis: {e}")
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        print(f"[ERROR] Message data: {data}")

