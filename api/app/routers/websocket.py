"""
WebSocket Router
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websocket_service import connection_manager
from uuid import UUID
import json
import asyncio
from datetime import datetime
from app.config import settings

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time progress updates"""
    try:
        # Validate job_id is a valid UUID
        job_uuid = UUID(job_id)
    except ValueError:
        await websocket.close(code=1008, reason="Invalid job ID")
        return
    
    await connection_manager.connect(websocket, job_id)
    print(f"[WebSocket] ✅ Connected WebSocket for job {job_id}")
    
    # Connect to Redis for pub/sub using sync client in async context
    redis_client = None
    pubsub = None
    listener_task = None
    
    try:
        import redis
        # Use sync Redis client (works better with asyncio)
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        pubsub = redis_client.pubsub()
        channel = f"job_updates:{job_id}"
        pubsub.subscribe(channel)
        print(f"[WebSocket] ✅ Subscribed to Redis channel: {channel}")
        
        # Start listening for messages from Redis in background
        async def listen_redis():
            try:
                print(f"[WebSocket] Started Redis listener for job {job_id}, channel: job_updates:{job_id}")
                loop = asyncio.get_event_loop()
                
                while True:
                    # Run blocking Redis call in thread pool
                    try:
                        message = await loop.run_in_executor(
                            None, 
                            lambda: pubsub.get_message(ignore_subscribe_messages=True, timeout=0.5)
                        )
                        
                        if message and message['type'] == 'message':
                            try:
                                data = json.loads(message['data'])
                                await websocket.send_json(data)
                                print(f"[WebSocket] ✅ Sent update to client for job {job_id}: {data.get('type', 'unknown')}")
                            except Exception as e:
                                print(f"[WebSocket] ❌ Error sending message: {e}")
                                import traceback
                                traceback.print_exc()
                    except Exception as e:
                        # Timeout or other error - continue loop
                        await asyncio.sleep(0.1)
                        
            except asyncio.CancelledError:
                print(f"[WebSocket] Redis listener cancelled for job {job_id}")
                pass
            except Exception as e:
                print(f"[WebSocket] Redis listener error: {e}")
                import traceback
                traceback.print_exc()
        
        # Start Redis listener task
        listener_task = asyncio.create_task(listen_redis())
        
        # Send heartbeat every 30 seconds to keep connection alive
        async def send_heartbeat():
            try:
                while True:
                    await asyncio.sleep(30)
                    try:
                        await websocket.send_json({"type": "heartbeat", "timestamp": datetime.utcnow().isoformat()})
                    except:
                        break
            except asyncio.CancelledError:
                pass
        
        heartbeat_task = asyncio.create_task(send_heartbeat())
        
        # Keep connection alive and handle ping/pong
        while True:
            try:
                # Wait for either WebSocket message or timeout
                try:
                    data = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                    
                    # Handle ping for keepalive
                    if data == "ping":
                        await websocket.send_text("pong")
                except asyncio.TimeoutError:
                    # Timeout is fine, just continue the loop
                    continue
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"[WebSocket] Error receiving: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket connection error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if 'heartbeat_task' in locals():
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
        
        if listener_task:
            listener_task.cancel()
            try:
                await listener_task
            except asyncio.CancelledError:
                pass
        
        if pubsub:
            try:
                pubsub.unsubscribe()
                pubsub.close()
            except:
                pass
        
        if redis_client:
            try:
                redis_client.close()
            except:
                pass
        
        connection_manager.disconnect(websocket, job_id)

