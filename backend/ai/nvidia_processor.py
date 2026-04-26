from ai.openai_processor import OpenAIProcessor
from config import settings

class NvidiaProcessor(OpenAIProcessor):
    """
    NVIDIA NIM 处理器。
    API 完全兼容 OpenAI SDK。
    """
    provider = "nvidia"

    def __init__(self):
        super().__init__()

    async def transcribe(self, audio_path: str) -> str:
        # NVIDIA NIM 目前主要侧重于推理模型
        # 转录建议使用 OpenAI 或本地 Whisper，或者 NVIDIA 特有的 Riva 服务
        return await super().transcribe(audio_path)
