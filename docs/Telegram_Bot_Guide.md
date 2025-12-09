# Telegram Bot 使用指南

## 快速开始

### 1. 创建Telegram Bot

1. 在Telegram中搜索 `@BotFather`
2. 发送 `/newbot` 命令
3. 按照提示设置Bot名称和用户名
4. 保存BotFather返回的Token

### 2. 配置环境变量

复制`.env.example`为`.env`并填入配置：

```bash
cp .env.example .env
```

编辑`.env`文件，至少需要设置：

```bash
# 必需
GOOGLE_API_KEY=your_gemini_api_key
THE_GRAPH_API_KEY=your_thegraph_api_key
TELEGRAM_BOT_TOKEN=your_bot_token

# 可选
BOT_ENABLE_SANITIZATION=true
BOT_RATE_LIMIT_PER_USER=10
```

### 3. 安装依赖

```bash
pip install python-telegram-bot
```

### 4. 运行Bot

```bash
python3 run_bot.py
```

或使用PYTHONPATH：

```bash
PYTHONPATH=$PWD python3 -m bot.telegram_bot
```

---

## 功能说明

### 支持的命令

| 命令 | 用法 | 说明 |
|------|------|------|
| `/start` | `/start` | 开始使用，显示欢迎信息 |
| `/help` | `/help` | 显示帮助信息 |
| `/analyze` | `/analyze <协议名>` | 分析指定DeFi协议 |
| `/strategy` | `/strategy [金额] [风险]` | 获取投资策略推荐 |
| `/compare` | `/compare <协议1> <协议2>` | 对比两个协议 |

### 命令示例

#### 分析协议
```
/analyze aave-v3
/analyze uniswap-v3
/analyze compound
```

#### 获取策略
```
/strategy
/strategy 100000 low
/strategy 50000 medium
```

#### 对比协议
```
/compare aave-v3 compound-v3
/compare uniswap-v3 curve
```

### 自然语言输入

Bot支持自然语言输入，无需使用命令：

```
"分析Aave V3的投资机会"
"我想用10万美金投资低风险的借贷协议"
"对比Uniswap和Curve在Arbitrum上的流动性池收益"
"找一个APY至少8%的稳定币策略"
"分析Ethereum上TVL大于1B的DEX协议"
```

Bot会自动提取您的意图并进行分析。

---

## 安全特性

### 输入净化

Bot集成了输入净化层，会自动：
- 检测提示注入攻击
- 过滤恶意命令
- 规范化用户输入
- 提取投资意图

如果您的输入被拒绝，请：
- 使用DeFi相关术语
- 避免特殊字符或系统命令
- 用自然语言描述投资需求

### 速率限制

默认限制：
- 每个用户每小时最多10次请求
- 超过限制后需要等待

管理员用户不受速率限制。

---

## 分析流程

Bot收到请求后会：

1. **安全检查**（如果启用）
   - 检测注入攻击
   - 提取投资意图
   - 显示理解的参数

2. **执行分析**
   - 调用DeFi Market Analyst
   - 调用Protocol Fundamentals Analyst
   - 调用Yield Analyst
   - 调用Risk Analyst
   - Bull/Bear辩论
   - 风险团队讨论
   - Trader最终决策

3. **返回结果**
   - 市场分析报告
   - 基本面分析
   - 收益分析
   - 风险评估
   - 最终投资建议

整个过程约需1-3分钟。

---

## 配置选项

### 环境变量

所有配置都通过环境变量设置：

```bash
# Bot Token
TELEGRAM_BOT_TOKEN=your_token

# Agent配置
AGENT_CONFIG_TYPE=gemini  # gemini/openai/ollama

# 消息长度限制
BOT_MAX_MESSAGE_LENGTH=4096

# 是否显示进度更新
BOT_ENABLE_PROGRESS=true

# 分析超时（秒）
BOT_ANALYSIS_TIMEOUT=180

# 是否启用输入净化
BOT_ENABLE_SANITIZATION=true

# 速率限制（请求数/小时）
BOT_RATE_LIMIT_PER_USER=10

# 速率限制窗口（秒）
BOT_RATE_LIMIT_WINDOW=3600

# 管理员用户ID（逗号分隔）
BOT_ADMIN_USER_IDS=123456789,987654321
```

### 修改配置

1. 编辑`.env`文件
2. 重启Bot使配置生效

---

## 故障排查

### Bot无法启动

**问题**：`TELEGRAM_BOT_TOKEN not found`

**解决方案**：
- 检查`.env`文件是否存在
- 确认Token已正确配置
- 尝试直接设置环境变量：
  ```bash
  export TELEGRAM_BOT_TOKEN=your_token
  python3 run_bot.py
  ```

### 分析超时

**问题**：分析时间过长，超过180秒

**解决方案**：
- 增加超时时间：`BOT_ANALYSIS_TIMEOUT=300`
- 检查网络连接
- 检查API密钥是否有效

### 速率限制错误

**问题**：提示"请求过于频繁"

**解决方案**：
- 等待一段时间后重试
- 增加速率限制：`BOT_RATE_LIMIT_PER_USER=20`
- 联系管理员添加到白名单

### 输入被拒绝

**问题**：提示"输入包含可疑内容"

**解决方案**：
- 使用DeFi相关术语
- 避免使用"system"、"ignore"等敏感词
- 用自然语言描述需求
- 如果误报，联系管理员

---

## 高级功能

### 管理员命令（TODO）

管理员用户可以使用额外命令：

```
/stats - 查看使用统计
/broadcast <消息> - 向所有用户广播
/whitelist <user_id> - 添加到白名单
```

### 集成到其他平台

Bot的核心功能可以轻松集成到：
- Discord Bot
- 微信公众号
- Slack Bot
- Web前端

只需实现对应平台的接口即可复用分析逻辑。

---

## 部署建议

### 本地开发

```bash
python3 run_bot.py
```

### 生产部署

#### 使用systemd（Linux）

创建服务文件 `/etc/systemd/system/defi-bot.service`：

```ini
[Unit]
Description=DeFi Telegram Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/TradingAgents
Environment="PYTHONPATH=/path/to/TradingAgents"
ExecStart=/usr/bin/python3 run_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable defi-bot
sudo systemctl start defi-bot
sudo systemctl status defi-bot
```

#### 使用Docker

创建`Dockerfile`：

```dockerfile
FROM python:3.10

WORKDIR /app
COPY . /app

RUN pip install -e .
RUN pip install python-telegram-bot

CMD ["python3", "run_bot.py"]
```

构建并运行：

```bash
docker build -t defi-bot .
docker run -d --name defi-bot --env-file .env defi-bot
```

#### 使用PM2（Node.js）

```bash
pm2 start run_bot.py --name defi-bot --interpreter python3
pm2 save
pm2 startup
```

---

## 成本估算

### 免费方案（推荐）

使用完全免费的服务：
- Google Gemini：免费（60 requests/分钟）
- The Graph：免费（100K queries/月）
- DeFi Llama：完全免费
- CoinGecko：免费（50 calls/分钟）

**总成本：$0/月**

适用场景：
- 个人使用
- 小团队（< 10用户）
- 轻度使用（< 100次分析/天）

### 付费方案

如需更高性能或更多用户：
- OpenAI API：$200-500/月（使用GPT-4）
- The Graph Pro：$390/月（无限查询）
- Alchemy/Infura：$50-200/月（高级RPC）

**总成本：$250-1000/月**

适用场景：
- 商业使用
- 大量用户（> 100用户）
- 高频使用（> 1000次分析/天）

---

## 常见问题

### Bot响应慢？

分析需要时间：
- 正常分析：60-120秒
- 复杂分析：120-180秒

如果超过3分钟，可能是网络问题或API限制。

### 支持哪些协议？

目前支持所有DeFi Llama收录的协议（1000+），包括：
- 借贷：Aave, Compound, Radiant
- DEX：Uniswap, Curve, Balancer
- 质押：Lido, Rocket Pool
- 衍生品：GMX, dYdX
- ...更多

### 数据准确性？

数据来源：
- DeFi Llama：TVL、APY等
- The Graph：链上交易数据
- CoinGecko：代币价格
- 链上RPC：实时数据

所有数据均来自公开API，准确性取决于数据源。

### 是否安全？

安全保障：
- 输入净化层防止注入攻击
- 不托管资金，不进行交易
- 仅提供分析建议
- 开源代码可审计

但请注意：
- 不构成投资建议
- 自行承担投资风险
- 保护好API密钥

---

## 联系和支持

- GitHub Issues：报告Bug或功能请求
- 文档：查看完整技术文档
- 社区：加入Discord/Telegram社区

---

*最后更新：2025-12-10*
*版本：v2.0-alpha*
