"""AI 相关 API"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.schemas.common import APIResponse
from app.schemas.ai import ChatResponse, GenerateStepsResponse, AnalyzePageResponse
from app.api.deps import get_current_user
from app.models.user import User
from app.engine.step_parser import parse_description_to_steps

router = APIRouter(prefix="/ai", tags=["AI 助手"])


class ChatReq(BaseModel):
    message: str
    conversation_id: int | None = None


class GenerateStepsReq(BaseModel):
    description: str


class AnalyzePageReq(BaseModel):
    url: str


@router.post("/chat", response_model=APIResponse[ChatResponse])
async def ai_chat(
    req: ChatReq,
    current_user: User = Depends(get_current_user),
):
    """
    AI 对话接口。

    向 LLM 发送消息，获取 AI 测试助手的回复。
    支持测试用例生成建议、测试策略咨询、错误分析等。

    - **message**: 用户输入的自然语言消息
    - **conversation_id**: 可选，多轮对话 ID
    """
    try:
        from app.llm import get_llm

        llm = get_llm()

        response = await llm.ainvoke([
            {"role": "system", "content": "你是一个 AI 测试助手，帮助用户生成测试用例、分析测试结果、提供测试建议。请用中文回答。"},
            {"role": "user", "content": req.message},
        ])

        return APIResponse(data=ChatResponse(reply=response.content))

    except ImportError:
        return APIResponse(data=ChatResponse(
            reply=f"已收到你的消息：「{req.message}」\n\n（LLM 未配置，这是一个模拟回复。请在后端设置 LLM API Key 以启用 AI 功能。）"
        ))
    except Exception as e:
        return APIResponse(data=ChatResponse(reply=f"AI 服务暂时不可用: {str(e)}"))


@router.post("/generate-steps", response_model=APIResponse[GenerateStepsResponse])
async def generate_steps(
    req: GenerateStepsReq,
    _: User = Depends(get_current_user),
):
    """
    AI 生成测试步骤。

    输入自然语言测试描述，AI 自动转换为结构化的测试步骤 JSON 数组。
    每个步骤包含 seq、action、target、value、expected 字段。
    支持的操作: navigate, click, input, select, hover, scroll, wait, assert, ai_action。

    - **description**: 自然语言测试描述，如 "打开百度首页，搜索AI测试，验证结果"
    """
    steps = await parse_description_to_steps(req.description)
    return APIResponse(data=GenerateStepsResponse(steps=steps))


@router.post("/analyze-page", response_model=APIResponse[AnalyzePageResponse])
async def analyze_page(
    req: AnalyzePageReq,
    _: User = Depends(get_current_user),
):
    """
    AI 分析页面可测试元素。

    使用 browser-use 智能代理打开目标页面，分析所有可交互元素
    （输入框、按钮、链接、下拉菜单等），以 JSON 格式列出每个元素的
    类型、文本/标签和建议的测试用例。

    - **url**: 要分析的目标页面 URL
    """
    try:
        from browser_use import Agent
        from app.llm import get_llm

        llm_provider = get_llm()

        agent = Agent(
            task=f"打开页面 {req.url}，分析页面上的所有可交互元素（输入框、按钮、链接、下拉菜单等），以 JSON 格式列出每个元素的类型、文本/标签和建议的测试用例。",
            llm=llm_provider.raw_client,
        )
        result = await agent.run()
        return APIResponse(data=AnalyzePageResponse(analysis=str(result)))

    except ImportError:
        return APIResponse(data=AnalyzePageResponse(analysis="browser-use 未安装，无法进行页面分析"))
    except Exception as e:
        return APIResponse(data=AnalyzePageResponse(analysis=f"页面分析失败: {str(e)}"))
