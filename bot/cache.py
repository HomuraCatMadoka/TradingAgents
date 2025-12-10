"""Redis cache client with graceful degradation."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

import redis

logger = logging.getLogger(__name__)


class CacheClient:
    """Lightweight Redis cache wrapper with JSON serialization and TTL."""

    _pools: Dict[str, redis.ConnectionPool] = {}

    def __init__(self, redis_url: str, ttl: int) -> None:
        self.redis_url = redis_url
        self.ttl = ttl
        self._client: Optional[redis.Redis] = None
        self._init_client()

    def _init_client(self) -> None:
        """Initialise Redis client lazily; disable on failure."""
        try:
            pool = self._pools.get(self.redis_url)
            if pool is None:
                pool = redis.ConnectionPool.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                self._pools[self.redis_url] = pool
            self._client = redis.Redis(connection_pool=pool, decode_responses=True)
        except Exception as exc:  # pragma: no cover - defensive downgrade
            logger.warning("Redis initialization failed, caching disabled: %s", exc)
            self._client = None

    def get(self, key: str) -> Optional[dict]:
        """Fetch cached value and deserialize JSON."""
        client = self._client
        if not client:
            return None
        try:
            value = client.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception as exc:
            logger.warning("Redis GET failed for key %s: %s", key, exc)
            return None

    def set(self, key: str, value: Dict[str, Any]) -> bool:
        """Store value as JSON with TTL."""
        client = self._client
        if not client:
            return False
        try:
            payload = json.dumps(value)
            return bool(client.set(key, payload, ex=self.ttl))
        except Exception as exc:
            logger.warning("Redis SET failed for key %s: %s", key, exc)
            return False

    def clear_prefix(self, prefix: str) -> int:
        """Delete keys matching prefix using SCAN."""
        client = self._client
        if not client:
            return 0
        try:
            total_deleted = 0
            cursor = 0
            pattern = f"{prefix}*"
            while True:
                cursor, keys = client.scan(cursor=cursor, match=pattern, count=100)
                if keys:
                    deleted = client.delete(*keys)
                    total_deleted += int(deleted or 0)
                if cursor == 0:
                    break
            return total_deleted
        except Exception as exc:
            logger.warning("Redis CLEAR failed for prefix %s: %s", prefix, exc)
            return 0
