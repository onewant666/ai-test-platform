"""OpenAI 兼容协议 Provider — 支持 OpenAI / DeepSeek / Ollama 等"""

from typing import Any
from langchain_openai import ChatOpenAI
from .base import BaseLLMProvider, LLMResponse


class OpenAICompatProvider(BaseLLMProvider):
    """
    封装 langchain_openai.ChatOpenAI，兼容所有实现 OpenAI API 协议的供应商:
    - OpenAI (api.openai.com)
    - DeepSeek (api.deepseek.com)
    - Ollama (localhost:11434)
    - 以及其他自定义端点
    """

    def __init__(
        self,
        model: str,
        api_key: str,
        base_url: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        kwargs: dict[str, Any] = {
            "model": model,
            "api_key": api_key,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if base_url:
            kwargs["base_url"] = base_url
        self._client = ChatOpenAI(**kwargs)

    def invoke(self, messages: list[dict[str, str]]) -> LLMResponse:
        resp = self._client.invoke(messages)
        return LLMResponse(content=str(resp.content))

    async def ainvoke(self, messages: list[dict[str, str]]) -> LLMResponse:
        resp = await self._client.ainvoke(messages)
        return LLMResponse(content=str(resp.content))

    @property
    def raw_client(self):
        return self._client
