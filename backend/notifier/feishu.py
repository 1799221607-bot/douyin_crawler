import httpx
from loguru import logger
from notifier.base import BaseNotifier


class FeishuNotifier(BaseNotifier):
    """飞书 Webhook 机器人通知"""

    channel = "feishu"

    async def send(self, event: str, payload: dict, config: dict) -> bool:
        webhook_url = config.get("webhook_url")
        if not webhook_url:
            logger.warning("[FeishuNotifier] webhook_url 未配置")
            return False

        msg = self._build_message(event, payload)
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(webhook_url, json=msg)
                data = resp.json()
                if data.get("code") == 0:
                    logger.info(f"[FeishuNotifier] 发送成功: {event}")
                    return True
                else:
                    logger.error(f"[FeishuNotifier] 发送失败: {data}")
                    return False
        except Exception as e:
            logger.error(f"[FeishuNotifier] 请求异常: {e}")
            return False

    def _build_message(self, event: str, payload: dict) -> dict:
        """构建飞书富文本消息"""
        if event == "new_video":
            creator_name = payload.get("creator_name", "未知博主")
            title = payload.get("title", "无标题")
            published_at = payload.get("published_at", "")
            like_count = payload.get("like_count") or 0
            play_url = payload.get("play_url", "")
            cover_url = payload.get("cover_url", "")

            content = [
                [{"tag": "text", "text": f"📹 博主：{creator_name}"}],
                [{"tag": "text", "text": f"标题：{title}"}],
                [{"tag": "text", "text": f"发布时间：{published_at}"}],
                [{"tag": "text", "text": f"点赞：{like_count}"}],
            ]
            if play_url:
                content.append([{"tag": "a", "text": "▶ 点击观看", "href": play_url}])

            return {
                "msg_type": "post",
                "content": {
                    "post": {
                        "zh_cn": {
                            "title": f"🎬 新视频提醒 — {creator_name}",
                            "content": content,
                        }
                    }
                },
            }

        elif event == "crawl_error":
            creator_name = payload.get("creator_name", "未知博主")
            error_msg = payload.get("error_msg", "")
            return {
                "msg_type": "text",
                "content": {
                    "text": f"⚠️ 采集出错\n博主：{creator_name}\n错误：{error_msg}"
                },
            }

        elif event == "ai_summary_done":
            title = payload.get("title", "")
            summary = payload.get("summary", "")
            return {
                "msg_type": "text",
                "content": {"text": f"🤖 AI 总结完成\n视频：{title}\n摘要：{summary[:200]}..."},
            }

        return {"msg_type": "text", "content": {"text": f"[{event}] {payload}"}}
