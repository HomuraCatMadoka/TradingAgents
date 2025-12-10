import importlib
import os

import pytest
from bot import config as bot_config


def _build_config(monkeypatch, env):
    keys = [
        "REDIS_URL",
        "BOT_CACHE_ENABLED",
        "BOT_CACHE_TTL_SECONDS",
        "TELEGRAM_BOT_TOKEN",
        "BOT_ADMIN_USER_IDS",
        "BOT_AUDIT_ENABLED",
        "BOT_AUDIT_DB_PATH",
    ]
    for key in keys:
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    module = importlib.reload(bot_config)
    module._config_instance = None
    return module


def _reload_default_config(monkeypatch, env):
    keys = ["MESSARI_API_KEY", "MESSARI_DEPLOYMENT_JSON_PATH"]
    for key in keys:
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)

    module = importlib.import_module("defiagents.default_config")
    return importlib.reload(module)


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
    assert cfg.audit_enabled is True
    assert cfg.audit_db_path == module.DEFAULT_AUDIT_DB_PATH
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


def test_messari_config(monkeypatch, tmp_path, caplog):
    caplog.clear()
    module = _reload_default_config(monkeypatch, {})
    messari_cfg = module.DEFAULT_CONFIG["messari"]
    expected_path = os.path.abspath(
        os.path.join(
            os.path.dirname(module.__file__),
            "../subgraph/deployment/deployment.json",
        )
    )

    assert messari_cfg["api_key"] == ""
    assert messari_cfg["deployment_json_path"] == expected_path

    priority = module.DEFAULT_CONFIG["data_source_priority"]
    assert priority["protocol_tvl"] == [
        "messari",
        "defillama",
        "the_graph",
        "onchain_rpc",
    ]
    assert priority["lending_markets"] == ["messari", "the_graph", "defillama"]
    assert priority["dex_pools"] == ["messari", "the_graph"]
    assert priority["token_prices"] == ["coingecko", "defillama"]

    module.validate_messari_config(module.DEFAULT_CONFIG)
    assert not caplog.records

    caplog.clear()
    custom_path = tmp_path / "deployment.json"
    custom_path.write_text("{}", encoding="utf-8")
    module = _reload_default_config(
        monkeypatch,
        {
            "MESSARI_API_KEY": "override-key",
            "MESSARI_DEPLOYMENT_JSON_PATH": str(custom_path),
        },
    )
    messari_cfg = module.DEFAULT_CONFIG["messari"]
    assert messari_cfg["api_key"] == "override-key"
    assert messari_cfg["deployment_json_path"] == str(custom_path)
    assert module.DEFAULT_CONFIG["data_source_priority"]["protocol_tvl"][0] == "messari"
    module.validate_messari_config(module.DEFAULT_CONFIG)
    assert not caplog.records

    caplog.clear()
    missing_path = tmp_path / "missing.json"
    module.DEFAULT_CONFIG["messari"]["deployment_json_path"] = str(missing_path)
    with caplog.at_level("WARNING"):
        module.validate_messari_config(module.DEFAULT_CONFIG)
    assert any("Deployment JSON not found" in record.message for record in caplog.records)
