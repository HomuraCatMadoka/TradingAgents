# DeFi Agent 文档中心

欢迎查看 DeFi Agent 项目文档。本文档中心提供完整的用户指南、开发者文档、规划文档和研究资料。

---

## 📖 快速导航

### 🎯 新用户入口
- **[项目主页](../README.md)** - 项目概述、安装指南、快速开始
- **[Telegram Bot 使用指南](Telegram_Bot_Guide.md)** - Bot 部署、命令参考、常见问题

### 👨‍💻 开发者文档
- **[项目状态跟踪](../PROJECT_STATUS.md)** ⭐⭐ - 活跃待办清单、当前状态、安全改进（主要跟踪文档）
- **[CLAUDE.md](../CLAUDE.md)** ⭐ - 开发者快速参考（架构、常用命令、关键模式）
- **[开发日志](../DeFiAgent_CHANGELOG.md)** - 完整开发历史和问题修复记录（只追加）
- **[测试文档](../测试文档.md)** - 协议测试状态、测试用例、性能基准
- **[贡献指南](CONTRIBUTING.md)** - 分支、提交规范、PR 流程、环境搭建
- **[API 设计规范](API_DESIGN.md)** - REST 命名、错误包、分页、版本策略
- **[前端开发指南](FRONTEND_GUIDE.md)** - 组件/状态/样式/安全约定

### 📋 规划文档
- **[后续开发计划](Future_Development_Plan.md)** - 中/低/长期优先级功能列表（已合并到 PROJECT_STATUS.md）
- **[安全增强计划](Security_Enhancement_Plan.md)** - 4个优先级的安全改进项（已合并到 PROJECT_STATUS.md）
- **[商业计划书](DeFiAgent_DEV.md)** - 项目愿景、技术架构、商业模式（早期版本，仅供参考）

### 🔬 研究资料
- **[DeFi 协议调研报告](调研结果.md)** - 11个核心协议的详细数据源映射
- **[协议调研模板](defi_protocol_research_prompt.md)** - 调研框架和检查清单

### 🧪 测试指南
- **[Bot 测试指南](Telegram_Bot_Testing_Guide.md)** - 手动测试步骤和验收标准

---

## 📚 文档分类索引

### 用户指南（User Guides）
面向最终用户的操作文档：

| 文档 | 说明 | 更新日期 |
|------|------|---------|
| [README.md](../README.md) | 项目主页和安装指南 | 2025-12-10 |
| [Telegram Bot 指南](Telegram_Bot_Guide.md) | Bot 部署、配置、命令参考 | 2025-12-10 |

### 开发者文档（Developer Docs）
面向开发者的技术文档：

| 文档 | 说明 | 更新日期 |
|------|------|---------|
| [项目状态跟踪](../PROJECT_STATUS.md) | ⭐ 活跃待办清单、当前状态、安全改进（主要跟踪文档） | 2025-12-10 |
| [CLAUDE.md](../CLAUDE.md) | 架构概览、常用命令、关键设计决策、文档更新协议 | 2025-12-10 |
| [开发日志](../DeFiAgent_CHANGELOG.md) | Phase 1-3 完整开发记录（历史，只追加） | 2025-12-10 |
| [测试文档](../测试文档.md) | 测试状态、协议覆盖、待优化项 | 2025-12-10 |
| [Bot 测试指南](Telegram_Bot_Testing_Guide.md) | 手动测试流程和验收标准 | 2025-12-10 |
| [贡献指南](CONTRIBUTING.md) | 分支策略、提交规范、PR Checklist、常见问题 | 2025-12-10 |
| [API 设计规范](API_DESIGN.md) | 路径命名、错误响应、分页/排序、版本策略 | 2025-12-10 |
| [前端开发指南](FRONTEND_GUIDE.md) | 目录结构、状态管理、样式、安全与性能 | 2025-12-10 |
| [安全层技术规格](../.claude/specs/security-validation-layers/dev-plan.md) | S1/S2 验证层设计、数据模型、集成点 | 2025-12-10 |

### 规划文档（Planning Docs）
项目路线图和改进计划：

| 文档 | 说明 | 更新日期 | 状态 |
|------|------|---------|------|
| [项目状态跟踪](../PROJECT_STATUS.md) | ⭐ 统一的活跃待办清单和状态跟踪 | 2025-12-10 | 主要文档 |
| [后续开发计划](Future_Development_Plan.md) | 原功能路线图（已合并到 PROJECT_STATUS.md） | 2025-12-10 | 参考 |
| [安全增强计划](Security_Enhancement_Plan.md) | 原安全改进项（已合并到 PROJECT_STATUS.md） | 2025-12-10 | 参考 |
| [商业计划书](DeFiAgent_DEV.md) | 早期愿景文档（市场定位、技术架构） | 2024-05 | 归档 |

### 研究资料（Research Materials）
DeFi 协议调研和数据源：

| 文档 | 说明 | 更新日期 |
|------|------|---------|
| [协议调研报告](调研结果.md) | 11个核心协议的 DeFi Llama/The Graph 数据源 | 2024-05 |
| [协议调研模板](defi_protocol_research_prompt.md) | 调研框架、数据表格模板、检查清单 | 2024-05 |

---

## 🔑 关键概念速查

### 架构核心
- **LangGraph 多智能体系统** - 5阶段流水线（分析→辩论→交易→风险→决策）
- **数据源层** - DeFi Llama（TVL）、The Graph（链上）、CoinGecko（价格）
- **安全层** - 注入检测 + 意图提取（两层防护）
- **记忆系统** - ChromaDB 向量数据库（学习历史案例）

### 重要文件路径
```
defiagents/
├── graph/setup.py              # LangGraph 工作流定义
├── agents/analysts/            # 6个分析师 Agent
├── agents/utils/defi_*_tools.py # 30+ DeFi 工具函数
├── dataflows/defi/             # 数据源客户端
└── security/                   # 输入净化模块

bot/
├── handlers.py                 # Telegram 命令处理
├── formatters.py               # 消息格式化
└── config.py                   # Bot 配置管理
```

### 配置文件
- `.env` - 环境变量（API Keys）
- `defiagents/default_config.py` - 全局配置
- `gemini_config.py` - Gemini LLM 配置（免费方案）
- `bot/config.py` - Bot 速率限制/超时配置

---

## 🚀 快速开始流程

### 1. 开发环境搭建
```bash
# 安装依赖
pip install -e .

# 配置 API Keys
cp .env.example .env
# 编辑 .env 添加 GOOGLE_API_KEY, THE_GRAPH_API_KEY, TELEGRAM_BOT_TOKEN
```

### 2. 运行测试
```bash
# 数据源测试
python test_defi_integration.py

# 端到端测试（完整分析流程）
python examples/test_defi_with_gemini.py
```

### 3. 启动 Bot
```bash
# 前台运行
python3 run_bot.py

# 后台部署（参考 Telegram_Bot_Guide.md）
```

详细步骤见 [README.md](../README.md) 和 [CLAUDE.md](../CLAUDE.md)。

---

## 📊 项目当前状态（2025-12-10）

### ✅ 已完成功能（Phase 1-2）
- [x] 项目架构改造（TradingAgents → DeFi Agent）
- [x] DeFi 数据源集成（4个主要数据源）
- [x] LangChain 工具接口（30+ 工具函数）
- [x] 6个 DeFi 专属分析师 Agent
- [x] 辩论机制和风险评估系统
- [x] 安全层（注入检测 + 意图提取）
- [x] Telegram Bot 前端（命令系统 + 自然语言交互）
- [x] 端到端测试验证（Aave V3、Uniswap V3）

### 🔄 当前进展
- 支持协议：2个已测试（Aave V3、Uniswap V3），理论支持所有 DeFi Llama 协议
- 支持区块链：5条（Ethereum, Arbitrum, Optimism, Base, Polygon）
- 单次分析时间：105-108 秒
- LLM 成本：$0（Gemini 免费层）
- Bot 功能：命令系统、自然语言、进度反馈、速率限制

### ⏳ 待完成功能（Phase 3+）
参考 [后续开发计划](Future_Development_Plan.md)：
- 中优先级：分析结果缓存、进度反馈优化、`/status` 命令
- 低优先级：更多协议支持、数据可视化、订阅通知
- 长期愿景：多语言支持、Web 仪表板、Discord Bot、SaaS 订阅

---

## 🐛 已知问题和解决方案

### 数据源相关
| 问题 | 影响 | 解决方案 | 文档位置 |
|------|------|---------|---------|
| DeFi Llama TVL 类型不一致 | 某些协议解析失败 | 实现 `_normalize_tvl()` 递归规范化 | [CHANGELOG:问题1](../DeFiAgent_CHANGELOG.md#问题1-defi-llama-tvl类型错误) |
| The Graph Aave V3 子图过时 | 无法获取实时借贷数据 | 使用 DeFi Llama 作为主数据源 | [测试文档:问题3](../测试文档.md#问题3-aave-v3-subgraph过时) |
| CoinGecko 合约查询限制 | 部分代币价格查询失败 | 非阻塞，降级为协议层数据 | [测试文档](../测试文档.md) |

### Telegram Bot 相关
| 问题 | 影响 | 解决方案 | 文档位置 |
|------|------|---------|---------|
| Markdown 解析错误 | 消息发送失败 | 转义 Agent 生成内容的特殊字符 | [CHANGELOG:错误6](../DeFiAgent_CHANGELOG.md#错误-6-telegram-markdown-解析错误) |
| GraphQL 连接冲突 | 并发查询失败 | 每次创建新 transport 对象 | [CHANGELOG:错误7](../DeFiAgent_CHANGELOG.md#错误-7-graphql-transport-connection-error) |

完整问题列表见 [开发日志](../DeFiAgent_CHANGELOG.md) 和 [测试文档](../测试文档.md)。

---

## 🤝 贡献指南

项目使用 AI 辅助开发（Claude Code + 用户协作），主要贡献方式：

1. **协议扩展** - 添加新 DeFi 协议支持（参考 [调研模板](defi_protocol_research_prompt.md)）
2. **安全增强** - 实现 [安全计划](Security_Enhancement_Plan.md) 中的改进项
3. **功能开发** - 实现 [后续开发计划](Future_Development_Plan.md) 中的功能
4. **测试覆盖** - 扩展协议测试覆盖（见 [测试文档](../测试文档.md)）
5. **文档完善** - 补充使用案例、API 文档、架构图

贡献前请阅读 [CLAUDE.md](../CLAUDE.md) 了解项目架构。

---

## 📞 联系方式

- **问题反馈**: [GitHub Issues](https://github.com/TauricResearch/TradingAgents/issues)
- **社区讨论**: [Discord](https://discord.com/invite/hk9PGKShPK)
- **官方网站**: [tauric.ai](https://tauric.ai/)

---

**最后更新**: 2025-12-10
**维护者**: DeFi Agent 开发团队
**文档版本**: v2.0（Phase 2 完成版）
