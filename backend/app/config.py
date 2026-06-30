"""应用配置 — 基于 pydantic-settings 加载环境变量"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── 数据库 ──
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = "root123"
    mysql_database: str = "ai_test_platform"

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            f"?charset=utf8mb4"
        )

    # ── Redis ──
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # ── JWT ──
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 小时

    # ── Zentao ──
    zentao_base_url: str = "http://zentao.example.com"
    zentao_apache_auth_user: str = ""
    zentao_apache_auth_pass: str = ""
    zentao_account: str = "admin"
    zentao_password: str = ""

    # ── LLM ──
    llm_provider: str = "deepseek"              # deepseek | openai | anthropic | gemini | ollama
    llm_api_key: str = ""                       # 通用 API Key（DeepSeek / OpenAI 共用）
    llm_api_base: str = "https://api.deepseek.com"  # OpenAI 兼容 API 地址
    llm_model: str = "deepseek-chat"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4096
    # 各供应商独立配置（可选，为空时回退到 llm_api_key）
    llm_openai_base_url: str = "https://api.openai.com/v1"
    llm_anthropic_api_key: str = ""             # Anthropic API Key (sk-ant-...)
    llm_google_api_key: str = ""                # Google AI API Key
    llm_ollama_base_url: str = "http://localhost:11434/v1"

    # ── Browser ──
    playwright_headless: bool = True
    playwright_browser: str = "chromium"
    max_concurrent_executions: int = 4

    # ── Upload ──
    upload_dir: str = "./uploads"
    max_upload_size: int = 10 * 1024 * 1024  # 10 MB

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
