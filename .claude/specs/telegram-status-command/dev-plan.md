# Telegram Bot /status 命令 - 开发计划

## 概述
为 Telegram Bot 实现系统状态监控命令，显示数据源健康度、用户速率限制状态，以及管理员专属的全局统计信息。

## 任务拆解

### Task 1: 实现数据源健康检查模块
- **ID**: task-1
- **Description**: 创建统一的健康检查模块，为 4 个关键数据源（DeFi Llama, The Graph, CoinGecko, Gemini LLM）实现轻量级健康检查逻辑，并实现 5 分钟 TTL 缓存机制以避免频繁 API 调用
- **File Scope**:
  - `defiagents/dataflows/defi/health_checker.py` (新建)
  - `defiagents/dataflows/defi/defillama.py` (读取现有客户端)
  - `defiagents/dataflows/defi/the_graph.py` (读取现有客户端)
  - `defiagents/dataflows/defi/coingecko.py` (读取现有 ping 方法)
  - `gemini_config.py` (读取配置)
- **Dependencies**: None
- **Test Command**:
  ```bash
  pytest tests/test_health_checker.py --cov=defiagents/dataflows/defi/health_checker --cov-report=term -v
  ```
- **Test Focus**:
  - 每个数据源的健康检查返回正确状态（online/offline/degraded）
  - 缓存机制正确工作（首次调用实时检测，后续 5 分钟内返回缓存结果）
  - API 失败时返回 offline 状态而非崩溃
  - 超时处理（每个检查限制 5 秒）
  - 模拟 API 故障场景（使用 mock）

### Task 2: 扩展速率限制逻辑与统计收集
- **ID**: task-2
- **Description**: 在现有 `CommandHandlers` 类中扩展速率限制机制，添加全局请求统计（总请求数、时间窗口开始时间）和管理员权限检查逻辑（读取 `BOT_ADMIN_USER_IDS` 环境变量实现速率限制豁免）
- **File Scope**:
  - `bot/handlers.py` (修改 `CommandHandlers` 类)
  - `bot/config.py` (新增管理员配置项)
  - `.env.example` (添加 `BOT_ADMIN_USER_IDS` 说明)
- **Dependencies**: None
- **Test Command**:
  ```bash
  pytest tests/test_rate_limit.py --cov=bot/handlers --cov-report=term -v -s
  ```
- **Test Focus**:
  - 管理员用户绕过速率限制检查
  - 普通用户触发速率限制时返回友好错误消息
  - 全局统计正确累加（跨用户请求计数）
  - 时间窗口重置后计数正确清零
  - 并发请求场景下计数准确（线程安全）
  - 无效管理员 ID 格式处理

### Task 3: 实现状态消息格式化器
- **ID**: task-3
- **Description**: 在 `bot/formatters.py` 添加 `format_status_message()` 函数，根据用户角色（普通/管理员）生成不同视图的状态报告，遵循现有 emoji 和 Markdown 风格，包含数据源健康度、速率限制状态、管理员专属统计
- **File Scope**:
  - `bot/formatters.py` (新增格式化函数)
- **Dependencies**: None
- **Test Command**:
  ```bash
  pytest tests/test_formatters.py::test_format_status_message --cov=bot/formatters --cov-report=term -v
  ```
- **Test Focus**:
  - 普通用户视图包含：数据源健康度、个人速率限制状态（已用/总配额、重置时间）
  - 管理员视图额外包含：全局请求数、平均响应时间、所有活跃用户计数
  - emoji 使用正确（✅ online, ❌ offline, ⚠️ degraded）
  - Markdown 格式符合 Telegram 规范（粗体、代码块、换行）
  - 长文本不超过 Telegram 4096 字符限制
  - 时间格式本地化（如"5分钟后重置"）

### Task 4: 注册 /status 命令并实现处理逻辑
- **ID**: task-4
- **Description**: 在 `bot/telegram_bot.py` 注册 `/status` 命令处理器，在 `bot/handlers.py` 实现 `status_command()` 方法，协调调用健康检查模块、统计收集逻辑和格式化器，完成端到端功能集成
- **File Scope**:
  - `bot/telegram_bot.py` (添加 CommandHandler 注册)
  - `bot/handlers.py` (新增 `status_command()` 方法)
- **Dependencies**: 依赖 task-1, task-2, task-3（需要健康检查模块、统计逻辑、格式化器）
- **Test Command**:
  ```bash
  # 单元测试
  pytest tests/test_handlers.py::test_status_command --cov=bot/handlers --cov-report=term -v

  # 集成测试（需要运行 Bot）
  python3 run_bot.py
  # 手动发送 /status 到 Bot 验证输出
  ```
- **Test Focus**:
  - 普通用户调用 `/status` 返回正确格式的状态报告
  - 管理员用户看到额外的全局统计信息
  - 命令调用不计入速率限制（元命令豁免）
  - 数据源健康检查失败时不影响命令响应（降级输出）
  - 异常处理（网络超时、配置缺失）返回友好错误而非崩溃
  - 响应时间 < 3 秒（健康检查有缓存）

## 验收标准
- [ ] `/status` 命令成功显示 4 个数据源的健康状态（online/offline/degraded）
- [ ] 普通用户看到个人速率限制状态（已用次数/总配额、重置时间）
- [ ] 管理员用户额外看到全局统计（总请求数、平均响应时间、活跃用户数）
- [ ] 健康检查实现 5 分钟缓存，避免频繁 API 调用
- [ ] 管理员用户不受速率限制影响（读取 `BOT_ADMIN_USER_IDS` 环境变量）
- [ ] 所有单元测试通过
- [ ] 代码覆盖率 ≥90%
- [ ] 命令响应时间 < 3 秒（95% 情况下）
- [ ] 文档更新：
  - `docs/Telegram_Bot_Guide.md` 添加 `/status` 命令使用说明
  - `.env.example` 添加 `BOT_ADMIN_USER_IDS` 配置项
  - `PROJECT_STATUS.md` 标记功能完成

## 技术注意事项

### 健康检查实现策略
- **DeFi Llama**: 调用 `/protocols` 端点（返回协议列表），响应成功即为 online
- **The Graph**: 执行简单 GraphQL 查询（如查询 Uniswap V3 前 1 个池），返回数据即为 online
- **CoinGecko**: 使用现有 `CoinGeckoAPI.ping()` 方法
- **Gemini LLM**: 检查 `gemini_config.py` 中的 API key 配置是否存在（不实际调用 LLM 避免浪费配额）

### 缓存机制设计
```python
from functools import lru_cache
from datetime import datetime, timedelta

# 使用 TTL 缓存装饰器
@lru_cache(maxsize=1)
def _cached_health_check(timestamp: int):
    # timestamp 每 5 分钟变化一次，触发缓存失效
    return _perform_actual_health_checks()

def get_system_health():
    # 计算当前 5 分钟时间窗口的 ID
    now = datetime.now()
    window_id = int(now.timestamp() // 300)  # 300秒 = 5分钟
    return _cached_health_check(window_id)
```

### 管理员权限判断
```python
# bot/config.py
import os

ADMIN_USER_IDS = set(
    int(uid.strip())
    for uid in os.getenv("BOT_ADMIN_USER_IDS", "").split(",")
    if uid.strip().isdigit()
)

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_USER_IDS
```

### 速率限制豁免模式
```python
# bot/handlers.py
def check_rate_limit(self, user_id: int) -> tuple[bool, str]:
    # 管理员豁免
    if is_admin(user_id):
        return (True, "")

    # 普通用户检查现有逻辑
    # ...
```

### 错误处理原则
- 所有健康检查必须在 5 秒内完成（超时视为 offline）
- 单个数据源失败不影响其他检查（并行执行）
- 配置缺失时返回 "未配置" 状态而非报错
- 网络异常时返回 "降级" 状态（degraded）

### 性能考虑
- 健康检查并行执行（使用 `asyncio.gather()` 或线程池）
- 首次调用可能耗时 3-5 秒，后续 5 分钟内 < 100ms（缓存）
- `/status` 命令本身不计入速率限制（避免用户无法查看限额状态）

### 输出格式示例

**普通用户视图**:
```
📊 系统状态

🔌 数据源健康度
✅ DeFi Llama: Online
✅ The Graph: Online
⚠️ CoinGecko: Degraded (响应慢)
✅ Gemini LLM: Configured

⏱️ 速率限制状态
已使用: 3/10 次
重置时间: 47分钟后
```

**管理员视图** (额外内容):
```
...

📈 全局统计 (仅管理员可见)
总请求数: 1,234 次
活跃用户: 56 人
平均响应时间: 2.3 秒
Bot 运行时间: 3天 12小时
```

### 待办事项与风险
- ⚠️ 健康检查可能增加外部 API 调用量（通过缓存缓解）
- ⚠️ 管理员 ID 存储在环境变量中，重启 Bot 后生效（无需热重载）
- 🔮 未来可扩展：持久化统计数据到 Redis/数据库（当前仅内存）
- 🔮 未来可扩展：Prometheus metrics 端点供外部监控系统抓取
