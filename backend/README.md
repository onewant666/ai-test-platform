# Backend — AI 智能测试平台

FastAPI 后端服务，提供 REST API + WebSocket 实时推送。

## 开发环境

### 环境准备

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium
```

### 数据库

确保 MySQL 8.0+ 和 Redis 7+ 运行中:

```bash
# 使用 Docker 快速启动
cd backend/docker
docker compose up -d mysql redis
```

数据库表由 FastAPI 启动时自动创建（`Base.metadata.create_all`），并自动初始化管理员账号 `admin/123456`。

### 启动服务

```bash
# FastAPI (开发模式)
uvicorn app.main:app --reload --port 8000

# Celery Worker (另一个终端)
celery -A app.celery_app worker --loglevel=info --concurrency=2
```

### API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## 目录结构

```
backend/
├── app/
│   ├── main.py                 # FastAPI 入口 & 生命周期
│   ├── config.py               # pydantic-settings 配置
│   ├── database.py             # SQLAlchemy 会话管理
│   ├── celery_app.py           # Celery 配置
│   │
│   ├── api/
│   │   ├── deps.py             # 依赖注入 (JWT 认证)
│   │   └── v1/
│   │       ├── auth.py         # 认证 API
│   │       ├── testcases.py    # 用例 CRUD API
│   │       ├── testplans.py    # 测试计划 & 执行 API
│   │       ├── projects.py     # 项目 API
│   │       ├── reports.py      # 报告 API
│   │       ├── ai.py           # AI 助手 API
│   │       ├── zentao.py       # 禅道集成 API
│   │       ├── settings.py     # 系统设置 API
│   │       └── ws.py           # WebSocket 推送
│   │
│   ├── engine/
│   │   ├── browser_agent.py    # AI 浏览器执行代理
│   │   ├── self_healing.py     # 自愈选择器策略
│   │   └── step_parser.py      # 自然语言→步骤 解析器
│   │
│   ├── llm/
│   │   ├── __init__.py         # LLM 工厂
│   │   ├── base.py             # 抽象基类
│   │   ├── openai_compat.py    # OpenAI / DeepSeek / Ollama
│   │   ├── anthropic_provider.py  # Anthropic Claude
│   │   └── google_provider.py  # Google Gemini
│   │
│   ├── models/                 # SQLAlchemy ORM 模型
│   ├── schemas/                # Pydantic 请求/响应模式
│   ├── services/               # 业务逻辑
│   ├── adapters/zentao/        # 禅道 REST 客户端
│   ├── tasks/                  # Celery 任务
│   └── utils/                  # 工具函数
│
├── docker/
│   ├── docker-compose.yml      # 完整服务编排
│   ├── Dockerfile              # 后端镜像
│   ├── nginx.conf              # 前端 Nginx 配置
│   └── .env.example           # 环境变量模板
│
└── requirements.txt
```

## LLM 供应商切换

在系统设置页面或通过 API 切换:

```bash
# 切换到 OpenAI
curl -X PUT http://localhost:8000/api/v1/settings/llm \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"provider":"openai","api_key":"sk-xxx","model":"gpt-4o","api_base":"https://api.openai.com/v1"}'

# 切换到本地 Ollama
curl -X PUT http://localhost:8000/api/v1/settings/llm \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"provider":"ollama","model":"qwen2.5:7b","api_base":"http://localhost:11434/v1"}'
```

## 自愈机制

浏览器代理执行测试时，自动使用5级选择器回退:

1. CSS 选择器（LLM 提供）
2. 文本选择器（Playwright text=、get_by_text）
3. 角色选择器（get_by_role: button / link / textbox）
4. 模糊属性（aria-label / placeholder / title）
5. LLM 重新分析（发送页面 HTML 请求新选择器）
6. XPath 兜底

每步最多重试 3 次，失败时自动截图保存到 `uploads/screenshots/`。
