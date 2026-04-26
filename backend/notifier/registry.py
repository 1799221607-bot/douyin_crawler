import json
from notifier.base import BaseNotifier
from notifier.feishu import FeishuNotifier
from notifier.email_notifier import EmailNotifier
from notifier.wechat_mp import WechatMpNotifier


class NotifierRegistry:
    """
    通知渠道插件注册表。
    新增渠道只需注册，其余代码无需修改。
    """

    def __init__(self):
        self._registry: dict[str, BaseNotifier] = {}

    def register(self, notifier: BaseNotifier):
        self._registry[notifier.channel] = notifier

    def get(self, channel: str) -> BaseNotifier:
        if channel not in self._registry:
            raise ValueError(f"未注册的通知渠道: {channel}")
        return self._registry[channel]

    def list_channels(self) -> list[str]:
        return list(self._registry.keys())

    async def dispatch(self, event: str, payload: dict, configs: list) -> None:
        """
        向所有订阅了该事件的已启用渠道发送通知。
        configs: 从数据库查询的 NotificationConfig 列表
        """
        for nc in configs:
            if not nc.enabled:
                continue
            events_list = json.loads(nc.events) if isinstance(nc.events, str) else nc.events
            if event not in events_list:
                continue
            try:
                notifier = self.get(nc.channel)
                cfg = json.loads(nc.config_json) if isinstance(nc.config_json, str) else {}
                await notifier.send(event, payload, cfg)
            except Exception as e:
                from loguru import logger
                logger.error(f"[NotifierRegistry] 发送失败 channel={nc.channel}: {e}")


# 全局单例注册表
notifier_registry = NotifierRegistry()
notifier_registry.register(FeishuNotifier())
notifier_registry.register(EmailNotifier())
notifier_registry.register(WechatMpNotifier())

# 后续扩展示例：
# from notifier.telegram import TelegramNotifier
# notifier_registry.register(TelegramNotifier())
