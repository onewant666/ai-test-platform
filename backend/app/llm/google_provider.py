"""Google Gemini Provider"""

from langchain_google_genai import ChatGoogleGenerativeAI
from .base import BaseLLMProvider, LLMResponse


class GoogleProvider(BaseLLMProvider):
    """封装 langchain_google_genai.ChatGoogleGenerativeAI，支持 Gemini 系列模型"""

    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        api_key: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        self._client = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=api_key,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

    def invoke(self, messages: list[dict[str, str]]) -> LLMResponse:
        resp = self._client.invoke(messages)
        return LLMResponse(content=str(resp.content))

    async def ainvoke(self, messages: list[dict[str, str]]) -> LLMResponse:
        resp = await self._client.ainvoke(messages)
        return LLMResponse(content=str(resp.content))

    @property
    def raw_client(self):
        return self._client
