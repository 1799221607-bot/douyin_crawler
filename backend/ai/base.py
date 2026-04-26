import os
import subprocess
import tempfile
from abc import ABC, abstractmethod
from loguru import logger


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

    async def _extract_audio(self, video_path: str) -> str:
        """从视频中提取音频并转换为小型 MP3"""
        temp_audio = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        temp_audio.close()
        output_path = temp_audio.name

        try:
            # 使用 ffmpeg 提取音频，单声道，低比特率以减小体积
            cmd = [
                "ffmpeg", "-y", "-i", video_path,
                "-vn", "-ar", "16000", "-ac", "1", "-ab", "32k", "-f", "mp3",
                output_path
            ]
            logger.info(f"[AI] 正在提取音频: {video_path} -> {output_path}")
            
            # 使用 subprocess.run 同步调用，通常很快
            # 增加 encoding 和 errors 处理 Windows 上的编码问题
            process = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                encoding='utf-8', 
                errors='ignore'
            )
            if process.returncode != 0:
                logger.error(f"[AI] ffmpeg 提取音频失败: {process.stderr}")
                return video_path # 失败则回退到原始路径
            
            return output_path
        except Exception as e:
            logger.error(f"[AI] 提取音频异常: {e}")
            return video_path

    async def process(self, video_path: str, title: str = "") -> dict:
        """
        完整处理流程：提取音频 → 转录 → 总结
        """
        # 1. 尝试提取音频以减小上传压力
        target_path = video_path
        temp_audio_path = None
        
        ext = os.path.splitext(video_path)[1].lower()
        if ext in ['.mp4', '.mkv', '.flv', '.mov', '.avi']:
            temp_audio_path = await self._extract_audio(video_path)
            if temp_audio_path != video_path:
                target_path = temp_audio_path
        
        try:
            # 2. 转录
            transcript = await self.transcribe(target_path)
            
            # 3. 总结
            result = await self.summarize(transcript, title=title)
            result["transcript"] = transcript
            result["model"] = self.provider
            return result
        finally:
            # 4. 清理临时音频文件
            if temp_audio_path and temp_audio_path != video_path and os.path.exists(temp_audio_path):
                try:
                    os.remove(temp_audio_path)
                    logger.debug(f"[AI] 已清理临时音频: {temp_audio_path}")
                except:
                    pass
