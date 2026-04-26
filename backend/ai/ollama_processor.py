import json
import httpx
from loguru import logger
from ai.base import BaseAIProcessor
from config import settings


class OllamaProcessor(BaseAIProcessor):
    """
    本地 Ollama 处理器（OpenAI API 兼容模式）。
    转录：需要本地 Whisper（whisper.cpp 或 faster-whisper）
    总结：使用 Ollama 运行本地模型（如 llama3, qwen2 等）
    """

    provider = "ollama"

    async def transcribe(self, audio_path: str) -> str:
        """
        本地 Whisper 转录。
        需要安装 faster-whisper 或 whisper.cpp。
        TODO: 集成 faster-whisper 库实现本地转录
        """
        try:
            # 方案：使用 faster-whisper（安装: pip install faster-whisper）
            # from faster_whisper import WhisperModel
            # model = WhisperModel("medium", device="cpu")
            # segments, _ = model.transcribe(audio_path, language="zh")
            # return " ".join([s.text for s in segments])
            logger.warning("[OllamaProcessor] 本地 Whisper 转录尚未配置，请安装 faster-whisper")
            return ""
        except Exception as e:
            logger.error(f"[OllamaProcessor] 转录失败: {e}")
            return ""

    async def summarize(self, transcript: str, title: str = "") -> dict:
        """使用 Ollama 本地模型生成总结"""
        if not transcript.strip():
            return {"summary": "（无内容）", "keywords": [], "category": "未知"}

        prompt = f"""分析以下视频内容并以JSON格式输出总结：
标题：{title}
内容：{transcript[:2000]}

输出格式：{{"summary":"总结","keywords":["kw1","kw2"],"category":"分类"}}"""

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(
                    f"{settings.ollama_base_url}/api/generate",
                    json={
                        "model": settings.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",
                    },
                )
                data = resp.json()
                result = json.loads(data.get("response", "{}"))
                logger.info(f"[OllamaProcessor] Ollama 总结完成")
                return result
        except Exception as e:
            logger.error(f"[OllamaProcessor] Ollama 请求失败: {e}")
            return {"summary": f"总结失败: {e}", "keywords": [], "category": "未知"}
