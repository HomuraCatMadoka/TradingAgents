import pytest

from bot.rate_limiter import RedisRateLimiter


class TimeStub:
    def __init__(self, start: float = 0.0, step: float = 1.0):
        self.current = start
        self.step = step

    def __call__(self) -> float:
        value = self.current
        self.current += self.step
        return value


class MockRedis:
    def __init__(self):
        self.store = {}
        self.expiry = {}

    def zremrangebyscore(self, key, min_score, max_score):
        entries = self.store.get(key, [])
        filtered = [(member, score) for member, score in entries if not (min_score <= score <= max_score)]
        self.store[key] = filtered
        return len(entries) - len(filtered)

    def zcard(self, key):
        return len(self.store.get(key, []))

    def zrange(self, key, start, end, withscores=False):
        entries = sorted(self.store.get(key, []), key=lambda item: item[1])
        if end == -1:
            sliced = entries[start:]
        else:
            sliced = entries[start : end + 1]
        if withscores:
            return [(member, score) for member, score in sliced]
        return [member for member, _ in sliced]

    def zadd(self, key, mapping):
        current = {member: score for member, score in self.store.get(key, [])}
        for member, score in mapping.items():
            current[str(member)] = float(score)
        self.store[key] = sorted(current.items(), key=lambda item: item[1])
        return len(mapping)

    def expire(self, key, ttl):
        self.expiry[key] = ttl
        return True


def test_redis_rate_limit_basic():
    """测试 Redis 速率限制基础功能。"""
    redis_client = MockRedis()
    time_stub = TimeStub()
    limiter = RedisRateLimiter(redis_client, window_seconds=60, max_requests=10, time_func=time_stub)

    for _ in range(10):
        allowed, _ = limiter.check_and_record(user_id=123)
        assert allowed

    allowed, reason = limiter.check_and_record(user_id=123)
    assert not allowed
    assert reason is not None and "请求过于频繁" in reason


def test_redis_fallback_to_memory():
    """测试 Redis 不可用时降级到内存。"""
    limiter = RedisRateLimiter(None, window_seconds=60, max_requests=5, time_func=TimeStub())

    assert not limiter.use_redis

    for _ in range(5):
        allowed, _ = limiter.check_and_record(user_id=456)
        assert allowed

    allowed, reason = limiter.check_and_record(user_id=456)
    assert not allowed
    assert reason and "请求过于频繁" in reason


def test_quota_status():
    """测试配额状态查询。"""
    redis_client = MockRedis()
    time_stub = TimeStub()
    limiter = RedisRateLimiter(redis_client, window_seconds=60, max_requests=10, time_func=time_stub)

    for _ in range(3):
        limiter.check_and_record(user_id=789)

    status = limiter.get_user_quota_status(user_id=789)
    assert status["used"] == 3
    assert status["remaining"] == 7
    assert status["limit"] == 10
