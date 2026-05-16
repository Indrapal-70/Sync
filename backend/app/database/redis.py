from __future__ import annotations

import redis

from app.core.config import settings

redis_client = redis.Redis.from_url(str(settings.redis_url), decode_responses=True)
