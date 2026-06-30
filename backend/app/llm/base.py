"""LLM Provider 抽象基类"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """统一的 LLM 响应包装"""
    content: str


class BaseLLMProvider(ABC):
    """
    所有 LLM Provider 的抽象基类。
    统一支持同步 invoke() 和异步 ainvoke() 两种调用方式。
    """

    @abstractmethod
    def invoke(self, messages: list[dict[str, str]]) -> LLMResponse:
        """同步调用 LLM（用于 Playwright 同步上下文中）"""
        ...

    @abstractmethod
    async def ainvoke(self, messages: list[dict[str, str]]) -> LLMResponse:
        """异步调用 LLM（用于 FastAPI 异步路由中）"""
        ...

    @property
    @abstractmethod
    def raw_client(self):
        """返回底层 LangChain 兼容的客户端实例（用于 browser-use Agent 等需要原始客户端的场景）"""
        ...
