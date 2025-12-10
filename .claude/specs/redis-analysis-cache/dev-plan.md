# Redis 分析结果缓存机制 - 开发计划

## 概述
为 Telegram Bot 实现 Redis 分析结果缓存机制，通过缓存完整分析结果减少重复计算，支持 30 分钟 TTL 自动过期、手动缓存清除命令，以及 Redis 不可用时的降级模式。

## 任务拆解

### Task 1: Redis 配置与环境变量
- **ID**: task-1
- **Description**: 在 `bot/config.py` 添加 Redis 相关配置参数（URL、TTL、启用开关），更新 `.env.example` 添加 `REDIS_URL`、`BOT_CACHE_ENABLED`、`BOT_CACHE_TTL_SECONDS` 配置说明，确保配置在 Bot 启动时正确加载并验证
- **File Scope**:
  - `bot/config.py` (修改 `BotConfig` 类，添加 Redis 配置属性)
  - `.env.example` (添加 Redis 配置项和详细注释)
- **Dependencies**: None
- **Test Command**:
  ```bash
  pytest tests/test_config.py::test_redis_config --cov=bot/config --cov-report=term -v
  ```
- **Test Focus**:
  - 默认值正确加载（Redis URL: redis://localhost:6379/0, TTL: 1800 秒, ENABLED: true）
  - 环境变量覆盖默认值
  - 配置类型正确（TTL 为整数，ENABLED 为布尔值）
  - 无效配置值处理（如 TTL 为负数时使用默认值）
  - 配置单例模式正确工作

### Task 2: Redis 客户端封装模块
- **ID**: task-2
- **Description**: 创建 `bot/cache.py` 模块，实现 `CacheClient` 类封装 Redis 操作（get/set/clear_prefix），集成连接池管理，实现错误降级逻辑（Redis 不可用时返回 None 而非崩溃），支持 JSON 序列化存储复杂对象
- **File Scope**:
  - `bot/cache.py` (新建，实现 `CacheClient` 类)
- **Dependencies**: None
- **Test Command**:
  ```bash
  pytest tests/test_cache.py --cov=bot/cache --cov-report=term -v -s
  ```
- **Test Focus**:
  - 基本操作：set() 写入，get() 读取，delete() 删除
  - TTL 机制：使用 `EX` 参数设置过期时间
  - 前缀批量删除：clear_prefix() 使用 SCAN + DEL 删除匹配键
  - JSON 序列化：复杂字典正确序列化和反序列化
  - 错误降级：Redis 连接失败时所有方法返回 None/False 而不抛异常
  - 连接池复用：多次调用使用同一连接池
  - 使用 `fakeredis` 模拟 Redis 行为（避免依赖真实 Redis）

### Task 3: 查询哈希与缓存集成
- **ID**: task-3
- **Description**: 在 `bot/handlers.py` 实现查询参数哈希生成逻辑（基于协议名、日期、其他参数的 MD5），在 `_perform_analysis()` 方法前置缓存检查（命中返回缓存结果），分析完成后将 `final_state` 写入 Redis，确保缓存键格式为 `defi_analysis:{protocol}:{date}:{query_hash}`
- **File Scope**:
  - `bot/handlers.py` (修改 `_perform_analysis()` 方法，添加缓存逻辑)
  - `bot/handlers.py` (添加 `_generate_query_hash()` 辅助方法)
- **Dependencies**: 依赖 task-1, task-2（需要 Redis 配置和缓存客户端）
- **Test Command**:
  ```bash
  pytest tests/test_handlers.py::test_cache_integration --cov=bot/handlers --cov-report=term -v -s
  ```
- **Test Focus**:
  - 缓存未命中时执行完整分析并写入缓存
  - 缓存命中时跳过分析直接返回缓存结果
  - query_hash 生成稳定（相同参数生成相同哈希）
  - 缓存键格式正确（`defi_analysis:{protocol}:{date}:{hash}`）
  - 分析失败时不写入缓存
  - 缓存禁用时（`BOT_CACHE_ENABLED=false`）跳过所有缓存逻辑
  - Redis 不可用时降级到无缓存模式（分析正常执行）
  - 多个用户相同查询复用缓存

### Task 4: 缓存标注与清除命令
- **ID**: task-4
- **Description**: 在 `bot/formatters.py` 添加 `add_cache_marker()` 函数为缓存结果添加时间戳标注，在 `bot/telegram_bot.py` 注册 `/clear_cache` 命令，在 `bot/handlers.py` 实现 `clear_cache_command()` 方法（仅管理员可用，调用 `CacheClient.clear_prefix()` 批量删除缓存）
- **File Scope**:
  - `bot/formatters.py` (新增 `add_cache_marker()` 函数)
  - `bot/telegram_bot.py` (注册 CommandHandler)
  - `bot/handlers.py` (实现 `clear_cache_command()` 方法)
- **Dependencies**: 依赖 task-3（需要缓存集成完成）
- **Test Command**:
  ```bash
  # 测试缓存标记
  pytest tests/test_formatters.py::test_add_cache_marker --cov=bot/formatters --cov-report=term -v

  # 测试清除命令
  pytest tests/test_handlers.py::test_clear_cache_command --cov=bot/handlers --cov-report=term -v

  # 集成测试（需要运行 Bot + Redis）
  python3 run_bot.py
  # 手动测试：
  # 1. 发送 /analyze aave-v3 两次，第二次应显示缓存标记
  # 2. 管理员发送 /clear_cache 应返回成功消息
  # 3. 再次查询不显示缓存标记
  ```
- **Test Focus**:
  - 缓存标记正确附加到消息末尾（`\n\n📦 来自缓存（生成于 14:35）`）
  - 时间格式本地化为 HH:MM 格式
  - `/clear_cache` 命令仅管理员可执行（普通用户收到权限拒绝消息）
  - 清除成功后返回友好消息（如"✅ 已清除 15 个缓存条目"）
  - 清除失败时返回错误消息（如 Redis 不可用）
  - 命令不计入速率限制（元命令）
  - 缓存标记不影响消息格式和 Markdown 解析

## 验收标准
- [ ] Redis 缓存配置正确加载（支持环境变量覆盖）
- [ ] 相同查询第二次执行直接返回缓存结果（跳过分析）
- [ ] 缓存结果消息显示生成时间标记（`📦 来自缓存（生成于 XX:XX）`）
- [ ] 缓存 30 分钟后自动过期（TTL 可配置）
- [ ] `/clear_cache` 命令成功清除所有分析缓存（仅管理员可用）
- [ ] Redis 不可用时自动降级到无缓存模式（不影响功能）
- [ ] 所有单元测试通过
- [ ] 代码覆盖率 ≥90%
- [ ] 文档更新：
  - `.env.example` 添加 Redis 配置项
  - `docs/Telegram_Bot_Guide.md` 添加缓存机制说明和 `/clear_cache` 命令文档
  - `PROJECT_STATUS.md` 标记功能完成

## 技术注意事项

### 缓存键设计
```python
# 键格式：defi_analysis:{protocol}:{date}:{query_hash}
# 示例：defi_analysis:aave-v3:2025-12-10:a1b2c3d4

def _generate_cache_key(protocol: str, date: str, **params) -> str:
    """生成缓存键"""
    # 1. 计算参数哈希
    query_hash = _generate_query_hash(**params)

    # 2. 组合键
    return f"defi_analysis:{protocol}:{date}:{query_hash}"

def _generate_query_hash(**params) -> str:
    """生成查询参数哈希（8位）"""
    import hashlib
    import json

    # 排序参数确保稳定性
    sorted_params = json.dumps(params, sort_keys=True)
    return hashlib.md5(sorted_params.encode()).hexdigest()[:8]
```

### Redis 客户端实现
```python
# bot/cache.py
import redis
import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

class CacheClient:
    """Redis 缓存客户端"""

    def __init__(self, redis_url: str, ttl: int = 1800):
        self.ttl = ttl
        self.redis_url = redis_url
        self._client: Optional[redis.Redis] = None
        self._init_client()

    def _init_client(self) -> None:
        """初始化 Redis 客户端（延迟连接）"""
        try:
            self._client = redis.Redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
        except Exception as e:
            logger.warning(f"Redis initialization failed, caching disabled: {e}")
            self._client = None

    def get(self, key: str) -> Optional[dict]:
        """获取缓存值"""
        if not self._client:
            return None

        try:
            value = self._client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Redis GET failed for key {key}: {e}")
            return None

    def set(self, key: str, value: dict) -> bool:
        """设置缓存值（带 TTL）"""
        if not self._client:
            return False

        try:
            self._client.set(
                key,
                json.dumps(value),
                ex=self.ttl  # EX 参数设置秒级 TTL
            )
            return True
        except Exception as e:
            logger.warning(f"Redis SET failed for key {key}: {e}")
            return False

    def clear_prefix(self, prefix: str) -> int:
        """批量删除指定前缀的键"""
        if not self._client:
            return 0

        try:
            count = 0
            cursor = 0
            pattern = f"{prefix}*"

            # 使用 SCAN 避免阻塞
            while True:
                cursor, keys = self._client.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100
                )
                if keys:
                    self._client.delete(*keys)
                    count += len(keys)

                if cursor == 0:
                    break

            return count
        except Exception as e:
            logger.warning(f"Redis CLEAR failed for prefix {prefix}: {e}")
            return 0
```

### 缓存集成逻辑
```python
# bot/handlers.py
async def _perform_analysis(self, protocol: str, date: str, **params) -> dict:
    """执行分析（带缓存）"""
    # 1. 检查缓存是否启用
    if not self.config.cache_enabled:
        return await self._execute_agent_analysis(protocol, date)

    # 2. 生成缓存键
    cache_key = self._generate_cache_key(protocol, date, **params)

    # 3. 尝试获取缓存
    cached_result = self.cache_client.get(cache_key)
    if cached_result:
        logger.info(f"Cache hit for {cache_key}")
        # 添加缓存标记
        cached_result["_from_cache"] = True
        cached_result["_cached_at"] = cached_result.get("_cached_at", time.time())
        return cached_result

    # 4. 缓存未命中，执行分析
    logger.info(f"Cache miss for {cache_key}")
    result = await self._execute_agent_analysis(protocol, date)

    # 5. 写入缓存
    if result:
        result["_cached_at"] = time.time()
        self.cache_client.set(cache_key, result)

    return result
```

### 缓存标记实现
```python
# bot/formatters.py
from datetime import datetime

def add_cache_marker(message: str, cached_at: float) -> str:
    """为缓存结果添加时间戳标记"""
    cached_time = datetime.fromtimestamp(cached_at).strftime("%H:%M")
    marker = f"\n\n📦 来自缓存（生成于 {cached_time}）"
    return message + marker
```

### 清除命令实现
```python
# bot/handlers.py
async def clear_cache_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """清除所有分析缓存（管理员命令）"""
    user_id = update.effective_user.id

    # 1. 权限检查
    if not is_admin(user_id):
        await update.message.reply_text("❌ 此命令仅管理员可用")
        return

    # 2. 清除缓存
    count = self.cache_client.clear_prefix("defi_analysis:")

    # 3. 返回结果
    if count > 0:
        await update.message.reply_text(f"✅ 已清除 {count} 个缓存条目")
    else:
        await update.message.reply_text("ℹ️ 缓存为空或 Redis 不可用")
```

### 错误处理原则
- **Redis 连接失败**：记录警告日志，降级到无缓存模式
- **序列化失败**：捕获异常，返回 None 触发正常分析
- **TTL 过期**：Redis 自动处理，无需手动清理
- **部分写入失败**：记录警告，不影响用户体验

### 性能考虑
- **缓存命中率**：预期 30-50%（相同查询重复请求）
- **响应时间优化**：缓存命中时从 100+ 秒降低到 < 1 秒
- **内存占用**：单个缓存条目约 50-100KB（完整 final_state）
- **Redis 连接池**：使用 `redis.Redis` 自动管理连接复用

### 配置示例
```bash
# .env
# ========== Redis 缓存配置 ==========
# Redis 连接 URL（默认本地 Redis）
REDIS_URL=redis://localhost:6379/0

# 启用缓存（默认 true，设为 false 禁用）
BOT_CACHE_ENABLED=true

# 缓存过期时间（秒，默认 1800 = 30分钟）
BOT_CACHE_TTL_SECONDS=1800
```

### 测试策略
- **单元测试**：使用 `fakeredis` 模拟 Redis 行为（无需真实 Redis）
- **集成测试**：启动真实 Redis 容器验证端到端流程
- **降级测试**：模拟 Redis 不可用场景确保功能正常

### 待办事项与风险
- ⚠️ Redis 容量规划：假设 1000 个活跃协议，每个 100KB，30 分钟内约 100MB
- ⚠️ 缓存失效策略：当前仅支持 TTL 自动过期，未来可扩展基于事件的主动失效
- 🔮 未来可扩展：支持缓存预热（定期刷新热门协议分析）
- 🔮 未来可扩展：支持 Redis Cluster 实现分布式缓存
