"""Anthropic Claude Provider"""

from langchain_anthropic import ChatAnthropic
from .base import BaseLLMProvider, LLMResponse


class AnthropicProvider(BaseLLMProvider):
    """封装 langchain_anthropic.ChatAnthropic，支持 Claude 系列模型"""

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        api_key: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        self._client = ChatAnthropic(
            model=model,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
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
