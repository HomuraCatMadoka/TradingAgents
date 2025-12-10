"""Redis 持久化速率限制器，支持内存降级。"""
from __future__ import annotations

import logging
import time
from threading import Lock
from typing import Callable, Dict, Optional, Tuple

import redis

logger = logging.getLogger(__name__)


class RedisRateLimiter:
    """Redis 持久化速率限制器."""

    def __init__(
        self,
        redis_client: Optional[redis.Redis],
        window_seconds: int,
        max_requests: int,
        time_func: Optional[Callable[[], float]] = None,
    ):
        """
        Args:
            redis_client: Redis 客户端（如为 None，降级到内存模式）
            window_seconds: 时间窗口（秒）
            max_requests: 最大请求数
            time_func: 时间函数，便于测试注入
        """
        self.redis_client = redis_client
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        self.time_func = time_func or time.time

        self.memory_tracker: Dict[int, list[float]] = {}
        self.use_redis = redis_client is not None
        self._lock = Lock()

    def check_and_record(self, user_id: int) -> Tuple[bool, Optional[str]]:
        """检查速率限制并记录请求."""
        if self.use_redis:
            return self._check_redis(user_id)
        return self._check_memory(user_id)

    def _check_redis(self, user_id: int) -> Tuple[bool, Optional[str]]:
        """使用 Redis Sorted Set 检查速率限制."""
        client = self.redis_client
        if client is None:
            self.use_redis = False
            return self._check_memory(user_id)

        key = f"rate_limit:{user_id}"
        now = self.time_func()
        window_start = now - self.window_seconds

        try:
            client.zremrangebyscore(key, 0, window_start)
            count = client.zcard(key)
            if count >= self.max_requests:
                oldest = client.zrange(key, 0, 0, withscores=True)
                if oldest:
                    oldest_time = oldest[0][1]
                    wait_time = max(0, int(oldest_time + self.window_seconds - now))
                    return False, f"请求过于频繁，请等待{wait_time}秒后再试"
                return False, "请求过于频繁，请稍后再试"

            client.zadd(key, {str(now): now})
            client.expire(key, self.window_seconds + 60)
            return True, None
        except Exception as exc:  # pragma: no cover - 避免 Redis 故障影响功能
            logger.error("Redis rate limit check failed: %s, falling back to memory", exc)
            self.use_redis = False
            return self._check_memory(user_id)

    def _check_memory(self, user_id: int) -> Tuple[bool, Optional[str]]:
        """内存降级模式."""
        now = self.time_func()
        window_start = now - self.window_seconds

        with self._lock:
            timestamps = [ts for ts in self.memory_tracker.get(user_id, []) if ts > window_start]
            self.memory_tracker[user_id] = timestamps

            if len(timestamps) >= self.max_requests:
                if timestamps:
                    wait_time = max(0, int(timestamps[0] + self.window_seconds - now))
                else:
                    wait_time = max(0, int(self.window_seconds))
                return False, f"请求过于频繁，请等待{wait_time}秒后再试"

            self.memory_tracker[user_id].append(now)
        return True, None

    def get_user_quota_status(self, user_id: int) -> Dict[str, int]:
        """获取用户配额状态."""
        if self.use_redis and self.redis_client is not None:
            key = f"rate_limit:{user_id}"
            now = self.time_func()
            window_start = now - self.window_seconds

            try:
                self.redis_client.zremrangebyscore(key, 0, window_start)
                used = self.redis_client.zcard(key)
                oldest = self.redis_client.zrange(key, 0, 0, withscores=True)
                reset_in = 0
                if oldest:
                    oldest_time = oldest[0][1]
                    reset_in = max(0, int(oldest_time + self.window_seconds - now))

                return {
                    "used": used,
                    "limit": self.max_requests,
                    "remaining": max(0, self.max_requests - used),
                    "reset_in_seconds": reset_in,
                }
            except Exception as exc:  # pragma: no cover - 避免 Redis 故障影响状态查询
                logger.error("Redis quota status failed: %s, falling back to memory", exc)
                self.use_redis = False

        timestamps = self.memory_tracker.get(user_id, [])
        return {
            "used": len(timestamps),
            "limit": self.max_requests,
            "remaining": max(0, self.max_requests - len(timestamps)),
            "reset_in_seconds": 0,
        }
