# S1 Agent 输出验证层 + S2 白名单协议验证层 - 开发计划

## 项目概述

为 DeFi Agent 系统增强安全防护，通过两个新的验证层提升系统可靠性：

**S1 Agent 输出验证层**：验证所有 Agent 输出内容，检测危险操作指令、异常金额、钓鱼地址等风险信号。危险输出将附加警告标记但允许继续处理（警告模式）。

**S2 白名单协议验证层**：通过多数据源交叉验证协议可信度，对协议进行分级（trusted / unverified / suspicious），为用户提供明确的风险提示。

**核心目标**：在不阻断用户体验的前提下，增加安全防护层次，降低系统被利用生成危险建议的风险。

---

## 技术规格

### S1 OutputValidator 数据模型

```python
# defiagents/security/output_validator.py

class ValidationContext(TypedDict):
    """验证上下文"""
    agent_name: str               # Agent 名称（如 "DeFi Trader"）
    protocol_name: str            # 协议名称
    investment_amount: Optional[float]  # 用户投资金额（如有）

class ValidationIssue(TypedDict):
    """验证问题记录"""
    severity: Literal["critical", "warning", "info"]
    category: str                 # 如 "dangerous_instruction", "suspicious_amount"
    matched_pattern: str          # 触发的模式
    location: str                 # 问题位置描述
    original_text: str            # 原始文本片段

class ValidationResult(TypedDict):
    """验证结果"""
    is_safe: bool                 # False 表示发现问题
    issues: List[ValidationIssue]
    patched_text: str             # 追加警告后的文本
    original_text: str            # 原始文本

class OutputValidator:
    """Agent 输出验证器"""

    DANGEROUS_PATTERNS = {
        "unlimited_approval": r"approve\s+unlimited|approve\s+max|approve\s+all",
        "transfer_all": r"transfer\s+all|drain|empty\s+wallet",
        "contract_attack": r"selfdestruct|delegatecall|rug\s+pull",
        "private_key": r"private\s+key|seed\s+phrase|mnemonic",
    }

    SUSPICIOUS_AMOUNT_THRESHOLDS = {
        "high": 1_000_000,     # >$1M 标记为 critical
        "medium": 100_000,     # >$100K 标记为 warning
    }

    def validate(
        self,
        text: str,
        context: ValidationContext
    ) -> ValidationResult:
        """验证 Agent 输出"""
        pass

    def _check_dangerous_instructions(self, text: str) -> List[ValidationIssue]:
        """检测危险操作指令"""
        pass

    def _check_suspicious_amounts(
        self,
        text: str,
        context: ValidationContext
    ) -> List[ValidationIssue]:
        """检测异常金额"""
        pass

    def _check_addresses(self, text: str) -> List[ValidationIssue]:
        """检测可疑地址（保留扩展点）"""
        pass

    def _patch_output(self, text: str, issues: List[ValidationIssue]) -> str:
        """在输出末尾追加警告段落"""
        pass
```

### S2 ProtocolWhitelist 数据模型

```python
# defiagents/security/protocol_whitelist.py

class ProtocolMetrics(TypedDict):
    """协议评估指标"""
    tvl: Optional[float]          # 总锁仓价值（美元）
    audit_count: Optional[int]    # 审计次数
    age_days: Optional[int]       # 存续时间（天）
    on_hardcoded_list: bool       # 是否在硬编码白名单

class WhitelistResult(TypedDict):
    """白名单验证结果"""
    status: Literal["trusted", "unverified", "suspicious"]
    protocol_slug: str            # 规范化协议 slug
    metrics: ProtocolMetrics      # 评估指标
    confidence_score: float       # 置信度 0-1
    data_sources: List[str]       # 成功的数据源列表
    reason: str                   # 判定原因（人类可读）

class ProtocolWhitelist:
    """协议白名单验证器"""

    # 硬编码可信协议（Top 30）
    HARDCODED_WHITELIST = {
        "aave-v3", "uniswap-v3", "compound-v3", "makerdao",
        "curve-finance", "lido", "rocket-pool", ...
    }

    # 判定规则
    TRUST_RULES = {
        "tvl_threshold": 100_000_000,     # $100M
        "audit_threshold": 2,              # ≥2次审计
        "age_threshold_days": 180,         # ≥6个月
        "min_criteria_met": 3,             # 至少满足3条
    }

    def __init__(self, config: Dict[str, Any]):
        """初始化（注入数据源客户端）"""
        self.defillama = DefiLlamaClient(config)
        self.coingecko = CoinGeckoClient(config)
        self.thegraph = TheGraphClient(config)
        self._cache = {}  # {slug: (result, timestamp)}

    def check(
        self,
        slug_or_name: str,
        chain: Optional[str] = None
    ) -> WhitelistResult:
        """验证协议可信度"""
        pass

    def _normalize_slug(self, slug_or_name: str) -> str:
        """规范化协议名称（复用现有 protocol_registry）"""
        pass

    def _fetch_metrics_parallel(
        self,
        slug: str,
        chain: Optional[str]
    ) -> ProtocolMetrics:
        """并行查询多数据源"""
        pass

    def _compute_trust_level(self, metrics: ProtocolMetrics) -> str:
        """根据指标计算信任级别"""
        pass
```

### 集成点设计

#### 集成点 1: LangGraph 节点包装器

```python
# defiagents/graph/propagation.py（新增文件）

from defiagents.security.output_validator import OutputValidator, ValidationContext

def wrap_agent_node_with_validation(
    node_func: Callable,
    agent_name: str,
    state_key: str
) -> Callable:
    """包装 Agent 节点，追加输出验证"""
    validator = OutputValidator()

    def validated_node(state: TradingAgentsState) -> dict:
        # 1. 执行原节点
        result = node_func(state)
        original_output = result.get(state_key, "")

        # 2. 验证输出
        context = ValidationContext(
            agent_name=agent_name,
            protocol_name=state.get("company_name", ""),
            investment_amount=state.get("investment_amount")
        )
        validation_result = validator.validate(original_output, context)

        # 3. 使用 patched_text（已追加警告）
        result[state_key] = validation_result["patched_text"]

        # 4. 记录问题到状态（供后续分析）
        if not validation_result["is_safe"]:
            result["validation_issues"] = result.get("validation_issues", [])
            result["validation_issues"].extend(validation_result["issues"])

        return result

    return validated_node
```

**修改 setup.py**：
```python
# defiagents/graph/setup.py

from defiagents.graph.propagation import wrap_agent_node_with_validation

# 原创建方式
trader_node = create_analyst_agent(...)

# 新包装方式
validated_trader_node = wrap_agent_node_with_validation(
    trader_node,
    agent_name="DeFi Trader",
    state_key="trader_plan"
)

graph.add_node("trader", validated_trader_node)
```

#### 集成点 2: Bot handlers 前置检查

```python
# bot/handlers.py

from defiagents.security.protocol_whitelist import ProtocolWhitelist

class DeFiAnalysisHandler:
    def __init__(self):
        self.whitelist = ProtocolWhitelist(config=GEMINI_CONFIG)
        self.output_validator = OutputValidator()

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # ... 现有输入净化 ...

        # S2 白名单验证
        whitelist_result = self.whitelist.check(
            slug_or_name=protocol_name,
            chain=extracted_chain
        )

        if whitelist_result["status"] == "suspicious":
            await update.message.reply_text(
                f"⚠️ 协议 `{protocol_name}` 存在风险：\n"
                f"{whitelist_result['reason']}\n\n"
                f"建议选择验证过的协议。是否继续？",
                parse_mode="Markdown"
            )
            # 等待用户确认或取消

        # 执行分析
        result = await self._run_analysis(protocol_name, ...)

        # S1 输出验证（复核最终决策）
        validation_result = self.output_validator.validate(
            text=result["final_decision"],
            context=ValidationContext(
                agent_name="Portfolio Manager",
                protocol_name=protocol_name,
                investment_amount=investment_amount
            )
        )

        # 使用 patched_text 发送（已包含警告）
        await self._send_formatted_report(
            update,
            final_decision=validation_result["patched_text"],
            ...
        )
```

---

## 任务分解

### Task 1: S1 OutputValidator 核心实现 + 单元测试

**ID**: task-1

**描述**：实现 Agent 输出验证器，检测危险指令、异常金额、可疑地址，生成带警告标记的 patched_text。

**文件范围**：
- `defiagents/security/output_validator.py`（核心实现，约 250 行）
- `tests/security/test_output_validator.py`（单测，约 350 行）

**依赖**：None

**实现要点**：
1. **数据模型**：定义 `ValidationContext`, `ValidationIssue`, `ValidationResult`（TypedDict）
2. **危险指令检测**：15+ 正则模式（transfer all, approve unlimited, selfdestruct, rug pull, 等）
3. **金额检测**：解析金额单位（K/M/B/万/亿），对比 `context.investment_amount`，超出阈值标记
4. **警告追加**：在文本末尾生成警告段落，格式如下：
   ```markdown
   ---
   ⚠️ **安全提示** (由 DeFi Agent 安全层检测)

   - [CRITICAL] 检测到危险指令: "approve unlimited" 可能导致资产风险
   - [WARNING] 建议金额异常: $5,000,000 超出预期投资额 $100,000

   请仔细审核以上建议，必要时咨询专业人士。
   ```
5. **扩展点**：地址验证方法预留（当前返回空列表）

**验收标准**：
- [ ] 正确检测 15+ 种危险指令模式
- [ ] 金额解析支持 K/M/B/万/亿 单位
- [ ] 金额异常检测准确率 ≥95%（对比 context.investment_amount）
- [ ] patched_text 格式符合 Markdown 规范，警告段落位于末尾
- [ ] 无危险内容时 `is_safe=True` 且 `patched_text == original_text`

**测试命令**：
```bash
pytest tests/security/test_output_validator.py \
  --cov=defiagents/security/output_validator \
  --cov-report=term \
  --cov-report=html \
  -v
```

**测试焦点**：
- 危险指令检测：20+ 案例（包含大小写、同义词变体）
- 金额解析：各种单位格式（$100K, 100万USDC, 1.5M, 5B）
- 金额异常判定：高于/低于/合理金额的边界情况
- 警告格式：验证 Markdown 语法正确性
- 空输入/无问题输入的边界情况

**覆盖率要求**：≥95%

---

### Task 2: S2 ProtocolWhitelist 核心实现 + 单元测试

**ID**: task-2

**描述**：实现协议白名单验证器，通过多数据源并行查询获取协议指标（TVL/审计/存续时间），根据规则判定可信度。

**文件范围**：
- `defiagents/security/protocol_whitelist.py`（核心实现，约 280 行）
- `tests/security/test_protocol_whitelist.py`（单测，约 400 行）

**依赖**：None

**实现要点**：
1. **数据模型**：定义 `ProtocolMetrics`, `WhitelistResult`（TypedDict）
2. **多数据源集成**：
   - DeFi Llama: `get_protocol_tvl()`, `get_protocol_info()`
   - CoinGecko: `get_coin_info()` → 解析 `genesis_date`, `security_audit`
   - The Graph: 查询 subgraph 存在性（用于验证协议活跃度）
3. **并行查询**：使用 `concurrent.futures.ThreadPoolExecutor`，超时 10 秒
4. **降级策略**：按优先级（DeFi Llama > CoinGecko > The Graph），单个失败不阻断
5. **判定逻辑**：
   ```python
   criteria_met = sum([
       metrics["tvl"] >= 100_000_000,
       metrics["audit_count"] >= 2,
       metrics["age_days"] >= 180,
       metrics["on_hardcoded_list"]
   ])
   if criteria_met >= 3:
       status = "trusted"
   elif criteria_met >= 1:
       status = "unverified"
   else:
       status = "suspicious"
   ```
6. **缓存**：LRU + TTL（300 秒），键格式 `{slug}:{chain}`
7. **协议名规范化**：复用 `protocol_registry.py` 的 fuzzy match 逻辑

**验收标准**：
- [ ] 正确集成 3 个数据源（DeFi Llama, CoinGecko, The Graph）
- [ ] 并行查询性能：3 个数据源总耗时 <15 秒（单个超时 10 秒）
- [ ] 降级策略：单个数据源失败时返回 `unverified` 而非异常
- [ ] 判定规则准确：硬编码白名单 30+ 协议全部返回 `trusted`
- [ ] 缓存命中率 ≥90%（重复查询场景）
- [ ] 协议名规范化：支持模糊匹配（aave → aave-v3）

**测试命令**：
```bash
pytest tests/security/test_protocol_whitelist.py \
  --cov=defiagents/security/protocol_whitelist \
  --cov-report=term \
  --cov-report=html \
  -v
```

**测试焦点**：
- 硬编码白名单协议：aave-v3, uniswap-v3, curve-finance 等（验证 `trusted` 状态）
- 新兴协议：TVL <$100M，审计 <2 次（验证 `unverified` 状态）
- 不存在协议：随机字符串（验证 `suspicious` 状态）
- 数据源降级：模拟 DeFi Llama 失败，验证 CoinGecko 回退
- 缓存效果：连续查询同一协议，验证第二次从缓存返回
- 协议名模糊匹配：输入 "aave", "Aave V3", "AAVE-v3" 均解析为 "aave-v3"
- 跨链查询：指定 `chain="ethereum"` vs `chain="polygon"`

**覆盖率要求**：≥95%

---

### Task 3: LangGraph 集成 - 节点包装器 + 状态传播

**ID**: task-3

**描述**：实现节点包装器 `wrap_agent_node_with_validation()`，在 Phase 3-5 关键节点（Trader, CRO, Portfolio Manager）应用输出验证，将验证问题累积到状态。

**文件范围**：
- `defiagents/graph/propagation.py`（新建文件，约 120 行）
- `defiagents/graph/setup.py`（修改，约 20 行）
- `defiagents/graph/state.py`（修改，新增字段）
- `tests/graph/test_output_validation_integration.py`（集成测试，约 200 行）

**依赖**：Task 1, Task 2

**实现要点**：
1. **包装器工厂函数**：
   ```python
   def wrap_agent_node_with_validation(
       node_func: Callable,
       agent_name: str,
       state_key: str
   ) -> Callable:
       # 执行原节点 → 验证输出 → 追加警告 → 更新状态
   ```
2. **状态字段扩展**（`state.py`）：
   ```python
   class TradingAgentsState(MessagesState):
       # ... 现有字段 ...
       validation_issues: Annotated[List[ValidationIssue], operator.add]
       protocol_trust_level: Optional[str]  # trusted/unverified/suspicious
   ```
3. **应用节点包装**（`setup.py`）：
   - Phase 3: Trader 节点
   - Phase 4: Chief Risk Officer 节点
   - Phase 5: Portfolio Manager 节点
4. **初始状态注入**：在 `TradingAgentsGraph.invoke()` 中添加协议白名单检查：
   ```python
   whitelist_result = self.whitelist.check(company_name)
   initial_state["protocol_trust_level"] = whitelist_result["status"]
   ```
5. **验证问题累积**：使用 `Annotated[List, operator.add]` 自动累加所有节点的问题

**验收标准**：
- [ ] 包装器正确拦截 3 个关键节点的输出
- [ ] 验证问题累积到 `state["validation_issues"]`（跨节点）
- [ ] patched_text 替换原始输出（在状态字段中）
- [ ] 协议信任级别正确注入初始状态
- [ ] 不影响图的正常执行流程（无异常抛出）

**测试命令**：
```bash
pytest tests/graph/test_output_validation_integration.py \
  --cov=defiagents/graph/propagation \
  --cov=defiagents/graph/setup \
  --cov-report=term \
  -v
```

**测试焦点**：
- 端到端流程：输入协议名 → 运行完整图 → 检查 `final_decision` 包含警告
- 问题累积：验证 `state["validation_issues"]` 包含所有节点的问题
- 危险输出传播：Trader 生成危险建议 → Portfolio Manager 看到警告
- 可信协议：白名单协议不触发警告
- 不可信协议：suspicious 协议生成警告但继续执行

**覆盖率要求**：≥90%

---

### Task 4: Telegram Bot 集成 - 前置检查 + 输出复核

**ID**: task-4

**描述**：在 Bot handlers 中集成 S2 白名单前置检查（分析前）和 S1 输出复核（报告发送前），更新消息格式化器支持警告显示。

**文件范围**：
- `bot/handlers.py`（修改 `handle_message()`, 约 50 行新增）
- `bot/formatters.py`（新增 `format_security_warning()`, 约 30 行）
- `tests/bot/test_handlers.py`（集成测试，约 150 行）

**依赖**：Task 1, Task 2

**实现要点**：
1. **前置白名单检查**（`handle_message()` 中）：
   ```python
   whitelist_result = self.whitelist.check(protocol_name)
   if whitelist_result["status"] == "suspicious":
       await update.message.reply_text(
           format_security_warning(whitelist_result),
           reply_markup=InlineKeyboardMarkup([
               [InlineKeyboardButton("继续分析", callback_data="proceed")],
               [InlineKeyboardButton("取消", callback_data="cancel")]
           ])
       )
       return  # 等待回调
   ```
2. **输出复核**（分析完成后）：
   ```python
   final_decision = result["final_decision"]
   validation_result = self.output_validator.validate(
       text=final_decision,
       context=ValidationContext(...)
   )
   formatted_report = format_final_report(
       decision=validation_result["patched_text"],  # 使用 patched 版本
       validation_issues=result.get("validation_issues", [])
   )
   ```
3. **格式化器扩展**（`formatters.py`）：
   - `format_security_warning()`：生成协议风险提示消息
   - `format_validation_issues()`：格式化验证问题列表（Telegram Markdown）
4. **回调处理**：注册 `proceed` / `cancel` 回调，处理用户确认
5. **超时处理**：用户 60 秒未确认自动取消

**验收标准**：
- [ ] suspicious 协议触发前置警告（带确认按钮）
- [ ] trusted 协议直接进入分析（无警告）
- [ ] 最终报告包含所有验证问题（格式化为 Telegram Markdown）
- [ ] 回调处理正确（用户确认 → 继续，用户取消 → 停止）
- [ ] 超时机制生效（60 秒后自动取消）

**测试命令**：
```bash
pytest tests/bot/test_handlers.py \
  --cov=bot/handlers \
  --cov=bot/formatters \
  --cov-report=term \
  -v
```

**测试焦点**：
- 白名单协议：aave-v3 → 直接分析，无警告
- 不可信协议：random-protocol-xyz → 触发警告 + 确认流程
- 用户确认：点击"继续分析" → 正常执行
- 用户取消：点击"取消" → 返回取消消息
- 超时：60 秒未响应 → 自动取消
- 输出包含警告：验证 Telegram 消息包含 `⚠️ **安全提示**` 段落
- 多条警告合并：验证多个 Agent 的问题正确聚合显示

**覆盖率要求**：≥90%

---

### Task 5: 端到端安全流程测试 + 覆盖率验证

**ID**: task-5

**描述**：实现端到端安全流程测试，覆盖输入 → 白名单检查 → Agent 分析 → 输出验证 → Bot 输出的完整链路。验证整体覆盖率 ≥95%。

**文件范围**：
- `tests/security/test_security_flow.py`（新建，约 300 行）
- `tests/conftest.py`（新增 fixtures）
- `.github/workflows/security-tests.yml`（新增 CI 配置）

**依赖**：Task 1, Task 2, Task 3, Task 4

**实现要点**：
1. **端到端场景覆盖**：
   - **Scenario 1: 可信协议正常流程**
     - 输入: "分析 aave-v3"
     - 白名单: trusted
     - Agent 输出: 无危险内容
     - 最终报告: 无警告
   - **Scenario 2: 可信协议危险输出**
     - 输入: "分析 uniswap-v3"
     - 白名单: trusted
     - Agent 输出: 包含 "approve unlimited"（模拟注入攻击）
     - 最终报告: 包含 ⚠️ 警告段落
   - **Scenario 3: 不可信协议**
     - 输入: "分析 unknown-defi-2025"
     - 白名单: suspicious
     - Bot: 触发前置警告 + 确认流程
     - 用户确认后: 继续分析 + 输出警告
   - **Scenario 4: 金额异常检测**
     - 输入: "用 $10K 投资 aave"
     - Agent 输出: 建议投资 $5M（异常）
     - 最终报告: 标记金额异常警告
2. **集成测试策略**：
   - 使用真实配置（Gemini）但 mock 外部 API（DeFi Llama, CoinGecko）
   - 验证状态传播：`protocol_trust_level` → `validation_issues` → `final_decision`
3. **覆盖率聚合**：
   ```bash
   pytest tests/security/ tests/graph/ tests/bot/ \
     --cov=defiagents/security \
     --cov=defiagents/graph/propagation \
     --cov=bot/handlers \
     --cov-report=html \
     --cov-report=term \
     --cov-fail-under=95
   ```
4. **CI 集成**（`.github/workflows/security-tests.yml`）：
   - 触发条件：PR 修改 `defiagents/security/`, `bot/`, `defiagents/graph/`
   - 失败条件：覆盖率 <95% 或任意测试失败

**验收标准**：
- [ ] 4 个端到端场景全部通过
- [ ] 状态字段正确传播（`protocol_trust_level`, `validation_issues`）
- [ ] Bot 消息格式正确（包含警告段落，Markdown 语法有效）
- [ ] 整体覆盖率 ≥95%（安全模块 + 图集成 + Bot handlers）
- [ ] CI 流程通过（GitHub Actions）

**测试命令**：
```bash
# 运行完整安全测试套件
pytest tests/security/test_security_flow.py -v

# 验证覆盖率
pytest tests/security/ tests/graph/ tests/bot/ \
  --cov=defiagents/security \
  --cov=defiagents/graph/propagation \
  --cov=bot/handlers \
  --cov-report=html \
  --cov-report=term \
  --cov-fail-under=95
```

**测试焦点**：
- **完整链路**：用户输入 → Bot 接收 → 白名单检查 → Agent 分析 → 输出验证 → 格式化发送
- **状态一致性**：验证 `state["protocol_trust_level"]` 在所有 Agent 间可见
- **问题累积**：验证多个 Agent 的警告正确累加到 `validation_issues`
- **格式正确性**：验证 Bot 消息符合 Telegram Markdown V2 语法
- **性能回归**：验证新增验证层不显著增加延迟（<5% 增量）

**覆盖率要求**：≥95%（整体）

---

## 风险和注意事项

### 高风险项

1. **误报率（False Positives）**
   - **风险**：合法投资建议被错误标记为危险
   - **缓解**：
     - 投资关键词白名单（stake, deposit, provide liquidity）
     - 严格区分 "approve" 和 "approve unlimited"
     - 金额检测允许 2x 误差容限
   - **测试重点**：收集真实 Agent 输出样本，验证误报率 <5%

2. **数据源依赖性**
   - **风险**：DeFi Llama/CoinGecko API 失败导致所有协议标记为 `unverified`
   - **缓解**：
     - 多数据源降级策略（3 个源按优先级尝试）
     - 缓存机制（5 分钟 TTL）
     - 硬编码白名单兜底（Top 30 协议）
   - **监控**：记录数据源失败率，触发告警

3. **性能影响**
   - **风险**：每个 Agent 节点增加验证开销，延长总响应时间
   - **缓解**：
     - 正则匹配优化（预编译模式）
     - 白名单缓存（避免重复查询）
     - 并行数据源查询（10 秒超时）
   - **目标**：验证层开销 <5% 总响应时间

### 中风险项

4. **协议名规范化失败**
   - **风险**：用户输入 "Aave Version 3" 无法匹配 "aave-v3"
   - **缓解**：复用 `protocol_registry.py` 的 fuzzy match（Levenshtein 距离）
   - **测试**：覆盖 50+ 协议别名（大小写、连字符、版本号变体）

5. **Telegram 消息格式兼容性**
   - **风险**：警告段落破坏 Markdown 语法（如未转义的下划线）
   - **缓解**：
     - 使用 `escape_markdown_v2()` 转义特殊字符
     - 测试工具：`python-telegram-bot` 的 Markdown 验证器
   - **测试**：验证 20+ 警告模板正确渲染

6. **状态字段冲突**
   - **风险**：新增 `validation_issues` 字段与现有 Agent 逻辑冲突
   - **缓解**：使用 `Annotated[List, operator.add]` 确保只追加不覆盖
   - **测试**：验证多个节点并发写入 `validation_issues` 不丢失数据

### 低风险项

7. **硬编码白名单过时**
   - **风险**：Top 30 协议列表未更新，遗漏新兴头部协议
   - **缓解**：每季度从 DeFi Llama TVL 排名更新列表（自动化脚本）
   - **文档**：在 `protocol_whitelist.py` 注释中记录更新日期

8. **测试数据真实性**
   - **风险**：mock 数据与真实 API 响应不一致
   - **缓解**：使用 `pytest-recording` 录制真实 API 响应作为 fixtures
   - **CI**：每周运行一次真实 API 测试（非 mock）验证兼容性

---

## 技术债务和未来优化

1. **地址验证扩展点**
   - **当前**：`OutputValidator._check_addresses()` 返回空列表
   - **未来**：集成链上地址黑名单（Chainalysis, Etherscan）
   - **优先级**：低（需要付费 API）

2. **机器学习模型**
   - **当前**：基于规则的正则匹配
   - **未来**：训练 LLM 分类器检测危险输出（few-shot 或 fine-tuned）
   - **优先级**：中（需要标注数据集）

3. **实时数据源**
   - **当前**：DeFi Llama 数据延迟 1 小时
   - **未来**：集成 The Graph 实时子图查询
   - **优先级**：低（性能 vs 准确度权衡）

4. **用户反馈循环**
   - **当前**：无用户反馈机制
   - **未来**：Bot 提供"报告误报"按钮，收集数据优化规则
   - **优先级**：中（依赖用户量）

---

## 附录：参考文档

- **现有安全架构**：`defiagents/security/input_sanitizer.py`（输入净化模式）
- **数据源模式**：`defiagents/dataflows/defi/defillama.py`（缓存 + 降级）
- **协议注册表**：`defiagents/protocol_registry.py`（硬编码白名单来源）
- **LangGraph 状态**：`defiagents/agents/utils/agent_states.py`（状态字段定义）
- **Bot handlers**：`bot/handlers.py`（现有安全集成点）

---

## 预估工作量

| 任务 | 预估时间 | 复杂度 | 依赖 |
|------|---------|-------|------|
| Task 1: S1 OutputValidator | 4-6h | 中 | None |
| Task 2: S2 ProtocolWhitelist | 5-7h | 高 | None |
| Task 3: LangGraph 集成 | 4-6h | 中 | Task 1, 2 |
| Task 4: Bot 集成 | 4-6h | 中 | Task 1, 2 |
| Task 5: 端到端测试 | 5-7h | 高 | Task 1-4 |
| **总计** | **22-32h** | - | - |

**关键路径**：Task 1/2 并行 → Task 3/4 并行 → Task 5

**建议迭代计划**：
- **Sprint 1**（Week 1）：完成 Task 1, 2（核心模块）
- **Sprint 2**（Week 2）：完成 Task 3, 4（集成）
- **Sprint 3**（Week 3）：完成 Task 5（端到端测试 + 优化）
