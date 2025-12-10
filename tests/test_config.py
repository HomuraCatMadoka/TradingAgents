import importlib
import pytest
from bot import config as bot_config


def _build_config(monkeypatch, env):
    keys = [
        "REDIS_URL",
        "BOT_CACHE_ENABLED",
        "BOT_CACHE_TTL_SECONDS",
        "TELEGRAM_BOT_TOKEN",
        "BOT_ADMIN_USER_IDS",
    ]
    for key in keys:
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    module = importlib.reload(bot_config)
    module._config_instance = None
    return module


def test_redis_config(monkeypatch):
    module = _build_config(
        monkeypatch,
        {
            "TELEGRAM_BOT_TOKEN": "",
            "BOT_ADMIN_USER_IDS": "abc",
        },
    )
    with pytest.raises(ValueError):
        module.BotConfig()

    module = _build_config(
        monkeypatch,
        {
            "TELEGRAM_BOT_TOKEN": "token-default",
            "REDIS_URL": "",
            "BOT_CACHE_ENABLED": "",
            "BOT_CACHE_TTL_SECONDS": "",
        },
    )
    cfg = module.BotConfig()
    assert cfg.redis_url == module.DEFAULT_REDIS_URL
    assert cfg.cache_enabled is True
    assert cfg.cache_ttl_seconds == module.DEFAULT_CACHE_TTL_SECONDS
    assert cfg.is_admin(0) is False
    assert module._parse_bool(None, False) is False
    assert module._parse_bool("TrUe", False) is True
    assert module._parse_cache_ttl(None) == module.DEFAULT_CACHE_TTL_SECONDS

    module = _build_config(
        monkeypatch,
        {
            "TELEGRAM_BOT_TOKEN": "token-override",
            "REDIS_URL": "redis://cache:6380/2",
            "BOT_CACHE_ENABLED": "false",
            "BOT_CACHE_TTL_SECONDS": "600",
        },
    )
    cfg = module.get_bot_config()
    assert cfg.redis_url == "redis://cache:6380/2"
    assert cfg.cache_enabled is False
    assert cfg.cache_ttl_seconds == 600
    assert module.get_bot_config() is cfg

    module = _build_config(
        monkeypatch,
        {
            "TELEGRAM_BOT_TOKEN": "token-invalid",
            "REDIS_URL": "",
            "BOT_CACHE_ENABLED": "not-a-bool",
            "BOT_CACHE_TTL_SECONDS": "-5",
        },
    )
    cfg = module.BotConfig()
    assert cfg.redis_url == module.DEFAULT_REDIS_URL
    assert cfg.cache_enabled is True
    assert cfg.cache_ttl_seconds == module.DEFAULT_CACHE_TTL_SECONDS
