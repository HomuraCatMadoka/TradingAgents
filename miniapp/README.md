# Miniapp CI/CD

[![Frontend CI](https://github.com/your-username/TradingAgents/actions/workflows/miniapp-frontend-ci.yml/badge.svg)](https://github.com/your-username/TradingAgents/actions/workflows/miniapp-frontend-ci.yml)
[![Backend CI](https://github.com/your-username/TradingAgents/actions/workflows/miniapp-backend-ci.yml/badge.svg)](https://github.com/your-username/TradingAgents/actions/workflows/miniapp-backend-ci.yml)

## Telegram Mini App Dashboard

DeFi Agent 的 Web 仪表盘，支持可视化分析报告、历史记录追踪、实时数据监控和用户账户管理。

## 项目结构

```
miniapp/
├── backend/        # FastAPI 后端
│   ├── models/     # SQLAlchemy 数据库模型
│   ├── schemas/    # Pydantic schemas
│   ├── alembic/    # 数据库迁移
│   └── tests/      # 后端测试
└── frontend/       # React 前端
    ├── src/
    │   ├── pages/      # 页面组件
    │   ├── components/ # 可复用组件
    │   ├── services/   # API 调用
    │   ├── store/      # Zustand 状态
    │   └── types/      # TypeScript 类型
    └── __tests__/      # 前端测试
```

## 快速开始

### 后端设置

```bash
cd miniapp/backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入数据库连接、Bot Token 等

# 运行数据库迁移
alembic upgrade head

# 种子数据（可选）
python -m scripts.seed_data

# 启动服务
python main.py
```

### 前端设置

```bash
cd miniapp/frontend
npm install

# 配置环境变量
cp .env.example .env
# 编辑 .env 填入 API URL

# 开发模式
npm run dev

# 生产构建
npm run build
```

## 本地测试

### 前端测试
```bash
cd miniapp/frontend
npm ci
npm run lint
npm run build
npm run test
```

### 后端测试
```bash
cd miniapp/backend
pip install -r requirements.txt -r requirements-dev.txt
ruff check .
mypy .
alembic upgrade head
pytest
```

## CI/CD

### 触发条件

- **Frontend CI**: Push 或 PR 到 `main`/`develop` 分支，且修改 `miniapp/frontend/**` 文件
- **Backend CI**: Push 或 PR 到 `main`/`develop` 分支，且修改 `miniapp/backend/**` 文件

### Workflow 步骤

**Frontend**:
1. Setup Node.js 18
2. 安装依赖（npm ci）
3. 代码检查（npm run lint）
4. 构建（npm run build）

**Backend**:
1. Setup Python 3.11 + PostgreSQL 16
2. 安装依赖（pip install）
3. 代码检查（ruff check）
4. 类型检查（mypy）
5. 数据库迁移（alembic upgrade head）
6. 运行测试（pytest）

## 技术栈

### 后端
- **FastAPI** - 异步 Web 框架
- **SQLAlchemy 2.0** - ORM
- **Alembic** - 数据库迁移
- **PostgreSQL** - 数据库
- **PyJWT** - JWT 认证

### 前端
- **React 18** + TypeScript
- **Vite** - 构建工具
- **React Router** - 路由
- **Zustand** - 状态管理
- **React Query** - 服务端状态缓存
- **AntD Mobile** - UI 组件库
- **ECharts** - 图表库
- **@twa-dev/sdk** - Telegram WebApp SDK

## 开发规范

详见：
- [贡献指南](../../docs/CONTRIBUTING.md)
- [API 设计规范](../../docs/API_DESIGN.md)
- [前端开发指南](../../docs/FRONTEND_GUIDE.md)

## License

与主项目相同
