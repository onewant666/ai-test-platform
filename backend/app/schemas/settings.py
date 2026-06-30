"""系统设置响应模式"""

from pydantic import BaseModel


class LLMConfigResponse(BaseModel):
    """LLM 配置响应（不返回敏感 API Key 原文）"""
    provider: str
    api_base: str
    model: str
    temperature: float
    max_tokens: int
    openai_base_url: str
    anthropic_api_key_set: bool
    google_api_key_set: bool
    ollama_base_url: str


class ExecutorConfigResponse(BaseModel):
    browser: str
    headless: bool
    viewport_width: int
    viewport_height: int
    browser_timeout: int
    retry_count: int
    max_concurrency: int


class NotificationConfigResponse(BaseModel):
    email_enabled: bool
    email_recipients: list[str]
    dingtalk_enabled: bool
    dingtalk_webhook: str
    feishu_enabled: bool
    feishu_webhook: str
    notify_on_failure: bool
    notify_on_complete: bool


class SettingsResponse(BaseModel):
    llm: LLMConfigResponse
    executor: ExecutorConfigResponse
    notification: NotificationConfigResponse
