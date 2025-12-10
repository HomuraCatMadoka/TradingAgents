# 快速开始指南

本指南帮助你在 **30 分钟内**启动 Telegram Mini App 开发环境并运行第一个原型。

---

## 前置条件检查

确保你的开发环境满足以下要求：

```bash
# 1. Node.js 18+
node --version  # 应显示 v18.x.x 或更高

# 2. Python 3.11+
python3 --version  # 应显示 Python 3.11.x 或更高

# 3. PostgreSQL 14+
psql --version  # 应显示 psql (PostgreSQL) 14.x 或更高

# 4. Redis 7+
redis-cli --version  # 应显示 redis-cli 7.x.x 或更高

# 5. Git
git --version
```

**如果缺少任何工具**：

```bash
# macOS（使用 Homebrew）
brew install node python@3.11 postgresql@16 redis

# 启动服务
brew services start postgresql@16
brew services start redis

# Ubuntu/Debian
sudo apt update
sudo apt install nodejs npm python3.11 python3-pip postgresql-16 redis-server

# 启动服务
sudo systemctl start postgresql
sudo systemctl start redis-server
```

---

## Step 1: 创建 Telegram Bot（5分钟）

### 1.1 创建 Bot

1. 在 Telegram 中搜索 **@BotFather**
2. 发送 `/newbot` 命令
3. 输入 Bot 名称（如 `DeFi Agent Mini App`）
4. 输入 Bot 用户名（如 `defi_agent_miniapp_bot`，必须以 `_bot` 结尾）
5. 保存返回的 **Bot Token**（格式：`1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`）

### 1.2 配置 Mini App（暂时跳过，后续设置）

稍后会配置 Bot 的 Menu Button 指向你的 Mini App URL。

---

## Step 2: 创建项目结构（5分钟）

### 2.1 克隆现有项目（推荐）

如果你已有 DeFi Agent 项目：

```bash
cd /Users/wangkunyu/develop/TradingAgents
mkdir -p miniapp/{frontend,backend}
```

### 2.2 或创建新项目

```bash
mkdir defi-miniapp && cd defi-miniapp
mkdir frontend backend docs

# 初始化 Git
git init
echo "node_modules/" >> .gitignore
echo "__pycache__/" >> .gitignore
echo ".env" >> .gitignore
echo "*.pyc" >> .gitignore
```

---

## Step 3: 前端快速启动（10分钟）

### 3.1 创建 React 项目（使用 Vite）

**注意**：使用 Vite 替代已弃用的 Create React App，获得更快的冷启动和 HMR。

```bash
cd frontend

# 使用 Vite 创建 React + TypeScript 项目
npm create vite@latest . -- --template react-ts

# 安装依赖
npm install @twa-dev/sdk react-router-dom zustand
npm install @tanstack/react-query axios
npm install antd-mobile echarts echarts-for-react

# 可选：Sass 支持（推荐）
npm install sass
```

### 3.2 配置 Vite

在 `vite.config.ts` 中配置相对资源路径和端口（保持 3000 便于后续 ngrok）：

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  base: './', // 确保资源路径相对化，便于 Telegram WebView 加载
  server: {
    host: true, // 允许外部访问（ngrok 调试需要）
    port: 3000, // 固定端口，后续暴露给 Telegram
  },
})
```

### 3.3 创建最小化 Mini App

创建 `src/App.tsx`：

```typescript
import React, { useEffect } from 'react';
import { WebApp } from '@twa-dev/sdk';

function App() {
  useEffect(() => {
    // 初始化 Telegram WebApp
    WebApp.ready();
    WebApp.expand(); // 全屏显示

    // 设置主题颜色
    WebApp.setHeaderColor(WebApp.colorScheme === 'dark' ? '#1f1f1f' : '#ffffff');

    console.log('Telegram User:', WebApp.initDataUnsafe.user);
  }, []);

  return (
    <div style={{
      padding: '20px',
      minHeight: '100vh',
      background: WebApp.colorScheme === 'dark' ? '#000' : '#fff',
      color: WebApp.colorScheme === 'dark' ? '#fff' : '#000',
    }}>
      <h1>🚀 DeFi Agent Mini App</h1>
      <p>用户ID: {WebApp.initDataUnsafe.user?.id}</p>
      <p>用户名: {WebApp.initDataUnsafe.user?.username || '未设置'}</p>
      <p>主题: {WebApp.colorScheme}</p>

      <button
        onClick={() => WebApp.showAlert('Hello from Mini App!')}
        style={{
          padding: '10px 20px',
          marginTop: '20px',
          background: '#0088cc',
          color: '#fff',
          border: 'none',
          borderRadius: '8px',
          cursor: 'pointer',
        }}
      >
        测试弹窗
      </button>
    </div>
  );
}

export default App;
```

**提示**：Vite 项目入口为 `src/main.tsx`，确保其中正确挂载了 `App`。

### 3.4 启动开发服务器

```bash
npm run dev
```

浏览器会自动打开 `http://localhost:3000`。在本地浏览器中看不到 Telegram 用户数据（需通过 Telegram WebView 访问）。

---

## Step 4: 使用 ngrok 暴露本地服务（5分钟）

开始前请确保 Vite 开发服务器已在 `http://localhost:3000` 运行。

### 4.1 安装 ngrok

```bash
# macOS
brew install ngrok

# 或从官网下载：https://ngrok.com/download
```

### 4.2 启动 ngrok

在**新终端**中运行：

```bash
ngrok http 3000
```

你会看到类似输出：

```
Forwarding   https://abc123.ngrok-free.app -> http://localhost:3000
```

**复制 HTTPS URL**（如 `https://abc123.ngrok-free.app`）。

---

## Step 5: 配置 Bot Menu Button（2分钟）

### 5.1 设置 Menu Button

回到 Telegram，找到 @BotFather，发送以下命令：

```
/setmenubutton
```

1. 选择你的 Bot
2. 输入按钮文本（如 `打开应用`）
3. 输入你的 ngrok URL（如 `https://abc123.ngrok-free.app`）

### 5.2 测试 Mini App

1. 在 Telegram 中找到你的 Bot
2. 点击底部的**菜单按钮**（📱）
3. 应该会打开你的 Mini App，并显示用户信息

**成功标志**：
- ✅ 看到你的 Telegram 用户ID 和用户名
- ✅ 主题颜色与 Telegram 一致（Dark/Light）
- ✅ 点击按钮弹出 Telegram 原生弹窗

---

## Step 6: 后端快速启动（3分钟）

### 6.1 创建 FastAPI 项目

```bash
cd ../backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate.fish
 
# 安装依赖
pip install fastapi uvicorn python-dotenv pyjwt
```

### 6.2 创建最小化 API

创建 `main.py`：

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="DeFi Agent API")

# 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境需限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "DeFi Agent API is running"}

@app.get("/api/protocols")
async def get_protocols():
    # Mock 数据
    return {
        "data": [
            {"name": "Aave V3", "tvl": 5_234_567_890, "apy": 3.5},
            {"name": "Uniswap V3", "tvl": 4_123_456_789, "apy": 12.8},
            {"name": "Compound V3", "tvl": 2_345_678_901, "apy": 4.2},
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 6.3 启动后端

```bash
python main.py
```

访问 `http://localhost:8000/docs` 查看自动生成的 API 文档（Swagger UI）。

---

## Step 7: 前后端联调（5分钟）

### 7.1 修改前端调用 API

更新 `frontend/src/App.tsx`：

```typescript
import React, { useEffect, useState } from 'react';
import { WebApp } from '@twa-dev/sdk';

function App() {
  const [protocols, setProtocols] = useState([]);

  useEffect(() => {
    WebApp.ready();
    WebApp.expand();

    // 调用后端 API
    fetch('http://localhost:8000/api/protocols')
      .then(res => res.json())
      .then(data => setProtocols(data.data))
      .catch(err => console.error(err));
  }, []);

  return (
    <div style={{ padding: '20px' }}>
      <h1>🚀 DeFi Agent</h1>
      <h2>协议列表</h2>
      <ul>
        {protocols.map((p: any) => (
          <li key={p.name}>
            {p.name} - TVL: ${(p.tvl / 1e9).toFixed(2)}B - APY: {p.apy}%
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;
```

### 7.2 刷新 Mini App

在 Telegram 中重新打开 Mini App，应该会看到协议列表。

---

## Step 8: 认证集成（可选，5分钟）

### 8.1 后端验证 Telegram 数据

创建 `backend/auth.py`：

```python
import hashlib
import hmac
from urllib.parse import parse_qsl

def verify_telegram_webapp_data(init_data: str, bot_token: str) -> dict | None:
    """验证 Telegram WebApp initData"""
    try:
        params = dict(parse_qsl(init_data))
        data_check_string = '\n'.join([
            f"{k}={v}" for k, v in sorted(params.items()) if k != 'hash'
        ])

        secret_key = hashlib.sha256(bot_token.encode()).digest()
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        if calculated_hash == params.get('hash'):
            import json
            return json.loads(params.get('user', '{}'))
    except Exception as e:
        print(f"验证失败: {e}")

    return None
```

### 8.2 添加认证端点

在 `main.py` 中添加：

```python
from fastapi import HTTPException
from pydantic import BaseModel
from auth import verify_telegram_webapp_data
import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token_here")

class AuthRequest(BaseModel):
    initData: str

@app.post("/api/auth/telegram")
async def telegram_auth(request: AuthRequest):
    user = verify_telegram_webapp_data(request.initData, BOT_TOKEN)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid authentication")

    # 生成 JWT Token（简化版）
    token = f"fake_jwt_token_for_user_{user['id']}"

    return {
        "user": user,
        "token": token
    }
```

### 8.3 前端发送认证请求

```typescript
useEffect(() => {
  WebApp.ready();

  // 发送 Telegram initData 到后端验证
  fetch('http://localhost:8000/api/auth/telegram', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ initData: WebApp.initData })
  })
    .then(res => res.json())
    .then(data => {
      console.log('认证成功:', data.user);
      localStorage.setItem('token', data.token);
    })
    .catch(err => console.error('认证失败:', err));
}, []);
```

---

## 常见问题

### Q1: ngrok URL 一直变怎么办？

**免费方案**：每次重启 ngrok 会生成新 URL，需重新配置 Bot Menu Button。

**付费方案**（$8/月）：可以固定域名（如 `defi-agent.ngrok.io`）。

**替代方案**：
- 使用 [localtunnel](https://localtunnel.github.io/www/)（免费）
- 使用 [Cloudflare Tunnel](https://www.cloudflare.com/products/tunnel/)（免费）

### Q2: 在浏览器中看不到 Telegram 用户数据？

这是正常的，因为不在 Telegram 环境中。`WebApp.initDataUnsafe` 只在 Telegram 内有效。

**解决方法**：
- 使用 Telegram Bot 打开 Mini App
- 或在代码中添加 Mock 数据用于本地开发

### Q3: 前端无法访问后端 API（CORS 错误）？

确保后端添加了 CORS 中间件（参考 Step 6.2）。

### Q4: Mini App 在 Telegram 中加载很慢？

**原因**：ngrok 免费版速度较慢。

**解决方法**：
- 升级到 ngrok 付费版
- 尽早部署到 Vercel（免费且极快）

---

## 下一步

恭喜！🎉 你已经成功搭建了 Telegram Mini App 开发环境。

**继续开发**：

1. **阅读完整开发计划**：[dev-plan.md](./dev-plan.md)
2. **开始 Phase 0 任务**：
   - Task 0.1: Telegram Mini App 功能验证
   - Task 0.2: FastAPI + WebSocket 原型
   - Task 0.3: 数据库设计

3. **部署到生产环境**：
   - 前端部署到 Vercel（免费）
   - 后端部署到 Railway（免费 $5 额度）

4. **加入开发**：
   - 查看 [architecture.md](./architecture.md) 了解整体架构
   - 查看 [tech-stack.md](./tech-stack.md) 了解技术选型

---

## 有用的资源

**官方文档**：
- [Telegram WebApp 文档](https://core.telegram.org/bots/webapps)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [React 文档](https://react.dev/)

**示例项目**：
- [Telegram Mini Apps React 模板](https://github.com/Telegram-Mini-Apps/reactjs-template)
- [FastAPI WebSocket 示例](https://github.com/tiangolo/fastapi/tree/master/tests/test_tutorial/test_websockets)

**社区**：
- [Telegram WebApp 开发者群](https://t.me/WebAppDevs)
- [FastAPI Discord](https://discord.gg/fastapi)

---

需要帮助？随时提问！
