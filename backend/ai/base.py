from abc import ABC, abstractmethod


class BaseAIProcessor(ABC):
    """
    AI 处理器插件基类。
    支持多模型后端：OpenAI、Ollama、本地 Whisper 等。
    新增模型只需继承此类，在 registry.py 中注册即可。
    """

    @property
    @abstractmethod
    def provider(self) -> str:
        """
        提供商标识，全局唯一。
        例: 'openai' | 'ollama' | 'local_whisper'
        """
        pass

    @abstractmethod
    async def transcribe(self, audio_path: str) -> str:
        """
        语音/视频 → 文字转录。
        Args:
            audio_path: 本地音频/视频文件路径
        Returns:
            转录文本
        """
        pass

    @abstractmethod
    async def summarize(self, transcript: str, title: str = "") -> dict:
        """
        文字 → AI 总结。
        Args:
            transcript: 转录文本
            title: 视频标题（作为上下文）
        Returns:
            {
                'summary': str,    # 内容总结
                'keywords': list,  # 关键词列表
                'category': str,   # 内容分类
            }
        """
        pass

    async def process(self, video_path: str, title: str = "") -> dict:
        """
        完整处理流程：转录 → 总结（模板方法，子类一般不需要重写）
        """
        transcript = await self.transcribe(video_path)
        result = await self.summarize(transcript, title=title)
        result["transcript"] = transcript
        result["model"] = self.provider
        return result
