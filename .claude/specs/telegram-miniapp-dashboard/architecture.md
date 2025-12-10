# Telegram Mini App 仪表盘 - 架构设计

## 项目概述

将现有的 DeFi Agent Telegram Bot 升级为完整的 Telegram Mini App，提供类似传统股票投资平台的用户体验，集成 AI Agent 功能。

**核心目标**：
- 从纯文本对话式交互升级为可视化仪表盘
- 保留 Agent 智能分析能力
- 提供历史记录追踪和实时数据监控
- 支持多用户账户管理

---

## 架构对比

### 当前架构（Bot Only）

```
用户
  ↓
Telegram Bot (python-telegram-bot)
  ↓
CommandHandlers (bot/handlers.py)
  ↓
DeFi Agent (LangGraph Multi-Agent System)
  ↓
数据源 (DeFi Llama, The Graph, CoinGecko)
```

**限制**：
- 纯文本交互，无可视化
- 无历史记录持久化
- 无用户账户体系
- 无实时数据更新

---

### 目标架构（Mini App + API）

```
┌─────────────────────────────────────────────────────────────┐
│                    Telegram Mini App                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 仪表盘页面   │  │ 分析页面     │  │ 历史记录页面 │      │
│  │ - 资产概览   │  │ - Agent对话  │  │ - 分析历史   │      │
│  │ - 实时行情   │  │ - 可视化图表 │  │ - 收藏协议   │      │
│  │ - 快捷操作   │  │ - 报告下载   │  │ - 筛选搜索   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                           │                                  │
│                    Telegram WebApp SDK                       │
└───────────────────────────┼──────────────────────────────────┘
                            │ HTTPS + WebSocket
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ REST API     │  │ WebSocket    │  │ Auth Module  │      │
│  │ - /api/v1/*  │  │ - 实时数据   │  │ - JWT Token  │      │
│  │ - CRUD操作   │  │ - Agent消息  │  │ - 用户会话   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                           │                                  │
│            ┌──────────────┼──────────────┐                  │
│            ↓              ↓               ↓                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ DeFi Agent   │  │ PostgreSQL   │  │ Redis        │      │
│  │ (现有系统)   │  │ - 用户数据   │  │ - 缓存       │      │
│  │              │  │ - 分析记录   │  │ - 会话       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ↓
              ┌─────────────────────────────┐
              │   DeFi 数据源              │
              │ - DeFi Llama               │
              │ - The Graph                │
              │ - CoinGecko                │
              └─────────────────────────────┘
```

---

## 技术栈选择

### 前端（Telegram Mini App）

**核心框架**：
- **React 18** + TypeScript
  - 理由：生态成熟，Telegram Mini App 官方示例支持
  - 替代：Vue.js（如果团队更熟悉）

**UI 组件库**：
- **Ant Design Mobile** 或 **Chakra UI**
  - 理由：移动端优化，组件丰富
  - 股票样式：集成 TradingView 轻量图表库

**状态管理**：
- **Zustand** 或 **Redux Toolkit**
  - 理由：轻量级，支持异步操作

**数据可视化**：
- **ECharts** 或 **Recharts**
  - K线图、趋势图、雷达图
  - 比 matplotlib 更适合 Web 交互

**实时通信**：
- **Socket.IO Client** 或原生 WebSocket
  - 接收 Agent 实时分析消息
  - 实时数据流更新

**Telegram 集成**：
- **@twa-dev/sdk** (Telegram WebApp SDK)
  - 用户身份验证
  - 主题适配（Dark/Light）
  - 支付集成（可选）

---

### 后端（API Server）

**Web 框架**：
- **FastAPI** (Python 3.11+)
  - 理由：与现有 Python 代码兼容，性能优异
  - 自动生成 OpenAPI 文档
  - 原生支持异步和 WebSocket

**数据库 ORM**：
- **SQLAlchemy 2.0** + **Alembic**
  - 数据库迁移管理
  - 支持 PostgreSQL

**认证授权**：
- **FastAPI-Users** 或自定义 JWT
  - Telegram User ID 作为主键
  - 无需传统密码登录

**异步任务**：
- **Celery** + **Redis**
  - 后台分析任务
  - 定时数据更新

**WebSocket 管理**：
- **FastAPI WebSocket** + **Redis Pub/Sub**
  - 多实例消息广播
  - Agent 进度实时推送

---

### 数据库设计

**PostgreSQL 表结构**：

```sql
-- 用户表
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    language_code VARCHAR(10),
    created_at TIMESTAMP DEFAULT NOW(),
    last_active TIMESTAMP,
    settings JSONB DEFAULT '{}'
);

-- 分析历史表
CREATE TABLE analysis_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    protocol_name VARCHAR(255) NOT NULL,
    query_text TEXT,
    query_type VARCHAR(50), -- 'analyze', 'compare', 'strategy', 'recommend'
    result JSONB NOT NULL,   -- 完整分析结果
    duration FLOAT,          -- 分析耗时（秒）
    created_at TIMESTAMP DEFAULT NOW(),
    cached BOOLEAN DEFAULT FALSE
);
CREATE INDEX idx_analysis_user_created ON analysis_history(user_id, created_at DESC);

-- 收藏协议表
CREATE TABLE favorites (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    protocol_name VARCHAR(255) NOT NULL,
    protocol_type VARCHAR(50), -- 'lending', 'dex', 'derivatives'
    added_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, protocol_name)
);

-- 用户会话表（用于 WebSocket 连接管理）
CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id INTEGER REFERENCES users(id),
    token VARCHAR(512) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 实时监控表（用户关注的协议）
CREATE TABLE watchlist (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    protocol_name VARCHAR(255) NOT NULL,
    alert_conditions JSONB, -- {'tvl_change': 10, 'apy_threshold': 5}
    last_notified TIMESTAMP,
    UNIQUE(user_id, protocol_name)
);

-- 分析任务队列表（可选，如果使用 Celery）
CREATE TABLE analysis_tasks (
    id UUID PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    status VARCHAR(50), -- 'pending', 'running', 'completed', 'failed'
    query_params JSONB,
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

### API 接口设计

#### 认证接口

```http
POST /api/v1/auth/telegram
# 请求体：Telegram WebApp initData
# 响应：JWT token

GET /api/v1/auth/me
# 响应：当前用户信息
```

#### 协议数据接口

```http
GET /api/v1/protocols
# 查询参数：type, chain, sort_by
# 响应：协议列表（支持分页）

GET /api/v1/protocols/{protocol_name}
# 响应：协议详细信息（TVL, APY, 风险评分等）

GET /api/v1/protocols/{protocol_name}/history?days=30
# 响应：历史数据（TVL 趋势、APY 变化）
```

#### 分析接口

```http
POST /api/v1/analysis/analyze
# 请求体：{"protocol": "aave-v3", "date": "2025-12-10"}
# 响应：分析结果（支持缓存）

POST /api/v1/analysis/compare
# 请求体：{"protocols": ["aave-v3", "compound-v3"]}
# 响应：对比报告

POST /api/v1/analysis/recommend
# 请求体：{"amount": 10000, "risk": "low", "apy_target": 5}
# 响应：推荐协议列表

GET /api/v1/analysis/history?limit=20&offset=0
# 响应：用户历史分析记录
```

#### 可视化接口

```http
GET /api/v1/charts/tvl-trend?protocol=aave-v3&days=30
# 响应：ECharts 配置对象（JSON）

GET /api/v1/charts/apy-comparison?protocols=aave-v3,compound-v3
# 响应：ECharts 配置对象
```

#### 用户收藏接口

```http
GET /api/v1/favorites
# 响应：收藏的协议列表

POST /api/v1/favorites
# 请求体：{"protocol": "aave-v3"}

DELETE /api/v1/favorites/{protocol_name}
```

#### 监控接口

```http
GET /api/v1/watchlist
# 响应：监控列表

POST /api/v1/watchlist
# 请求体：{"protocol": "aave-v3", "alert_conditions": {...}}

WebSocket /api/v1/ws/realtime
# 实时数据推送：TVL 变化、APY 更新、Agent 分析进度
```

---

## 前端页面结构

### 1. 仪表盘页面（Dashboard）

**路由**：`/dashboard`

**功能模块**：
- **顶部导航**：
  - 用户头像（Telegram 头像）
  - 总资产概览（可选：连接钱包后显示）
  - 消息通知图标
- **快捷操作卡片**：
  - 分析协议（跳转到分析页面）
  - 协议对比
  - 投资推荐
  - 风险评估
- **实时行情**：
  - Top 10 协议 TVL 排行
  - 24小时 TVL 变化率
  - APY 热门榜
- **我的收藏**：
  - 收藏的协议列表
  - 一键快速分析
- **最近分析**：
  - 最近 5 条分析记录
  - 点击查看详情

**技术实现**：
- 使用 React Query 缓存数据
- 下拉刷新（react-spring）
- 骨架屏加载（Skeleton）

---

### 2. 分析页面（Analysis）

**路由**：`/analysis`

**功能模块**：
- **协议选择器**：
  - 搜索框（支持模糊匹配）
  - 协议分类筛选（Lending, DEX, Derivatives）
  - 链筛选（Ethereum, Arbitrum, etc.）
- **Agent 对话区**：
  - 聊天气泡界面（类似 ChatGPT）
  - 显示 Agent 分析步骤
  - 实时进度条
  - 支持打断/重新分析
- **可视化报告区**：
  - 标签页切换：
    - **概览**：关键指标卡片（TVL, APY, 风险评分）
    - **图表**：TVL 趋势、收益分解、风险雷达图
    - **详细报告**：6 个 Analyst 的完整报告（可折叠）
    - **最终决策**：Portfolio Manager 的投资建议
  - 导出按钮（PDF/Markdown）
- **底部操作栏**：
  - 收藏协议
  - 分享报告（生成短链接）
  - 添加到监控列表

**技术实现**：
- WebSocket 实时接收 Agent 消息
- ECharts 动态渲染图表
- Markdown 渲染器（react-markdown）
- 虚拟滚动（react-window）处理长报告

---

### 3. 历史记录页面（History）

**路由**：`/history`

**功能模块**：
- **筛选器**：
  - 时间范围选择（今天/7天/30天/自定义）
  - 查询类型（分析/对比/推荐）
  - 协议名称搜索
- **记录列表**：
  - 时间线展示
  - 每条记录显示：
    - 协议名称和类型
    - 分析时间
    - 关键指标摘要（TVL, APY, 决策）
    - 缓存标识
  - 下拉加载更多（无限滚动）
- **详情抽屉**：
  - 点击记录展开完整报告
  - 支持重新运行分析（对比新旧结果）

**技术实现**：
- React Query 分页缓存
- 虚拟列表（react-virtual）
- 抽屉组件（Ant Design Drawer）

---

### 4. 实时监控页面（Watchlist）

**路由**：`/watchlist`

**功能模块**：
- **监控列表**：
  - 协议卡片（显示实时 TVL/APY）
  - 变化率高亮（红涨绿跌）
  - 警报状态指示
- **添加监控**：
  - 协议选择器
  - 警报条件设置：
    - TVL 变化阈值（±10%）
    - APY 阈值（低于/高于 X%）
    - 风险评分变化
- **警报历史**：
  - 触发过的警报记录
  - 通知方式：Telegram Bot 消息

**技术实现**：
- WebSocket 实时数据流
- 数字滚动动画（react-countup）
- 通知系统（Telegram WebApp API）

---

### 5. 设置页面（Settings）

**路由**：`/settings`

**功能模块**：
- **账户信息**：
  - Telegram 用户名
  - 注册时间
  - 使用统计（总分析次数、收藏数）
- **偏好设置**：
  - 默认风险偏好（低/中/高）
  - 默认投资金额
  - 通知开关
- **数据管理**：
  - 导出所有分析记录（JSON/CSV）
  - 清除缓存
  - 删除账户
- **关于**：
  - 版本号
  - 更新日志
  - 帮助文档链接

---

## 实时数据更新机制

### 方案 1：WebSocket（推荐）

**优点**：
- 真正的双向通信
- 低延迟
- 适合 Agent 实时消息

**实现**：
```javascript
// 前端
const socket = io('wss://api.example.com', {
  auth: { token: jwtToken }
});

socket.on('analysis_progress', (data) => {
  // 更新进度条
  setProgress(data.step, data.total);
});

socket.on('data_update', (data) => {
  // 更新 TVL/APY 实时数据
  updateProtocolData(data.protocol, data.metrics);
});
```

```python
# 后端
@app.websocket("/api/v1/ws/realtime")
async def websocket_endpoint(websocket: WebSocket, token: str):
    await websocket.accept()
    user = verify_token(token)

    # 订阅用户监控的协议
    async for message in redis_subscriber(user.watchlist):
        await websocket.send_json(message)
```

---

### 方案 2：Server-Sent Events（SSE）

**优点**：
- 实现简单
- 自动重连
- 适合单向数据推送

**适用场景**：
- 实时数据监控（只需服务端推送）
- Agent 分析进度（不需要客户端发消息）

---

## 用户认证流程

### Telegram Mini App 身份验证

```javascript
// 前端：获取 Telegram WebApp 初始化数据
import { WebApp } from '@twa-dev/sdk';

const initData = WebApp.initData;
const initDataUnsafe = WebApp.initDataUnsafe;

// 发送到后端验证
const response = await fetch('/api/v1/auth/telegram', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ initData })
});

const { token } = await response.json();
localStorage.setItem('jwt_token', token);
```

```python
# 后端：验证 Telegram 数据
from hashlib import sha256
import hmac

def verify_telegram_auth(init_data: str, bot_token: str) -> dict:
    """验证 Telegram WebApp initData"""
    # 解析 URL 参数
    params = dict(parse_qsl(init_data))
    hash_value = params.pop('hash', None)

    # 构造数据字符串
    data_check_string = '\n'.join([f"{k}={v}" for k, v in sorted(params.items())])

    # 计算 HMAC-SHA256
    secret_key = sha256(bot_token.encode()).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), sha256).hexdigest()

    if calculated_hash != hash_value:
        raise HTTPException(401, "Invalid authentication")

    return json.loads(params['user'])

@app.post("/api/v1/auth/telegram")
async def telegram_auth(request: TelegramAuthRequest):
    user_data = verify_telegram_auth(request.initData, BOT_TOKEN)

    # 创建或更新用户
    user = await get_or_create_user(user_data['id'])

    # 生成 JWT
    token = create_jwt_token(user.id)
    return {"token": token}
```

---

## 性能优化策略

### 1. 数据缓存

**多层缓存架构**：
```
前端缓存（React Query）
    ↓ 5秒 TTL
Redis 缓存（热数据）
    ↓ 5分钟 TTL
PostgreSQL（持久化）
    ↓
DeFi 数据源
```

**缓存键设计**：
- `protocol:{name}:summary` - 协议摘要（5分钟）
- `protocol:{name}:history:{days}` - 历史数据（1小时）
- `analysis:{protocol}:{date}:{hash}` - 分析结果（30分钟）

---

### 2. 数据库查询优化

**索引策略**：
```sql
-- 用户查询索引
CREATE INDEX idx_user_telegram ON users(telegram_id);

-- 分析历史查询索引
CREATE INDEX idx_analysis_user_created ON analysis_history(user_id, created_at DESC);
CREATE INDEX idx_analysis_protocol ON analysis_history(protocol_name);

-- 收藏查询索引
CREATE INDEX idx_favorites_user ON favorites(user_id);
```

**查询优化**：
- 使用 `LIMIT` + `OFFSET` 分页
- 避免 `SELECT *`，只查询需要的字段
- 使用 `EXISTS` 替代 `COUNT(*)`

---

### 3. API 响应优化

**压缩**：
- 启用 Gzip/Brotli 压缩
- FastAPI 自动支持

**分页**：
```python
from fastapi import Query

@app.get("/api/v1/protocols")
async def get_protocols(
    limit: int = Query(20, le=100),
    offset: int = Query(0)
):
    protocols = await db.query(Protocol).limit(limit).offset(offset).all()
    total = await db.query(Protocol).count()
    return {
        "data": protocols,
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset
        }
    }
```

**字段裁剪**（GraphQL 风格）：
```python
@app.get("/api/v1/protocols/{name}")
async def get_protocol(
    name: str,
    fields: str = Query("name,tvl,apy")  # 客户端指定需要的字段
):
    protocol = await db.get_protocol(name)
    return {k: v for k, v in protocol.dict().items() if k in fields.split(',')}
```

---

### 4. 前端性能优化

**代码分割**：
```javascript
// 路由懒加载
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Analysis = lazy(() => import('./pages/Analysis'));

<Route path="/dashboard" element={<Suspense><Dashboard /></Suspense>} />
```

**虚拟滚动**：
```javascript
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={historyList.length}
  itemSize={80}
>
  {({ index, style }) => (
    <div style={style}>{historyList[index]}</div>
  )}
</FixedSizeList>
```

**图片优化**：
- 协议 Logo 使用 WebP 格式
- CDN 加速（Cloudflare）
- 懒加载（Intersection Observer）

---

## 部署架构

### 推荐部署方案（云原生）

```
                   Cloudflare CDN
                          │
                          ↓
                   Nginx (反向代理)
                          │
         ┌────────────────┼────────────────┐
         ↓                ↓                 ↓
    Frontend         Backend           WebSocket
    (Vercel)       (FastAPI)           (FastAPI)
                    │      │
         ┌──────────┘      └──────────┐
         ↓                             ↓
    PostgreSQL                      Redis
  (Supabase)                   (Redis Cloud)
```

**服务选择**：
- **前端托管**：Vercel 或 Netlify（自动部署，CDN 加速）
- **后端托管**：Railway 或 Render（支持 Python，内置 PostgreSQL）
- **数据库**：Supabase（免费 500MB，自动备份）
- **Redis**：Redis Cloud（免费 30MB）
- **监控**：Sentry（错误追踪）+ Plausible（用户分析）

---

## 安全考虑

### 1. API 安全

**速率限制**：
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.get("/api/v1/protocols")
@limiter.limit("100/minute")  # 每分钟 100 次请求
async def get_protocols():
    ...
```

**CORS 配置**：
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-miniapp-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### 2. 数据安全

**敏感数据加密**：
- JWT Token 使用 RS256 签名
- 数据库字段加密（如用户钱包地址）

**SQL 注入防护**：
- 使用 SQLAlchemy ORM（参数化查询）
- 避免拼接 SQL 字符串

**XSS 防护**：
- 前端使用 DOMPurify 清理用户输入
- Markdown 渲染使用 sanitize 选项

---

## 成本估算

### 开发阶段（免费方案）

| 服务 | 提供商 | 免费额度 | 限制 |
|------|--------|---------|------|
| 前端托管 | Vercel | 100GB/月流量 | 无域名限制 |
| 后端托管 | **Render** | 免费实例 | 休眠机制（请求延迟），不支持持久化磁盘 |
| 后端托管(备选) | Railway | $5 试用金 | 试用结束后需付费（起步约 $5/月） |
| PostgreSQL | Supabase | 500MB 存储 | 2 个项目 |
| Redis | Redis Cloud | 30MB | 30 并发连接 |
| **总成本** | - | **$0/月** | 适合 MVP 测试 |

---

### 生产阶段（扩展方案）

| 服务 | 提供商 | 成本 | 配置 |
|------|--------|------|------|
| 后端托管 | Railway / Render | ~$10-20/月 | 2GB 内存，保证高可用 |
| PostgreSQL | Supabase Pro | $25/月 | 8GB 存储，100GB 流量 |
| Redis | Redis Cloud | $7/月 | 250MB，100 并发 |
| 监控 | Sentry | $26/月 | 50K 错误/月 |
| **总成本** | - | **$78/月** | 支持 1000+ 用户 |

---

## 风险评估

| 风险 | 影响 | 概率 | 缓解策略 |
|------|------|------|---------|
| Telegram API 限制 | 高 | 中 | 实现速率限制，使用 Bot API 降级方案 |
| DeFi 数据源不稳定 | 中 | 高 | 多数据源回退，本地缓存 |
| 并发分析请求过多 | 高 | 中 | 任务队列（Celery），限制并发数 |
| 数据库性能瓶颈 | 中 | 低 | 读写分离，索引优化 |
| 前端加载慢 | 中 | 中 | 代码分割，SSR（可选） |
| 安全漏洞 | 高 | 低 | 定期安全审计，依赖更新 |

---

## 后续扩展方向

### Phase 4+（未来计划）

1. **钱包连接**：
   - 集成 WalletConnect
   - 显示用户真实持仓
   - 一键执行 Agent 建议

2. **社交功能**：
   - 分享分析报告到 Telegram 群组
   - 协议讨论区（类似股票论坛）
   - 关注其他用户的投资组合

3. **高级分析**：
   - 回测功能（如果采纳 Agent 建议，历史收益如何）
   - 组合优化（MPT 理论）
   - 风险压力测试

4. **移动 App**：
   - 独立 iOS/Android App（React Native）
   - 推送通知
   - 离线模式

---

## 总结

本架构设计将现有的 DeFi Agent 从纯 Bot 交互升级为完整的 Web 应用，同时保留 Agent 的核心能力。通过 Telegram Mini App 平台，用户可以享受到：

- **更好的用户体验**：可视化界面替代纯文本
- **完整的数据管理**：历史记录、收藏、监控
- **实时数据更新**：WebSocket 推送
- **可扩展性**：清晰的 API 设计，易于后续功能迭代

**技术栈优势**：
- 前后端分离，独立部署
- 与现有 Python 代码无缝集成
- 成本低（免费方案可支持 MVP）
- 技术栈主流，易于招募开发者

**关键挑战**：
- 前端开发工作量大（3-4周）
- 需要学习 Telegram Mini App SDK
- 数据库设计需要考虑未来扩展
