import json
import os
import httpx
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
        self._chat_client = None
        self._whisper_client = None

    @property
    def client(self) -> AsyncOpenAI:
        """Chat 客户端"""
        if self._chat_client is None:
            self._chat_client = self._get_client(settings.openai_base_url)
        return self._chat_client

    @property
    def whisper_client(self) -> AsyncOpenAI:
        """Whisper 客户端"""
        if self._whisper_client is None:
            # 如果配置了独立的 whisper_base_url 则使用，否则回退到全局 base_url
            base_url = settings.whisper_base_url or settings.openai_base_url
            self._whisper_client = self._get_client(base_url)
        return self._whisper_client

    def _get_client(self, base_url: str) -> AsyncOpenAI:
        # 兼容性处理：如果用户填的是全路径（包含 /audio/），剥离它以防 SDK 重复追加
        if "/audio" in base_url:
            logger.info(f"[OpenAIProcessor] 检测到全路径端点，正在适配: {base_url}")
            base_url = base_url.split("/audio")[0]

        logger.debug(f"[OpenAIProcessor] 初始化客户端: base_url={base_url}, proxy={settings.proxy}")
        
        http_client = None
        if settings.proxy:
            os.environ["HTTP_PROXY"] = settings.proxy
            os.environ["HTTPS_PROXY"] = settings.proxy
            
            http_client = httpx.AsyncClient(
                proxy=settings.proxy,
                limits=httpx.Limits(max_connections=20, max_keepalive_connections=5),
                timeout=httpx.Timeout(120.0, connect=20.0),
                verify=False
            )

        return AsyncOpenAI(
            api_key=settings.openai_api_key,
            base_url=base_url,
            http_client=http_client,
            max_retries=3
        )

    async def transcribe(self, audio_path: str) -> str:
        """使用 Whisper API 转录视频/音频"""
        base_url = settings.whisper_base_url or settings.openai_base_url
        model = settings.whisper_model
        
        # 自动修正 NVIDIA 模型名称
        if "nvidia" in base_url.lower() and not model.startswith("nvidia/"):
            logger.info(f"[OpenAIProcessor] 修正 NVIDIA 模型名称: {model} -> nvidia/whisper-large-v3")
            model = "nvidia/whisper-large-v3"

        # 如果是专用的 ai.api.nvidia.com 且包含模型路径，走原生 Base64 模式
        if "ai.api.nvidia.com" in base_url.lower() and "whisper" in base_url.lower():
            return await self._transcribe_nvidia_native(audio_path, base_url, model)
            
        try:
            logger.info(f"[OpenAIProcessor] 正在转录 (OpenAI 模式): {base_url}, 模型: {model}")
            with open(audio_path, "rb") as f:
                response = await self.whisper_client.audio.transcriptions.create(
                    model=model,
                    file=f,
                    language="zh",
                    response_format="text",
                )
            text = response if isinstance(response, str) else getattr(response, 'text', str(response))
            logger.info(f"[OpenAIProcessor] 转录完成，字数: {len(text)}")
            return text
        except Exception as e:
            if "404" in str(e) and "integrate.api.nvidia.com" in base_url:
                logger.warning("[OpenAIProcessor] 404 错误，尝试切换到原生 Base64 模式重试...")
                # 尝试一个备选的 NVIDIA 原生端点
                fallback_url = f"https://ai.api.nvidia.com/v1/audio/nvidia/whisper-large-v3"
                return await self._transcribe_nvidia_native(audio_path, fallback_url, "nvidia/whisper-large-v3")
            
            logger.exception("[OpenAIProcessor] Whisper 转录异常")
            return ""

    async def _transcribe_nvidia_native(self, audio_path: str, url: str, model: str) -> str:
        """NVIDIA 原生 API 转录逻辑 (Base64 + JSON)"""
        import base64
        try:
            logger.info(f"[OpenAIProcessor] 正在转录 (NVIDIA 原生模式): {url}")
            
            headers = {
                "Authorization": f"Bearer {settings.openai_api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
            
            with open(audio_path, "rb") as f:
                audio_base64 = base64.b64encode(f.read()).decode("utf-8")
            
            payload = {
                "audio": audio_base64,
                "model": model
            }
            
            async with httpx.AsyncClient(proxy=settings.proxy, verify=False, timeout=120.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                
                if response.status_code != 200:
                    logger.error(f"[OpenAIProcessor] NVIDIA 原生模式转录失败: {response.status_code} {response.text}")
                    return ""
                
                result = response.json()
                text = result.get("text", "")
                logger.info(f"[OpenAIProcessor] NVIDIA 原生模式转录成功，字数: {len(text)}")
                return text
        except Exception:
            logger.exception("[OpenAIProcessor] NVIDIA 原生模式转录异常")
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
