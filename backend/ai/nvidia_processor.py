from ai.openai_processor import OpenAIProcessor
from loguru import logger

class NvidiaProcessor(OpenAIProcessor):
    """
    NVIDIA NIM 处理器。
    API 完全兼容 OpenAI SDK。
    """
    provider = "nvidia"

    async def transcribe(self, audio_path: str) -> str:
        """NVIDIA NIM 的转录实现"""
        logger.info(f"[NvidiaProcessor] 正在使用 NVIDIA 接口转录音频...")
        # 直接复用父类经过代理加固的 client 和 transcribe 逻辑
        return await super().transcribe(audio_path)
