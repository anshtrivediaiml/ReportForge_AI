"""
Time Utilities - Get accurate UTC time using external API as fallback
"""
from datetime import datetime, timezone
import httpx
import logging

logger = logging.getLogger(__name__)

# Cache for API time to avoid too many requests
_cached_time = None
_cache_timestamp = None
CACHE_DURATION_SECONDS = 60  # Cache for 1 minute


def get_accurate_utc_time() -> datetime:
    """
    Get accurate UTC time, using external API as fallback if system time seems off.
    Falls back to system time if API fails.
    """
    global _cached_time, _cache_timestamp
    
    # Use cached time if available and recent
    if _cached_time and _cache_timestamp:
        age = (datetime.now(timezone.utc) - _cache_timestamp).total_seconds()
        if age < CACHE_DURATION_SECONDS:
            return _cached_time
    
    try:
        # Try multiple time APIs for reliability
        time_apis = [
            "http://worldtimeapi.org/api/timezone/Etc/UTC",
            "https://worldtimeapi.org/api/timezone/Etc/UTC",
        ]
        
        for api_url in time_apis:
            try:
                response = httpx.get(api_url, timeout=2.0, follow_redirects=True)
                if response.status_code == 200:
                    data = response.json()
                    utc_time_str = data.get('datetime')
                    if utc_time_str:
                        # Parse the datetime string (format: 2025-12-25T11:21:00.123456+00:00)
                        utc_time = datetime.fromisoformat(utc_time_str.replace('Z', '+00:00'))
                        # Ensure it's timezone-aware UTC
                        if utc_time.tzinfo is None:
                            utc_time = utc_time.replace(tzinfo=timezone.utc)
                        else:
                            utc_time = utc_time.astimezone(timezone.utc)
                        
                        _cached_time = utc_time
                        _cache_timestamp = datetime.now(timezone.utc)
                        logger.debug(f"Got accurate UTC time from API: {utc_time}")
                        return utc_time
            except Exception as api_error:
                logger.debug(f"API {api_url} failed: {api_error}, trying next...")
                continue
    except Exception as e:
        logger.warning(f"All time APIs failed, using system time: {e}")
    
    # Fallback to system time
    system_time = datetime.now(timezone.utc)
    _cached_time = system_time
    _cache_timestamp = system_time
    return system_time

