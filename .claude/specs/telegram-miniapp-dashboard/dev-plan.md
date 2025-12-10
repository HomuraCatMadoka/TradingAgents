# Telegram Mini App 仪表盘 - 开发计划

## 总体时间线

**总工期**：8-10 周（全职开发）

```
Phase 0: 架构设计与技术验证  [1-2周]  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 1: 后端 API 开发       [2-3周]  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 2: 前端 Mini App 开发  [3-4周]  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 3: 集成测试与部署      [1-2周]  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Phase 0: 架构设计与技术验证（1-2周）

**目标**：验证技术可行性，搭建基础开发环境

### Week 1: 技术调研与原型验证

#### 任务 0.1：Telegram Mini App 技术验证 ⏱️ 2-3天

**目标**：确认 Telegram WebApp SDK 功能和限制

**子任务**：
- [ ] 阅读官方文档：https://core.telegram.org/bots/webapps
- [ ] 创建测试 Bot（@BotFather）
- [ ] 搭建最小化 React 项目
  ```bash
  npm create vite@latest miniapp-test -- --template react-ts
  cd miniapp-test && npm install
  npm install @twa-dev/sdk
  ```
- [ ] 实现功能验证：
  - [ ] 用户身份验证（initData 获取）
  - [ ] 主题适配（Dark/Light 模式）
  - [ ] 主按钮（MainButton）交互
  - [ ] 返回按钮（BackButton）
  - [ ] 打开外部链接（openLink）
- [ ] 测试部署：
  - [ ] 使用 ngrok 临时域名
  - [ ] 设置 Bot Menu Button（@BotFather）
  - [ ] 手机端测试（iOS/Android）

**验收标准**：
- ✅ 能从 Telegram 打开 WebApp
- ✅ 正确获取用户信息
- ✅ 主题切换正常
- ✅ 按钮交互无延迟

**风险**：
- Telegram WebApp 某些 API 可能在部分平台不可用
- 缓解：准备降级方案（使用 Bot 消息交互）

---

#### 任务 0.2：FastAPI + WebSocket 原型 ⏱️ 2-3天

**目标**：验证后端实时通信能力

**子任务**：
- [ ] 创建 FastAPI 项目结构
  ```bash
  mkdir backend && cd backend
  poetry init
  poetry add fastapi uvicorn sqlalchemy alembic redis
  ```
- [ ] 实现基础功能：
  - [ ] REST API 端点（GET /api/health）
  - [ ] WebSocket 端点（/api/ws）
  - [ ] Redis Pub/Sub 集成
  - [ ] JWT 认证中间件
- [ ] 前后端联调测试：
  - [ ] 前端连接 WebSocket
  - [ ] 测试实时消息推送
  - [ ] 测试断线重连
- [ ] 性能测试：
  - [ ] 使用 `websocket-bench` 测试并发连接数
  - [ ] 目标：支持 100+ 并发连接

**验收标准**：
- ✅ WebSocket 连接稳定
- ✅ 消息延迟 <500ms
- ✅ 断线自动重连

**关键文件**：
```
backend/
├── app/
│   ├── main.py          # FastAPI 应用入口
│   ├── api/
│   │   ├── websocket.py # WebSocket 路由
│   │   └── auth.py      # 认证逻辑
│   ├── models/          # 数据库模型
│   ├── schemas/         # Pydantic 模型
│   └── core/
│       ├── config.py    # 配置管理
│       └── redis.py     # Redis 客户端
├── tests/
└── requirements.txt
```

---

#### 任务 0.3：数据库设计与迁移脚本 ⏱️ 1-2天

**目标**：完成 PostgreSQL 表结构设计

**子任务**：
- [ ] 安装 PostgreSQL（本地开发）
  ```bash
  # macOS
  brew install postgresql@16
  brew services start postgresql@16
  ```
- [ ] 初始化 Alembic
  ```bash
  alembic init alembic
  alembic revision --autogenerate -m "Initial schema"
  alembic upgrade head
  ```
- [ ] 创建数据库表（参考 architecture.md）：
  - [ ] `users` - 用户表
  - [ ] `analysis_history` - 分析历史
  - [ ] `favorites` - 收藏协议
  - [ ] `sessions` - 用户会话
  - [ ] `watchlist` - 监控列表
- [ ] 编写种子数据脚本
  ```python
  # scripts/seed_data.py
  # 插入测试用户、示例分析记录
  ```
- [ ] 测试迁移：
  - [ ] 向前迁移（upgrade）
  - [ ] 回滚迁移（downgrade）
  - [ ] 重复执行验证幂等性

**验收标准**：
- ✅ 所有表创建成功
- ✅ 索引正确创建
- ✅ 外键约束有效

**关键文件**：
```
backend/
├── alembic/
│   ├── versions/
│   │   └── 001_initial_schema.py
│   └── env.py
├── app/
│   └── models/
│       ├── user.py
│       ├── analysis.py
│       └── favorite.py
└── scripts/
    └── seed_data.py
```

---

### Week 2: 项目脚手架与开发规范

#### 任务 0.4：前端项目脚手架 ⏱️ 1天

**目标**：搭建前端开发环境和工具链

**子任务**：
- [ ] 创建 React 项目（TypeScript + Vite）
  ```bash
  # 在 frontend 目录下
  npm create vite@latest . -- --template react-ts
  npm install
  ```
- [ ] 安装核心依赖：
  ```bash
  npm install @twa-dev/sdk react-router-dom zustand
  npm install @tanstack/react-query axios socket.io-client
  npm install antd-mobile echarts echarts-for-react
  npm install react-markdown dompurify
  npm install --save-dev @types/dompurify

  # 可选：样式方案
  npm install sass
  ```
- [ ] 配置开发工具：
  - [ ] ESLint + Prettier（代码格式化）
  - [ ] Husky + lint-staged（Git 钩子）
  - [ ] TypeScript 严格模式
  - [ ] 配置 `vite.config.ts`（端口、别名 `@` 等）
- [ ] 配置环境变量：
  ```env
  # .env
  VITE_API_URL=http://localhost:8000/api/v1
  VITE_WS_URL=ws://localhost:8000/api/v1/ws
  ```
  > Vite 通过 `import.meta.env` 读取环境变量，变量名需以 `VITE_` 开头。
- [ ] 创建项目结构：
  ```
  src/
  ├── components/      # 可复用组件
  ├── pages/           # 页面组件
  ├── hooks/           # 自定义 Hooks
  ├── services/        # API 调用
  ├── store/           # Zustand 状态管理
  ├── utils/           # 工具函数
  ├── types/           # TypeScript 类型定义
  └── App.tsx
  ```

**验收标准**：
- ✅ 项目启动无错误（npm run dev）
- ✅ 打包成功（npm run build）
- ✅ ESLint 检查通过

---

#### 任务 0.5：开发规范文档 ⏱️ 1天

**目标**：制定团队协作规范

**子任务**：
- [ ] 编写 `docs/CONTRIBUTING.md`：
  - Git 分支策略（Git Flow）
  - Commit 消息规范（Conventional Commits）
  - PR 审查流程
- [ ] 编写 `docs/API_DESIGN.md`：
  - RESTful API 命名规范
  - 错误响应格式
  - 分页、排序规范
- [ ] 编写 `docs/FRONTEND_GUIDE.md`：
  - 组件命名规范
  - 状态管理原则
  - 性能优化指南
- [ ] 创建 Issue 模板：
  - Bug 报告模板
  - 功能请求模板

**验收标准**：
- ✅ 文档覆盖核心开发流程
- ✅ 团队成员理解并同意规范

---

#### 任务 0.6：CI/CD 流水线搭建 ⏱️ 1-2天

**目标**：自动化测试和部署

**子任务**：
- [ ] 前端 CI（GitHub Actions）：
  ```yaml
  # .github/workflows/frontend-ci.yml
  name: Frontend CI
  on: [push, pull_request]
  jobs:
    test:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v3
        - uses: actions/setup-node@v3
        - run: npm ci
        - run: npm run lint
        - run: npm test
        - run: npm run build
  ```
- [ ] 后端 CI（GitHub Actions）：
  ```yaml
  # .github/workflows/backend-ci.yml
  name: Backend CI
  on: [push, pull_request]
  jobs:
    test:
      runs-on: ubuntu-latest
      services:
        postgres:
          image: postgres:16
          env:
            POSTGRES_PASSWORD: testpass
      steps:
        - uses: actions/checkout@v3
        - uses: actions/setup-python@v4
        - run: pip install -r requirements.txt
        - run: pytest --cov=app tests/
  ```
- [ ] 配置自动部署：
  - [ ] 前端：Vercel（连接 GitHub 仓库）
  - [ ] 后端：Railway（连接 GitHub 仓库）
- [ ] 配置环境隔离：
  - `main` 分支 → 生产环境
  - `develop` 分支 → 测试环境

**验收标准**：
- ✅ Push 代码自动运行测试
- ✅ 合并到 main 自动部署

---

## Phase 1: 后端 API 开发（2-3周）

**目标**：完成所有后端接口和业务逻辑

### Week 3-4: 核心 API 开发

#### 任务 1.1：认证系统 ⏱️ 2-3天

**目标**：实现 Telegram 身份验证和 JWT

**子任务**：
- [ ] 实现 Telegram WebApp 数据验证：
  ```python
  # app/core/telegram_auth.py
  def verify_telegram_webapp_data(init_data: str, bot_token: str) -> dict:
      """验证 Telegram initData 的有效性"""
      # 1. 解析 URL 参数
      # 2. 验证 hash 签名
      # 3. 检查过期时间（auth_date）
      # 4. 返回用户信息
  ```
- [ ] 实现 JWT 生成和验证：
  ```python
  # app/core/jwt.py
  def create_access_token(user_id: int, expires_delta: timedelta):
      """生成 JWT Token"""

  def verify_token(token: str) -> int:
      """验证 Token 并返回 user_id"""
  ```
- [ ] 创建认证中间件：
  ```python
  # app/api/deps.py
  async def get_current_user(token: str = Depends(oauth2_scheme)):
      """从 Token 获取当前用户"""
  ```
- [ ] 实现 API 端点：
  - `POST /api/v1/auth/telegram` - Telegram 登录
  - `GET /api/v1/auth/me` - 获取当前用户信息
  - `POST /api/v1/auth/refresh` - 刷新 Token
- [ ] 编写单元测试：
  - [ ] 测试 Telegram 数据验证（有效/无效/过期）
  - [ ] 测试 JWT 生成和验证
  - [ ] 测试认证中间件（有 Token/无 Token/过期 Token）

**验收标准**：
- ✅ 测试覆盖率 ≥90%
- ✅ 所有认证测试通过
- ✅ Postman 集合测试通过

**测试命令**：
```bash
pytest tests/test_auth.py -v --cov=app/core/telegram_auth --cov=app/core/jwt
```

---

#### 任务 1.2：用户管理 API ⏱️ 1-2天

**目标**：实现用户 CRUD 操作

**子任务**：
- [ ] 实现数据库操作层：
  ```python
  # app/crud/user.py
  async def get_user_by_telegram_id(telegram_id: int) -> User:
  async def create_user(user_data: dict) -> User:
  async def update_user_settings(user_id: int, settings: dict):
  ```
- [ ] 实现 API 端点：
  - `GET /api/v1/users/me` - 获取当前用户详细信息
  - `PATCH /api/v1/users/me/settings` - 更新用户设置
  - `DELETE /api/v1/users/me` - 删除账户（软删除）
  - `GET /api/v1/users/me/stats` - 获取用户统计信息
- [ ] 编写测试：
  - [ ] 测试用户创建和获取
  - [ ] 测试设置更新
  - [ ] 测试账户删除

**验收标准**：
- ✅ 所有端点返回正确状态码
- ✅ 测试覆盖率 ≥85%

---

#### 任务 1.3：协议数据 API ⏱️ 2-3天

**目标**：集成现有 DeFi 数据源，提供 API 接口

**子任务**：
- [ ] 重构现有数据源客户端：
  ```python
  # app/services/defi_data.py
  class DeFiDataService:
      async def get_protocol_summary(self, protocol: str) -> ProtocolSummary:
          """获取协议摘要（TVL, APY, 风险评分）"""

      async def get_protocol_history(self, protocol: str, days: int):
          """获取历史数据"""

      async def search_protocols(self, query: str, filters: dict):
          """搜索协议"""
  ```
- [ ] 实现缓存层：
  ```python
  # app/core/cache.py
  @cache(ttl=300)  # 5分钟缓存
  async def get_protocol_tvl(protocol: str):
      ...
  ```
- [ ] 实现 API 端点：
  - `GET /api/v1/protocols` - 协议列表（支持分页、筛选、排序）
  - `GET /api/v1/protocols/{name}` - 协议详情
  - `GET /api/v1/protocols/{name}/history` - 历史数据
  - `GET /api/v1/protocols/search?q=aave` - 搜索协议
- [ ] 集成现有工具函数：
  - 复用 `defiagents/dataflows/defi/` 中的代码
  - 添加异步支持（使用 `asyncio.to_thread`）
- [ ] 编写测试：
  - [ ] Mock DeFi Llama API 响应
  - [ ] 测试缓存命中/未命中
  - [ ] 测试错误处理（API 失败回退）

**验收标准**：
- ✅ 所有端点响应时间 <500ms（缓存命中）
- ✅ 缓存命中率 >80%（模拟测试）
- ✅ 测试覆盖率 ≥85%

---

#### 任务 1.4：分析历史 API ⏱️ 2天

**目标**：保存和查询分析记录

**子任务**：
- [ ] 实现数据库操作：
  ```python
  # app/crud/analysis.py
  async def create_analysis_record(
      user_id: int,
      protocol: str,
      query: str,
      result: dict
  ) -> Analysis:

  async def get_user_analysis_history(
      user_id: int,
      limit: int,
      offset: int,
      filters: dict
  ) -> List[Analysis]:
  ```
- [ ] 实现 API 端点：
  - `POST /api/v1/analysis/save` - 保存分析结果
  - `GET /api/v1/analysis/history` - 获取历史记录
  - `GET /api/v1/analysis/{id}` - 获取单条记录详情
  - `DELETE /api/v1/analysis/{id}` - 删除记录
- [ ] 实现搜索和筛选：
  - 按协议名称搜索
  - 按查询类型筛选（analyze/compare/recommend）
  - 按时间范围筛选
- [ ] 编写测试：
  - [ ] 测试记录创建和查询
  - [ ] 测试分页功能
  - [ ] 测试筛选和搜索

**验收标准**：
- ✅ 分页功能正常
- ✅ 搜索响应时间 <300ms
- ✅ 测试覆盖率 ≥85%

---

#### 任务 1.5：收藏和监控 API ⏱️ 1-2天

**目标**：实现协议收藏和监控列表

**子任务**：
- [ ] 实现收藏功能：
  - `GET /api/v1/favorites` - 获取收藏列表
  - `POST /api/v1/favorites` - 添加收藏
  - `DELETE /api/v1/favorites/{protocol}` - 取消收藏
- [ ] 实现监控列表：
  - `GET /api/v1/watchlist` - 获取监控列表
  - `POST /api/v1/watchlist` - 添加监控
  - `PATCH /api/v1/watchlist/{id}` - 更新警报条件
  - `DELETE /api/v1/watchlist/{id}` - 移除监控
- [ ] 实现警报逻辑（后台任务）：
  ```python
  # app/tasks/alerts.py
  @celery_app.task
  async def check_watchlist_alerts():
      """定期检查监控列表，触发警报"""
      # 1. 获取所有监控项
      # 2. 检查条件（TVL 变化、APY 阈值）
      # 3. 发送 Telegram 通知
  ```
- [ ] 编写测试：
  - [ ] 测试收藏增删查
  - [ ] 测试监控增删改查
  - [ ] 测试警报触发逻辑

**验收标准**：
- ✅ 收藏和监控操作响应时间 <200ms
- ✅ 警报触发准确（无误报）
- ✅ 测试覆盖率 ≥85%

---

### Week 5: Agent 集成与 WebSocket

#### 任务 1.6：Agent 分析 API ⏱️ 3-4天

**目标**：将现有 DeFi Agent 集成到 FastAPI

**子任务**：
- [ ] 创建 Agent 服务层：
  ```python
  # app/services/agent.py
  class DeFiAgentService:
      async def analyze_protocol(
          self,
          protocol: str,
          date: str,
          progress_callback: Callable
      ) -> dict:
          """异步执行分析，通过回调报告进度"""
          # 1. 在线程池中运行同步 Agent
          # 2. 定期调用 progress_callback 更新进度
          # 3. 返回完整结果
  ```
- [ ] 实现 API 端点：
  - `POST /api/v1/analysis/analyze` - 分析单个协议
  - `POST /api/v1/analysis/compare` - 对比协议
  - `POST /api/v1/analysis/recommend` - 推荐协议
  - `POST /api/v1/analysis/strategy` - 投资策略
- [ ] 集成缓存：
  - 复用现有 `bot/cache.py` 逻辑
  - 缓存键格式：`analysis:{protocol}:{date}:{hash}`
- [ ] 实现任务队列（Celery）：
  ```python
  # app/tasks/analysis.py
  @celery_app.task(bind=True)
  async def run_analysis_task(self, user_id: int, protocol: str):
      """后台分析任务"""
      # 1. 更新任务状态（running）
      # 2. 执行分析
      # 3. 保存结果到数据库
      # 4. 发送 WebSocket 通知
  ```
- [ ] 编写测试：
  - [ ] Mock Agent 调用
  - [ ] 测试缓存命中/未命中
  - [ ] 测试任务队列（使用 Celery mock）

**验收标准**：
- ✅ 分析接口成功调用现有 Agent
- ✅ 缓存正常工作
- ✅ 任务队列可靠运行
- ✅ 测试覆盖率 ≥80%

---

#### 任务 1.7：WebSocket 实时通信 ⏱️ 2-3天

**目标**：实现前后端实时通信

**子任务**：
- [ ] 实现 WebSocket 连接管理：
  ```python
  # app/api/websocket.py
  class ConnectionManager:
      def __init__(self):
          self.active_connections: Dict[int, WebSocket] = {}

      async def connect(self, user_id: int, websocket: WebSocket):
          """建立连接"""

      async def disconnect(self, user_id: int):
          """断开连接"""

      async def send_to_user(self, user_id: int, message: dict):
          """发送消息给指定用户"""

      async def broadcast(self, message: dict):
          """广播消息"""
  ```
- [ ] 实现消息类型：
  ```python
  # app/schemas/websocket.py
  class WebSocketMessage(BaseModel):
      type: str  # 'analysis_progress', 'data_update', 'alert'
      payload: dict

  class AnalysisProgress(BaseModel):
      step: str
      current: int
      total: int

  class DataUpdate(BaseModel):
      protocol: str
      metrics: dict
  ```
- [ ] 集成 Redis Pub/Sub：
  ```python
  # app/core/redis_pubsub.py
  async def publish_analysis_progress(user_id: int, progress: dict):
      """发布分析进度到 Redis"""
      await redis.publish(f"user:{user_id}:progress", json.dumps(progress))

  async def subscribe_user_channel(user_id: int, callback: Callable):
      """订阅用户频道，接收消息"""
      pubsub = redis.pubsub()
      await pubsub.subscribe(f"user:{user_id}:progress")
      async for message in pubsub.listen():
          await callback(message)
  ```
- [ ] 实现心跳机制（避免超时断开）：
  ```python
  async def websocket_heartbeat(websocket: WebSocket):
      while True:
          await asyncio.sleep(30)
          await websocket.send_json({"type": "ping"})
  ```
- [ ] 编写测试：
  - [ ] 测试连接建立和断开
  - [ ] 测试消息发送和接收
  - [ ] 测试多用户并发连接
  - [ ] 测试 Redis Pub/Sub

**验收标准**：
- ✅ 支持 100+ 并发连接
- ✅ 消息延迟 <500ms
- ✅ 断线自动重连（客户端实现）
- ✅ 测试覆盖率 ≥75%

---

#### 任务 1.8：可视化数据 API ⏱️ 1-2天

**目标**：为前端图表提供数据接口

**子任务**：
- [ ] 实现图表数据接口：
  - `GET /api/v1/charts/tvl-trend?protocol=aave&days=30`
    - 返回：`{ dates: [...], values: [...] }`
  - `GET /api/v1/charts/apy-comparison?protocols=aave,compound`
    - 返回：`{ protocols: [...], apys: [...] }`
  - `GET /api/v1/charts/risk-radar?protocol=aave`
    - 返回：`{ dimensions: [...], scores: [...] }`
- [ ] 复用现有可视化代码：
  ```python
  # app/services/visualization.py
  from defiagents.visualization.data_fetcher import DataFetcher

  async def get_tvl_trend_data(protocol: str, days: int):
      """获取 TVL 趋势数据（不生成图片，只返回数据）"""
      fetcher = DataFetcher()
      data = await asyncio.to_thread(fetcher.get_tvl_history, protocol, days)
      return {
          "dates": [d["date"] for d in data],
          "values": [d["tvl"] for d in data]
      }
  ```
- [ ] 编写测试：
  - [ ] Mock DeFi Llama API
  - [ ] 测试数据格式正确性

**验收标准**：
- ✅ 所有图表数据接口返回正确格式
- ✅ 响应时间 <1秒
- ✅ 测试覆盖率 ≥80%

---

## Phase 2: 前端 Mini App 开发（3-4周）

**目标**：完成所有前端页面和交互

### Week 6: 基础设施与通用组件

#### 任务 2.1：Telegram WebApp 集成 ⏱️ 1-2天

**目标**：集成 Telegram SDK 和路由系统

**子任务**：
- [ ] 初始化 Telegram WebApp：
  ```typescript
  // src/App.tsx
  import { WebApp } from '@twa-dev/sdk';

  function App() {
    useEffect(() => {
      WebApp.ready();
      WebApp.expand(); // 全屏显示
      WebApp.setHeaderColor('#1890ff'); // 设置顶部颜色

      // 监听主题变化
      WebApp.onEvent('themeChanged', () => {
        console.log('Theme changed:', WebApp.colorScheme);
      });
    }, []);

    return <RouterProvider router={router} />;
  }
  ```
- [ ] 配置路由系统（React Router v6）：
  ```typescript
  // src/router.tsx
  const router = createBrowserRouter([
    {
      path: '/',
      element: <Layout />,
      children: [
        { index: true, element: <Navigate to="/dashboard" /> },
        { path: 'dashboard', element: <Dashboard /> },
        { path: 'analysis', element: <Analysis /> },
        { path: 'history', element: <History /> },
        { path: 'watchlist', element: <Watchlist /> },
        { path: 'settings', element: <Settings /> },
      ],
    },
  ]);
  ```
- [ ] 创建布局组件：
  ```typescript
  // src/components/Layout.tsx
  import { TabBar } from 'antd-mobile';

  function Layout() {
    const navigate = useNavigate();
    const location = useLocation();

    const tabs = [
      { key: 'dashboard', icon: <DashboardOutlined />, title: '仪表盘' },
      { key: 'analysis', icon: <LineChartOutlined />, title: '分析' },
      { key: 'history', icon: <HistoryOutlined />, title: '历史' },
      { key: 'watchlist', icon: <EyeOutlined />, title: '监控' },
      { key: 'settings', icon: <SettingOutlined />, title: '设置' },
    ];

    return (
      <div className="layout">
        <main className="content">
          <Outlet />
        </main>
        <TabBar activeKey={activeTab} onChange={navigate}>
          {tabs.map(tab => (
            <TabBar.Item key={tab.key} icon={tab.icon} title={tab.title} />
          ))}
        </TabBar>
      </div>
    );
  }
  ```
- [ ] 实现主题适配：
  ```typescript
  // src/hooks/useTelegramTheme.ts
  export function useTelegramTheme() {
    const [theme, setTheme] = useState(WebApp.colorScheme);

    useEffect(() => {
      const handleThemeChange = () => {
        setTheme(WebApp.colorScheme);
      };
      WebApp.onEvent('themeChanged', handleThemeChange);
      return () => WebApp.offEvent('themeChanged', handleThemeChange);
    }, []);

    return theme; // 'light' | 'dark'
  }
  ```

**验收标准**：
- ✅ Telegram 中打开应用正常
- ✅ 路由切换流畅
- ✅ 主题切换立即生效
- ✅ 底部导航栏高亮正确

---

#### 任务 2.2：API 客户端封装 ⏱️ 1天

**目标**：封装 HTTP 和 WebSocket 客户端

**子任务**：
- [ ] 创建 Axios 实例：
  ```typescript
  // src/services/api.ts
  import axios from 'axios';

  const apiClient = axios.create({
    baseURL: import.meta.env.VITE_API_URL,
    timeout: 10000,
  });

  // 请求拦截器（添加 Token）
  apiClient.interceptors.request.use(config => {
    const token = localStorage.getItem('jwt_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  // 响应拦截器（处理错误）
  apiClient.interceptors.response.use(
    response => response.data,
    error => {
      if (error.response?.status === 401) {
        // Token 过期，跳转登录
        window.location.href = '/login';
      }
      return Promise.reject(error);
    }
  );
  ```
- [ ] 创建 API 方法：
  ```typescript
  // src/services/protocols.ts
  export const protocolsApi = {
    getList: (params: ProtocolListParams) =>
      apiClient.get('/protocols', { params }),

    getDetail: (name: string) =>
      apiClient.get(`/protocols/${name}`),

    getHistory: (name: string, days: number) =>
      apiClient.get(`/protocols/${name}/history`, { params: { days } }),
  };
  ```
- [ ] 创建 WebSocket 客户端：
  ```typescript
  // src/services/websocket.ts
  import { io, Socket } from 'socket.io-client';

  class WebSocketClient {
    private socket: Socket | null = null;

    connect(token: string) {
      this.socket = io(import.meta.env.VITE_WS_URL!, {
        auth: { token },
        transports: ['websocket'],
      });

      this.socket.on('connect', () => {
        console.log('WebSocket connected');
      });

      this.socket.on('disconnect', () => {
        console.log('WebSocket disconnected');
      });
    }

    on(event: string, callback: (data: any) => void) {
      this.socket?.on(event, callback);
    }

    emit(event: string, data: any) {
      this.socket?.emit(event, data);
    }

    disconnect() {
      this.socket?.disconnect();
    }
  }

  export const wsClient = new WebSocketClient();
  ```

**验收标准**：
- ✅ API 请求携带 Token
- ✅ 401 错误自动跳转登录
- ✅ WebSocket 连接成功
- ✅ 断线自动重连

---

#### 任务 2.3：状态管理与缓存 ⏱️ 1天

**目标**：使用 Zustand 和 React Query 管理状态

**子任务**：
- [ ] 创建全局状态 Store：
  ```typescript
  // src/store/useAuthStore.ts
  import { create } from 'zustand';

  interface AuthState {
    user: User | null;
    token: string | null;
    setAuth: (user: User, token: string) => void;
    logout: () => void;
  }

  export const useAuthStore = create<AuthState>((set) => ({
    user: null,
    token: null,
    setAuth: (user, token) => {
      localStorage.setItem('jwt_token', token);
      set({ user, token });
    },
    logout: () => {
      localStorage.removeItem('jwt_token');
      set({ user: null, token: null });
    },
  }));
  ```
- [ ] 配置 React Query：
  ```typescript
  // src/App.tsx
  import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 5 * 60 * 1000, // 5分钟内数据不过期
        cacheTime: 10 * 60 * 1000, // 缓存10分钟
        retry: 2,
      },
    },
  });

  function App() {
    return (
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
      </QueryClientProvider>
    );
  }
  ```
- [ ] 创建自定义 Hooks：
  ```typescript
  // src/hooks/useProtocols.ts
  import { useQuery } from '@tanstack/react-query';

  export function useProtocols(params: ProtocolListParams) {
    return useQuery({
      queryKey: ['protocols', params],
      queryFn: () => protocolsApi.getList(params),
    });
  }

  export function useProtocolDetail(name: string) {
    return useQuery({
      queryKey: ['protocol', name],
      queryFn: () => protocolsApi.getDetail(name),
      enabled: !!name, // 只有 name 存在时才请求
    });
  }
  ```

**验收标准**：
- ✅ 用户状态持久化到 localStorage
- ✅ React Query 缓存正常工作
- ✅ 数据自动刷新（过期后）

---

#### 任务 2.4：通用组件开发 ⏱️ 2-3天

**目标**：开发可复用的 UI 组件

**子任务**：
- [ ] 创建协议卡片组件：
  ```typescript
  // src/components/ProtocolCard.tsx
  interface ProtocolCardProps {
    name: string;
    logo: string;
    tvl: number;
    apy: number;
    riskScore: number;
    onAnalyze?: () => void;
    onFavorite?: () => void;
  }

  export function ProtocolCard(props: ProtocolCardProps) {
    return (
      <Card>
        <div className="header">
          <img src={props.logo} alt={props.name} />
          <h3>{props.name}</h3>
        </div>
        <div className="metrics">
          <div className="metric">
            <span className="label">TVL</span>
            <span className="value">${formatNumber(props.tvl)}</span>
          </div>
          <div className="metric">
            <span className="label">APY</span>
            <span className="value">{props.apy.toFixed(2)}%</span>
          </div>
          <div className="metric">
            <span className="label">风险</span>
            <RiskBadge score={props.riskScore} />
          </div>
        </div>
        <div className="actions">
          <Button onClick={props.onAnalyze}>分析</Button>
          <Button onClick={props.onFavorite}>收藏</Button>
        </div>
      </Card>
    );
  }
  ```
- [ ] 创建图表组件封装：
  ```typescript
  // src/components/charts/TvlTrendChart.tsx
  import ReactECharts from 'echarts-for-react';

  interface TvlTrendChartProps {
    data: { dates: string[]; values: number[] };
  }

  export function TvlTrendChart({ data }: TvlTrendChartProps) {
    const option = {
      xAxis: { type: 'category', data: data.dates },
      yAxis: { type: 'value' },
      series: [{ type: 'line', data: data.values }],
    };

    return <ReactECharts option={option} style={{ height: '300px' }} />;
  }
  ```
- [ ] 创建加载和错误状态组件：
  ```typescript
  // src/components/LoadingState.tsx
  export function LoadingState() {
    return <Skeleton animated />;
  }

  // src/components/ErrorState.tsx
  export function ErrorState({ message, onRetry }: ErrorStateProps) {
    return (
      <div className="error-state">
        <ErrorOutlined />
        <p>{message}</p>
        <Button onClick={onRetry}>重试</Button>
      </div>
    );
  }
  ```

**验收标准**：
- ✅ 组件可复用且参数化
- ✅ 样式适配 Dark/Light 主题
- ✅ 加载和错误状态友好

---

### Week 7-8: 核心页面开发

#### 任务 2.5：仪表盘页面 ⏱️ 2-3天

**目标**：完成仪表盘核心功能

**子任务**：
- [ ] 实现快捷操作卡片：
  ```typescript
  // src/pages/Dashboard/QuickActions.tsx
  const actions = [
    { title: '分析协议', icon: <BarChartOutlined />, path: '/analysis' },
    { title: '协议对比', icon: <SwapOutlined />, onClick: handleCompare },
    { title: '投资推荐', icon: <BulbOutlined />, onClick: handleRecommend },
  ];
  ```
- [ ] 实现实时行情模块：
  ```typescript
  // src/pages/Dashboard/MarketOverview.tsx
  export function MarketOverview() {
    const { data, isLoading } = useQuery({
      queryKey: ['market-overview'],
      queryFn: protocolsApi.getTopProtocols,
      refetchInterval: 30000, // 每30秒刷新
    });

    return (
      <div className="market-overview">
        <h3>实时行情</h3>
        {data?.map(protocol => (
          <ProtocolRow key={protocol.name} {...protocol} />
        ))}
      </div>
    );
  }
  ```
- [ ] 实现收藏列表：
  ```typescript
  // src/pages/Dashboard/Favorites.tsx
  export function Favorites() {
    const { data: favorites } = useQuery({
      queryKey: ['favorites'],
      queryFn: favoritesApi.getList,
    });

    return (
      <div className="favorites">
        <h3>我的收藏</h3>
        <Swiper>
          {favorites?.map(fav => (
            <SwiperSlide key={fav.protocol}>
              <ProtocolCard {...fav} />
            </SwiperSlide>
          ))}
        </Swiper>
      </div>
    );
  }
  ```
- [ ] 实现最近分析列表：
  ```typescript
  // src/pages/Dashboard/RecentAnalysis.tsx
  export function RecentAnalysis() {
    const { data } = useQuery({
      queryKey: ['recent-analysis'],
      queryFn: () => analysisApi.getHistory({ limit: 5 }),
    });

    return (
      <List>
        {data?.map(item => (
          <List.Item
            key={item.id}
            onClick={() => navigate(`/history/${item.id}`)}
          >
            <div className="analysis-item">
              <div className="protocol-name">{item.protocol}</div>
              <div className="timestamp">{formatTime(item.created_at)}</div>
              <div className="decision">{item.result.final_decision}</div>
            </div>
          </List.Item>
        ))}
      </List>
    );
  }
  ```

**验收标准**：
- ✅ 仪表盘加载时间 <2秒
- ✅ 下拉刷新正常
- ✅ 所有卡片可点击跳转

---

#### 任务 2.6：分析页面 ⏱️ 3-4天

**目标**：实现 Agent 分析功能和可视化报告

**子任务**：
- [ ] 实现协议选择器：
  ```typescript
  // src/pages/Analysis/ProtocolSelector.tsx
  export function ProtocolSelector({ onSelect }: ProtocolSelectorProps) {
    const [query, setQuery] = useState('');
    const { data: protocols } = useQuery({
      queryKey: ['protocols', query],
      queryFn: () => protocolsApi.search(query),
    });

    return (
      <div className="protocol-selector">
        <SearchBar
          placeholder="搜索协议名称..."
          value={query}
          onChange={setQuery}
        />
        <List>
          {protocols?.map(p => (
            <List.Item key={p.name} onClick={() => onSelect(p)}>
              {p.name}
            </List.Item>
          ))}
        </List>
      </div>
    );
  }
  ```
- [ ] 实现 Agent 对话区：
  ```typescript
  // src/pages/Analysis/AgentChat.tsx
  export function AgentChat({ protocol }: AgentChatProps) {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const { mutate: startAnalysis, isLoading } = useMutation({
      mutationFn: analysisApi.analyze,
      onSuccess: result => {
        setMessages(prev => [...prev, { role: 'assistant', content: result.final_decision }]);
      },
    });

    // 监听 WebSocket 实时进度
    useEffect(() => {
      wsClient.on('analysis_progress', (progress) => {
        setMessages(prev => [...prev, { role: 'system', content: progress.step }]);
      });
    }, []);

    return (
      <div className="agent-chat">
        <div className="messages">
          {messages.map((msg, idx) => (
            <ChatBubble key={idx} {...msg} />
          ))}
        </div>
        <Button
          onClick={() => startAnalysis({ protocol })}
          loading={isLoading}
        >
          开始分析
        </Button>
      </div>
    );
  }
  ```
- [ ] 实现可视化报告区：
  ```typescript
  // src/pages/Analysis/VisualizationReport.tsx
  export function VisualizationReport({ result }: VisualizationReportProps) {
    const [activeTab, setActiveTab] = useState('overview');

    const tabs = [
      { key: 'overview', title: '概览', content: <OverviewTab data={result} /> },
      { key: 'charts', title: '图表', content: <ChartsTab data={result} /> },
      { key: 'reports', title: '详细报告', content: <ReportsTab data={result} /> },
      { key: 'decision', title: '最终决策', content: <DecisionTab data={result} /> },
    ];

    return (
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        {tabs.map(tab => (
          <Tabs.Tab key={tab.key} title={tab.title}>
            {tab.content}
          </Tabs.Tab>
        ))}
      </Tabs>
    );
  }
  ```
- [ ] 实现导出功能：
  ```typescript
  // src/pages/Analysis/ExportButton.tsx
  export function ExportButton({ result }: ExportButtonProps) {
    const handleExport = (format: 'pdf' | 'markdown') => {
      if (format === 'markdown') {
        const markdown = generateMarkdown(result);
        downloadFile(markdown, `${result.protocol}-analysis.md`, 'text/markdown');
      } else {
        // 使用 jsPDF 生成 PDF
        const pdf = generatePDF(result);
        pdf.save(`${result.protocol}-analysis.pdf`);
      }
    };

    return (
      <Dropdown
        trigger={<Button>导出报告</Button>}
        menu={[
          { key: 'markdown', label: 'Markdown', onClick: () => handleExport('markdown') },
          { key: 'pdf', label: 'PDF', onClick: () => handleExport('pdf') },
        ]}
      />
    );
  }
  ```

**验收标准**：
- ✅ Agent 分析成功执行
- ✅ 实时进度正确显示
- ✅ 报告可视化完整
- ✅ 导出功能正常

---

#### 任务 2.7：历史记录页面 ⏱️ 2天

**目标**：展示和管理分析历史

**子任务**：
- [ ] 实现筛选器：
  ```typescript
  // src/pages/History/Filters.tsx
  export function Filters({ onChange }: FiltersProps) {
    const [filters, setFilters] = useState({
      dateRange: 'week',
      queryType: 'all',
      protocol: '',
    });

    return (
      <div className="filters">
        <Select
          value={filters.dateRange}
          onChange={val => handleChange('dateRange', val)}
        >
          <Select.Option value="today">今天</Select.Option>
          <Select.Option value="week">7天</Select.Option>
          <Select.Option value="month">30天</Select.Option>
        </Select>
        {/* 其他筛选器 */}
      </div>
    );
  }
  ```
- [ ] 实现记录列表（虚拟滚动）：
  ```typescript
  // src/pages/History/HistoryList.tsx
  import { FixedSizeList } from 'react-window';

  export function HistoryList() {
    const { data, fetchNextPage, hasNextPage } = useInfiniteQuery({
      queryKey: ['analysis-history'],
      queryFn: ({ pageParam = 0 }) => analysisApi.getHistory({ offset: pageParam }),
      getNextPageParam: (lastPage, pages) => lastPage.hasMore ? pages.length * 20 : undefined,
    });

    const items = data?.pages.flatMap(page => page.data) || [];

    return (
      <FixedSizeList
        height={600}
        itemCount={items.length}
        itemSize={80}
        onItemsRendered={({ visibleStopIndex }) => {
          if (visibleStopIndex === items.length - 1 && hasNextPage) {
            fetchNextPage();
          }
        }}
      >
        {({ index, style }) => (
          <div style={style}>
            <HistoryItem data={items[index]} />
          </div>
        )}
      </FixedSizeList>
    );
  }
  ```
- [ ] 实现详情抽屉：
  ```typescript
  // src/pages/History/DetailDrawer.tsx
  export function DetailDrawer({ id, visible, onClose }: DetailDrawerProps) {
    const { data } = useQuery({
      queryKey: ['analysis', id],
      queryFn: () => analysisApi.getDetail(id),
      enabled: visible,
    });

    return (
      <Drawer visible={visible} onClose={onClose}>
        <VisualizationReport result={data} />
        <Button onClick={handleRerun}>重新运行分析</Button>
      </Drawer>
    );
  }
  ```

**验收标准**：
- ✅ 筛选器工作正常
- ✅ 虚拟滚动流畅（1000+ 条记录）
- ✅ 详情抽屉加载快速

---

#### 任务 2.8：监控列表页面 ⏱️ 2天

**目标**：实现实时监控和警报

**子任务**：
- [ ] 实现监控列表：
  ```typescript
  // src/pages/Watchlist/WatchlistGrid.tsx
  export function WatchlistGrid() {
    const { data: watchlist } = useQuery({
      queryKey: ['watchlist'],
      queryFn: watchlistApi.getList,
    });

    // 监听 WebSocket 实时数据
    useEffect(() => {
      wsClient.on('data_update', (update) => {
        queryClient.setQueryData(['watchlist'], (old: any) => {
          return old.map((item: any) =>
            item.protocol === update.protocol ? { ...item, ...update.metrics } : item
          );
        });
      });
    }, []);

    return (
      <div className="watchlist-grid">
        {watchlist?.map(item => (
          <WatchlistCard key={item.id} {...item} />
        ))}
      </div>
    );
  }
  ```
- [ ] 实现添加监控对话框：
  ```typescript
  // src/pages/Watchlist/AddDialog.tsx
  export function AddDialog({ visible, onClose }: AddDialogProps) {
    const [protocol, setProtocol] = useState('');
    const [conditions, setConditions] = useState({
      tvlChange: 10,
      apyThreshold: 5,
    });

    const { mutate: addWatchlist } = useMutation({
      mutationFn: watchlistApi.add,
      onSuccess: () => {
        queryClient.invalidateQueries(['watchlist']);
        onClose();
      },
    });

    return (
      <Dialog visible={visible} onClose={onClose}>
        <Form>
          <Form.Item label="选择协议">
            <ProtocolSelector onSelect={setProtocol} />
          </Form.Item>
          <Form.Item label="TVL 变化警报（±%）">
            <Slider value={conditions.tvlChange} onChange={val => setConditions({ ...conditions, tvlChange: val })} />
          </Form.Item>
          <Form.Item label="APY 阈值警报（%）">
            <Input value={conditions.apyThreshold} onChange={val => setConditions({ ...conditions, apyThreshold: val })} />
          </Form.Item>
          <Button onClick={() => addWatchlist({ protocol, conditions })}>
            添加监控
          </Button>
        </Form>
      </Dialog>
    );
  }
  ```
- [ ] 实现警报历史：
  ```typescript
  // src/pages/Watchlist/AlertHistory.tsx
  export function AlertHistory() {
    const { data: alerts } = useQuery({
      queryKey: ['alert-history'],
      queryFn: watchlistApi.getAlerts,
    });

    return (
      <List>
        {alerts?.map(alert => (
          <List.Item key={alert.id}>
            <div className="alert-item">
              <span className="protocol">{alert.protocol}</span>
              <span className="condition">{alert.message}</span>
              <span className="time">{formatTime(alert.triggered_at)}</span>
            </div>
          </List.Item>
        ))}
      </List>
    );
  }
  ```

**验收标准**：
- ✅ 实时数据更新流畅
- ✅ 添加监控成功
- ✅ 警报历史正确显示

---

#### 任务 2.9：设置页面 ⏱️ 1天

**目标**：用户设置和数据管理

**子任务**：
- [ ] 实现账户信息：
  ```typescript
  // src/pages/Settings/AccountInfo.tsx
  export function AccountInfo() {
    const { user } = useAuthStore();
    const { data: stats } = useQuery({
      queryKey: ['user-stats'],
      queryFn: userApi.getStats,
    });

    return (
      <List>
        <List.Item title="用户名">{user?.username}</List.Item>
        <List.Item title="注册时间">{formatDate(user?.created_at)}</List.Item>
        <List.Item title="总分析次数">{stats?.total_analysis}</List.Item>
        <List.Item title="收藏数">{stats?.favorites_count}</List.Item>
      </List>
    );
  }
  ```
- [ ] 实现偏好设置：
  ```typescript
  // src/pages/Settings/Preferences.tsx
  export function Preferences() {
    const { user } = useAuthStore();
    const [settings, setSettings] = useState(user?.settings || {});

    const { mutate: updateSettings } = useMutation({
      mutationFn: userApi.updateSettings,
      onSuccess: () => {
        queryClient.invalidateQueries(['user']);
      },
    });

    return (
      <Form>
        <Form.Item label="默认风险偏好">
          <Selector
            value={settings.risk_preference}
            onChange={val => handleChange('risk_preference', val)}
            options={[
              { label: '低风险', value: 'low' },
              { label: '中风险', value: 'medium' },
              { label: '高风险', value: 'high' },
            ]}
          />
        </Form.Item>
        <Button onClick={() => updateSettings(settings)}>保存设置</Button>
      </Form>
    );
  }
  ```
- [ ] 实现数据管理：
  ```typescript
  // src/pages/Settings/DataManagement.tsx
  export function DataManagement() {
    const handleExport = async () => {
      const data = await userApi.exportData();
      downloadFile(JSON.stringify(data), 'defi-agent-data.json', 'application/json');
    };

    const handleClearCache = () => {
      queryClient.clear();
      localStorage.clear();
      Toast.show('缓存已清除');
    };

    const handleDeleteAccount = () => {
      Dialog.confirm({
        content: '确认删除账户？此操作不可恢复。',
        onConfirm: async () => {
          await userApi.deleteAccount();
          logout();
        },
      });
    };

    return (
      <List>
        <List.Item onClick={handleExport}>导出所有数据</List.Item>
        <List.Item onClick={handleClearCache}>清除缓存</List.Item>
        <List.Item onClick={handleDeleteAccount} style={{ color: 'red' }}>
          删除账户
        </List.Item>
      </List>
    );
  }
  ```

**验收标准**：
- ✅ 设置保存成功
- ✅ 数据导出正常
- ✅ 账户删除确认流程安全

---

### Week 9: 优化与完善

#### 任务 2.10：性能优化 ⏱️ 2-3天

**目标**：提升应用加载速度和响应性

**子任务**：
- [ ] 代码分割：
  ```typescript
  // src/router.tsx
  const Dashboard = lazy(() => import('./pages/Dashboard'));
  const Analysis = lazy(() => import('./pages/Analysis'));

  // 使用 Suspense 包裹
  <Suspense fallback={<LoadingState />}>
    <Dashboard />
  </Suspense>
  ```
- [ ] 图片优化：
  - [ ] 转换协议 Logo 为 WebP 格式
  - [ ] 使用 CDN 加速（Cloudflare）
  - [ ] 实现懒加载（Intersection Observer）
- [ ] 打包优化：
  ```typescript
  // vite.config.ts
  export default defineConfig({
    build: {
      rollupOptions: {
        output: {
          manualChunks: {
            'react-vendor': ['react', 'react-dom', 'react-router-dom'],
            'ui-vendor': ['antd-mobile'],
            'charts-vendor': ['echarts', 'echarts-for-react'],
          },
        },
      },
    },
  });
  ```
- [ ] 性能测试：
  - [ ] 使用 Lighthouse 测试（目标 >90 分）
  - [ ] 测试首屏加载时间（目标 <3秒）
  - [ ] 测试 TTI（Time to Interactive，目标 <5秒）

**验收标准**：
- ✅ Lighthouse 性能评分 >90
- ✅ 首屏加载 <3秒（4G 网络）
- ✅ 包体积 <2MB（gzip 后）

---

#### 任务 2.11：错误处理与用户体验 ⏱️ 1-2天

**目标**：完善错误处理和交互反馈

**子任务**：
- [ ] 实现全局错误边界：
  ```typescript
  // src/components/ErrorBoundary.tsx
  class ErrorBoundary extends React.Component<Props, State> {
    static getDerivedStateFromError(error: Error) {
      return { hasError: true, error };
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
      console.error('Error caught:', error, errorInfo);
      // 可选：上报到 Sentry
    }

    render() {
      if (this.state.hasError) {
        return <ErrorFallback error={this.state.error} />;
      }
      return this.props.children;
    }
  }
  ```
- [ ] 实现离线检测：
  ```typescript
  // src/hooks/useOnlineStatus.ts
  export function useOnlineStatus() {
    const [isOnline, setIsOnline] = useState(navigator.onLine);

    useEffect(() => {
      const handleOnline = () => setIsOnline(true);
      const handleOffline = () => setIsOnline(false);

      window.addEventListener('online', handleOnline);
      window.addEventListener('offline', handleOffline);

      return () => {
        window.removeEventListener('online', handleOnline);
        window.removeEventListener('offline', handleOffline);
      };
    }, []);

    return isOnline;
  }
  ```
- [ ] 实现 Toast 提示：
  ```typescript
  // src/utils/toast.ts
  export const toast = {
    success: (message: string) => Toast.show({ icon: 'success', content: message }),
    error: (message: string) => Toast.show({ icon: 'fail', content: message }),
    loading: (message: string) => Toast.show({ icon: 'loading', content: message }),
  };
  ```

**验收标准**：
- ✅ 错误不会导致白屏
- ✅ 离线时显示友好提示
- ✅ 所有操作有反馈

---

## Phase 3: 集成测试与部署（1-2周）

**目标**：完成测试和生产环境部署

### Week 10: 测试与修复

#### 任务 3.1：端到端测试 ⏱️ 2-3天

**目标**：编写 E2E 测试覆盖核心流程

**子任务**：
- [ ] 安装 Playwright：
  ```bash
  npm install -D @playwright/test
  npx playwright install
  ```
- [ ] 编写测试用例：
  ```typescript
  // tests/e2e/dashboard.spec.ts
  import { test, expect } from '@playwright/test';

  test('仪表盘加载正常', async ({ page }) => {
    await page.goto('http://localhost:3000/dashboard');
    await expect(page.locator('h1')).toContainText('仪表盘');
  });

  test('分析协议流程', async ({ page }) => {
    await page.goto('http://localhost:3000/analysis');
    await page.fill('input[placeholder="搜索协议"]', 'aave');
    await page.click('text=Aave V3');
    await page.click('button:has-text("开始分析")');
    await expect(page.locator('.analysis-progress')).toBeVisible();
  });
  ```
- [ ] 运行测试：
  ```bash
  npx playwright test
  ```

**验收标准**：
- ✅ 所有关键流程测试通过
- ✅ 测试覆盖率 >70%

---

#### 任务 3.2：部署到生产环境 ⏱️ 2-3天

**目标**：完成前后端部署

**子任务**：
- [ ] 前端部署（Vercel）：
  ```bash
  # 连接 GitHub 仓库
  # Vercel 会自动检测 React 项目

  # 配置环境变量
  VITE_API_URL=https://api.your-domain.com/api/v1
  VITE_WS_URL=wss://api.your-domain.com/api/v1/ws
  ```
- [ ] 后端部署（Railway）：
  ```bash
  # 连接 GitHub 仓库
  # Railway 会自动检测 Python 项目

  # 配置环境变量
  DATABASE_URL=postgresql://...
  REDIS_URL=redis://...
  BOT_TOKEN=...
  JWT_SECRET=...
  ```
- [ ] 配置域名：
  - [ ] 前端：miniapp.your-domain.com
  - [ ] 后端：api.your-domain.com
- [ ] 配置 SSL 证书（自动）
- [ ] 测试生产环境：
  - [ ] 前端访问正常
  - [ ] API 调用成功
  - [ ] WebSocket 连接正常
  - [ ] Telegram Bot 打开 Mini App 正常

**验收标准**：
- ✅ 生产环境访问正常
- ✅ 所有功能可用
- ✅ 性能符合预期

---

#### 任务 3.3：监控和日志 ⏱️ 1天

**目标**：配置错误追踪和性能监控

**子任务**：
- [ ] 集成 Sentry（错误追踪）：
  ```typescript
  // src/main.tsx
  import * as Sentry from '@sentry/react';

  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    integrations: [new Sentry.BrowserTracing()],
    tracesSampleRate: 1.0,
  });
  ```
- [ ] 集成 Plausible（用户分析）：
  ```html
  <!-- index.html -->
  <script defer data-domain="miniapp.your-domain.com" src="https://plausible.io/js/script.js"></script>
  ```
- [ ] 配置后端日志：
  ```python
  # app/core/logging.py
  import logging
  from pythonjsonlogger import jsonlogger

  handler = logging.StreamHandler()
  formatter = jsonlogger.JsonFormatter()
  handler.setFormatter(formatter)
  logger.addHandler(handler)
  ```

**验收标准**：
- ✅ 错误自动上报到 Sentry
- ✅ 用户访问数据可见
- ✅ 后端日志结构化

---

## 开发资源

### 必读文档

**Telegram Mini Apps**：
- 官方文档：https://core.telegram.org/bots/webapps
- SDK 仓库：https://github.com/twa-dev/sdk
- 示例项目：https://github.com/Telegram-Mini-Apps/reactjs-template

**React + TypeScript**：
- React Query：https://tanstack.com/query/latest
- Zustand：https://docs.pmnd.rs/zustand
- React Router：https://reactrouter.com/

**FastAPI**：
- 官方文档：https://fastapi.tiangolo.com/
- WebSocket 指南：https://fastapi.tiangolo.com/advanced/websockets/

**数据库**：
- SQLAlchemy：https://docs.sqlalchemy.org/
- Alembic：https://alembic.sqlalchemy.org/

---

### 推荐工具

**开发工具**：
- VSCode + Prettier + ESLint
- Postman（API 测试）
- TablePlus（数据库管理）
- Redis Insight（Redis 可视化）

**调试工具**：
- React DevTools
- Redux DevTools（如果使用 Redux）
- Chrome DevTools（Network, Performance）

**设计工具**：
- Figma（UI 设计）
- Excalidraw（架构图）

---

## 风险管理

### 高风险项

| 风险 | 缓解策略 | 应急预案 |
|------|---------|---------|
| Telegram API 限制导致功能不可用 | 提前测试所有 API，准备降级方案 | 使用 Bot 消息交互替代 Mini App |
| WebSocket 并发性能不足 | 负载测试，使用 Redis Pub/Sub 分布式 | 使用轮询（Polling）替代 |
| 数据库查询慢导致超时 | 索引优化，查询分页 | 增加缓存层，Redis 缓存热数据 |
| 前端打包过大导致加载慢 | 代码分割，按需加载 | 使用 CDN 加速，启用 Gzip |

---

### 低风险项

| 风险 | 缓解策略 |
|------|---------|
| DeFi 数据源 API 偶尔失败 | 多数据源回退，本地缓存 |
| 用户量增长导致成本上升 | 监控使用量，提前扩容计划 |
| 某些浏览器兼容性问题 | 使用 Babel 兼容，测试主流浏览器 |

---

## 下一步行动

### 立即开始（本周）

1. **创建 GitHub 仓库**：
   ```bash
   mkdir defi-miniapp && cd defi-miniapp
   git init
   git remote add origin https://github.com/your-org/defi-miniapp.git
   ```

2. **创建项目结构**：
   ```bash
   mkdir -p backend frontend docs
   cd frontend && npm create vite@latest . -- --template react-ts && npm install
   cd ../backend && poetry init
   ```

3. **设置开发环境**：
   - 安装 PostgreSQL 和 Redis
   - 创建 Telegram Test Bot
   - 配置 ngrok 用于本地测试

4. **启动 Phase 0 Task 0.1**：
   - 阅读 Telegram Mini App 文档
   - 创建最小化原型
   - 验证用户认证

---

## 总结

本开发计划将 DeFi Agent 从纯 Bot 升级为完整的 Telegram Mini App，共分为 3 个阶段：

- **Phase 0（1-2周）**：架构设计与技术验证
- **Phase 1（2-3周）**：后端 API 开发
- **Phase 2（3-4周）**：前端 Mini App 开发
- **Phase 3（1-2周）**：集成测试与部署

**总工期**：8-10周（全职开发）

**关键里程碑**：
- Week 2：技术原型验证完成
- Week 5：后端 API 全部完成
- Week 9：前端所有页面完成
- Week 10：生产环境上线

**下一步**：开始 Phase 0 Task 0.1（Telegram Mini App 技术验证）。
