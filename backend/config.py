from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import yaml
import os


class Settings(BaseSettings):
    # App
    app_name: str = "抖音采集平台"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str = "sqlite+aiosqlite:///./douyin_crawler.db"

    # Security
    secret_key: str = "your-secret-key-here-please-change-it"
    access_token_expire_minutes: int = 60 * 24  # 默认 24 小时

    # Redis (for Celery)
    redis_url: str = "redis://localhost:6379/0"

    # Download
    download_dir: str = "./videos"
    proxy: Optional[str] = None
    collector_proxy_enabled: bool = False  # 默认采集抖音不走代理
    cookie: str = ""

    # OpenAI
    openai_api_key: Optional[str] = None
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"
    whisper_model: str = "whisper-1"
    whisper_base_url: Optional[str] = None

    # Ollama (fallback)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"

    # AI Provider: "openai" | "ollama"
    ai_provider: str = "openai"

    # CORS
    cors_origins: list[str] = [
        "http://localhost:5173", 
        "http://localhost:3000",
        "https://www.douyin.com",
        "https://douyin.com"
    ]

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), "..", ".env")
        env_file_encoding = "utf-8"


def load_yaml_config() -> dict:
    """加载 config.yaml 中的博主列表等配置"""
    config_path = os.path.join(os.path.dirname(__file__), "..", "config.yaml")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


settings = Settings()
