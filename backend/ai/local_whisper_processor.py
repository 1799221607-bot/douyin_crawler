import os
import torch
import whisper
from loguru import logger
from ai.base import BaseAIProcessor
from config import settings
import asyncio


class LocalWhisperProcessor(BaseAIProcessor):
    """
    本地 Whisper 处理器。
    直接在本地运行模型，无需 API Key，无需网络。
    """

    provider = "local_whisper"

    def __init__(self):
        self.model = None
        self._lock = asyncio.Lock() # 避免并发加载模型

    async def _load_model(self):
        """延迟加载模型"""
        if self.model is None:
            async with self._lock:
                if self.model is None:
                    model_size = os.getenv("LOCAL_WHISPER_MODEL", "base")
                    logger.info(f"[LocalWhisper] 正在加载模型: {model_size} (设备: {'cuda' if torch.cuda.is_available() else 'cpu'})...")
                    
                    # 在线程池中加载，避免阻塞事件循环
                    loop = asyncio.get_event_loop()
                    self.model = await loop.run_in_executor(None, lambda: whisper.load_model(model_size))
                    logger.info("[LocalWhisper] 模型加载完成")

    async def transcribe(self, audio_path: str) -> str:
        """本地转录"""
        try:
            await self._load_model()
            
            logger.info(f"[LocalWhisper] 正在本地转录: {audio_path}")
            
            # 在线程池中运行推理
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                lambda: self.model.transcribe(
                    audio_path, 
                    language="zh",
                    task="transcribe",
                    initial_prompt="以下是抖音视频的配音内容，包含科普、技术或新闻资讯。"
                )
            )
            
            text = result.get("text", "").strip()
            logger.info(f"[LocalWhisper] 转录完成，内容长度: {len(text)}")
            if len(text) > 0:
                logger.debug(f"[LocalWhisper] 转录文本预览: {text[:50]}...")
            return text
        except Exception:
            logger.exception("[LocalWhisper] 本地转录发生异常")
            return ""

    async def summarize(self, transcript: str, title: str = "") -> dict:
        """
        本地转录完成后，依然使用云端模型进行总结。
        """
        from ai.registry import ai_registry
        
        # 获取云端总结器
        try:
            # 优先尝试 nvidia，不行再试 openai
            try:
                proc = ai_registry.get("nvidia")
            except:
                proc = ai_registry.get("openai")
                
            return await proc.summarize(transcript, title=title)
        except Exception as e:
            logger.error(f"[LocalWhisper] 总结阶段失败: {e}")
            return {"summary": f"转录成功但总结失败: {str(e)}", "keywords": [], "category": "错误"}
