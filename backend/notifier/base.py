from abc import ABC, abstractmethod


class BaseNotifier(ABC):
    """
    通知渠道插件基类。
    新增推送渠道只需继承此类并实现 send()，
    然后在 registry.py 中注册即可。
    """

    @property
    @abstractmethod
    def channel(self) -> str:
        """
        渠道唯一标识。
        例: 'feishu' | 'email' | 'wechat_mp' | 'telegram'
        """
        pass

    @abstractmethod
    async def send(self, event: str, payload: dict, config: dict) -> bool:
        """
        发送通知。

        Args:
            event: 事件类型
                - 'new_video'        新视频采集到
                - 'crawl_error'      采集出错
                - 'ai_summary_done'  AI 总结完成
            payload: 事件数据（随 event 不同而不同）
            config: 该渠道的配置（从数据库 config_json 解析）
                - feishu:    {'webhook_url': str}
                - email:     {'smtp_host': str, 'smtp_port': int, 'username': str,
                              'password': str, 'from_addr': str, 'to_addrs': list[str]}
                - wechat_mp: {'app_id': str, 'app_secret': str, 'template_id': str,
                              'open_ids': list[str]}

        Returns:
            bool: 发送是否成功
        """
        pass

    def format_new_video_msg(self, payload: dict) -> dict:
        """生成新视频通知的标准消息体（子类可重写）"""
        creator_name = payload.get("creator_name", "未知博主")
        title = payload.get("title", "无标题")
        published_at = payload.get("published_at", "")
        like_count = payload.get("like_count", 0)
        return {
            "title": f"📹 {creator_name} 发布了新视频",
            "body": f"**{title}**\n发布时间：{published_at}\n点赞数：{like_count}",
            "url": payload.get("play_url", ""),
        }
