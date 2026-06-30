# AI 智能测试平台

**Web 用例自动执行 & 禅道集成** — AI 驱动的浏览器自动化测试平台

## 架构概览

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────┐
│   React 前端     │────▶│  FastAPI 后端     │────▶│   MySQL 数据库 │
│   (Ant Design)   │◀────│  (REST + WS)      │◀────│   Redis 缓存   │
└─────────────────┘     └────────┬─────────┘     └──────────────┘
                                 │
                        ┌────────▼─────────┐
                        │   Celery Worker   │
                        │  (异步任务执行)    │
                        └────────┬─────────┘
                                 │
                        ┌────────▼─────────┐
                        │  Playwright + LLM │
                        │  (AI 浏览器代理)   │
                        └────────┬─────────┘
                                 │
                        ┌────────▼─────────┐
                        │   禅道 API 集成    │
                        │ (用例同步/Bug回写) │
                        └──────────────────┘
```

## 核心功能

- **AI 驱动测试执行**: 使用 LLM 决策 + Playwright 浏览器自动化执行 Web 测试用例
- **自然语言生成步骤**: 输入中文描述，AI 自动转换为结构化测试步骤
- **自愈选择器**: 5级元素定位回退（CSS → 文本 → 角色 → 模糊属性 → LLM重分析 → XPath）
- **多LLM供应商**: 支持 DeepSeek / OpenAI / Anthropic Claude / Google Gemini / Ollama 本地模型
- **禅道深度集成**: 双向同步用例、自动创建 Bug、回写测试结果
- **实时执行监控**: WebSocket 实时推送执行状态，可视化步骤进度
- **测试报告**: 通过率仪表盘、执行步骤详情、历史趋势分析

## 快速开始

### 前置要求

- Docker & Docker Compose
- Python 3.12+（本地开发）
- Node.js 22+（前端开发）

### Docker 一键部署

```bash
cd backend/docker
cp .env.example .env
# 编辑 .env 填入 LLM_API_KEY
docker compose up -d
```

访问:
- 前端: http://localhost
- API 文档: http://localhost:8000/docs
- 默认账号: admin / 123456

### 本地开发

**后端:**
```bash
cd backend
pip install -r requirements.txt
# 确保 MySQL 和 Redis 已启动
uvicorn app.main:app --reload
```

**前端:**
```bash
cd frontend
npm install
npm run dev
```

**Celery Worker:**
```bash
cd backend
celery -A app.celery_app worker --loglevel=info
```

## API 概览

| 方法 | 端点 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/v1/auth/login` | JWT 登录 | 否 |
| GET | `/api/v1/auth/me` | 当前用户信息 | JWT |
| GET | `/api/v1/testcases` | 用例列表 | JWT |
| POST | `/api/v1/testcases` | 创建用例 | JWT |
| PUT | `/api/v1/testcases/{id}` | 更新用例 | JWT |
| DELETE | `/api/v1/testcases/{id}` | 删除用例 | JWT |
| GET | `/api/v1/testplans` | 测试计划列表 | JWT |
| POST | `/api/v1/testplans` | 创建测试计划 | JWT |
| POST | `/api/v1/testplans/{id}/run` | 启动执行 | JWT |
| GET | `/api/v1/executions` | 执行记录列表 | JWT |
| GET | `/api/v1/projects` | 项目列表 | JWT |
| GET | `/api/v1/reports` | 测试报告列表 | JWT |
| POST | `/api/v1/ai/chat` | AI 对话 | JWT |
| POST | `/api/v1/ai/generate-steps` | AI 生成步骤 | JWT |
| GET | `/api/v1/zentao/products` | 禅道产品列表 | 否 |
| POST | `/api/v1/zentao/sync/cases` | 同步禅道用例 | JWT |
| POST | `/api/v1/zentao/report-bug` | 创建禅道 Bug | JWT |
| GET | `/api/v1/settings` | 系统设置 | JWT |
| PUT | `/api/v1/settings/llm` | 更新 LLM 配置 | JWT |
| WS | `/ws/executions/{id}` | 实时执行状态 | -

完整 API 文档请访问 Swagger UI: `/docs`

## 配置参考

### LLM 配置

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `LLM_PROVIDER` | `deepseek` | deepseek / openai / anthropic / gemini / ollama |
| `LLM_API_KEY` | - | API 密钥（DeepSeek / OpenAI 共用） |
| `LLM_API_BASE` | `https://api.deepseek.com` | API 地址 |
| `LLM_MODEL` | `deepseek-chat` | 模型名称 |
| `LLM_TEMPERATURE` | `0.7` | 生成温度 (0-2) |
| `LLM_MAX_TOKENS` | `4096` | 最大 Token 数 |
| `LLM_ANTHROPIC_API_KEY` | - | Anthropic API Key（可选） |
| `LLM_GOOGLE_API_KEY` | - | Google Gemini API Key（可选） |

### 数据库 & 缓存

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `MYSQL_HOST` | `localhost` | MySQL 地址 |
| `MYSQL_PORT` | `3306` | MySQL 端口 |
| `MYSQL_USER` | `root` | MySQL 用户 |
| `MYSQL_PASSWORD` | - | MySQL 密码 |
| `MYSQL_DATABASE` | `ai_test_platform` | 数据库名 |
| `REDIS_HOST` | `localhost` | Redis 地址 |
| `REDIS_PORT` | `6379` | Redis 端口 |

### 禅道集成

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `ZENTAO_BASE_URL` | - | 禅道系统地址 |
| `ZENTAO_ACCOUNT` | `admin` | 禅道账号 |
| `ZENTAO_PASSWORD` | - | 禅道密码 |
| `ZENTAO_APACHE_AUTH_USER` | - | Apache 认证用户（可选） |
| `ZENTAO_APACHE_AUTH_PASS` | - | Apache 认证密码（可选） |

## 技术栈

- **后端**: Python 3.12+ / FastAPI / SQLAlchemy / Celery / Playwright
- **前端**: React 19 / TypeScript / Ant Design 6 / ECharts / Zustand
- **AI**: LangChain / DeepSeek / OpenAI / Anthropic / Gemini / Ollama
- **基础设施**: MySQL 8.0 / Redis 7 / Docker / Nginx

## 项目结构

```
├── backend/
│   ├── app/
│   │   ├── api/v1/        # REST API 路由
│   │   ├── engine/        # 浏览器代理 & 自愈引擎
│   │   ├── llm/           # LLM 供应商适配层
│   │   ├── models/        # SQLAlchemy 数据模型
│   │   ├── schemas/       # Pydantic 请求/响应模式
│   │   ├── services/      # 业务逻辑层
│   │   ├── adapters/      # 禅道客户端 & 同步
│   │   └── tasks/         # Celery 异步任务
│   ├── docker/            # Docker Compose 配置
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── pages/         # 页面组件
    │   ├── services/      # API 调用层
    │   ├── stores/        # 状态管理 (Zustand)
    │   └── types/         # TypeScript 类型
    └── package.json
```
