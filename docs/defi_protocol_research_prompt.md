# DeFi 协议深度调研 Prompt

## 调研目标

为 DeFi AI Agent 项目收集主流 DeFi 协议的详细信息，包括数据源、API 接口、关键指标计算方法等，以便实现自动化分析和策略建议功能。

---

## 调研任务说明

请按照以下分类和要求，调研主流 DeFi 协议的详细信息。对于每个协议，需要提供完整的数据源映射和技术细节。

---

## Part 1: DEX（去中心化交易所）协议

### 目标：调研至少 6 个主流 DEX 协议

**必需协议（优先）：**
- Uniswap V3
- Curve Finance
- Balancer
- SushiSwap
- PancakeSwap（BSC）

**可选协议：**
- Aerodrome（Base）
- Velodrome（Optimism）
- Trader Joe（Avalanche）
- Camelot（Arbitrum）

### 对于每个 DEX 协议，请提供以下信息：

#### 1. 基本信息
- **协议名称**：完整名称和常用简称
- **协议类型**：AMM（自动做市商）/ 订单簿 / 混合型
- **支持的区块链**：列出所有支持的链（如 Ethereum, Arbitrum, Optimism 等）
- **官网**：官方网站 URL
- **文档**：开发者文档 URL

#### 2. DeFi Llama 集成
- **协议 Slug**：DeFi Llama API 中使用的协议标识符
  - 示例：`uniswap-v3`, `curve-dex`
  - 验证方法：访问 `https://api.llama.fi/protocol/{slug}` 测试是否返回数据
- **TVL 获取方式**：是否支持单独获取各链的 TVL
- **历史数据**：是否可以获取历史 TVL 和交易量数据

#### 3. The Graph 子图
- **子图名称**：完整的子图 ID
  - 格式：`{organization}/{subgraph-name}`
  - 示例：`uniswap/uniswap-v3`
- **子图端点**：针对每条支持的链提供子图地址
  - Ethereum 主网子图
  - Arbitrum 子图
  - Optimism 子图
  - 其他链的子图
- **关键查询示例**：提供 GraphQL 查询示例，包括：
  - 获取流动性池列表（前 10 个按 TVL 排序）
  - 获取单个池的详细信息（TVL、交易量、费用）
  - 获取池的 24 小时交易量

**GraphQL 查询模板：**
```graphql
# 查询示例 1: 获取 Top 流动性池
{
  pools(first: 10, orderBy: totalValueLockedUSD, orderDirection: desc) {
    id
    token0 { symbol, name }
    token1 { symbol, name }
    totalValueLockedUSD
    volumeUSD
    feeTier
  }
}

# 查询示例 2: 获取特定池的数据
{
  pool(id: "0x...") {
    token0 { symbol }
    token1 { symbol }
    totalValueLockedUSD
    volumeUSD
    feeTier
    liquidity
  }
}
```

#### 4. 官方 API（如果有）
- **API 端点**：官方提供的 REST API 或 GraphQL API
- **认证方式**：是否需要 API Key
- **数据类型**：可以获取哪些数据（池列表、价格、APY 等）
- **速率限制**：请求频率限制

#### 5. 关键指标与计算方法
- **流动性深度（TVL）**：如何计算单个池的 TVL
- **交易量**：24h / 7d / 30d 交易量的数据来源
- **费用收入**：
  - 费率结构（如 Uniswap V3 的 0.05% / 0.3% / 1%）
  - 如何计算 LP 的费用收益
- **无常损失（Impermanent Loss）**：
  - 是否有现成的 IL 计算工具
  - IL 计算公式或参考链接
- **APY/APR 计算**：
  - 如何计算流动性提供者的年化收益
  - 是否包含代币激励（流动性挖矿）

#### 6. 智能合约地址
- **主要合约**：每条链上的核心合约地址
  - Factory 合约
  - Router 合约
  - Pool 合约（示例）
- **合约源码验证**：Etherscan / Arbiscan 等浏览器链接

#### 7. 风险评估
- **审计报告**：审计机构和报告链接
- **历史漏洞**：是否有过安全事故
- **TVL 等级**：当前 TVL（> $1B / $100M-1B / < $100M）
- **风险等级**：蓝筹 / 成熟 / 新兴 / 实验性

---

## Part 2: 借贷协议

### 目标：调研至少 4 个主流借贷协议

**必需协议（优先）：**
- Aave V3
- Compound V3
- Radiant Capital

**可选协议：**
- Morpho
- Spark Protocol
- Venus Protocol（BSC）

### 对于每个借贷协议，请提供以下信息：

#### 1. 基本信息
- **协议名称**
- **协议类型**：超额抵押 / 点对点借贷 / 其他
- **支持的区块链**
- **官网**和**文档**

#### 2. DeFi Llama 集成
- **协议 Slug**：示例 `aave-v3`
- **TVL 分类**：是否区分存款 TVL 和借款量
- **多链支持**：各链的独立数据

#### 3. The Graph 子图
- **子图名称**：示例 `aave/protocol-v3`
- **支持的链**：列出每条链的子图端点
- **关键查询示例**：
  - 获取所有资产的存款 APY 和借款 APY
  - 获取单个用户的抵押品和借款情况
  - 获取资产的利用率和清算阈值

**GraphQL 查询模板：**
```graphql
# 查询示例: 获取资产列表及利率
{
  reserves(first: 20) {
    symbol
    name
    liquidityRate        # 存款利率
    variableBorrowRate   # 借款利率
    totalLiquidity       # 总存款
    totalDebt            # 总借款
    utilizationRate      # 利用率
    liquidationThreshold # 清算阈值
  }
}
```

#### 4. 官方 API（如果有）
- **API 端点**：示例 `api.aave.com`
- **提供的数据**：实时利率、资产列表、用户数据

#### 5. 关键指标与计算方法
- **存款 APY**：如何计算年化存款收益
  - 基础利率计算公式
  - 是否包含激励代币（如 AAVE、COMP）
  - 复利计算方式（如果有）
- **借款利率**：
  - 固定利率 vs 浮动利率
  - 利率模型（如何根据利用率调整利率）
- **清算机制**：
  - 清算阈值（Loan-to-Value, LTV）
  - 清算惩罚（Liquidation Penalty）
  - 健康因子（Health Factor）计算
- **利用率（Utilization Rate）**：
  - 计算公式：`借款量 / 总存款`
  - 如何影响利率

#### 6. 支持的资产列表
- **主要资产**：列出支持的主要加密资产（如 ETH, USDC, USDT, DAI, WBTC 等）
- **稳定币**：支持哪些稳定币
- **长尾资产**：是否支持风险较高的资产

#### 7. 智能合约地址
- **每条链的主要合约**：
  - Pool 合约
  - Pool Configurator
  - Oracle（价格预言机）
  - 各资产的 aToken / cToken 地址

#### 8. 风险评估
- **审计报告**
- **历史安全事件**
- **TVL 等级**
- **风险等级**

---

## Part 3: 收益类协议

### 目标：调研至少 4 个收益类协议

**分类 A - 收益聚合器（至少 2 个）：**
- Yearn Finance
- Beefy Finance

**分类 B - 流动性质押（至少 1 个）：**
- Lido
- Rocket Pool

**分类 C - 收益代币化（至少 1 个）：**
- Pendle Finance

### 对于每个收益协议，请提供以下信息：

#### 1. 基本信息
- **协议名称**
- **协议类型**：收益聚合器 / 流动性质押 / 收益代币化
- **支持的区块链**
- **官网**和**文档**

#### 2. DeFi Llama 集成
- **协议 Slug**
- **TVL 数据**
- **收益率数据**：是否提供 APY

#### 3. The Graph 子图
- **子图名称**
- **关键查询示例**：
  - 获取策略列表和 APY
  - 获取用户的存款和收益历史

#### 4. 策略详情
- **底层策略**：资金部署到哪些协议（如 Yearn 的 USDC vault 可能部署到 Aave, Compound, Curve 等）
- **收益来源**：
  - 交易费用分成
  - 借贷利息
  - 流动性挖矿激励
  - 其他
- **自动复利**：是否自动复投收益

#### 5. 费用结构
- **管理费（Management Fee）**：通常为年化 0-2%
- **业绩费（Performance Fee）**：通常为收益的 5-20%
- **提款费**：是否有提前取款费用

#### 6. 历史收益表现
- **数据来源**：在哪里可以查看历史 APY
- **平均 APY**：过去 30 天、90 天、1 年的平均收益率
- **最高/最低 APY**：历史波动范围

#### 7. 流动性质押特有信息（如果适用）
- **质押资产**：如 ETH → stETH（Lido）
- **质押 APR**：基础质押收益率
- **流动性溢价/折价**：stETH 相对于 ETH 的价格偏差
- **退出机制**：
  - 是否需要等待解锁期
  - 是否支持即时退出（通过 DEX）

#### 8. 收益代币化特有信息（如果适用 - Pendle）
- **PT（Principal Token）**：本金代币
- **YT（Yield Token）**：收益代币
- **固定收益率**：如何确定
- **到期时间**：代币的到期日期
- **隐含 APY**：如何计算

#### 9. 智能合约地址
- **Vault / Pool 合约**
- **Strategy 合约**
- **Token 合约**（如 stETH, yvUSDC 等）

#### 10. 风险评估
- **智能合约风险**
- **策略风险**：底层协议的风险叠加
- **审计报告**
- **TVL 等级**
- **风险等级**

---

## Part 4: 额外协议（可选，根据时间和资源）

### 衍生品协议（1-2 个）
- **GMX**（永续合约）
- **dYdX**（订单簿永续合约）

### 稳定币协议（1-2 个）
- **MakerDAO**（DAI）
- **Frax Finance**（FRAX）

### 跨链桥（1 个）
- **Stargate Finance**

---

## 输出格式要求

### 格式 1: 协议数据表格（用于快速查看）

```markdown
| 协议名称 | 类型 | 支持的链 | DeFi Llama Slug | The Graph 子图 | 官方 API | TVL | 风险等级 | 备注 |
|---------|------|---------|----------------|---------------|---------|-----|---------|------|
| Uniswap V3 | DEX | ETH/ARB/OP/BASE/POLY | uniswap-v3 | uniswap/uniswap-v3 | - | $4.5B | 蓝筹 | 费率 0.05%-1% |
| Aave V3 | 借贷 | ETH/ARB/OP/BASE/POLY | aave-v3 | aave/protocol-v3 | api.aave.com | $12B | 蓝筹 | 支持 20+ 资产 |
| ... | ... | ... | ... | ... | ... | ... | ... | ... |
```

### 格式 2: 详细协议文档（每个协议一个独立文档）

```markdown
# 协议名称: Uniswap V3

## 1. 基本信息
- **类型**: DEX (AMM)
- **官网**: https://uniswap.org
- **文档**: https://docs.uniswap.org
- **支持的链**: Ethereum, Arbitrum, Optimism, Base, Polygon

## 2. 数据源配置

### DeFi Llama
- **Slug**: `uniswap-v3`
- **TVL API**: `https://api.llama.fi/protocol/uniswap-v3`
- **多链支持**: ✅

### The Graph 子图

#### Ethereum 主网
- **子图 ID**: `uniswap/uniswap-v3`
- **端点**: `https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3`

#### Arbitrum
- **子图 ID**: `uniswap/uniswap-v3-arbitrum`
- **端点**: `https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3-arbitrum`

（其他链类似）

### GraphQL 查询示例

```graphql
# 获取 Top 10 流动性池
{
  pools(first: 10, orderBy: totalValueLockedUSD, orderDirection: desc) {
    id
    token0 {
      symbol
      name
      decimals
    }
    token1 {
      symbol
      name
      decimals
    }
    totalValueLockedUSD
    volumeUSD
    feeTier
    liquidity
  }
}

# 获取池的 24h 数据
{
  poolDayDatas(
    first: 1
    orderBy: date
    orderDirection: desc
    where: { pool: "0x..." }
  ) {
    volumeUSD
    tvlUSD
    feesUSD
  }
}
```

## 3. 关键指标计算

### TVL（总锁仓量）
- **计算方式**: `(token0_reserve * token0_price) + (token1_reserve * token1_price)`
- **数据来源**: The Graph 子图或 DeFi Llama API

### 交易量
- **24h 交易量**: 通过 `poolDayDatas` 查询
- **7d/30d 交易量**: 累加多天的 `volumeUSD`

### 费用收入
- **费率**: 0.05% (500), 0.3% (3000), 1% (10000)
- **LP 收益**: `fees = volume * fee_tier`

### APY 计算
```
年化收益率 = (24h 费用 * 365) / TVL * 100%
```

### 无常损失
- **公式**: 参考 https://docs.uniswap.org/concepts/protocol/concentrated-liquidity
- **工具**: https://defi-lab.xyz/uniswapv3simulator

## 4. 智能合约地址

### Ethereum 主网
- **Factory**: `0x1F98431c8aD98523631AE4a59f267346ea31F984`
- **Router**: `0xE592427A0AEce92De3Edee1F18E0157C05861564`
- **NFT Position Manager**: `0xC36442b4a4522E871399CD717aBDD847Ab11FE88`

（其他链类似）

## 5. 风险评估
- **审计机构**: Trail of Bits, ABDK, Certora
- **历史漏洞**: 无重大事故
- **TVL**: $4.5B（2024-01）
- **风险等级**: 蓝筹（低风险）
- **运营时间**: 2021 年 5 月至今（3+ 年）

## 6. 参考资料
- 官方文档: https://docs.uniswap.org
- GitHub: https://github.com/Uniswap/v3-core
- 审计报告: [链接]
```

---

## 数据验证检查清单

在完成调研后，请验证以下内容：

### DeFi Llama 数据验证
- [ ] 访问 `https://api.llama.fi/protocol/{slug}` 确认返回有效数据
- [ ] 检查返回的 TVL 数据是否合理
- [ ] 确认支持的链列表是否准确

### The Graph 子图验证
- [ ] 访问子图端点，执行示例查询
- [ ] 确认查询返回有效数据（非空）
- [ ] 检查数据的时效性（最近更新时间）

### 智能合约验证
- [ ] 在区块链浏览器（Etherscan 等）上验证合约地址
- [ ] 确认合约已验证源码
- [ ] 检查合约的审计报告链接

### 数据一致性检查
- [ ] 对比 DeFi Llama TVL 与 The Graph 数据
- [ ] 检查不同数据源的 TVL 差异是否在合理范围（< 10%）
- [ ] 确认 APY 计算方法的合理性

---

## 调研优先级建议

### 第一优先级（立即调研）：
1. **Uniswap V3** - 最大的 DEX
2. **Aave V3** - 最大的借贷协议
3. **Lido** - 最大的流动性质押协议

### 第二优先级（尽快完成）：
4. **Curve Finance** - 稳定币 DEX
5. **Compound V3** - 老牌借贷协议
6. **Yearn Finance** - 收益聚合器

### 第三优先级（可延后）：
7. **Pendle Finance** - 收益代币化
8. **GMX** - 衍生品
9. 其他协议

---

## 调研资源推荐

### 数据聚合平台
- **DeFi Llama**: https://defillama.com - TVL、APY 数据
- **The Graph**: https://thegraph.com/explorer - 子图浏览
- **DeBank**: https://debank.com - 多链 DeFi 数据

### 技术文档
- **各协议官方文档**: 优先参考
- **GitHub 仓库**: 查看合约源码
- **DeFi SDK**: https://github.com/DeFi-SDK

### 审计报告来源
- **DeFi Safety**: https://defisafety.com
- **Code4rena**: https://code4rena.com
- **Sherlock**: https://www.sherlock.xyz

### 社区资源
- **DeFi Pulse**: https://defipulse.com
- **L2Beat**: https://l2beat.com（L2 协议数据）
- **Dune Analytics**: https://dune.com（自定义查询）

---

## 输出交付物

### 必需交付物：
1. **协议总览表格**（格式 1）- Excel 或 Markdown 格式
2. **详细协议文档**（格式 2）- 每个协议一个 Markdown 文件
3. **The Graph 查询集合** - 包含所有测试通过的 GraphQL 查询

### 可选交付物：
4. **数据验证报告** - 记录数据源的准确性和可靠性
5. **API 集成示例代码** - Python 代码示例
6. **协议对比分析** - 同类协议的优劣对比

---

## 注意事项

1. **数据时效性**: DeFi 协议更新迅速，记录调研日期
2. **多链差异**: 同一协议在不同链上可能有不同的参数和限制
3. **费率变化**: 某些协议的费率可能动态调整，记录当前值和调整机制
4. **测试网 vs 主网**: 确保收集的是主网数据
5. **API 限制**: 注意各 API 的速率限制和使用条款

---

## 时间估算

- **单个 DEX 协议**: 1-2 小时
- **单个借贷协议**: 1.5-2.5 小时（更复杂）
- **单个收益协议**: 1-2 小时
- **总计（15 个协议）**: 约 20-30 小时

建议分多次完成，每次专注 2-3 个协议，确保质量。
