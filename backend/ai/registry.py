from ai.base import BaseAIProcessor
from ai.openai_processor import OpenAIProcessor
from ai.ollama_processor import OllamaProcessor
from ai.glm_processor import GLMProcessor
from ai.nvidia_processor import NvidiaProcessor
from ai.local_whisper_processor import LocalWhisperProcessor
from config import settings


class AIProcessorRegistry:
    """AI 处理器插件注册表"""

    def __init__(self):
        self._registry: dict[str, BaseAIProcessor] = {}

    def register(self, processor: BaseAIProcessor):
        self._registry[processor.provider] = processor

    def get(self, provider: str) -> BaseAIProcessor:
        if provider not in self._registry:
            raise ValueError(f"未注册的 AI 处理器: {provider}")
        return self._registry[provider]

    def get_active(self) -> BaseAIProcessor:
        """获取当前配置的活跃处理器"""
        return self.get(settings.ai_provider)

    def list_providers(self) -> list[str]:
        return list(self._registry.keys())


# 全局单例
ai_registry = AIProcessorRegistry()
ai_registry.register(OpenAIProcessor())
ai_registry.register(OllamaProcessor())
ai_registry.register(GLMProcessor())
ai_registry.register(NvidiaProcessor())
ai_registry.register(LocalWhisperProcessor())
