from ai.openai_processor import OpenAIProcessor
from config import settings

class GLMProcessor(OpenAIProcessor):
    """
    智谱 AI (GLM) 处理器。
    继承自 OpenAIProcessor，因为其 API 完全兼容 OpenAI SDK。
    """
    provider = "glm"

    def __init__(self):
        super().__init__()
        # 如果有 GLM 特有的初始化逻辑可以写在这里
        pass

    async def transcribe(self, audio_path: str) -> str:
        # 注意：智谱目前主要提供文本/视觉模型，转录（Whisper）可能仍需配合 OpenAI 或本地 Whisper
        # 这里默认尝试使用其兼容接口，或者提示不支持
        return await super().transcribe(audio_path)
