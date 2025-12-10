import hashlib
import hmac
import json
import logging
import time
from collections.abc import MutableMapping
from typing import Any, Dict, Optional
from urllib.parse import parse_qsl

AUTH_WINDOW_SECONDS = 300

logger = logging.getLogger(__name__)
_replay_cache: MutableMapping[str, int] = {}


def _record_hash(hash_value: str, now: int, cache: MutableMapping[str, int]) -> bool:
    """Return True if the hash was seen within the validity window."""
    expired = [key for key, ts in cache.items() if now - ts > AUTH_WINDOW_SECONDS]
    for key in expired:
        cache.pop(key, None)

    if hash_value in cache:
        return True

    cache[hash_value] = now
    return False


def clear_replay_cache() -> None:
    """Clear the in-memory replay cache (used by tests)."""
    _replay_cache.clear()


def verify_telegram_webapp_data(
    init_data: str,
    bot_token: str,
    *,
    now: Optional[int] = None,
    replay_cache: Optional[MutableMapping[str, int]] = None,
) -> Optional[Dict[str, Any]]:
    """Validate Telegram WebApp initData. Returns parsed data on success."""
    if not init_data or not bot_token:
        logger.warning("Missing initData or bot_token for Telegram auth")
        return None

    cache = replay_cache or _replay_cache
    timestamp = now or int(time.time())

    try:
        params = dict(parse_qsl(init_data, keep_blank_values=True))
        received_hash = params.get("hash")

        if not received_hash:
            logger.warning("Telegram initData missing hash")
            return None

        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(params.items()) if k != "hash"
        )
        secret_key = hashlib.sha256(bot_token.encode()).digest()
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256,
        ).hexdigest()

        if calculated_hash != received_hash:
            logger.warning("Telegram initData hash mismatch")
            return None

        auth_date_raw = params.get("auth_date")
        if not auth_date_raw:
            logger.warning("Telegram initData missing auth_date")
            return None

        auth_date = int(auth_date_raw)
        if abs(timestamp - auth_date) > AUTH_WINDOW_SECONDS:
            logger.warning("Telegram auth expired: age=%s", timestamp - auth_date)
            return None

        if _record_hash(received_hash, timestamp, cache):
            logger.warning("Telegram initData replay detected")
            return None

        user_raw = params.get("user")
        if not user_raw:
            logger.warning("Telegram initData missing user payload")
            return None

        user = json.loads(user_raw)
        if not isinstance(user, dict):
            logger.warning("Telegram user payload malformed")
            return None

        return {"user": user, "auth_date": auth_date, "hash": received_hash}
    except Exception:
        logger.exception("Failed to verify Telegram initData")
        return None
