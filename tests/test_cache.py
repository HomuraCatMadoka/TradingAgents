import re
import time
from types import SimpleNamespace
from typing import Dict, Optional

import pytest

from bot.cache import CacheClient

try:  # Prefer real fakeredis if available
    import fakeredis  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - offline fallback

    class FakeConnectionPool:
        def __init__(self):
            self.store: Dict[str, str] = {}
            self.expiry: Dict[str, float] = {}

        @classmethod
        def from_url(cls, *args, **kwargs):
            return cls()

    class FakeRedis:
        def __init__(self, connection_pool: Optional[FakeConnectionPool] = None, decode_responses: bool = False, **kwargs):
            self.connection_pool = connection_pool or FakeConnectionPool()
            self._store = self.connection_pool.store
            self._expiry = self.connection_pool.expiry
            self._decode_responses = decode_responses

        @classmethod
        def from_url(cls, url, **kwargs):
            pool = kwargs.pop("connection_pool", None)
            return cls(connection_pool=pool or FakeConnectionPool(), decode_responses=kwargs.get("decode_responses", False))

        def set(self, key, value, ex=None):
            self._store[key] = value
            if ex:
                self._expiry[key] = time.time() + ex
            else:
                self._expiry.pop(key, None)
            return True

        def get(self, key):
            self._purge_expired(key)
            return self._store.get(key)

        def delete(self, *keys):
            removed = 0
            for key in keys:
                self._purge_expired(key)
                if key in self._store:
                    del self._store[key]
                    self._expiry.pop(key, None)
                    removed += 1
            return removed

        def scan(self, cursor=0, match=None, count=None):
            self._purge_expired()
            keys = list(self._store.keys())
            if match:
                regex = "^" + re.escape(match).replace("\\*", ".*") + "$"
                keys = [k for k in keys if re.match(regex, k)]
            return 0, keys

        def flushall(self):
            self._store.clear()
            self._expiry.clear()

        def _purge_expired(self, key=None):
            now = time.time()
            targets = [key] if key else list(self._expiry.keys())
            for name in targets:
                expiry = self._expiry.get(name)
                if expiry is not None and expiry <= now:
                    self._store.pop(name, None)
                    self._expiry.pop(name, None)

    fakeredis = SimpleNamespace(FakeRedis=FakeRedis, FakeConnectionPool=FakeConnectionPool)


import bot.cache as cache_module
import redis


@pytest.fixture(autouse=True)
def reset_cache_client_pools():
    cache_module.CacheClient._pools.clear()
    yield
    cache_module.CacheClient._pools.clear()


@pytest.fixture
def cache_client():
    pool = fakeredis.FakeConnectionPool()
    client = CacheClient("redis://localhost:6379/0", ttl=5)
    client._client = fakeredis.FakeRedis(connection_pool=pool, decode_responses=True)
    if hasattr(client._client, "flushall"):
        client._client.flushall()
    return client


def test_set_and_get_roundtrip(cache_client):
    assert cache_client.set("k1", {"foo": "bar"}) is True
    assert cache_client.get("k1") == {"foo": "bar"}


def test_get_missing_returns_none(cache_client):
    assert cache_client.get("missing") is None


def test_json_serialization_roundtrip(cache_client):
    data = {"foo": "bar", "nested": {"count": 2}, "items": [1, 2, 3]}
    cache_client.set("json-key", data)
    assert cache_client.get("json-key") == data


def test_ttl_expiration(monkeypatch):
    pool = fakeredis.FakeConnectionPool()
    client = CacheClient("redis://localhost:6379/0", ttl=1)
    client._client = fakeredis.FakeRedis(connection_pool=pool, decode_responses=True)
    client.set("ttl-key", {"value": 1})
    time.sleep(1.1)
    assert client.get("ttl-key") is None


def test_clear_prefix_deletes_matching(cache_client):
    cache_client.set("cache:1", {"a": 1})
    cache_client.set("cache:2", {"b": 2})
    cache_client.set("other:3", {"c": 3})

    deleted = cache_client.clear_prefix("cache:")

    assert deleted == 2
    assert cache_client.get("cache:1") is None
    assert cache_client.get("other:3") == {"c": 3}


def test_error_downgrade_on_init_failure(monkeypatch):
    def broken_pool(*args, **kwargs):
        raise redis.ConnectionError("boom")

    monkeypatch.setattr(cache_module.redis.ConnectionPool, "from_url", broken_pool)

    client = CacheClient("redis://localhost:6379/0", ttl=5)
    assert client._client is None
    assert client.get("any") is None
    assert client.set("any", {"v": 1}) is False
    assert client.clear_prefix("cache:") == 0


def test_operation_errors_are_swallowed(cache_client, monkeypatch):
    def boom(*args, **kwargs):
        raise redis.RedisError("fail")

    monkeypatch.setattr(cache_client._client, "get", boom)
    monkeypatch.setattr(cache_client._client, "set", boom)
    monkeypatch.setattr(cache_client._client, "scan", boom)

    assert cache_client.get("key") is None
    assert cache_client.set("key", {"v": 1}) is False
    assert cache_client.clear_prefix("cache:") == 0


def test_connection_pool_reused(monkeypatch):
    pool = fakeredis.FakeConnectionPool()
    created = 0

    def pool_factory(*args, **kwargs):
        nonlocal created
        created += 1
        return pool

    monkeypatch.setattr(cache_module.redis.ConnectionPool, "from_url", pool_factory)
    monkeypatch.setattr(cache_module.redis, "Redis", fakeredis.FakeRedis)

    client1 = CacheClient("redis://localhost:6379/0", ttl=5)
    client2 = CacheClient("redis://localhost:6379/0", ttl=5)

    assert created == 1  # second client reuses cached pool
    assert client1._client is not None and client2._client is not None
    assert client1._client.connection_pool is client2._client.connection_pool
