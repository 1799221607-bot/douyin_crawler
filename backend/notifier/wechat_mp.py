from loguru import logger
from notifier.base import BaseNotifier


class WechatMpNotifier(BaseNotifier):
    """
    微信公众号模板消息通知（预留接口）。
    需要：认证服务号 + 已申请模板消息权限。

    config 字段：
        app_id: str         公众号 AppID
        app_secret: str     公众号 AppSecret
        template_id: str    消息模板 ID
        open_ids: list[str] 接收者 OpenID 列表
    """

    channel = "wechat_mp"

    async def send(self, event: str, payload: dict, config: dict) -> bool:
        # TODO: 待认证服务号接入后实现
        # 实现步骤：
        # 1. 调用 https://api.weixin.qq.com/cgi-bin/token 获取 access_token
        # 2. 调用 https://api.weixin.qq.com/cgi-bin/message/template/send
        #    发送模板消息到每个 open_id
        logger.warning(
            "[WechatMpNotifier] 微信公众号通知尚未实现，"
            "需要认证服务号后完成接入（AppID/AppSecret/TemplateID）"
        )
        return False
