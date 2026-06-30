"""AI 相关响应模式"""

from pydantic import BaseModel


class ChatResponse(BaseModel):
    """AI 对话响应"""
    reply: str


class GenerateStepsResponse(BaseModel):
    """AI 生成测试步骤响应"""
    steps: list[dict]


class AnalyzePageResponse(BaseModel):
    """AI 页面分析响应"""
    analysis: str


class ChatRequest(BaseModel):
    """AI 对话请求"""
    message: str
    conversation_id: int | None = None


class GenerateStepsRequest(BaseModel):
    """AI 生成步骤请求"""
    description: str


class AnalyzePageRequest(BaseModel):
    """AI 页面分析请求"""
    url: str
