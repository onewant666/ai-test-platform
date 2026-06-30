"""FastAPI 主入口"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # 启动时：创建表 & 初始化管理员
    Base.metadata.create_all(bind=engine)
    from app.database import SessionLocal
    from app.services.auth_service import create_initial_admin
    db = SessionLocal()
    try:
        create_initial_admin(db)
    finally:
        db.close()
    # 确保上传目录存在
    os.makedirs(settings.upload_dir, exist_ok=True)
    yield
    # 关闭时清理资源
    pass


app = FastAPI(
    title="AI 智能测试平台 API",
    description="""
## AI-Powered Web Test Automation Platform

Web 用例自动执行 & 禅道集成 — 后端服务

### 核心能力
- **AI 浏览器测试**: 使用 LLM + Playwright 自动执行 Web 测试用例，支持5级自愈选择器
- **禅道集成**: 双向同步用例、自动创建 Bug、回写测试结果
- **多 LLM 供应商**: DeepSeek / OpenAI / Anthropic Claude / Google Gemini / Ollama
- **实时监控**: WebSocket 实时推送执行状态和步骤进度

### 认证
除登录接口外，所有 API 需在 Header 中携带 JWT Token:
```
Authorization: Bearer <token>
```

### 响应格式
所有响应遵循统一格式:
```json
{"code": 200, "message": "success", "data": {...}}
```
分页列表:
```json
{"items": [...], "total": 100, "page": 1, "limit": 20, "total_pages": 5}
```
    """,
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "认证", "description": "JWT 登录认证、令牌刷新、用户信息"},
        {"name": "用例管理", "description": "测试用例 CRUD、AI 辅助生成测试步骤"},
        {"name": "测试计划", "description": "测试计划管理、启动执行、执行记录查询"},
        {"name": "项目管理", "description": "项目 CRUD 操作"},
        {"name": "报告", "description": "测试执行报告和趋势分析"},
        {"name": "AI 助手", "description": "AI 对话、自然语言生成步骤、页面元素分析"},
        {"name": "禅道集成", "description": "禅道连接测试、用例同步、Bug 创建、结果回写"},
        {"name": "系统设置", "description": "LLM 配置、执行器配置、通知设置"},
    ],
)

# CORS — 允许前端跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 注册路由 ──
from app.api.v1 import auth, testcases, testplans, reports, zentao, ai, ws, projects
from app.api.v1 import settings as settings_api  # 避免与 config settings 冲突

app.include_router(auth.router, prefix="/api/v1")
app.include_router(testcases.router, prefix="/api/v1")
app.include_router(testplans.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(zentao.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(settings_api.router, prefix="/api/v1")
app.include_router(ws.router)  # WebSocket 路由，不使用 /api/v1 前缀


@app.get("/")
def root():
    return {
        "name": "AI 智能测试平台",
        "version": "0.1.0",
        "docs": "/docs",
        "status": "running",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
