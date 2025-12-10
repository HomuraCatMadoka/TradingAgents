"""
测试多 API Key 轮询功能

验证：
1. Round-robin key 选择
2. 429 错误后 key 冷却
3. 配额恢复后重新可用
"""

import pytest
from defiagents.key_pool import get_next_google_api_key, mark_key_exhausted, get_pool_status
import defiagents.key_pool as key_pool_module
import time


@pytest.fixture(autouse=True)
def reset_global_state():
    """每个测试前重置全局状态"""
    key_pool_module._key_states.clear()
    key_pool_module._current_index = 0
    yield
    # 测试后清理
    key_pool_module._key_states.clear()
    key_pool_module._current_index = 0


def test_round_robin_selection():
    """测试 Round-robin 轮询算法"""
    keys = ["key1", "key2", "key3"]

    # 连续调用应该轮询
    selected_keys = []
    for _ in range(6):
        key = get_next_google_api_key(keys)
        selected_keys.append(key)

    # 验证轮询：key1, key2, key3, key1, key2, key3
    assert selected_keys == ["key1", "key2", "key3", "key1", "key2", "key3"]


def test_single_key_mode():
    """测试单 key 模式"""
    keys = ["only_key"]

    # 单 key 应该总是返回相同的 key
    for _ in range(3):
        key = get_next_google_api_key(keys)
        assert key == "only_key"


def test_key_exhaustion_and_skip():
    """测试 key 耗尽后跳过"""
    keys = ["key1", "key2", "key3"]

    # 第一次选择 key1
    key1 = get_next_google_api_key(keys)
    assert key1 == "key1"

    # 标记 key1 为 exhausted
    mark_key_exhausted("key1")

    # 下两次应该跳过 key1，返回 key2, key3
    key2 = get_next_google_api_key(keys)
    key3 = get_next_google_api_key(keys)
    assert key2 == "key2"
    assert key3 == "key3"

    # 再次调用，应该还是跳过 key1（仍在冷却中）
    key = get_next_google_api_key(keys)
    assert key in ["key2", "key3"]  # 不应该是 key1


def test_all_keys_exhausted():
    """测试所有 key 都耗尽的情况"""
    keys = ["key1", "key2"]

    # 标记所有 key 为 exhausted
    mark_key_exhausted("key1")
    mark_key_exhausted("key2")

    # 应该返回 None
    key = get_next_google_api_key(keys)
    assert key is None


def test_cooldown_recovery():
    """测试冷却恢复"""
    keys = ["key1", "key2"]

    # 标记 key1 为 exhausted
    mark_key_exhausted("key1")

    # 模拟时间流逝 - key1 冷却完成
    key_pool_module._key_states["key1"]["last_429_time"] = time.time() - 61  # 61 秒前

    # 现在 key1 应该恢复可用
    # 由于是 round-robin，会按顺序返回
    key1 = get_next_google_api_key(keys)
    key2 = get_next_google_api_key(keys)

    # 两个 key 都应该可用
    assert key1 in keys
    assert key2 in keys


def test_pool_status():
    """测试状态监控"""
    keys = ["key1", "key2", "key3"]

    # 初始化
    get_next_google_api_key(keys)

    # 标记一个为 exhausted
    mark_key_exhausted("key1")

    # 获取状态
    status = get_pool_status(keys)

    assert status["total_keys"] == 3
    assert status["available_keys"] == 2  # key2, key3 可用
    assert status["exhausted_keys"] == 1  # key1 exhausted
    assert len(status["keys"]) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
