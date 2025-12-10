"""
LLM Pool Manager - 多 API Key 轮询和智能降级

支持：
1. 多 AI Studio Key 轮询（免费配额叠加）
2. 429 错误自动切换下一个 key
3. 配额追踪和恢复检测
4. 可选：Vertex AI 降级（终极后备）
"""

import os
import time
import logging
from typing import List, Optional, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)


class LLMPool:
    """LLM API Key 池管理器，支持轮询和降级"""

    def __init__(
        self,
        api_keys: Optional[List[str]] = None,
        model_name: str = "gemini-2.5-flash",
        quota_window: int = 60,  # 配额窗口（秒）
        enable_vertex_fallback: bool = False,
        vertex_project: Optional[str] = None,
        vertex_location: str = "us-central1"
    ):
        """
        初始化 LLM 池

        Args:
            api_keys: AI Studio API Key 列表（如为 None，从环境变量读取）
            model_name: 模型名称
            quota_window: 配额窗口（秒），默认 60 秒
            enable_vertex_fallback: 是否启用 Vertex AI 降级
            vertex_project: GCP 项目 ID（如果启用降级）
            vertex_location: GCP 区域
        """
        self.model_name = model_name
        self.quota_window = quota_window
        self.enable_vertex_fallback = enable_vertex_fallback
        self.vertex_project = vertex_project
        self.vertex_location = vertex_location

        # 从环境变量或参数加载 API Keys
        if api_keys is None:
            api_keys = self._load_keys_from_env()

        if not api_keys:
            raise ValueError(
                "No API keys provided. Set GOOGLE_API_KEY or GOOGLE_API_KEYS environment variable."
            )

        self.api_keys = api_keys
        self.current_key_index = 0

        # 配额追踪（每个 key 的使用记录）
        self.key_usage: Dict[str, Dict[str, Any]] = {}
        for key in api_keys:
            self.key_usage[key] = {
                "requests": 0,
                "window_start": time.time(),
                "last_429_time": None,
                "is_available": True
            }

        logger.info(f"LLM Pool initialized with {len(api_keys)} API keys for model {model_name}")

    def _load_keys_from_env(self) -> List[str]:
        """从环境变量加载 API Keys"""
        # 支持两种格式：
        # 1. GOOGLE_API_KEY=single_key
        # 2. GOOGLE_API_KEYS=key1,key2,key3（逗号分隔）
        single_key = os.getenv("GOOGLE_API_KEY")
        multi_keys = os.getenv("GOOGLE_API_KEYS")

        keys = []
        if multi_keys:
            keys = [k.strip() for k in multi_keys.split(",") if k.strip()]
        elif single_key:
            keys = [single_key]

        return keys

    def _reset_window_if_needed(self, key: str) -> None:
        """重置配额窗口（如果已过期）"""
        now = time.time()
        usage = self.key_usage[key]

        if now - usage["window_start"] >= self.quota_window:
            # 窗口已过期，重置
            usage["requests"] = 0
            usage["window_start"] = now
            usage["is_available"] = True
            logger.debug(f"Key {key[:10]}... quota window reset")

    def _get_next_available_key(self) -> Optional[str]:
        """获取下一个可用的 API Key（轮询算法）"""
        tried_keys = 0

        while tried_keys < len(self.api_keys):
            # Round-robin 轮询
            key = self.api_keys[self.current_key_index]
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)

            # 检查配额窗口
            self._reset_window_if_needed(key)

            usage = self.key_usage[key]

            # 如果最近遇到 429，检查是否已冷却
            if usage["last_429_time"]:
                cooldown_time = 60  # 429 后等待 60 秒
                if time.time() - usage["last_429_time"] < cooldown_time:
                    tried_keys += 1
                    continue
                else:
                    # 冷却完成，重置
                    usage["last_429_time"] = None
                    usage["is_available"] = True

            # 检查是否可用
            if usage["is_available"]:
                return key

            tried_keys += 1

        # 所有 key 都不可用
        logger.warning("All API keys exhausted")
        return None

    def _mark_key_exhausted(self, key: str) -> None:
        """标记 key 已达配额"""
        usage = self.key_usage[key]
        usage["last_429_time"] = time.time()
        usage["is_available"] = False
        logger.warning(f"Key {key[:10]}... marked as exhausted (429 error)")

    def _track_usage(self, key: str) -> None:
        """追踪 key 使用量"""
        usage = self.key_usage[key]
        usage["requests"] += 1
        logger.debug(f"Key {key[:10]}... usage: {usage['requests']}/{self.quota_window}s window")

    def get_llm(self, **kwargs) -> ChatGoogleGenerativeAI:
        """
        获取可用的 LLM 实例（智能 key 选择）

        Returns:
            ChatGoogleGenerativeAI 实例

        Raises:
            RuntimeError: 如果所有 key 都不可用且无降级方案
        """
        # 尝试获取免费 key
        key = self._get_next_available_key()

        if key:
            self._track_usage(key)
            return ChatGoogleGenerativeAI(
                model=self.model_name,
                google_api_key=key,
                **kwargs
            )

        # 所有免费 key 都不可用
        if self.enable_vertex_fallback and self.vertex_project:
            logger.warning("Falling back to Vertex AI (all free keys exhausted)")
            from langchain_google_vertexai import ChatVertexAI
            return ChatVertexAI(
                model=self.model_name,
                project=self.vertex_project,
                location=self.vertex_location,
                **kwargs
            )

        # 无可用 key 且无降级方案
        raise RuntimeError(
            "All API keys exhausted and no fallback configured. "
            "Wait for quota reset or enable Vertex AI fallback."
        )

    def handle_429_error(self, current_key: str) -> ChatGoogleGenerativeAI:
        """
        处理 429 错误：标记当前 key 为不可用，尝试下一个

        Args:
            current_key: 遇到 429 的 key

        Returns:
            新的 LLM 实例（使用下一个 key）

        Raises:
            RuntimeError: 如果所有 key 都不可用
        """
        self._mark_key_exhausted(current_key)
        return self.get_llm()

    def get_pool_status(self) -> Dict[str, Any]:
        """获取池状态（用于监控）"""
        now = time.time()
        status = {
            "total_keys": len(self.api_keys),
            "available_keys": 0,
            "exhausted_keys": 0,
            "keys_detail": []
        }

        for key in self.api_keys:
            self._reset_window_if_needed(key)
            usage = self.key_usage[key]

            if usage["is_available"]:
                status["available_keys"] += 1
            else:
                status["exhausted_keys"] += 1

            # 计算恢复时间
            recovery_time = None
            if usage["last_429_time"]:
                elapsed = now - usage["last_429_time"]
                recovery_time = max(0, 60 - elapsed)

            status["keys_detail"].append({
                "key_prefix": key[:10] + "...",
                "available": usage["is_available"],
                "requests_in_window": usage["requests"],
                "recovery_time_seconds": recovery_time
            })

        return status


# 单例模式（全局共享 pool）
_quick_think_pool: Optional[LLMPool] = None
_deep_think_pool: Optional[LLMPool] = None


def get_quick_think_pool(config: Dict) -> LLMPool:
    """获取 Quick Think LLM 池（单例）"""
    global _quick_think_pool
    if _quick_think_pool is None:
        _quick_think_pool = LLMPool(
            model_name=config.get("quick_think_llm", "gemini-2.5-flash"),
            enable_vertex_fallback=config.get("enable_vertex_fallback", False),
            vertex_project=config.get("gcp_project"),
            vertex_location=config.get("gcp_location", "us-central1")
        )
    return _quick_think_pool


def get_deep_think_pool(config: Dict) -> LLMPool:
    """获取 Deep Think LLM 池（单例）"""
    global _deep_think_pool
    if _deep_think_pool is None:
        _deep_think_pool = LLMPool(
            model_name=config.get("deep_think_llm", "gemini-2.0-flash-exp"),
            enable_vertex_fallback=config.get("enable_vertex_fallback", False),
            vertex_project=config.get("gcp_project"),
            vertex_location=config.get("gcp_location", "us-central1")
        )
    return _deep_think_pool
