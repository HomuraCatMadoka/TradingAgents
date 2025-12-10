"""
Google API Key 轮询管理器

提供全局 key 轮询和冷却管理，支持：
1. Round-robin key 选择
2. 429 错误后 key 冷却（60秒）
3. 配额窗口自动重置
"""

import time
import logging
import threading
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# 全局状态（线程安全）
_lock = threading.Lock()
_key_states: Dict[str, Dict] = {}
_current_index = 0


def get_next_google_api_key(api_keys: list, cooldown_dict: Optional[Dict] = None) -> Optional[str]:
    """
    获取下一个可用的 Google API Key（Round-robin + 冷却管理）

    Args:
        api_keys: API Key 列表
        cooldown_dict: 冷却字典（可选，用于跨调用共享状态）

    Returns:
        可用的 API Key，如果所有 key 都在冷却中返回 None
    """
    global _current_index, _key_states, _lock

    if not api_keys:
        return None

    if len(api_keys) == 1:
        # 单 key 模式，直接返回
        return api_keys[0]

    with _lock:
        # 初始化 key 状态
        for key in api_keys:
            if key not in _key_states:
                _key_states[key] = {
                    "last_429_time": None,
                    "is_available": True
                }

        # 尝试找到可用的 key
        now = time.time()
        cooldown_period = 60  # 429 后冷却 60 秒

        for _ in range(len(api_keys)):
            key = api_keys[_current_index]
            _current_index = (_current_index + 1) % len(api_keys)

            state = _key_states[key]

            # 检查是否在冷却中
            if state["last_429_time"]:
                elapsed = now - state["last_429_time"]
                if elapsed < cooldown_period:
                    # 仍在冷却中
                    logger.debug(f"Key {key[:10]}... in cooldown ({cooldown_period - elapsed:.0f}s remaining)")
                    continue
                else:
                    # 冷却完成，重置
                    state["last_429_time"] = None
                    state["is_available"] = True
                    logger.info(f"Key {key[:10]}... cooldown complete, now available")

            # 找到可用 key
            return key

        # 所有 key 都在冷却中
        logger.warning("All API keys are in cooldown period")
        return None


def mark_key_exhausted(key: str) -> None:
    """
    标记 key 已达配额（遇到 429 错误）

    Args:
        key: API Key
    """
    global _key_states, _lock

    with _lock:
        if key in _key_states:
            _key_states[key]["last_429_time"] = time.time()
            _key_states[key]["is_available"] = False
            logger.warning(f"Key {key[:10]}... marked as exhausted (429 error)")


def get_pool_status(api_keys: list) -> Dict:
    """
    获取 key 池状态（用于监控）

    Args:
        api_keys: API Key 列表

    Returns:
        状态字典
    """
    global _key_states, _lock

    with _lock:
        now = time.time()
        available = 0
        exhausted = 0
        details = []

        for key in api_keys:
            if key not in _key_states:
                continue

            state = _key_states[key]
            is_available = state["is_available"]

            if is_available:
                available += 1
            else:
                exhausted += 1

            # 计算恢复时间
            recovery_time = None
            if state["last_429_time"]:
                elapsed = now - state["last_429_time"]
                recovery_time = max(0, 60 - elapsed)

            details.append({
                "key_prefix": key[:10] + "...",
                "available": is_available,
                "recovery_time_seconds": recovery_time
            })

        return {
            "total_keys": len(api_keys),
            "available_keys": available,
            "exhausted_keys": exhausted,
            "keys": details
        }
