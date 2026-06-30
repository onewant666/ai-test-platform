"""系统设置 API"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.schemas.common import APIResponse
from app.schemas.settings import SettingsResponse, LLMConfigResponse, ExecutorConfigResponse, NotificationConfigResponse
from app.api.deps import get_current_user
from app.models.user import User
from app.config import get_settings

router = APIRouter(prefix="/settings", tags=["系统设置"])


# ── LLM 配置 ──
class LLMConfigSchema(BaseModel):
    provider: str = "deepseek"
    api_key: str = ""
    api_base: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"
    temperature: float = 0.7
    max_tokens: int = 4096
    openai_base_url: str = "https://api.openai.com/v1"
    anthropic_api_key: str = ""
    google_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434/v1"


# ── 执行器配置 ──
class ExecutorConfigSchema(BaseModel):
    browser: str = "chromium"
    headless: bool = True
    viewport_width: int = 1920
    viewport_height: int = 1080
    browser_timeout: int = 30
    retry_count: int = 2
    max_concurrency: int = 4


# ── 通知配置 ──
class NotificationConfigSchema(BaseModel):
    email_enabled: bool = True
    email_recipients: list[str] = []
    dingtalk_enabled: bool = False
    dingtalk_webhook: str = ""
    feishu_enabled: bool = False
    feishu_webhook: str = ""
    notify_on_failure: bool = True
    notify_on_complete: bool = True


@router.get("", response_model=APIResponse[SettingsResponse])
def get_all_settings(_: User = Depends(get_current_user)):
    """
    获取所有系统设置。

    返回 LLM 配置、执行器配置、通知配置三部分。
    LLM API Key 仅返回是否已设置（布尔值），不返回原文。
    """
    s = get_settings()
    return APIResponse(data={
        "llm": {
            "provider": s.llm_provider,
            "api_base": s.llm_api_base,
            "model": s.llm_model,
            "temperature": s.llm_temperature,
            "max_tokens": s.llm_max_tokens,
            "openai_base_url": s.llm_openai_base_url,
            "anthropic_api_key_set": bool(s.llm_anthropic_api_key),
            "google_api_key_set": bool(s.llm_google_api_key),
            "ollama_base_url": s.llm_ollama_base_url,
        },
        "executor": {
            "browser": s.playwright_browser,
            "headless": s.playwright_headless,
            "viewport_width": 1920,
            "viewport_height": 1080,
            "browser_timeout": 30,
            "retry_count": 2,
            "max_concurrency": s.max_concurrent_executions,
        },
        "notification": {
            "email_enabled": True,
            "email_recipients": [],
            "dingtalk_enabled": False,
            "dingtalk_webhook": "",
            "feishu_enabled": False,
            "feishu_webhook": "",
            "notify_on_failure": True,
            "notify_on_complete": True,
        },
    })


@router.put("/llm")
def update_llm_config(
    config: LLMConfigSchema,
    _: User = Depends(get_current_user),
):
    """更新 LLM 配置（运行时生效，不持久化到 .env）"""
    s = get_settings()
    s.llm_provider = config.provider
    s.llm_api_key = config.api_key
    s.llm_api_base = config.api_base
    s.llm_model = config.model
    s.llm_temperature = config.temperature
    s.llm_max_tokens = config.max_tokens
    s.llm_openai_base_url = config.openai_base_url
    if config.anthropic_api_key:
        s.llm_anthropic_api_key = config.anthropic_api_key
    if config.google_api_key:
        s.llm_google_api_key = config.google_api_key
    s.llm_ollama_base_url = config.ollama_base_url
    return APIResponse(data=None, message="LLM 配置已更新（运行时生效）")


@router.put("/executor")
def update_executor_config(
    config: ExecutorConfigSchema,
    _: User = Depends(get_current_user),
):
    """更新执行器配置"""
    s = get_settings()
    s.playwright_browser = config.browser
    s.playwright_headless = config.headless
    s.max_concurrent_executions = config.max_concurrency
    return APIResponse(data=None, message="执行器配置已更新（运行时生效）")


@router.put("/notification")
def update_notification_config(
    config: NotificationConfigSchema,
    _: User = Depends(get_current_user),
):
    """更新通知配置（运行时生效，不持久化）"""
    return APIResponse(data=None, message="通知配置已更新（运行时生效）")
