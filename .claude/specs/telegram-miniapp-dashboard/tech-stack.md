# 技术栈选型与对比

## 前端框架选择

### React vs Vue.js vs Svelte

| 维度 | React | Vue.js | Svelte |
|------|-------|--------|--------|
| **学习曲线** | 中等（JSX + Hooks） | 较低（模板语法） | 较低（编译时框架） |
| **生态系统** | ⭐⭐⭐⭐⭐ 最丰富 | ⭐⭐⭐⭐ 丰富 | ⭐⭐⭐ 中等 |
| **TypeScript 支持** | ⭐⭐⭐⭐⭐ 原生支持 | ⭐⭐⭐⭐ 良好支持 | ⭐⭐⭐⭐ 良好支持 |
| **Telegram 示例** | ✅ 官方示例 | ✅ 社区示例 | ❌ 无官方示例 |
| **打包体积** | ~42KB (gzip) | ~33KB (gzip) | ~7KB (gzip) |
| **性能** | ⭐⭐⭐⭐ 良好 | ⭐⭐⭐⭐ 良好 | ⭐⭐⭐⭐⭐ 优秀 |
| **移动端优化** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **开发者招募** | ⭐⭐⭐⭐⭐ 容易 | ⭐⭐⭐⭐ 较易 | ⭐⭐⭐ 中等 |

**推荐**：**React + Vite**
- Vite 替代 CRA，启动与 HMR 更快，TypeScript 体验更好
- Telegram 官方有 React 示例项目
- 生态系统最成熟（图表库、UI 库丰富）
- 如果团队更熟悉 Vue，可选 Vue.js 作为备选

---

## UI 组件库选择

### Ant Design Mobile vs Chakra UI vs Material-UI

| 维度 | Ant Design Mobile | Chakra UI | Material-UI |
|------|-------------------|-----------|-------------|
| **移动端优化** | ⭐⭐⭐⭐⭐ 专为移动端设计 | ⭐⭐⭐ 响应式 | ⭐⭐⭐ 响应式 |
| **组件丰富度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **定制化** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **股票样式** | ⭐⭐⭐ 中性 | ⭐⭐⭐ 现代风格 | ⭐⭐⭐ 扁平风格 |
| **打包体积** | ~150KB (gzip) | ~120KB (gzip) | ~300KB (gzip) |
| **中文文档** | ✅ 完善 | ❌ 英文为主 | ✅ 较完善 |
| **TypeScript** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**推荐**：**Ant Design Mobile**
- 专为移动端设计，触摸优化
- 组件丰富（List, Tabs, Drawer, Picker 等）
- 中文文档完善
- 支持主题定制（适配 Telegram Dark/Light 模式）

**备选**：如果需要更强的定制化，选择 Chakra UI

---

## 图表库选择

### ECharts vs Recharts vs Chart.js

| 维度 | ECharts | Recharts | Chart.js |
|------|---------|----------|----------|
| **功能丰富度** | ⭐⭐⭐⭐⭐ 最丰富 | ⭐⭐⭐⭐ 中等 | ⭐⭐⭐ 基础 |
| **性能** | ⭐⭐⭐⭐⭐ 优秀（Canvas） | ⭐⭐⭐ 中等（SVG） | ⭐⭐⭐⭐ 良好（Canvas） |
| **移动端优化** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **股票图表** | ✅ K线图、指标图 | ⚠️ 需自定义 | ⚠️ 需自定义 |
| **交互性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **打包体积** | ~300KB (gzip) | ~50KB (gzip) | ~80KB (gzip) |
| **React 集成** | echarts-for-react | ✅ 原生 React | react-chartjs-2 |

**推荐**：**ECharts**
- 功能最丰富（K线图、雷达图、热力图等）
- 性能优秀（支持大数据量）
- 官方支持 React（echarts-for-react）
- 适合股票/金融场景

**备选**：如果只需简单图表且注重体积，选择 Recharts

---

## 状态管理选择

### Zustand vs Redux Toolkit vs Context API

| 维度 | Zustand | Redux Toolkit | Context API |
|------|---------|--------------|-------------|
| **学习曲线** | ⭐⭐⭐⭐⭐ 极简 | ⭐⭐⭐ 中等 | ⭐⭐⭐⭐ 简单 |
| **样板代码** | ⭐⭐⭐⭐⭐ 极少 | ⭐⭐⭐ 较少 | ⭐⭐⭐⭐ 少 |
| **性能** | ⭐⭐⭐⭐⭐ 优秀 | ⭐⭐⭐⭐ 良好 | ⭐⭐⭐ 中等（重渲染） |
| **DevTools** | ✅ 支持 | ✅ 官方工具 | ❌ 无 |
| **异步支持** | ⭐⭐⭐⭐⭐ 简单 | ⭐⭐⭐⭐ RTK Query | ⚠️ 需自行处理 |
| **TypeScript** | ⭐⭐⭐⭐⭐ 完美 | ⭐⭐⭐⭐⭐ 完美 | ⭐⭐⭐⭐ 良好 |
| **打包体积** | ~2KB | ~12KB | 0KB（内置） |

**推荐**：**Zustand + React Query**
- Zustand 用于全局状态（用户信息、主题等）
- React Query 用于服务端状态（API 数据缓存）
- 两者结合，职责清晰

**示例**：
```typescript
// 全局状态（Zustand）
const useAuthStore = create((set) => ({
  user: null,
  setUser: (user) => set({ user }),
}));

// 服务端状态（React Query）
const { data: protocols } = useQuery({
  queryKey: ['protocols'],
  queryFn: fetchProtocols,
});
```

---

## 后端框架选择

### FastAPI vs Flask vs Django

| 维度 | FastAPI | Flask | Django |
|------|---------|-------|--------|
| **性能** | ⭐⭐⭐⭐⭐ 最快 | ⭐⭐⭐ 中等 | ⭐⭐⭐ 中等 |
| **异步支持** | ✅ 原生支持 | ⚠️ 需插件 | ⚠️ Django 4.1+ |
| **WebSocket** | ✅ 内置支持 | ⚠️ 需 Flask-SocketIO | ✅ Channels |
| **API 文档** | ⭐⭐⭐⭐⭐ 自动生成 | ⚠️ 需手动 | ⚠️ 需 DRF |
| **学习曲线** | ⭐⭐⭐⭐ 中等 | ⭐⭐⭐⭐⭐ 简单 | ⭐⭐⭐ 陡峭 |
| **与现有代码兼容** | ✅ Python 3.11+ | ✅ Python 2.7+ | ✅ Python 3.8+ |
| **ORM** | SQLAlchemy | SQLAlchemy | Django ORM |
| **适用场景** | API + 实时 | 简单 API | 全栈应用 |

**推荐**：**FastAPI**
- 性能最优（基于 Starlette + Pydantic）
- 原生异步支持（与现有 DeFi Agent 兼容）
- 自动生成 OpenAPI 文档（Swagger UI）
- WebSocket 内置支持

**与现有代码集成**：
```python
# 复用现有 DeFi Agent 代码
from defiagents.graph.trading_graph import TradingAgentsGraph
from gemini_config import GEMINI_CONFIG

@app.post("/api/v1/analysis/analyze")
async def analyze(request: AnalyzeRequest):
    agent = TradingAgentsGraph(config=GEMINI_CONFIG)
    # 在线程池中运行同步 Agent
    result = await asyncio.to_thread(agent.invoke, ...)
    return result
```

---

## 数据库选择

### PostgreSQL vs MySQL vs MongoDB

| 维度 | PostgreSQL | MySQL | MongoDB |
|------|------------|-------|---------|
| **JSON 支持** | ⭐⭐⭐⭐⭐ JSONB | ⭐⭐⭐ JSON | ⭐⭐⭐⭐⭐ 原生 |
| **事务支持** | ⭐⭐⭐⭐⭐ 完整 ACID | ⭐⭐⭐⭐ InnoDB | ⭐⭐⭐⭐ 4.0+ |
| **全文搜索** | ⭐⭐⭐⭐ 内置 | ⭐⭐⭐ 内置 | ⭐⭐⭐⭐ Atlas |
| **扩展性** | ⭐⭐⭐⭐ 分片 | ⭐⭐⭐⭐ 分片 | ⭐⭐⭐⭐⭐ 自动分片 |
| **免费托管** | ✅ Supabase | ✅ PlanetScale | ✅ MongoDB Atlas |
| **ORM 支持** | ⭐⭐⭐⭐⭐ SQLAlchemy | ⭐⭐⭐⭐⭐ SQLAlchemy | ⭐⭐⭐⭐ Motor |
| **适用场景** | 关系数据 + JSON | 关系数据 | 文档数据 |

**推荐**：**PostgreSQL**
- JSONB 类型存储分析结果（灵活）
- 强大的索引支持（GIN 索引）
- Supabase 免费托管（500MB）
- 与 SQLAlchemy 集成完美

**数据模型示例**：
```python
# 分析结果存储为 JSONB
class Analysis(Base):
    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True)
    protocol_name = Column(String)
    result = Column(JSONB)  # 完整的 Agent 输出
    created_at = Column(DateTime)

# 查询示例
session.query(Analysis).filter(
    Analysis.result['final_decision'].astext.contains('INVEST')
).all()
```

---

## 缓存选择

### Redis vs Memcached vs In-Memory

| 维度 | Redis | Memcached | In-Memory |
|------|-------|-----------|-----------|
| **数据结构** | ⭐⭐⭐⭐⭐ 丰富 | ⭐⭐ K-V | ⭐⭐⭐ Dict |
| **持久化** | ✅ AOF/RDB | ❌ 无 | ❌ 无 |
| **Pub/Sub** | ✅ 支持 | ❌ 无 | ❌ 无 |
| **性能** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **免费托管** | ✅ Redis Cloud | ✅ 部分 | N/A |
| **分布式** | ✅ 集群 | ✅ 一致性哈希 | ❌ 单机 |
| **适用场景** | 复杂缓存 + Pub/Sub | 简单缓存 | 开发测试 |

**推荐**：**Redis**
- 支持 Pub/Sub（WebSocket 消息广播）
- 数据结构丰富（List, Set, Sorted Set）
- 现有项目已使用 Redis

**用途**：
1. 分析结果缓存（String）
2. WebSocket 消息广播（Pub/Sub）
3. 会话存储（Hash）
4. 热门协议榜单（Sorted Set）

---

## 实时通信选择

### WebSocket vs SSE vs Long Polling

| 维度 | WebSocket | SSE | Long Polling |
|------|-----------|-----|-------------|
| **双向通信** | ✅ 是 | ❌ 单向（服务端→客户端） | ❌ 单向 |
| **性能** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **实现复杂度** | ⭐⭐⭐ 中等 | ⭐⭐⭐⭐ 简单 | ⭐⭐⭐⭐⭐ 极简 |
| **断线重连** | ⚠️ 需手动实现 | ✅ 自动重连 | ✅ 自动重连 |
| **兼容性** | ⭐⭐⭐⭐ 现代浏览器 | ⭐⭐⭐⭐⭐ 更广泛 | ⭐⭐⭐⭐⭐ 最广泛 |
| **适用场景** | 双向实时 | 单向推送 | 兼容老浏览器 |

**推荐**：**WebSocket**
- Agent 分析需要实时进度更新（双向）
- 监控列表需要实时数据推送
- FastAPI 内置支持

**降级方案**：如果 WebSocket 连接失败，降级到 Long Polling

---

## 部署方案选择

### Vercel vs Netlify vs CloudFlare Pages（前端）

| 维度 | Vercel | Netlify | CloudFlare Pages |
|------|--------|---------|------------------|
| **部署速度** | ⭐⭐⭐⭐⭐ 极快 | ⭐⭐⭐⭐ 快 | ⭐⭐⭐⭐⭐ 极快 |
| **构建时间** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **免费额度** | 100GB/月 | 100GB/月 | 无限流量 |
| **自定义域名** | ✅ 免费 | ✅ 免费 | ✅ 免费 |
| **SSL 证书** | ✅ 自动 | ✅ 自动 | ✅ 自动 |
| **边缘函数** | ✅ 支持 | ✅ 支持 | ✅ Workers |
| **GitHub 集成** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

**推荐**：**Vercel**
- Next.js 开发商（React 生态最优）
- 部署速度极快（CDN 全球分发）
- 免费额度充足

---

### Railway vs Render vs Fly.io（后端）

| 维度 | Railway | Render | Fly.io |
|------|---------|--------|--------|
| **PostgreSQL** | ✅ 内置 | ✅ 内置 | ⚠️ 需单独配置 |
| **Redis** | ✅ 内置 | ✅ 插件 | ⚠️ 需单独配置 |
| **部署速度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **免费额度** | $5/月 | 750小时/月 | 3 个免费实例 |
| **自动扩容** | ⚠️ 手动 | ✅ 自动 | ✅ 自动 |
| **日志查看** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **GitHub 集成** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

**推荐**：**Railway**
- 最简单的部署体验（连接 GitHub 即可）
- 内置 PostgreSQL + Redis（无需额外配置）
- 日志查看和调试友好

---

## 监控和日志选择

### Sentry vs LogRocket vs Bugsnag（错误追踪）

| 维度 | Sentry | LogRocket | Bugsnag |
|------|--------|-----------|---------|
| **错误追踪** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **会话回放** | ⚠️ 付费功能 | ✅ 核心功能 | ❌ 无 |
| **性能监控** | ✅ 支持 | ✅ 支持 | ⚠️ 基础 |
| **免费额度** | 5K errors/月 | 1K sessions/月 | 7.5K events/月 |
| **React 支持** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **价格** | $26/月起 | $99/月起 | $59/月起 |

**推荐**：**Sentry**
- 开源且免费额度充足
- React 集成完善（@sentry/react）
- 错误追踪功能最强大

---

### Plausible vs Google Analytics vs Mixpanel（用户分析）

| 维度 | Plausible | Google Analytics | Mixpanel |
|------|-----------|------------------|----------|
| **隐私友好** | ⭐⭐⭐⭐⭐ 不跟踪用户 | ⭐⭐ 跟踪用户 | ⭐⭐⭐ 可配置 |
| **页面加载影响** | ⭐⭐⭐⭐⭐ <1KB | ⭐⭐⭐ ~17KB | ⭐⭐⭐⭐ ~10KB |
| **实时数据** | ✅ 是 | ⚠️ 延迟 | ✅ 是 |
| **事件追踪** | ⭐⭐⭐ 基础 | ⭐⭐⭐⭐ 丰富 | ⭐⭐⭐⭐⭐ 最强 |
| **免费额度** | ❌ 无免费版 | ✅ 完全免费 | ✅ 20M events/月 |
| **价格** | $9/月起 | 免费 | $25/月起 |

**推荐**：**Plausible**（如果注重隐私）或 **Google Analytics**（如果需要完全免费）

---

## 最终推荐技术栈

### 前端

```javascript
// 核心框架
- React 18 + TypeScript
- React Router v6

// 状态管理
- Zustand（全局状态）
- React Query（服务端状态）

// UI 库
- Ant Design Mobile（组件库）
- ECharts（图表）
- Tailwind CSS（样式）

// 实时通信
- Socket.IO Client

// 工具库
- Axios（HTTP 请求）
- date-fns（日期处理）
- react-markdown（Markdown 渲染）
- DOMPurify（XSS 防护）
```

### 后端

```python
# Web 框架
- FastAPI 0.104+
- Uvicorn（ASGI 服务器）

# 数据库
- PostgreSQL 16（主数据库）
- Redis 7（缓存 + Pub/Sub）
- SQLAlchemy 2.0（ORM）
- Alembic（迁移）

# 异步任务
- Celery（后台任务）
- Redis（消息队列）

# 认证
- PyJWT（JWT Token）

# 工具库
- Pydantic（数据验证）
- python-multipart（文件上传）
- httpx（异步 HTTP 客户端）
```

### 部署

```yaml
# 前端
- 托管：Vercel
- CDN：Cloudflare
- 监控：Sentry + Plausible

# 后端
- 托管：Railway
- 数据库：Railway PostgreSQL
- 缓存：Redis Cloud

# CI/CD
- GitHub Actions
```

---

## 成本估算（首年）

### 开发阶段（免费）

| 项目 | 成本 |
|------|------|
| Vercel（前端托管） | $0 |
| Railway（后端托管） | $0（$5 免费额度） |
| Supabase（PostgreSQL） | $0（500MB） |
| Redis Cloud | $0（30MB） |
| **总计** | **$0/月** |

### 生产阶段（1000+ 用户）

| 项目 | 成本 |
|------|------|
| Railway Pro | $20/月 |
| Supabase Pro | $25/月 |
| Redis Cloud | $7/月 |
| Sentry | $26/月 |
| **总计** | **$78/月** |

---

## 下一步

1. **确认技术栈**：根据团队熟悉度调整
2. **创建项目**：按照 dev-plan.md 开始 Phase 0
3. **搭建开发环境**：安装依赖和数据库
4. **开始原型验证**：Task 0.1（Telegram Mini App 技术验证）

有任何技术选型疑问随时询问！
