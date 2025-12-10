# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

DeFi Agent 是一个基于 LangGraph 的多智能体投资分析系统，源自 TradingAgents 框架。系统使用多个专业 Agent 协作分析 DeFi 协议，通过辩论机制和风险评估生成投资建议。

**核心特性**：
- 多智能体协作（5阶段流水线）
- LangGraph 状态管理和条件路由
- ChromaDB 记忆系统（学习历史案例）
- Bull/Bear 辩论机制
- 两层安全架构（注入检测 + 意图提取）
- 多链 DeFi 数据集成（The Graph, DeFi Llama, Web3.py）
- Telegram Bot 前端

## 常用命令

### 安装依赖
```bash
pip install -e .
```

### 配置环境变量
复制 `.env.example` 到 `.env` 并填入 API 密钥：
```bash
cp .env.example .env
# 编辑 .env 文件
```

**必需变量**：
- `GOOGLE_API_KEY` - Google Gemini LLM（免费，60 requests/分钟）
- `THE_GRAPH_API_KEY` - The Graph 链上数据（免费 100K queries/月）
- `TELEGRAM_BOT_TOKEN` - Telegram Bot Token（从 @BotFather 获取）

**可选变量**：
- `OPENAI_API_KEY` - 如果使用 OpenAI 替代 Gemini
- `BOT_RATE_LIMIT_PER_USER` - Bot 速率限制（默认 10次/小时）
- `BOT_ADMIN_USER_IDS` - 管理员用户 ID（逗号分隔，无速率限制）
- `ETHEREUM_RPC_URL` 等 - 自定义 RPC 节点（可选，有免费公共节点）

完整变量列表参见 `.env.example`。

### 运行测试
```bash
# DeFi 数据源测试
python test_defi_integration.py

# Gemini 配置端到端测试（完整分析流程）
python examples/test_defi_with_gemini.py

# The Graph Gateway 配置测试
python test_thegraph_gateway.py

# 安全模块测试
cd defiagents/security
python injection_detector.py  # 8个注入攻击测试案例
python intent_extractor.py    # 10个意图提取测试案例
python input_sanitizer.py     # 综合测试
```

**运行单个测试**：
```bash
# 仅测试 DeFi Llama 数据源
python -m pytest tests/test_defi_datasources_only.py::test_defillama_tvl -v

# 仅测试安全模块的注入检测
python -m pytest defiagents/security/test_injection_detector.py -v

# 调试模式运行测试（显示 print 输出）
python -m pytest tests/test_defi_integration.py -s -v
# -s: 显示 print 输出
# -v: 详细模式
```

### 运行系统

**命令行模式**（传统 CLI）：
```bash
python -m cli.main
```

**Telegram Bot 模式**（推荐）：
```bash
python3 run_bot.py
# 或使用 systemd/PM2 守护进程部署（参考 docs/Telegram_Bot_Guide.md）
```

**Python API 模式**：
```python
from gemini_config import GEMINI_CONFIG
from defiagents.graph.trading_graph import TradingAgentsGraph

agent = TradingAgentsGraph(config=GEMINI_CONFIG)
result = agent.invoke(
    company_name="aave-v3",  # DeFi 协议 slug
    trade_date="2025-01-15"
)
```

## 高层架构

### 多智能体工作流（5阶段流水线）

系统使用 **LangGraph StateGraph** 编排多个 Agent 顺序协作，每个 Agent 专注特定分析维度：

```
用户输入
  ↓
[Input Sanitization] ← 安全层（注入检测 + 意图提取）
  ↓
[Phase 1: 并行分析师] ← 6个分析师同时工作
  ├─ DeFi Market Analyst (TVL/流动性/市场趋势)
  ├─ Protocol Fundamentals Analyst (代币经济学/审计/收入)
  ├─ Yield Analyst (APY/收益来源/无常损失)
  ├─ Risk Analyst (智能合约/治理/流动性风险)
  ├─ News Analyst (DeFi 新闻/事件)
  └─ Social Media Analyst (Twitter/Discord 情绪)
  ↓
[Phase 2: 研究员辩论] ← Bull vs Bear 对抗
  ├─ Bull Researcher (乐观论据)
  ├─ Bear Researcher (风险论据)
  └─ Research Manager (综合评估)
  ↓
[Phase 3: 交易员] ← 制定初步策略
  └─ DeFi Trader (INVEST/HOLD/AVOID + 具体步骤)
  ↓
[Phase 4: 风险管理团队辩论] ← Risky vs Safe vs Neutral 三方讨论
  ├─ Risky Risk Manager (激进策略)
  ├─ Safe Risk Manager (保守策略)
  ├─ Neutral Risk Manager (平衡策略)
  └─ Chief Risk Officer (最终审核)
  ↓
[Phase 5: 投资组合经理] ← 最终决策
  └─ Portfolio Manager (输出最终报告)
  ↓
输出给用户
```

**关键文件**：
- `defiagents/graph/setup.py` - StateGraph 构建和节点注册
- `defiagents/graph/state.py` - 状态定义（MessagesState + 自定义字段）
- `defiagents/graph/edges.py` - 条件路由逻辑
- `defiagents/graph/trading_graph.py` - 主入口类

### LangGraph 状态管理

系统使用 **TypedDict** 定义不可变状态，在 Agent 间传递：

```python
# defiagents/graph/state.py
class TradingAgentsState(MessagesState):
    # 基础字段
    company_name: str              # 协议名（如 "aave-v3"）
    trade_date: str                # 分析日期

    # 分析师报告（Phase 1）
    market_report: str
    fundamentals_report: str
    yield_report: str
    risk_report: str
    news_report: str
    social_report: str

    # 研究员报告（Phase 2）
    bull_report: str
    bear_report: str
    research_manager_report: str

    # 交易员计划（Phase 3）
    trader_plan: str

    # 风险管理报告（Phase 4）
    risky_report: str
    safe_report: str
    neutral_report: str
    chief_risk_officer_report: str

    # 最终决策（Phase 5）
    final_decision: str
```

**关键模式**：
- 每个 Agent 节点是纯函数：`(state: TradingAgentsState) -> dict`
- 返回的 dict 会被 **merge** 到全局状态
- 使用 `messages` 字段累积 LLM 对话历史
- 使用 `send()` 和 `Annotation` 实现并行分析师

### Agent 创建模式

所有 Agent 使用统一的工厂函数创建，配置包含：

```python
# defiagents/agents/utils/node.py
analyst = create_analyst_agent(
    name="DeFi Market Analyst",
    system_message=MARKET_ANALYST_PROMPT,  # Jinja2 模板
    tools=[                                 # LangChain @tool 装饰的函数
        get_protocol_tvl,
        get_uniswap_pool_details,
        get_aave_lending_markets,
        # ... 更多工具
    ],
    state_key="market_report"  # 写入状态的字段名
)
```

**工具调用流程**：
1. LLM 生成工具调用（JSON 格式）
2. LangGraph 自动执行工具函数
3. 工具返回 Markdown 格式化的数据
4. LLM 基于工具结果生成报告
5. 报告写入状态的 `state_key` 字段

**关键文件**：
- `defiagents/agents/utils/node.py` - `create_analyst_agent()` 工厂函数
- `defiagents/agents/analysts/*.py` - 各分析师提示词
- `defiagents/agents/utils/defi_*_tools.py` - 工具函数定义

### 工具层抽象

工具层分为三层：

**Layer 1: 数据源客户端**（原始 API 调用）
- `defiagents/dataflows/defi/defillama.py` - DeFi Llama API（TVL/APY/协议列表）
- `defiagents/dataflows/defi/the_graph.py` - The Graph 子图查询（Uniswap/Aave 池数据）
- `defiagents/dataflows/defi/coingecko.py` - CoinGecko API（代币价格/市值）
- `defiagents/dataflows/defi/onchain.py` - Web3.py 直连 RPC（余额/Gas/区块数据）

**Layer 2: 数据源路由**（多源回退 + 缓存）
- `defiagents/dataflows/interface.py` - 统一接口，按优先级尝试多个数据源
- 例：TVL 数据优先 DeFi Llama，失败回退到 The Graph，再失败回退到链上计算

**Layer 3: LangChain 工具**（LLM 可调用）
- `defiagents/agents/utils/defi_protocol_tools.py` - 协议分析工具（12个函数）
- `defiagents/agents/utils/defi_pool_tools.py` - 流动性池工具（5个函数）
- `defiagents/agents/utils/defi_wallet_tools.py` - 钱包分析工具（6个函数）
- `defiagents/agents/utils/defi_market_tools.py` - 市场数据工具（7个函数）
- 每个工具用 `@tool` 装饰，返回 Markdown 格式字符串

**关键模式**：
- 所有数据源函数包含 `_normalize_tvl()` 等类型规范化逻辑（处理 API 返回 float/list/dict 不一致问题）
- 工具函数内部调用 Layer 2 接口，捕获异常并返回友好错误信息
- 缓存在 Layer 1 实现（functools.lru_cache + TTL）

### 辩论机制模式

系统在两个阶段使用辩论机制：

**Phase 2: Bull/Bear 研究员辩论**
```python
# defiagents/graph/setup.py
def research_team_debate_node(state):
    # 1. Bull Researcher 生成乐观论据
    bull_report = bull_researcher.invoke(state)

    # 2. Bear Researcher 看到 Bull 的报告后生成反驳
    bear_report = bear_researcher.invoke({**state, "bull_report": bull_report})

    # 3. Research Manager 综合评估
    manager_report = research_manager.invoke({
        **state,
        "bull_report": bull_report,
        "bear_report": bear_report
    })

    return {"research_manager_report": manager_report}
```

**Phase 4: Risk Management 三方辩论**
```python
def risk_management_debate_node(state):
    # 三个风险经理并行生成报告
    risky_report = risky_risk_manager.invoke(state)
    safe_report = safe_risk_manager.invoke(state)
    neutral_report = neutral_risk_manager.invoke(state)

    # Chief Risk Officer 综合三方意见
    cro_report = chief_risk_officer.invoke({
        **state,
        "risky_report": risky_report,
        "safe_report": safe_report,
        "neutral_report": neutral_report
    })

    return {"chief_risk_officer_report": cro_report}
```

**价值**：通过对抗性讨论减少 AI 幻觉，提供多角度风险评估。

### 安全架构（两层防护）

**Layer 1: 注入检测器**（`defiagents/security/injection_detector.py`）
- 15+ 正则模式检测提示注入攻击（ignore previous, system:, act as, 等）
- 风险评分系统（0-1.0）
- 投资关键词白名单（降低误报率）
- 严格模式开关（可配置敏感度）

**Layer 2: 意图提取器**（`defiagents/security/intent_extractor.py`）
- 从自然语言提取结构化投资参数：
  - 协议名（支持模糊匹配：aave → aave-v3）
  - 投资金额（支持单位：10K, 1M, 100万, 1亿）
  - 风险偏好（low/medium/high）
  - 目标 APY/TVL/链/代币
- 置信度评分（基于提取参数数量）

**统一接口**（`defiagents/security/input_sanitizer.py`）
```python
sanitizer = InputSanitizer(strict_mode=False)
result = sanitizer.sanitize("用10万USDC投资aave，低风险")

if not result.is_safe:
    # 返回拒绝消息
    print(result.rejection_reason)
else:
    # 提取到的参数
    print(result.intent.protocol_name)      # "aave-v3"
    print(result.intent.investment_amount)  # 100000.0
    print(result.intent.risk_preference)    # "low"
```

**集成点**：
- **Telegram Bot**: `bot/handlers.py:227` - 在处理消息前调用
- **LangGraph**: 可作为第一个节点（当前未启用，Bot 层已防护）

### 记忆系统

使用 **ChromaDB + OpenAI Embeddings** 实现案例学习：

```python
# defiagents/agents/utils/memory.py
class AgentMemory:
    def store_case(self, protocol: str, analysis: str, outcome: str):
        # 存储历史分析案例到向量数据库

    def retrieve_similar_cases(self, query: str, top_k=3):
        # 基于语义相似度检索历史案例
        # 注入到 Agent 提示词的 "past experiences" 部分
```

**用途**：
- 学习历史成功/失败案例
- 在分析新协议时参考相似协议经验
- 支持反思机制（Agent 可总结教训并存储）

**关键文件**：
- `defiagents/agents/utils/memory.py` - 记忆系统实现
- `defiagents/default_config.py:40-48` - ChromaDB 配置

### 配置系统层次

配置优先级（从高到低）：

1. **运行时传参** - `TradingAgentsGraph(config={...})`
2. **环境变量** - `.env` 文件
3. **默认配置** - `defiagents/default_config.py`

**重要配置节**：
```python
# defiagents/default_config.py
DEFAULT_CONFIG = {
    # LLM 配置
    "llm": {
        "model": "gemini-2.0-flash-exp",  # 免费模型
        "temperature": 0.7,
    },

    # DeFi 数据源
    "defi_llama": {...},
    "the_graph": {
        "api_key": os.getenv("THE_GRAPH_API_KEY"),
        "api_url": "https://gateway.thegraph.com/api",
        "subgraphs": {
            "uniswap_v3_ethereum": "5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV",
            # ... 部署 ID
        }
    },

    # 记忆系统
    "memory": {
        "enabled": True,
        "persist_directory": "./data/chroma_db",
    },

    # 安全配置
    "security": {
        "enable_sanitization": True,
        "strict_mode": False,
    }
}
```

**特定配置文件**：
- `gemini_config.py` - Gemini 专用配置（免费方案，$0成本）
- `openai_config.py` - OpenAI 配置（备用，付费）
- `bot/config.py` - Telegram Bot 配置（速率限制/管理员/超时）

### Telegram Bot 架构

**异步事件驱动架构**：

```python
# bot/telegram_bot.py
class DeFiTelegramBot:
    def setup_handlers(self, application):
        # 命令处理器
        application.add_handler(CommandHandler("analyze", analyze_command))
        # 自然语言处理器
        application.add_handler(MessageHandler(filters.TEXT, handle_message))
        # 错误处理器
        application.add_error_handler(error_handler)
```

**关键流程**：
1. 用户发送消息 → `handle_message()`
2. 速率限制检查（10次/小时/用户）
3. 输入净化（`InputSanitizer`）
4. 异步调用 DeFi Agent（`loop.run_in_executor()`）
5. 实时更新进度消息（每10秒，8步进度）
6. 格式化结果为 Telegram Markdown
7. 分多条消息发送（避免4096字符限制）

**关键文件**：
- `bot/handlers.py` - 命令处理和 Agent 调用
- `bot/formatters.py` - 消息格式化（欢迎/帮助/报告/错误）
- `bot/config.py` - Bot 配置管理
- `run_bot.py` - 启动脚本

## 关键设计决策

### 为什么使用 LangGraph 而非 LangChain Agents？

LangGraph 提供：
- **显式状态管理**：每个 Agent 的输入/输出清晰可控
- **条件路由**：根据分析结果动态决定下一步（如跳过辩论）
- **并行执行**：Phase 1 的6个分析师可同时工作
- **可视化**：工作流可导出为 Mermaid 图
- **调试友好**：每个节点的输入/输出可单独检查

### 为什么选择 Gemini 作为默认 LLM？

- **免费额度**：60 requests/分钟，无月度限制
- **性能**：gemini-2.0-flash-exp 速度快，适合多 Agent 场景
- **成本**：测试显示单次完整分析 $0（15次调用全在免费额度内）
- **对比**：OpenAI GPT-4o-mini 需付费，估算 $0.15-0.30/次分析

### 为什么实现两层安全架构？

- **Layer 1（注入检测）**：阻止恶意输入（如"ignore previous instructions"）
- **Layer 2（意图提取）**：理解合法输入（如"用10万投资aave"）
- **分离关注点**：检测器专注安全，提取器专注理解
- **测试独立**：可分别测试攻击防护和意图理解准确率

### 为什么 Bot 层已实现安全但 LangGraph 未集成？

- **防御深度**：Bot 是公开入口，必须防护
- **开发灵活性**：CLI/Python API 用于内部测试，无需强制净化
- **性能考虑**：避免重复检测（Bot 已检测，Agent 无需再检测）
- **未来可选**：可通过配置启用 LangGraph 安全节点

## 重要注意事项

### DeFi Llama API 类型处理

DeFi Llama 返回 TVL 的类型不一致（float/list/dict），**必须**使用 `_normalize_tvl()` 规范化：

```python
from defiagents.dataflows.defi.defillama import _normalize_tvl

tvl_raw = get_protocol_tvl("aave-v3")  # 可能是 float/list/dict
tvl = _normalize_tvl(tvl_raw)          # 保证返回 float
```

### The Graph Subgraph 版本

部分 subgraph 可能过期（如 Aave V3 子图3年未更新）。**优先使用 DeFi Llama**，The Graph 作为备选：

```python
# 推荐模式
try:
    data = get_from_defillama(protocol)
except Exception:
    data = get_from_thegraph(protocol)  # 回退
```

### 环境变量加载

测试脚本**必须**显式加载 `.env` 文件：

```python
from dotenv import load_dotenv
load_dotenv()  # 必须在所有导入之前

from defiagents.graph.trading_graph import TradingAgentsGraph
```

### Telegram Bot 速率限制

默认 10 次请求/小时/用户，可通过 `.env` 调整：

```env
BOT_RATE_LIMIT_PER_USER=20       # 增加到20次
BOT_RATE_LIMIT_WINDOW=3600       # 时间窗口（秒）
```

### 成本优化

当前配置使用 **Gemini 免费层**，实测单次分析 $0。如需切换到 OpenAI：

1. 修改 `bot/handlers.py:40-44`：
   ```python
   from openai_config import OPENAI_CONFIG  # 改用 OpenAI 配置
   self._agent = TradingAgentsGraph(config=OPENAI_CONFIG)
   ```

2. 预期成本：$0.15-0.30/次分析（GPT-4o-mini）

## 调试和日志

### 启用调试模式
```python
from defiagents.graph.trading_graph import TradingAgentsGraph
from gemini_config import GEMINI_CONFIG

agent = TradingAgentsGraph(config=GEMINI_CONFIG, debug=True)
# 调试模式会打印每个 Agent 的输入/输出和工具调用详情
```

### 查看 LangGraph 节点输出
```python
result = agent.invoke(company_name="aave-v3", trade_date="2025-01-15")

# 访问状态中的特定报告
print(result["market_report"])        # 市场分析师报告
print(result["trader_plan"])          # 交易员计划
print(result["final_decision"])       # 最终决策

# 查看所有可用字段
print(result.keys())
```

### 工具调用日志
所有工具函数内部已包含错误日志，失败时会返回友好错误信息：
```
❌ 错误: 无法获取 Uniswap 池数据
原因: The Graph API rate limit exceeded
建议: 稍后重试或检查 THE_GRAPH_API_KEY 配置
```

### Telegram Bot 日志
Bot 日志包含用户请求、速率限制、分析进度等信息：
```bash
# 运行 Bot 时自动打印到控制台
python3 run_bot.py

# 查看日志示例：
# INFO - 用户 123456789 请求分析: aave-v3
# INFO - 速率限制检查: 3/10
# INFO - 输入净化通过
# INFO - 开始分析...
# INFO - Phase 1 完成: 6个分析师报告已生成
```

## 开发工作流

### 添加新的 DeFi 协议支持

**步骤 1: 检查数据源支持**
```bash
# 检查协议是否在 DeFi Llama 中
python -c "
from defiagents.dataflows.defi.defillama import get_protocol_tvl
print(get_protocol_tvl('compound-v3'))
"
```

**步骤 2: 创建协议专属工具**（如需要）
```python
# defiagents/agents/utils/defi_protocol_tools.py
from langchain.tools import tool
from defiagents.dataflows.defi.defillama import get_protocol_tvl

@tool
def get_compound_markets(protocol: str = "compound-v3") -> str:
    """获取 Compound 借贷市场数据

    Args:
        protocol: 协议 slug (默认 "compound-v3")

    Returns:
        Markdown 格式的市场数据
    """
    try:
        # 调用数据源
        tvl = get_protocol_tvl(protocol)

        # 格式化为 Markdown
        return f"""## Compound V3 市场概览

**总锁仓价值 (TVL)**: ${tvl:,.0f}

**支持资产**: USDC, ETH, WBTC
**借贷利率**: 查看详细数据...
"""
    except Exception as e:
        return f"❌ 错误: 无法获取 Compound 数据\n原因: {str(e)}"
```

**步骤 3: 注册工具到 Agent**
```python
# defiagents/graph/setup.py
from defiagents.agents.utils.defi_protocol_tools import get_compound_markets

# 在创建分析师时添加工具
market_analyst = create_analyst_agent(
    name="DeFi Market Analyst",
    system_message=MARKET_ANALYST_PROMPT,
    tools=[
        get_protocol_tvl,
        get_compound_markets,  # 添加新工具
        # ... 其他工具
    ],
    state_key="market_report"
)
```

**步骤 4: 测试新协议**
```bash
# 创建测试脚本
python -c "
from gemini_config import GEMINI_CONFIG
from defiagents.graph.trading_graph import TradingAgentsGraph

agent = TradingAgentsGraph(config=GEMINI_CONFIG, debug=True)
result = agent.invoke(company_name='compound-v3', trade_date='2025-01-15')
print(result['final_decision'])
"
```

### 添加新的 Analyst Agent

**步骤 1: 创建提示词模板**
```python
# defiagents/agents/analysts/new_analyst.py
NEW_ANALYST_PROMPT = """
你是一个 DeFi 安全审计专家。你的职责是：
1. 分析协议的智能合约审计报告
2. 评估历史安全事件和漏洞
3. 检查多签钱包和治理机制
4. 提供安全评分和风险建议

使用提供的工具获取协议审计数据、历史漏洞记录等信息。

输出格式：
## 安全审计分析

**审计覆盖率**: X%
**历史漏洞**: 列表
**风险评分**: X/10
**建议**: ...
"""
```

**步骤 2: 注册新 Agent 到状态**
```python
# defiagents/graph/state.py
class TradingAgentsState(MessagesState):
    # ... 现有字段
    security_audit_report: str  # 添加新字段
```

**步骤 3: 在 setup.py 中创建和注册**
```python
# defiagents/graph/setup.py
from defiagents.agents.analysts.new_analyst import NEW_ANALYST_PROMPT

# 创建 Agent
security_auditor = create_analyst_agent(
    name="Security Auditor",
    system_message=NEW_ANALYST_PROMPT,
    tools=[get_audit_reports, get_security_incidents],
    state_key="security_audit_report"
)

# 注册到 LangGraph
graph.add_node("security_auditor", security_auditor)

# 添加边（在 Phase 1 并行执行）
graph.add_edge("market_analyst", "security_auditor")
graph.add_edge("security_auditor", "research_team")
```

**步骤 4: 更新其他 Agent 提示词**
确保下游 Agent（如 Research Manager）的提示词能看到新的报告：
```python
# defiagents/agents/researchers/research_manager.py
RESEARCH_MANAGER_PROMPT = """
你将收到以下报告：
- 市场分析
- 基本面分析
- ...
- **安全审计分析**（新增）

综合所有报告生成投资建议...
"""
```

### 添加新的数据源

**步骤 1: 实现数据源客户端**
```python
# defiagents/dataflows/defi/new_source.py
import requests
from functools import lru_cache

@lru_cache(maxsize=128)
def get_data_from_new_source(protocol: str) -> dict:
    """从新数据源获取协议数据

    Args:
        protocol: 协议 slug

    Returns:
        标准化的协议数据字典
    """
    try:
        response = requests.get(
            f"https://api.newsource.com/v1/protocols/{protocol}",
            timeout=10
        )
        response.raise_for_status()

        data = response.json()

        # 标准化返回格式
        return {
            "tvl": float(data.get("tvl", 0)),
            "apy": float(data.get("apy", 0)),
            # ... 更多字段
        }
    except Exception as e:
        raise RuntimeError(f"NewSource API 错误: {str(e)}")
```

**步骤 2: 更新配置**
```python
# defiagents/default_config.py
DEFAULT_CONFIG = {
    # ... 现有配置
    "new_source": {
        "api_url": "https://api.newsource.com/v1",
        "api_key": os.getenv("NEW_SOURCE_API_KEY"),
        "cache_ttl": 300,  # 5分钟缓存
    }
}
```

**步骤 3: 更新 .env.example**
```bash
# .env.example
# ========== New Data Source ==========
NEW_SOURCE_API_KEY=your_api_key_here
```

**步骤 4: 创建回退逻辑**（可选）
```python
# defiagents/dataflows/interface.py
def get_protocol_tvl_with_fallback(protocol: str) -> float:
    """多数据源回退机制"""
    try:
        return get_defillama_tvl(protocol)
    except:
        try:
            return get_data_from_new_source(protocol)["tvl"]
        except:
            return get_thegraph_tvl(protocol)  # 最后回退
```

## 性能优化提示

### LLM 模型选择策略

**当前默认配置**（最优性价比）：
```python
# gemini_config.py
config["llm"]["model"] = "gemini-2.0-flash-exp"
config["llm"]["temperature"] = 0.7
# 响应时间: ~2-3秒/调用
# 成本: $0（免费额度）
# 质量: 适合大多数 DeFi 分析场景
```

**高质量分析配置**（更慢但更准确）：
```python
config["llm"]["model"] = "gemini-1.5-pro"
config["llm"]["temperature"] = 0.5
# 响应时间: ~5-8秒/调用
# 成本: $0.00125/1K tokens（输入）
# 适用场景: 复杂协议分析、高风险决策
```

**快速测试配置**：
```python
config["llm"]["model"] = "gemini-2.0-flash-exp"
config["llm"]["temperature"] = 1.0  # 更快但更随机
# 响应时间: ~1-2秒/调用
# 适用场景: 开发调试、单元测试
```

### 并行执行优化

**Phase 1 自动并行**：
6个分析师 Agent 已使用 LangGraph `send()` 机制并行执行，无需额外配置。单个分析师失败不会阻塞整体流程。

**预期性能**：
- 串行执行: 6 agents × 15秒 = 90秒
- 并行执行: max(15秒) + 网络延迟 ≈ 20秒
- **加速比**: ~4.5x

**查看并行日志**：
```python
agent = TradingAgentsGraph(config=GEMINI_CONFIG, debug=True)
# 日志会显示：
# [Phase 1] Starting 6 analysts in parallel...
# [Market Analyst] Completed in 12.3s
# [Yield Analyst] Completed in 14.8s
# ...
```

### 缓存策略

**Layer 1 数据源缓存**（内存，跨调用）：
```python
# defiagents/dataflows/defi/defillama.py
@lru_cache(maxsize=256)  # 缓存 256 个协议数据
def get_protocol_tvl(slug: str) -> float:
    # TTL: 1小时（隐式，通过 lru_cache）
    pass
```

**当前 TTL 设置**：
- DeFi Llama: 1小时（TVL 更新慢）
- The Graph: 5分钟（链上数据更新快）
- CoinGecko: 5分钟（价格波动快）

**清除缓存**：
```python
from defiagents.dataflows.defi.defillama import get_protocol_tvl
get_protocol_tvl.cache_clear()  # 清除 LRU 缓存
```

**持久化缓存**（计划中）：
参见 `PROJECT_STATUS.md` 的"分析结果缓存机制"待办（Redis/TTLCache）。

### 工具调用优化

**减少不必要的工具调用**：
在提示词中明确指示 Agent 优先使用已有信息：
```python
ANALYST_PROMPT = """
...
⚠️ 注意：优先分析已提供的数据，仅在必要时调用工具获取额外信息。
避免重复调用相同参数的工具。
"""
```

**工具超时设置**：
```python
# defiagents/dataflows/defi/defillama.py
response = requests.get(url, timeout=10)  # 10秒超时
```

### Telegram Bot 优化

**进度反馈频率**：
```python
# bot/handlers.py
UPDATE_INTERVAL = 10  # 每10秒更新一次进度消息
# 减少到 5 秒可提升用户体验，但增加 Telegram API 调用量
```

**消息分块发送**：
```python
# bot/formatters.py
MAX_MESSAGE_LENGTH = 4096  # Telegram 限制
# 自动拆分长消息为多条，避免截断
```

### 成本监控

**估算单次分析成本**：
```python
# 使用 Gemini 免费层：$0
# 使用 OpenAI GPT-4o-mini：
# - ~15次 LLM 调用/分析
# - ~500 tokens 输入/调用 × 15 = 7500 tokens
# - ~1000 tokens 输出/调用 × 15 = 15000 tokens
# - 成本: (7500×$0.15 + 15000×$0.60) / 1M ≈ $0.10/分析
```

**监控 API 使用量**：
```bash
# 查看 DeFi Llama 使用量（无限制）
curl https://api.llama.fi/protocols/aave-v3

# 查看 The Graph 使用量
# 登录 https://thegraph.com/studio/ 查看剩余 queries
```

## 📝 文档更新协议（重要！）

**作为 AI 开发助手，每次修改代码后必须按以下规则更新文档**：

### 主要文档职责

| 文档 | 用途 | 何时更新 | 更新方式 |
|------|------|---------|---------|
| [PROJECT_STATUS.md](PROJECT_STATUS.md) | 活跃状态跟踪 | 完成功能/修复问题/添加待办 | ✏️ 修改现有内容 |
| [DeFiAgent_CHANGELOG.md](DeFiAgent_CHANGELOG.md) | 历史记录 | Phase 完成/重大变更 | ➕ 只追加，不修改 |
| [CLAUDE.md](CLAUDE.md) | 架构参考 | 架构级别变更 | ✏️ 谨慎更新 |
| [docs/README.md](docs/README.md) | 文档索引 | 新增文档/状态变化 | ✏️ 更新索引表 |

### 详细更新规则

#### 更新 `PROJECT_STATUS.md` 的情况

**完成待办事项**:
```markdown
- [x] 分析结果缓存机制（已完成于 2025-12-11）
```
同时在"已完成功能"部分追加。

**修复问题**:
```markdown
| DeFi Llama TVL 错误 | 已修复 | `_normalize_tvl()` | ✅ 已解决 | ... |
```

**添加新待办**:
在对应优先级章节（🔴高/🟡中/🟢低）添加新条目。

**性能指标变化**:
更新"性能指标"表格的"当前值"列。

#### 更新 `DeFiAgent_CHANGELOG.md` 的情况

**完成 Phase 里程碑**（如 Phase 3 完成）:
```markdown
## Phase 3: 性能优化与测试 ✅
**完成日期**: 2025-12-15
**主要变更**:
- ...
```

**修复重大 Bug**:
```markdown
### 问题8: 新问题标题
**发现日期**: 2025-12-11
**状态**: ✅ 已修复
**问题描述**: ...
**解决方案**: ...
```

**重要：只能追加内容到文件末尾，不要修改历史条目**。

#### 更新 `CLAUDE.md` 的情况（谨慎）

**仅在以下情况更新**:
1. 新增核心架构模式（如新增 Agent 类型）
2. 改变数据流架构（如新增数据源层）
3. 新增关键设计决策
4. 更新重要文件路径（新增核心模块）

**不要更新的情况**:
- 小功能添加
- Bug 修复
- 配置调整
- 优化改进

### 快速检查清单

完成一个功能后，问自己：
1. ✅ 我是否在 `PROJECT_STATUS.md` 中标记了待办为完成？
2. ✅ 我是否更新了"已完成功能"列表？
3. ✅ 如果是重大变更，我是否在 `CHANGELOG.md` 追加了条目？
4. ✅ 如果是新文档，我是否更新了 `docs/README.md` 索引？

---

## 参考文档

- **项目状态跟踪**：`PROJECT_STATUS.md` ⭐ - 活跃待办清单和当前状态（主要文档）
- **用户指南**：`docs/Telegram_Bot_Guide.md` - Bot 部署和使用
- **测试文档**：`测试文档.md` - 协议测试状态和待办
- **开发日志**：`DeFiAgent_CHANGELOG.md` - 完整开发历史（只追加）
- **文档中心**：`docs/README.md` - 完整文档索引

## 架构图

```
┌─────────────────────────────────────────────────────────┐
│                      Telegram Bot                        │
│  (异步Handler + 速率限制 + 进度反馈 + 消息格式化)           │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────┐
│                   Input Sanitization                     │
│    (注入检测 + 意图提取 → SanitizationResult)              │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ↓
┌─────────────────────────────────────────────────────────┐
│              TradingAgentsGraph (LangGraph)              │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  Phase 1: Parallel Analysts (6 agents)         │    │
│  │    → market/fundamentals/yield/risk/news/social│    │
│  └─────────────────┬──────────────────────────────┘    │
│                    ↓                                     │
│  ┌────────────────────────────────────────────────┐    │
│  │  Phase 2: Research Team Debate                 │    │
│  │    → bull/bear researchers → research manager  │    │
│  └─────────────────┬──────────────────────────────┘    │
│                    ↓                                     │
│  ┌────────────────────────────────────────────────┐    │
│  │  Phase 3: Trader                               │    │
│  │    → initial strategy plan                     │    │
│  └─────────────────┬──────────────────────────────┘    │
│                    ↓                                     │
│  ┌────────────────────────────────────────────────┐    │
│  │  Phase 4: Risk Management Debate               │    │
│  │    → risky/safe/neutral → CRO                  │    │
│  └─────────────────┬──────────────────────────────┘    │
│                    ↓                                     │
│  ┌────────────────────────────────────────────────┐    │
│  │  Phase 5: Portfolio Manager                    │    │
│  │    → final decision                            │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
└───────────────────────┬─────────────────────────────────┘
                        │
          ┌─────────────┴──────────────┐
          ↓                            ↓
┌──────────────────┐         ┌──────────────────┐
│   Tool Layer     │         │  Memory System   │
│                  │         │  (ChromaDB)      │
│ - DeFi Llama     │         │                  │
│ - The Graph      │         │ - Store cases    │
│ - CoinGecko      │         │ - Retrieve       │
│ - Web3.py (RPC)  │         │ - Reflect        │
└──────────────────┘         └──────────────────┘
```
