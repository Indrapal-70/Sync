import redis
import json
from datetime import datetime
from app.core.config import settings

_redis = redis.from_url(settings.redis_url, decode_responses=True)

def publish_event(event: str, payload: dict) -> None:
    """Publish an event to the sync_events Redis channel."""
    message = {
        "event": event,
        "payload": payload,
        "timestamp": datetime.utcnow().isoformat()
    }
    _redis.publish("sync_events", json.dumps(message))

def get_redis() -> redis.Redis:
    return _redis
