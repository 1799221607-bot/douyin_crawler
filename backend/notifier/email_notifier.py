import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from loguru import logger
from notifier.base import BaseNotifier


class EmailNotifier(BaseNotifier):
    """SMTP 邮件通知"""

    channel = "email"

    async def send(self, event: str, payload: dict, config: dict) -> bool:
        smtp_host = config.get("smtp_host", "smtp.gmail.com")
        smtp_port = int(config.get("smtp_port", 587))
        username = config.get("username", "")
        password = config.get("password", "")
        from_addr = config.get("from_addr", username)
        
        # 修复收件人解析：支持逗号分隔的字符串
        to_input = config.get("to_addrs", "")
        if isinstance(to_input, str):
            to_addrs = [addr.strip() for addr in to_input.split(",") if addr.strip()]
        else:
            to_addrs = to_input

        if not to_addrs:
            logger.warning("[EmailNotifier] 收件人列表为空")
            return False

        subject, html_body = self._build_content(event, payload)
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = ", ".join(to_addrs)
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        try:
            # QQ 邮箱 465 端口需要使用 use_tls=True (SSL)
            # 587 端口通常使用 start_tls=True
            use_tls = (smtp_port == 465)
            start_tls = (smtp_port == 587)
            
            await aiosmtplib.send(
                msg,
                hostname=smtp_host,
                port=smtp_port,
                username=username,
                password=password,
                use_tls=use_tls,
                start_tls=start_tls,
            )
            logger.info(f"[EmailNotifier] 邮件发送成功: {subject}")
            return True
        except Exception as e:
            logger.error(f"[EmailNotifier] 发送失败: {e}")
            return False

    def _build_content(self, event: str, payload: dict) -> tuple[str, str]:
        if event == "new_video":
            creator_name = payload.get("creator_name", "未知博主")
            title = payload.get("title", "无标题")
            published_at = payload.get("published_at", "")
            like_count = payload.get("like_count") or 0
            play_url = payload.get("play_url", "#")
            cover_url = payload.get("cover_url", "")

            subject = f"📹 {creator_name} 发布了新视频"
            html = f"""
            <div style="font-family: Arial; max-width: 600px; margin: auto;">
              <h2 style="color: #fe2c55;">🎬 新视频提醒</h2>
              {"<img src='" + cover_url + "' style='width:100%;border-radius:8px;'/>" if cover_url else ""}
              <h3>{title}</h3>
              <p>博主：<strong>{creator_name}</strong></p>
              <p>发布时间：{published_at}</p>
              <p>点赞数：❤️ {like_count}</p>
              <a href="{play_url}" style="background:#fe2c55;color:white;padding:10px 20px;
                 text-decoration:none;border-radius:5px;display:inline-block;">▶ 观看视频</a>
            </div>
            """
            return subject, html

        elif event == "crawl_error":
            creator_name = payload.get("creator_name", "")
            error_msg = payload.get("error_msg", "")
            subject = f"⚠️ 抖音采集出错 — {creator_name}"
            html = f"<p>博主 <strong>{creator_name}</strong> 采集失败</p><p>错误：{error_msg}</p>"
            return subject, html

        elif event == "ai_summary_done":
            title = payload.get("title", "")
            summary = payload.get("summary", "")
            subject = f"🤖 AI 总结完成 — {title}"
            html = f"<h3>{title}</h3><p>{summary}</p>"
            return subject, html

        return f"[{event}]", str(payload)
