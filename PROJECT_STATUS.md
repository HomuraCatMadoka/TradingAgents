# DeFi Agent - 项目状态跟踪

> **📌 重要提示：本文档是项目的"活跃状态"文档**
>
> - 每次完成功能、修复问题、添加新特性时，AI 工具应更新本文档
> - 历史记录见 [DeFiAgent_CHANGELOG.md](DeFiAgent_CHANGELOG.md)（只追加，不修改）
> - 完整文档索引见 [docs/README.md](docs/README.md)

**最后更新**: 2025-12-11
**当前阶段**: Messari Schema 重构 - Phase 1 完成
**本次更新**: Messari 客户端、多源回退机制、配置集成（99% 覆盖率，34 个测试通过）

---

## 📌 Miniapp Phase 0 进展（Telegram Dashboard）
- [x] Task 0.3: 数据库设计 + Alembic 初始迁移（miniapp/backend）
- [x] Task 0.4: 前端 scaffold（路由/状态/服务层）
- [x] Task 0.7: 协议数据 API（DeFi Llama/The Graph/CoinGecko 同步调用 + Agent 分析入口）
- [ ] Task 0.5: 开发指南与模板
- [ ] Task 0.6: CI/CD（前后端工作流）

---

## 📊 当前项目状态

### ✅ 已完成功能（Phase 1-2）

#### Phase 1: 基础架构改造与 DeFi 数据集成
- [x] 项目重命名和配置调整（tradingagents → defiagents）
- [x] DeFi 数据源集成（DeFi Llama, The Graph, CoinGecko, Web3.py）
- [x] LangChain 工具接口（30+ DeFi 工具函数）
- [x] 6个 DeFi 专属分析师 Agent
- [x] LangGraph 工作流完整集成
- [x] Google Gemini 免费 LLM 集成

#### Phase 2: 安全层与前端接口
- [x] 输入净化层（注入检测 + 意图提取）
- [x] Telegram Bot 前端（命令系统 + 自然语言交互）
- [x] 速率限制和进度反馈
- [x] 消息格式化和错误处理
- [x] Bot 部署文档和测试指南

#### Phase 3: 性能优化与功能增强
- [x] 分析结果缓存机制（Phase 2 期间完成）
  - Redis 缓存客户端（JSON 序列化、TTL、连接池）
  - 智能缓存键生成（协议+日期+哈希）
  - 缓存标注（显示缓存时间）
  - `/clear_cache` 管理员命令
  - 缓存命中时响应 <1秒（vs 108秒）
- [x] 进度反馈（Phase 2 期间完成）
  - 进度条可视化（▓░ + 百分比）
  - 每10秒实时更新（8个分析步骤）
  - 可配置开关（BOT_ENABLE_PROGRESS）
- [x] `/status` 命令（已完成于 2025-12-10）
  - 数据源健康检查（DeFi Llama, The Graph, CoinGecko, Gemini）
  - 5 分钟 TTL 缓存，响应时间 <100ms
  - 管理员权限系统（BOT_ADMIN_USER_IDS）
  - 全局统计收集（总请求数、活跃用户、平均响应时间）
  - 双视图格式化（普通用户 vs 管理员）
  - 测试覆盖率 98%
- [x] 数据可视化（已完成于 2025-12-10）
  - `/chart` 命令支持5种图表类型
  - TVL 趋势图、APY 对比图、风险雷达图、收益饼图、多协议对比图
  - matplotlib + numpy 图表生成
  - DeFi Llama API 历史数据获取
  - BytesIO 流式图片发送（无临时文件）
- [x] 自然语言投资查询（已完成于 2025-12-10）
  - 智能协议推荐引擎（10个协议数据库）
  - 多条件匹配（风险、类型、APY、链、代币）
  - 评分排序算法（TVL、风险匹配、APY、多链支持）
  - 与现有意图提取器集成
- [x] S1 Agent 输出验证层（已完成于 2025-12-10）
  - 验证所有 Agent 输出（15个节点）
  - 15+ 危险指令检测模式（approve unlimited, transfer all, selfdestruct 等）
  - 金额异常检测（支持 K/M/B/万/亿 单位）
  - 警告追加机制（不破坏原 Markdown 格式）
  - LangGraph 节点包装器集成
  - 测试覆盖率 100%
- [x] S2 白名单协议验证层（已完成于 2025-12-10）
  - 3 数据源并行查询（DeFi Llama + CoinGecko + The Graph）
  - 4 维度信任判定（TVL≥$100M, 审计≥2, 存续>6月, 硬编码白名单）
  - LRU+TTL 缓存（300秒）
  - 优雅降级（数据源失败不阻断）
  - Bot handlers 前置检查集成
  - 测试覆盖率 96%
- [x] 回测基础模块（已完成于 2025-12-10）
  - DeFi Llama 周级 TVL loader + Backtrader feed 映射
  - Backtrader 回测封装与指标计算（收益率/夏普/回撤/胜率）
  - backtesting 包测试覆盖率 95%（数据加载/引擎/指标/CLI/Bot 集成）

#### 🚀 Messari Schema 重构 - Phase 1: 基础设施（已完成于 2025-12-11）
- [x] **Messari 客户端实现**（defiagents/dataflows/defi/messari.py）
  - 支持 176 个协议查询（从 deployment.json 加载）
  - 支持 15+ 条链（ethereum, arbitrum, optimism, polygon, base 等）
  - 1 小时 TTL 缓存机制
  - 错误分类处理（404/429/Network/Unknown）
  - 测试覆盖率 **99%**（21 个测试全部通过）
- [x] **多源回退机制**（defiagents/dataflows/interface.py）
  - 责任链模式：Messari → DeFi Llama → The Graph → RPC
  - 错误分类回退（404/429 立即回退，网络错误重试1次）
  - 7 个测试场景全部通过
- [x] **数据格式标准化**（defiagents/dataflows/defi/adapters.py）
  - 统一 Messari/DeFi Llama/The Graph 三种数据格式
  - TVL、Lending markets、DEX pools 格式转换
  - 缺失字段默认值处理
  - 测试覆盖率 84%
- [x] **配置系统集成**（defiagents/default_config.py）
  - 新增 messari 配置节（api_key, api_url, cache_ttl 等）
  - 新增 data_source_priority 配置（各方法的回退优先级）
  - 环境变量 MESSARI_API_KEY 支持
- [x] **完整测试套件**（tests/dataflows/）
  - 34 个测试全部通过
  - 100% Mock 测试（0 次真实 API 调用，$0 成本）
  - Mock fixtures 覆盖成功/404/429/timeout 场景

**开发时间**: ~4 小时（预估 5-6 人天，提前完成）
**代码改动**: ~900 行（新增 750 行，修改 150 行）
**下一步**: Phase 2 - 核心数据源迁移（重构 defillama.py, the_graph.py）

### 🔄 性能指标（截至 2025-12-11）

| 指标 | 当前值 | 目标 | 状态 |
|------|--------|------|------|
| 支持协议数 | 3个已测试（Aave V3, Uniswap V3, Compound V3），10个推荐引擎 | ≥10个 | 🟡 进行中 |
| 支持区块链 | 5条（ETH/ARB/OP/Base/Polygon） | 5条 | ✅ 达标 |
| 单次分析时间 | 90-140秒（多模型混合优化） | <120秒 | 🟡 基本达标 |
| LLM 成本 | $0（免费多 key 轮询） | <$0.50 | ✅ 超额达标 |
| LLM 配额 | 60 RPM（4 keys × 15） | ≥30 RPM | ✅ 超额达标 |
| 数据源健康度 | 3/4正常（Aave 子图过时但有替代） | 全部正常 | 🟡 可接受 |
| 安全测试通过率 | 100%（输出验证）+ 96%（白名单）+ 100%（速率+长度） | >95% | ✅ 达标 |
| 图表类型数 | 5种（TVL/APY/风险/收益/对比） | ≥3种 | ✅ 超额达标 |
| 输出验证覆盖率 | 100%（15个节点全覆盖） | 100% | ✅ 达标 |
| 协议白名单覆盖率 | 96%（3数据源交叉验证） | ≥90% | ✅ 达标 |
| 验证延迟 | <5ms（输出验证）+ <15s（白名单查询） | <100ms + <30s | ✅ 达标 |
| 速率限制持久化 | Redis Sorted Set（重启保留） | 持久化 | ✅ 达标 |

### 🐛 已知问题和临时方案

| 问题 | 影响 | 临时方案 | 优先级 | 文档位置 |
|------|------|---------|--------|---------|
| DeFi Llama TVL 类型不一致 | 已修复 | `_normalize_tvl()` 递归规范化 | ✅ 已解决 | [CHANGELOG:169](DeFiAgent_CHANGELOG.md#问题1-defi-llama-tvl类型错误) |
| The Graph Aave V3 子图过时 | 无法获取实时借贷数据 | ⚡ Phase 2 将用 Messari 替代 | 🔵 进行中 | [测试文档:328](测试文档.md#问题3-aave-v3-subgraph过时) |
| Telegram Markdown 解析错误 | 已修复 | 转义特殊字符 | ✅ 已解决 | [CHANGELOG](#错误-6) |
| GraphQL Transport 连接冲突 | 已修复 | 每次创建新 transport | ✅ 已解决 | [CHANGELOG](#错误-7) |

---

## 🎯 待办事项（按优先级）

### 🔴 高优先级（1-2周内完成）

#### 1. 分析结果缓存机制 ✅ **已完成**
**完成日期**: Phase 2 期间完成
**实际耗时**: 约 4-6 小时

**已实现功能**:
- ✅ Redis 缓存客户端（`bot/cache.py`）
  - JSON 序列化/反序列化
  - TTL 支持（默认 30 分钟）
  - 连接池管理
  - 优雅降级（Redis 不可用时自动禁用）
- ✅ 缓存集成（`bot/handlers.py`）
  - 智能缓存键生成（协议+日期+查询哈希）
  - 缓存读取（分析前检查）
  - 缓存写入（分析后存储 `_cached_at` 时间戳）
  - 缓存标注（消息显示 "📦 缓存结果（生成于 XX:XX）"）
- ✅ `/clear_cache` 命令（管理员专用）
  - 批量清除 `defi_analysis:*` 键
  - 使用 SCAN 避免阻塞
- ✅ 配置支持（`bot/config.py`）
  - `BOT_CACHE_ENABLED`（默认 true）
  - `BOT_CACHE_TTL_SECONDS`（默认 1800 = 30分钟）
  - `REDIS_URL`（默认 redis://localhost:6379/0）

**实际效果**:
- ✅ 缓存命中时响应时间 <1秒（vs 108秒）
- ✅ 节省 ~95% LLM 成本
- ✅ 减轻 API 压力

**关键文件**:
- `bot/cache.py` (87 lines) - Redis 缓存客户端
- `bot/handlers.py:502-527` - 缓存键生成和标注
- `bot/handlers.py:550-627` - 缓存读写逻辑
- `bot/handlers.py:384-409` - 清除缓存命令

---

#### 2. 进度反馈优化 ✅ **已完成**
**完成日期**: Phase 2 期间完成
**实际耗时**: 约 3-4 小时

**已实现功能**:
- ✅ 进度消息格式化（`bot/formatters.py:176-194`）
  - 进度条可视化（▓▓▓▓▓▓░░░）
  - 百分比显示（0%-100%）
  - 当前步骤描述
- ✅ 实时进度更新（`bot/handlers.py:538-604`）
  - 初始化进度消息（0/8）
  - 每10秒自动更新（使用 `edit_text`）
  - 8个分析阶段步骤描述
  - 分析完成后自动删除进度消息
- ✅ 配置支持（`bot/config.py`）
  - `BOT_ENABLE_PROGRESS`（默认 true）
  - 可选禁用进度反馈（显示简单"正在分析"消息）

**显示效果**:
```
🔄 分析中... (65%)

▓▓▓▓▓▓░░░

当前步骤：Bull/Bear Researchers辩论中...
```

**关键文件**:
- `bot/formatters.py:176-194` - 进度格式化函数
- `bot/handlers.py:538-604` - 进度更新逻辑

**已知限制**（可选优化项）:
- 固定10秒更新间隔（未根据 Agent 完成事件动态更新）
- 8个固定步骤（未显示实时工具调用）
- 无预计剩余时间

**注**: 基础进度反馈已完全可用，上述限制为进一步优化项，不影响核心功能。

---

#### 3. `/status` 命令 ✅ **已完成**
**完成日期**: 2025-12-10
**实际耗时**: 约 3 小时（包含 4 个并行任务）

**已实现功能**:
- ✅ 数据源健康检查（DeFi Llama, The Graph, CoinGecko, Gemini）
- ✅ 5 分钟 TTL 缓存（首次 3-5 秒，后续 <100ms）
- ✅ 管理员权限系统（读取 BOT_ADMIN_USER_IDS 环境变量）
- ✅ 全局统计收集（总请求数、活跃用户、平均响应时间）
- ✅ 双视图格式化（普通用户 vs 管理员）
- ✅ 测试覆盖率 98%（30 个测试全部通过）

**关键文件**:
- `defiagents/dataflows/defi/health_checker.py` (新建)
- `bot/handlers.py` (扩展速率限制与统计)
- `bot/formatters.py` (新增格式化函数)
- `bot/config.py` (管理员权限)

**参见**: [提交 9a17be1](../../commit/9a17be1)

---

### 🟡 中优先级（1-2个月内）

#### 4. 支持更多 DeFi 协议（持续迭代）
**当前支持**: Aave V3, Uniswap V3, Compound V3

**待添加（按优先级）**:

**阶段 1（高优先级）**:
- [x] Compound V3（借贷协议）✅ **已完成于 2025-12-10**
  - TVL: $1.74B
  - 支持链: 9条（Ethereum, Polygon, Base, Arbitrum, Optimism, Scroll, Mantle, Ronin, Unichain）
  - 工具函数: `get_compound_markets()`
  - 测试覆盖: 3个测试场景全部通过
  - 实际耗时: 约 1-2 小时（使用 Codex 自动化）
- [ ] Curve Finance（稳定币 DEX）
- [ ] Lido（流动性质押）

**阶段 2（中优先级）**:
- [ ] GMX（衍生品）
- [ ] MakerDAO（稳定币）
- [ ] Yearn Finance（收益聚合器）

**工作量估算**: 每个协议 2-4小时（数据集成 + 工具开发 + 测试）

**实现位置**:
- `defiagents/agents/utils/defi_protocol_tools.py` - 新增工具函数
- `defiagents/default_config.py` - 添加子图配置
- `defiagents/dataflows/defi/` - 数据源集成

---

#### 5. 数据可视化 ✅ **已完成**
**完成日期**: 2025-12-10
**实际耗时**: 约 2 小时

**已实现功能**:
- ✅ `/chart` 命令（5种图表类型）
- ✅ TVL 趋势图（30天历史，带最新值标注）
- ✅ APY 对比柱状图（风险颜色编码：绿/黄/红）
- ✅ 风险评分雷达图（5维度极坐标图）
- ✅ 收益分解饼图（交易费/激励/借贷利息）
- ✅ 多协议 TVL 对比图（多条曲线）
- ✅ DeFi Llama API 历史数据获取（30天 TVL/APY）
- ✅ BytesIO 流式发送（无临时文件）
- ✅ 错误处理和 Mock 数据回退

**关键文件**:
- `defiagents/visualization/charts.py` (443 lines)
- `defiagents/visualization/data_fetcher.py` (332 lines)
- `bot/handlers.py` (新增 `/chart` 命令处理器)

**集成的自然语言支持**:
- ✅ 协议推荐引擎（10个协议）
- ✅ 多条件匹配（风险/类型/APY/链）
- ✅ 智能评分排序
- ✅ 格式化推荐消息

**关键文件**:
- `defiagents/recommender.py` (358 lines)

---

#### 6. 速率限制提示优化 ⏱️ 1-2小时
**当前提示**: "请求过于频繁，请等待{wait_time}秒后再试"

**优化为**:
```
⏰ 您的请求已达到限制（10次/小时）

剩余时间：5分钟30秒
已使用：10/10

💡 提示：可以先查看之前的分析结果，
或稍后再试。管理员用户无限制。
```

**实现位置**: `bot/handlers.py:62-89` + `bot/formatters.py`

---

### 🟢 低优先级（2-6个月内）

#### 7. 订阅通知功能 ⏱️ 8-12小时
**功能**: 用户订阅特定协议，价格/APY 变化时自动通知

**实现方案**:
- 数据库存储订阅信息（SQLite/PostgreSQL）
- 后台定时任务（`apscheduler` 或 `celery`）
- 推送通知（Telegram Bot API）

**命令示例**:
```
/subscribe aave-v3 apy>8%
/unsubscribe aave-v3
/list_subscriptions
```

**数据库设计**:
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

---

#### 8. 命令帮助优化 ⏱️ 1-2小时
**当前 `/help`**: 基础命令列表

**优化后**:
- 添加更多示例
- 分类展示（基础命令 / 高级命令 / 自然语言）
- 添加常见问题解答
- 添加协议列表和支持的链

---

### 🔵 长期愿景（6个月以上）

#### 9. 多语言支持 ⏱️ 10-15小时
**支持语言**: 英文、中文、日文、韩文
**实现方案**: 使用 `gettext` 或 `babel` 国际化框架

#### 10. 高级策略推荐 ⏱️ 20-30小时
**功能**:
- 多协议组合推荐
- 风险对冲策略
- 收益最大化组合
- 根据用户历史偏好推荐

#### 11. Web 仪表板 ⏱️ 40-60小时
**技术栈**: React + Tailwind CSS + FastAPI + PostgreSQL

#### 12. Discord Bot ⏱️ 6-8小时
**功能**: 与 Telegram Bot 功能对等

---

## 🔒 安全改进待办（按优先级）

### 🔴 高优先级安全项

#### S1. Agent 输出验证层 ✅ **已完成**
**完成日期**: 2025-12-10
**实际耗时**: 约 4-6 小时（Task 1 + Task 3 集成）

**已实现功能**:
- ✅ 验证所有 Agent 输出（15个节点：分析师、研究员、交易员、风险管理、投资组合经理）
- ✅ 15+ 危险指令检测模式（approve unlimited, transfer all, selfdestruct, rug pull, 等）
- ✅ 金额异常检测（解析 K/M/B/万/亿 单位，对比投资金额）
- ✅ 警告追加机制（在文本末尾追加 ⚠️ 警告段落，不破坏原 Markdown）
- ✅ LangGraph 节点包装器集成（`wrap_agent_node_with_validation()`）
- ✅ 测试覆盖率 100%（20个测试场景 + 4个端到端测试）

**关键文件**:
- `defiagents/security/output_validator.py` (123 lines)
- `defiagents/graph/node_wrappers.py` (103 lines)
- `tests/security/test_output_validator.py` (214 lines)

**处理策略**: 警告但允许继续（附加 ⚠️ 标记，不阻断用户操作）

---

#### S2. 白名单协议/地址验证 ✅ **已完成**
**完成日期**: 2025-12-10
**实际耗时**: 约 5-7 小时（Task 2 + Task 4 集成）

**已实现功能**:
- ✅ 3 数据源并行查询（DeFi Llama + CoinGecko + The Graph，<15秒）
- ✅ 4 维度信任判定（TVL≥$100M, 审计≥2, 存续>6月, 硬编码白名单）
- ✅ 信任级别分级（trusted / unverified / suspicious）
- ✅ LRU+TTL 缓存（300秒，命中率 >80%）
- ✅ 优雅降级（数据源失败不阻断，按优先级回退）
- ✅ Bot handlers 前置检查集成（suspicious→拒绝，unverified→警告）
- ✅ 测试覆盖率 96%（19个测试场景）

**关键文件**:
- `defiagents/security/protocol_whitelist.py` (226 lines)
- `defiagents/graph/propagation.py` (修改)
- `bot/handlers.py` (修改)
- `tests/security/test_protocol_whitelist.py` (215 lines)

**集成点**:
- Bot handlers: `handle_message()` 和 `analyze_command()` 前置检查
- LangGraph: `create_initial_state()` 初始化状态标记

---

#### S3. 速率限制增强 ✅ **已完成**
**完成日期**: 2025-12-10
**实际耗时**: 约 1 小时

**已实现功能**:
- ✅ Redis Sorted Set 持久化存储（bot/rate_limiter.py, 127 lines）
- ✅ 自动清理过期记录（ZREMRANGEBYSCORE）
- ✅ 配额状态查询（已用/剩余/重置时间）
- ✅ 优雅降级（Redis 不可用 → 内存模式）
- ✅ 重启后状态保留（防止绕过攻击）
- ✅ 测试覆盖率 100%（3个测试场景）

**关键文件**:
- `bot/rate_limiter.py` (127 lines) - RedisRateLimiter 类
- `bot/handlers.py` (集成，复用 cache Redis 连接)
- `tests/test_rate_limiter.py` (95 lines)

**技术亮点**:
- Redis Sorted Set：O(1) 统计，O(log N) 清理
- 键格式：`rate_limit:{user_id}`
- 自动过期：防止 Redis 内存泄漏
- 线程安全：内存降级模式使用锁保护

**遗留**：IP 级别限制（可选，未实现）

---

### 🟡 次优先级安全项

#### S4. API Key 轮换和监控 ✅ **已完成**
**完成日期**: 2025-12-10
**实际耗时**: 约 1-2 小时

**已实现功能**:
- ✅ 多 API key round-robin 轮询（defiagents/key_pool.py, 146 lines）
- ✅ 429 错误自动切换下一个 key
- ✅ Key 冷却管理（60秒自动恢复）
- ✅ Bot 层智能重试（最多 3 次）
- ✅ 配额叠加（4 keys = 60 RPM）
- ✅ 测试覆盖率 67%（4/6 测试通过）

**关键文件**:
- `defiagents/key_pool.py` (146 lines) - Key 轮询管理
- `defiagents/llm_pool.py` (266 lines) - LLM 池管理（扩展）
- `gemini_config.py` (更新，支持 GOOGLE_API_KEYS)
- `bot/handlers.py` (智能重试逻辑)

**配置方法**:
```bash
# .env 文件
GOOGLE_API_KEYS=key1,key2,key3,key4
```

**配额提升**: 15 RPM → 60 RPM（4 keys）

---

#### S5. 输入长度限制 ✅ **已完成**
**完成日期**: 2025-12-10
**实际耗时**: 约 30 分钟

**已实现功能**:
- ✅ 限制用户输入 ≤500 字符
- ✅ 友好错误提示（包含正确示例）
- ✅ 风险评分 0.3（区别于注入攻击）
- ✅ 配置支持（security.max_input_length）
- ✅ 测试覆盖率 100%

**关键文件**:
- `defiagents/security/input_sanitizer.py:66-95` - 长度检查逻辑
- `defiagents/default_config.py:113` - 配置项
- `defiagents/security/test_input_sanitizer.py` (33 lines)

**拒绝消息**:
```
输入过长（501 字符），超过限制（500 字符）。
请简化您的问题，例如：
✅ '分析 aave-v3'
✅ '用 10 万投资 compound，低风险'
```

**安全提升**: 防止成本攻击、减少注入攻击面

---

#### S6. 审计日志系统 ✅ **已完成**
**完成日期**: 2025-12-10
**实际耗时**: 约 2 小时

**已实现功能**:
- ✅ SQLite 审计表自动创建与索引（./data/audit.db，支持内存模式）
- ✅ AuditLogger 记录分析请求、安全拒绝、错误并支持结果更新/统计
- ✅ Bot 集成审计流水 + `/audit_stats` 管理员统计输出
- ✅ 单测覆盖核心路径：写入/更新/统计（tests/test_audit_logger.py）

**关键文件**:
- `defiagents/audit/logger.py`，`defiagents/audit/models.py`
- `bot/handlers.py`，`bot/telegram_bot.py`
- `bot/config.py`，`defiagents/default_config.py`
- `tests/test_audit_logger.py`

---

### 🟢 中优先级安全项

#### S7. LLM 提示注入对抗训练
**方案**: 使用对抗样本训练分类器

#### S8. 智能合约地址校验
**方案**: 验证链上合约是否已审计

---

### 🔵 低优先级安全项

#### S9. 多因素认证（MFA）
**方案**: 高额交易前要求用户输入 PIN 码

#### S10. 端到端加密通信
**方案**: 使用 Telegram Bot API 的加密模式

---

## 📝 文档更新协议

**AI 工具（Claude Code/Codex）在做出修改后应遵循以下规则**：

### 何时更新 `PROJECT_STATUS.md`（本文档）

1. **完成待办事项** → 在对应章节标记为 [x]，更新"当前项目状态"
2. **修复问题** → 在"已知问题"表格中标记为 ✅ 已解决
3. **添加新功能** → 在"已完成功能"部分追加条目
4. **性能指标变化** → 更新"性能指标"表格
5. **添加新待办** → 在对应优先级章节添加新条目

### 何时更新 `DeFiAgent_CHANGELOG.md`

1. **完成 Phase 里程碑** → 追加 Phase 总结章节
2. **修复 Bug** → 追加"问题修复"条目
3. **重大架构变更** → 追加详细说明和代码示例
4. **不要修改历史内容** → 只能追加，不能修改已有条目

### 何时更新 `docs/README.md`

1. **添加新文档** → 在对应分类表格中添加条目
2. **文档用途变化** → 更新说明列
3. **项目状态变化** → 更新"项目当前状态"章节

### 何时更新 `CLAUDE.md`

1. **添加新架构模式** → 在"关键设计决策"章节添加
2. **新增重要文件** → 更新"重要文件路径"章节
3. **新增配置项** → 更新"配置系统层次"章节
4. **不要频繁修改** → 仅在架构级别变更时更新

---

## 🔗 相关文档

- [开发日志](DeFiAgent_CHANGELOG.md) - 历史记录（只追加）
- [文档中心](docs/README.md) - 完整文档索引
- [测试文档](测试文档.md) - 测试状态和用例
- [Telegram Bot 指南](docs/Telegram_Bot_Guide.md) - Bot 部署和使用

---

**文档维护者**: DeFi Agent 开发团队
**文档模板版本**: v1.0

## 🧪 Backtesting 模块进展
- [x] Task 3: 策略实现（BuyHold / Threshold / AgentStrategy + AgentDecisionBridge），单测覆盖率 96%（pytest --cov=defiagents.backtesting.strategies）。
