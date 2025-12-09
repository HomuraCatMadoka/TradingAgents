# DeFi Telegram Bot - 后续开发计划

> **📌 文档合并通知（2025-12-10）**
>
> 本文档的内容已合并到 **[PROJECT_STATUS.md](../PROJECT_STATUS.md)** 作为活跃的待办清单。
>
> - 🔄 如需查看最新待办事项和状态，请访问 [PROJECT_STATUS.md](../PROJECT_STATUS.md)
> - ✏️ AI 工具在添加/完成功能时，请更新 PROJECT_STATUS.md，而非本文档
> - 📖 本文档保留作为参考，记录初始规划内容

---

## 📋 概述

本文档记录了已完成的核心功能外，后续可以逐步完善的功能和优化项。按优先级和难度分类。

---

## 🔷 中优先级优化（建议在 1-2 个月内完成）

### 1. 分析结果缓存机制 ⏱️ 预计 4-6 小时

**目标：** 相同协议+日期的查询直接返回缓存结果

**实现方案：**
- 使用 Redis 或内存缓存（如 `cachetools.TTLCache`）
- 缓存键：`f"analysis:{protocol}:{date}"`
- TTL：30 分钟（可配置）
- 在返回消息中标注"📦 缓存结果（生成于 XX:XX）"

**预期效果：**
- 重复查询从 108 秒降至 < 1 秒
- 节省 95% LLM 成本
- 减轻 API 压力

**实现位置：**
```python
# bot/handlers.py:263
async def _perform_analysis(self, update: Update, query: str):
    # 1. 检查缓存
    cache_key = f"analysis:{query}:{datetime.now().strftime('%Y-%m-%d')}"
    cached_result = cache.get(cache_key)
    if cached_result:
        # 返回缓存结果
        return cached_result

    # 2. 执行分析
    result = await analysis_task

    # 3. 存入缓存
    cache.set(cache_key, result, ttl=1800)
```

---

### 2. 进度反馈优化 ⏱️ 预计 3-4 小时

**当前问题：**
- 每 10 秒更新一次，某些步骤很快完成但进度卡住
- 8 个固定步骤不够灵活
- 用户看不到实时工具调用

**优化方案：**
- 根据 Agent 完成事件动态更新（而非固定 10 秒）
- 显示当前正在调用的工具名称
- 添加预计剩余时间（基于历史平均值）

**实现示例：**
```
🔄 分析中... (65%)
▓▓▓▓▓▓░░░

🔧 当前步骤：查询 Uniswap 池数据
⏱️ 预计剩余：35 秒
```

**实现位置：**
- `bot/handlers.py:289-316` - 进度更新逻辑
- 使用 LangGraph 的回调机制捕获工具调用事件

---

### 3. 速率限制提示优化 ⏱️ 预计 1-2 小时

**当前提示：**
```
请求过于频繁，请等待{wait_time}秒后再试
```

**优化为：**
```
⏰ 您的请求已达到限制（10次/小时）

剩余时间：5 分钟 30 秒
已使用：10/10

💡 提示：可以先查看之前的分析结果，
或稍后再试。管理员用户无限制。
```

**实现位置：**
- `bot/handlers.py:62-89` - `check_rate_limit()` 方法
- `bot/formatters.py` - 添加 `format_rate_limit_message()` 方法

---

### 4. 添加 `/status` 命令 ⏱️ 预计 2-3 小时

**功能：** 显示系统健康状态和统计信息

**实现示例：**
```
📊 系统状态

**数据源健康度**
✅ DeFi Llama API: 正常
⚠️ The Graph API: 部分可用 (Uniswap ✅, Aave ⚠️)
✅ CoinGecko API: 正常
✅ Gemini LLM: 正常

**使用统计**
📈 今日分析次数: 15
⏱️ 平均响应时间: 105 秒
💰 今日成本: $0.00 (免费额度)

**您的使用情况**
📊 今日请求: 3/10
⏰ 速率限制重置: 45 分钟后
```

**实现位置：**
- `bot/handlers.py` - 添加 `status_command()` 方法
- 需要持久化统计数据（可用 SQLite 或 JSON 文件）

---

## 🔶 低优先级功能（2-6 个月内逐步实现）

### 5. 支持更多 DeFi 协议 ⏱️ 持续迭代

**当前支持：**
- ✅ Aave V3（借贷）
- ✅ Uniswap V3（DEX）

**待添加（按优先级）：**

#### 阶段 1（高优先级）
- **Compound V3** - 借贷协议
- **Curve Finance** - 稳定币 DEX
- **Lido** - 流动性质押

#### 阶段 2（中优先级）
- **GMX** - 衍生品
- **MakerDAO** - 稳定币
- **Yearn Finance** - 收益聚合器

#### 阶段 3（低优先级）
- **Balancer** - DEX
- **Synthetix** - 衍生品
- **Rocket Pool** - ETH 质押

**工作量估算：**
- 每个协议：2-4 小时（数据集成 + 工具开发 + 测试）
- 总计：约 20-40 小时

**实现位置：**
- `defiagents/agents/utils/defi_protocol_tools.py` - 新增工具函数
- `defiagents/default_config.py` - 添加子图配置
- `defiagents/dataflows/defi/` - 数据源集成

---

### 6. 数据可视化 ⏱️ 预计 6-8 小时

**功能：** 生成图表并作为图片发送

**实现方案：**
- 使用 `matplotlib` 或 `plotly` 生成图表
- 保存为临时文件
- 通过 Telegram Bot API 发送图片

**可视化内容：**
1. **TVL 趋势图**（30 天历史）
2. **APY 对比柱状图**（多个协议对比）
3. **风险评分雷达图**
4. **收益分解饼图**（交易费 vs 激励 vs 借贷利息）

**实现示例：**
```python
import matplotlib.pyplot as plt
from io import BytesIO

def generate_tvl_chart(protocol: str, data: list) -> BytesIO:
    plt.figure(figsize=(10, 6))
    plt.plot(dates, tvl_values)
    plt.title(f"{protocol} TVL Trend (30 Days)")
    plt.xlabel("Date")
    plt.ylabel("TVL (USD)")

    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return buf

# 在 Bot 中发送
await update.message.reply_photo(photo=chart_image)
```

**实现位置：**
- `defiagents/visualization/` - 新建可视化模块
- `bot/handlers.py` - 分析完成后生成图表

---

### 7. 命令帮助优化 ⏱️ 预计 1-2 小时

**当前 `/help`：** 基础命令列表

**优化后：**
- 添加更多示例
- 分类展示（基础命令 / 高级命令 / 自然语言）
- 添加常见问题解答
- 添加协议列表和支持的链

**实现示例：**
```
📖 **帮助文档**

**基础命令**
/start - 开始使用
/help - 查看帮助
/status - 系统状态

**分析命令**
/analyze <协议> - 分析DeFi协议
  示例：/analyze aave-v3

/strategy [金额] [风险] - 投资策略推荐
  示例：/strategy 100000 low

/compare <协议1> <协议2> - 对比协议
  示例：/compare aave-v3 compound-v3

**自然语言示例**
• "用10万USDC投资低风险协议"
• "找一个APY至少8%的稳定币策略"
• "对比Uniswap和Curve在Arbitrum上的收益"

**支持的协议**
🏦 借贷：Aave V3, Compound V3
💱 DEX：Uniswap V3, Curve
🔐 质押：Lido, Rocket Pool
📊 衍生品：GMX, dYdX

**支持的链**
Ethereum, Arbitrum, Optimism, Base, Polygon

**常见问题**
Q: 分析需要多久？
A: 通常 1-2 分钟

Q: 支持哪些语言？
A: 中文和英文

Q: 数据来源？
A: DeFi Llama, The Graph, CoinGecko等
```

---

### 8. 订阅通知功能 ⏱️ 预计 8-12 小时

**功能：** 用户订阅特定协议，价格/APY 变化时自动通知

**实现方案：**

#### 8.1 订阅管理
```
/subscribe <协议> [条件]

示例：
/subscribe aave-v3 apy>8%
/subscribe uniswap-v3 tvl_change>10%

/unsubscribe <协议>
/list_subscriptions
```

#### 8.2 后台监控
- 每小时检查一次订阅协议的数据
- 满足条件时发送通知

#### 8.3 通知示例
```
🔔 **订阅提醒**

Aave V3 USDC 存款 APY 变化

📊 当前 APY: 9.2%（↑ 15%）
💡 您的订阅条件已满足（APY > 8%）

🔗 查看详情：/analyze aave-v3
```

**技术要求：**
- 数据库存储订阅信息（SQLite/PostgreSQL）
- 后台定时任务（`apscheduler` 或 `celery`）
- 推送通知（Telegram Bot API）

**数据库设计：**
```sql
CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY,
    user_id BIGINT NOT NULL,
    protocol TEXT NOT NULL,
    condition_type TEXT,  -- 'apy', 'tvl_change', 'price'
    threshold FLOAT,
    created_at TIMESTAMP,
    UNIQUE(user_id, protocol, condition_type)
);
```

**实现位置：**
- `bot/subscriptions.py` - 订阅管理模块
- `bot/monitor.py` - 后台监控任务
- `bot/database.py` - 数据库操作

---

## 🔻 长期愿景功能（6 个月以上）

### 9. 多语言支持 ⏱️ 预计 10-15 小时

**支持语言：** 英文、中文、日文、韩文

**实现方案：**
- 使用 `gettext` 或 `babel` 国际化框架
- 用户设置语言：`/language en`
- 自动检测消息语言

---

### 10. 高级策略推荐 ⏱️ 预计 20-30 小时

**功能：**
- 多协议组合推荐
- 风险对冲策略
- 收益最大化组合
- 根据用户历史偏好推荐

**示例：**
```
/advanced_strategy 100000 medium

推荐组合：
1. 60% Aave V3 USDC (低风险, 5% APY)
2. 30% Uniswap V3 ETH/USDC (中风险, 12% APY)
3. 10% GMX GLP (高风险, 18% APY)

预期年化收益：8.5%
风险评级：中等
```

---

### 11. Web 仪表板 ⏱️ 预计 40-60 小时

**功能：**
- 可视化分析报告
- 历史分析记录
- 实时数据监控
- 用户账户管理

**技术栈：**
- 前端：React + Tailwind CSS
- 后端：FastAPI
- 数据库：PostgreSQL
- 部署：Vercel/Netlify + Railway

---

### 12. Discord Bot ⏱️ 预计 6-8 小时

**功能：** 与 Telegram Bot 功能对等

**实现位置：**
- `bot/discord_bot.py` - 使用 `discord.py` 库
- 复用 `bot/handlers.py` 和 `bot/formatters.py` 逻辑

---

### 13. SaaS 订阅系统 ⏱️ 预计 30-40 小时

**功能：**
- 免费层：10 次/天
- 基础版：$9.9/月，100 次/天
- 专业版：$29.9/月，无限次 + 高级功能

**支付集成：** Stripe

---

## 📊 开发优先级建议

### 短期（1-2 个月）
1. ✅ 分析结果缓存机制（影响大，实现简单）
2. ✅ 进度反馈优化（用户体验提升）
3. ✅ `/status` 命令（实用且易实现）

### 中期（3-6 个月）
4. 支持更多协议（阶段 1: Compound, Curve, Lido）
5. 数据可视化（差异化功能）
6. 订阅通知功能（提升用户粘性）

### 长期（6 个月以上）
7. 高级策略推荐
8. Web 仪表板
9. Discord Bot
10. SaaS 订阅系统

---

## 🛠️ 技术债务

### 需要重构的部分

1. **The Graph 子图配置管理**
   - 当前：硬编码 deployment ID
   - 改进：动态获取最新 deployment ID（The Graph API）

2. **错误处理标准化**
   - 当前：各模块错误处理不一致
   - 改进：统一错误处理中间件

3. **测试覆盖率**
   - 当前：< 30%
   - 目标：> 80%

4. **文档完善**
   - API 文档（Swagger）
   - 架构文档
   - 贡献指南

---

## 📝 注意事项

1. **保持简洁原则**：不要过度设计，先实现核心功能
2. **用户反馈驱动**：根据实际用户需求调整优先级
3. **性能监控**：每次新增功能后监控响应时间和成本
4. **向后兼容**：API 变更时保持向后兼容

---

## 🔗 相关文档

- [Telegram Bot 使用指南](./Telegram_Bot_Guide.md)
- [安全增强计划](./Security_Enhancement_Plan.md)
- [测试文档](../测试文档.md)
- [开发日志](../DeFiAgent_CHANGELOG.md)

---

**最后更新：** 2025-12-10
**维护者：** DeFi Agent 开发团队
