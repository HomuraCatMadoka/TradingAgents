# 部署指南

## 1. 系统要求
- Python 3.10+
- PostgreSQL 14+（生产环境禁止使用 SQLite）
- Redis 6+（缓存、会话、速率限制）
- 操作系统：Linux/macOS（推荐使用 systemd 或容器编排）

## 2. 安装步骤
1. 创建虚拟环境并安装依赖：
   ```bash
   cd miniapp/backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. 配置环境变量：复制 `.env.production.example` 到 `.env` 并填入生产值。
3. 初始化数据库：
   ```bash
   psql -c "CREATE DATABASE miniapp;"  # 如已存在可跳过
   alembic upgrade head
   ```
4. 确认 Redis 可用（`redis-cli PING` 返回 PONG）。

## 3. 环境变量说明
- `DATABASE_URL`：PostgreSQL 连接串，示例 `postgresql+asyncpg://user:pass@host:5432/miniapp`
- `ALEMBIC_CONFIG`：Alembic 配置文件路径，默认 `miniapp/backend/alembic.ini`
- `SQL_ECHO`：是否打印 SQL（生产应为 `0`）
- `JWT_SECRET` / `JWT_SECRET_KEY`：JWT 签名密钥（必须为强随机值）
- `JWT_EXPIRES_MINUTES`：Access Token 过期时间，默认 60 分钟
- `JWT_REFRESH_DAYS`：Refresh Token 过期天数，默认 7 天
- `TELEGRAM_BOT_TOKEN`：Bot Token，用于授权登录/接口保护
- `REDIS_URL`：Redis 连接串（含密码），示例 `redis://:password@redis:6379/0`
- `REDIS_SSL`：是否启用 SSL，`true/false`
- `LOG_LEVEL`：日志级别（info、warning、error），默认 info

## 4. 启动命令
- 开发模式：
  ```bash
  uvicorn main:app --reload --host 0.0.0.0 --port 8000
  ```
- 生产模式（示例）：
  ```bash
  uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 --proxy-headers --forwarded-allow-ips="*"
  ```
  建议搭配 systemd、supervisor 或容器编排运行，并由反向代理（如 Nginx）处理 TLS。

## 5. 常见问题排查
- **无法连接数据库**：检查 `DATABASE_URL`、网络防火墙、PostgreSQL 角色权限；使用 `psql <DATABASE_URL>` 验证。
- **Alembic 找不到配置**：确认 `ALEMBIC_CONFIG` 指向正确路径，或在项目根目录执行命令。
- **Redis 连接失败**：确认 `REDIS_URL`、密码和 SSL 设定，使用 `redis-cli -u <REDIS_URL> PING` 测试。
- **JWT 校验失败**：确保 Access/Refresh 密钥一致且未使用默认值；检查时间同步。
- **CORS 问题**：生产环境应限制 `allow_origins`，必要时在反向代理层添加白名单。

## 6. 监控与日志
- 健康检查：`GET /api/health`
- OpenAPI 文档：`/api/docs` (Swagger UI)，`/api/redoc`
- 日志：默认输出到标准输出，使用 `LOG_LEVEL` 控制；建议由进程管理器或容器日志采集到集中系统（ELK/Cloud Logging 等）。
- 数据库迁移：部署后运行 `alembic upgrade head`，版本对齐后再发布应用进程。
