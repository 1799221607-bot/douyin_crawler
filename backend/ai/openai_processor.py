import json
from openai import AsyncOpenAI
from loguru import logger
from ai.base import BaseAIProcessor
from config import settings


class OpenAIProcessor(BaseAIProcessor):
    """
    OpenAI Whisper（转录）+ GPT-4o（总结）处理器。
    优先使用，需要配置 OPENAI_API_KEY。
    """

    provider = "openai"

    def __init__(self):
        self._client = None

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=settings.openai_api_key,
                base_url=settings.openai_base_url,
            )
        return self._client

    async def transcribe(self, audio_path: str) -> str:
        """使用 Whisper API 转录视频/音频"""
        try:
            with open(audio_path, "rb") as f:
                response = await self.client.audio.transcriptions.create(
                    model=settings.whisper_model,
                    file=f,
                    language="zh",  # 中文优先，可自动识别
                    response_format="text",
                )
            logger.info(f"[OpenAIProcessor] 转录完成，字数: {len(response)}")
            return response
        except Exception as e:
            logger.error(f"[OpenAIProcessor] Whisper 转录失败: {e}")
            return ""

    async def summarize(self, transcript: str, title: str = "") -> dict:
        """使用 GPT-4o 生成内容总结"""
        if not transcript.strip():
            return {"summary": "（无转录内容，无法生成总结）", "keywords": [], "category": "未知"}

        prompt = f"""你是一个专业的内容分析助手。请对以下抖音视频内容进行分析总结。

视频标题：{title or "（无标题）"}

视频转录内容：
{transcript[:3000]}

请以 JSON 格式输出，包含以下字段：
{{
  "summary": "200字以内的内容总结，重点提炼核心信息",
  "keywords": ["关键词1", "关键词2", "关键词3"],
  "category": "视频内容分类，如：美食/科技/娱乐/教育/生活/其他",
  "highlights": "最值得关注的1-2个亮点"
}}"""

        try:
            response = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.3,
            )
            result = json.loads(response.choices[0].message.content)
            logger.info(f"[OpenAIProcessor] GPT 总结完成: {result.get('category')}")
            return result
        except Exception as e:
            logger.error(f"[OpenAIProcessor] GPT 总结失败: {e}")
            return {"summary": f"总结生成失败: {e}", "keywords": [], "category": "未知"}
