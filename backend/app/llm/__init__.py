"""LLM Provider 工厂 — 统一入口

用法:
    from app.llm import get_llm

    llm = get_llm()
    # 同步调用（Playwright 同步上下文）
    resp = llm.invoke([{"role": "user", "content": "你好"}])
    # 异步调用（FastAPI 路由）
    resp = await llm.ainvoke([{"role": "user", "content": "你好"}])
"""

import logging
from app.config import get_settings
from app.llm.base import BaseLLMProvider

logger = logging.getLogger(__name__)

# 供应商路由表: provider_key → (provider_class, module_path)
_PROVIDER_REGISTRY = {
    "deepseek": ("OpenAICompatProvider", "openai_compat"),
    "openai":   ("OpenAICompatProvider", "openai_compat"),
    "ollama":   ("OpenAICompatProvider", "openai_compat"),
    "anthropic": ("AnthropicProvider", "anthropic_provider"),
    "gemini":   ("GoogleProvider", "google_provider"),
}


def get_llm() -> BaseLLMProvider:
    """根据 Settings 中的 llm_provider 配置，返回对应的 LLM Provider 实例。

    支持:
    - deepseek  → DeepSeek (api.deepseek.com)
    - openai    → OpenAI (api.openai.com/v1)
    - ollama    → Ollama 本地模型 (localhost:11434/v1)
    - anthropic → Anthropic Claude
    - gemini    → Google Gemini

    Raises:
        ValueError: 未知的 provider 名称
        ImportError: 对应的 langchain 依赖未安装
    """
    settings = get_settings()
    provider_name = settings.llm_provider.lower().strip()

    if provider_name not in _PROVIDER_REGISTRY:
        supported = ", ".join(_PROVIDER_REGISTRY.keys())
        raise ValueError(
            f"不支持的 LLM Provider: '{provider_name}'。支持的提供商: {supported}"
        )

    class_name, module_path = _PROVIDER_REGISTRY[provider_name]

    # ── OpenAI 兼容协议供应商 (deepseek / openai / ollama) ──
    if provider_name in ("deepseek", "openai", "ollama"):
        from app.llm.openai_compat import OpenAICompatProvider

        # 根据 provider 选择默认 base_url
        default_base_urls = {
            "deepseek": "https://api.deepseek.com",
            "openai":   "https://api.openai.com/v1",
            "ollama":   "http://localhost:11434/v1",
        }

        # ollama 允许无 api_key
        api_key = settings.llm_api_key
        if provider_name == "ollama" and not api_key:
            api_key = "ollama"  # ollama 不需要真实 key

        return OpenAICompatProvider(
            model=settings.llm_model,
            api_key=api_key,
            base_url=settings.llm_api_base or default_base_urls[provider_name],
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
        )

    # ── Anthropic Claude ──
    elif provider_name == "anthropic":
        from app.llm.anthropic_provider import AnthropicProvider

        api_key = settings.llm_anthropic_api_key or settings.llm_api_key
        return AnthropicProvider(
            model=settings.llm_model or "claude-sonnet-4-20250514",
            api_key=api_key,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
        )

    # ── Google Gemini ──
    elif provider_name == "gemini":
        from app.llm.google_provider import GoogleProvider

        api_key = settings.llm_google_api_key or settings.llm_api_key
        return GoogleProvider(
            model=settings.llm_model or "gemini-2.5-flash",
            api_key=api_key,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
        )

    # 不应该到达这里
    raise ValueError(f"Provider '{provider_name}' 已注册但未实现")
