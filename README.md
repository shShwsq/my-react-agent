# Not-Toy-Anymore - AI Chat System

一个基于 FastAPI + Vue 3 的 AI 聊天系统，支持多模态输入、Agent 任务编排、语音合成等功能。

## 功能特性

- **多模态输入**：支持文本、语音、图片输入
- **Agent 系统**：Brain Agent、Check Agent、Task Agent 协作处理复杂任务
- **语音合成**：集成阿里云 CosyVoice TTS 服务
- **文件处理**：支持上传和处理多种文件格式（Word、PDF、Excel 等）
- **房间管理**：支持多会话房间管理
- **用户认证**：JWT Token 认证机制
- **性能测试**：集成 Locust 压力测试框架（**注意：Locust 测试功能还未调试好**）

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | FastAPI + SQLAlchemy + PostgreSQL |
| 前端 | Vue 3 + TypeScript + Vite |
| 部署 | Docker Compose + Nginx |
| 性能测试 | Locust |

## 目录结构

```
.
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── agents/          # Agent 实现
│   │   ├── routers/         # API 路由
│   │   ├── services/        # 业务服务
│   │   ├── tasks/           # 任务处理
│   │   └── main.py          # 入口文件
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env                 # 后端环境变量
├── frontend/                # 前端代码
│   ├── src/
│   └── package.json
├── docker-compose.yml       # Docker 编排配置
├── nginx.conf               # Nginx 配置
└── .env                     # 部署配置
```

## 快速开始

### 前置要求

- Docker & Docker Compose
- Node.js 18+（本地开发）
- Python 3.10+（本地开发）
- PostgreSQL 数据库

### 方式一：Docker 部署（推荐）

#### 1. 配置环境变量

```bash
# 复制并编辑部署配置
cp .env.example .env
```

编辑 `.env` 文件：

```ini
# 前端外部访问地址
FRONTEND_EXTERNAL_URL=http://your-server-ip:40000

# 前端端口
FRONTEND_PORT=40000

# Locust 代理路径
LOCUST_PROXY_PATH=/locust/
```

```bash
# 复制并编辑后端配置
cp backend/backend.env.example backend/.env
```

编辑 `backend/.env` 文件：

```ini
# 数据库连接
DATABASE_URL=postgresql://user:password@host:5432/database_name

# JWT 配置
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# TTS 语音配置（可选）
TTS_DEFAULT_VOICE_COSYVOICE_V35_FLASH=cosyvoice-v3.5-flash-vd-announcer-xxx
TTS_DEFAULT_VOICE_COSYVOICE_V35_PLUS=cosyvoice-v3.5-plus-vd-announcer-xxx
```

#### 2. 构建前端

```bash
cd frontend
npm install
npm run build
cd ..
```

#### 3. 启动服务

```bash
docker-compose up -d --build
```

#### 4. 访问应用

- 前端：`http://your-server-ip:40000`
- API 文档：`http://your-server-ip:40000/api/docs`
- Locust Web UI：`http://your-server-ip:40000/locust/`（**功能还未调试好**）

### 方式二：本地开发部署

#### 1. 配置后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp backend.env.example .env
# 编辑 .env 配置数据库等信息

# 启动后端
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. 配置前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

#### 3. 访问应用

- 前端：`http://localhost:5173`
- 后端 API：`http://localhost:8000`
- API 文档：`http://localhost:8000/docs`

## API 接口

| 路径 | 说明 |
|------|------|
| `POST /api/auth/register` | 用户注册 |
| `POST /api/auth/login` | 用户登录 |
| `GET /api/rooms` | 获取房间列表 |
| `POST /api/rooms` | 创建房间 |
| `POST /api/text/chat` | 文本聊天 |
| `POST /api/voice/transcribe` | 语音转文字 |
| `POST /api/voice/tts` | 文字转语音 |
| `POST /api/vision/analyze` | 图片分析 |
| `POST /api/agent-loop` | Agent 流式处理 |
| `GET /api/health` | 健康检查 |

完整 API 文档请访问 `/api/docs`。

## 环境变量说明

### 部署配置（`.env`）

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `FRONTEND_EXTERNAL_URL` | 前端外部访问地址 | `http://localhost:40000` |
| `FRONTEND_PORT` | 前端监听端口 | `40000` |
| `LOCUST_PROXY_PATH` | Locust 代理路径 | `/locust/` |

### 后端配置（`backend/.env`）

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | PostgreSQL 连接字符串 | 必填 |
| `SECRET_KEY` | JWT 密钥 | 必填 |
| `ALGORITHM` | JWT 算法 | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token 过期时间（分钟） | `1440` |
| `TTS_DEFAULT_VOICE_COSYVOICE_V35_FLASH` | TTS 快速模型语音 ID | 可选 |
| `TTS_DEFAULT_VOICE_COSYVOICE_V35_PLUS` | TTS 高质量模型语音 ID | 可选 |

## 性能测试

项目集成了 Locust 性能测试框架。

> ⚠️ **注意：Locust 测试功能还未调试好，可能无法正常使用。**

启动 Locust：

```bash
cd backend
locust -f app/tasks/tools/locust_tool.py
```

或通过 Docker 部署后访问 `/locust/` 路径。

## 常见问题

### 1. 数据库连接失败

检查 `DATABASE_URL` 格式是否正确：
```
postgresql://用户名:密码@主机:端口/数据库名
```

### 2. 前端无法连接后端

确保 Nginx 正确代理了 `/api/` 路径，或开发环境下配置了正确的代理。

### 3. Pydantic 验证错误

如果遇到 `Extra inputs are not permitted` 错误，说明 `.env` 中有未在 `Settings` 类中定义的变量。需要在 `backend/app/config.py` 中添加对应字段。

## License

MIT
