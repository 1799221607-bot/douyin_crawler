import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from db.repository import NotificationRepo
from notifier.registry import notifier_registry

router = APIRouter(prefix="/api/notifications", tags=["通知配置"])


class NotificationCreate(BaseModel):
    channel: str                    # feishu | email | wechat_mp
    name: str
    config_json: dict               # 渠道特定配置
    events: list[str] = ["new_video"]
    enabled: bool = True


class NotificationUpdate(BaseModel):
    name: Optional[str] = None
    config_json: Optional[dict] = None
    events: Optional[list[str]] = None
    enabled: Optional[bool] = None


def _to_dict(nc) -> dict:
    return {
        "id": nc.id,
        "channel": nc.channel,
        "name": nc.name,
        "config_json": json.loads(nc.config_json) if isinstance(nc.config_json, str) else nc.config_json,
        "events": json.loads(nc.events) if isinstance(nc.events, str) else nc.events,
        "enabled": nc.enabled,
        "created_at": nc.created_at.isoformat() if nc.created_at else None,
    }


@router.get("/channels")
async def list_channels():
    """返回已注册的通知渠道列表及配置字段说明"""
    schemas = {
        "feishu": {
            "label": "飞书机器人",
            "fields": [{"key": "webhook_url", "label": "Webhook URL", "type": "text", "required": True}],
        },
        "email": {
            "label": "邮件",
            "fields": [
                {"key": "smtp_host", "label": "SMTP 服务器", "type": "text", "required": True},
                {"key": "smtp_port", "label": "端口", "type": "number", "required": True},
                {"key": "username", "label": "用户名", "type": "text", "required": True},
                {"key": "password", "label": "密码", "type": "password", "required": True},
                {"key": "from_addr", "label": "发件人", "type": "text", "required": False},
                {"key": "to_addrs", "label": "收件人（逗号分隔）", "type": "text", "required": True},
            ],
        },
        "wechat_mp": {
            "label": "微信公众号（预留）",
            "fields": [
                {"key": "app_id", "label": "AppID", "type": "text", "required": True},
                {"key": "app_secret", "label": "AppSecret", "type": "password", "required": True},
                {"key": "template_id", "label": "模板 ID", "type": "text", "required": True},
                {"key": "open_ids", "label": "OpenID 列表（逗号分隔）", "type": "text", "required": True},
            ],
            "note": "需要认证服务号，当前功能为预留接口",
        },
    }
    available = notifier_registry.list_channels()
    return {"data": {ch: schemas[ch] for ch in available if ch in schemas}}


@router.get("")
async def list_notifications(db: AsyncSession = Depends(get_db)):
    repo = NotificationRepo(db)
    configs = await repo.list_all()
    return {"data": [_to_dict(c) for c in configs]}


@router.post("", status_code=201)
async def create_notification(body: NotificationCreate, db: AsyncSession = Depends(get_db)):
    if body.channel not in notifier_registry.list_channels():
        raise HTTPException(status_code=400, detail=f"不支持的渠道: {body.channel}")
    repo = NotificationRepo(db)
    config = await repo.create(
        channel=body.channel,
        name=body.name,
        config_json=json.dumps(body.config_json, ensure_ascii=False),
        events=json.dumps(body.events, ensure_ascii=False),
        enabled=body.enabled,
    )
    await db.commit()
    return {"data": _to_dict(config)}


@router.put("/{config_id}")
async def update_notification(config_id: int, body: NotificationUpdate, db: AsyncSession = Depends(get_db)):
    repo = NotificationRepo(db)
    config = await repo.get_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    update_data = {}
    if body.name is not None:
        update_data["name"] = body.name
    if body.config_json is not None:
        update_data["config_json"] = json.dumps(body.config_json, ensure_ascii=False)
    if body.events is not None:
        update_data["events"] = json.dumps(body.events, ensure_ascii=False)
    if body.enabled is not None:
        update_data["enabled"] = body.enabled

    config = await repo.update(config_id, **update_data)
    await db.commit()
    return {"data": _to_dict(config)}


@router.delete("/{config_id}")
async def delete_notification(config_id: int, db: AsyncSession = Depends(get_db)):
    repo = NotificationRepo(db)
    await repo.delete(config_id)
    await db.commit()
    return {"message": "已删除"}


@router.post("/{config_id}/test")
async def test_notification(config_id: int, db: AsyncSession = Depends(get_db)):
    """发送测试通知"""
    repo = NotificationRepo(db)
    config = await repo.get_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    try:
        notifier = notifier_registry.get(config.channel)
        cfg = json.loads(config.config_json) if isinstance(config.config_json, str) else {}
        ok = await notifier.send(
            "new_video",
            {
                "creator_name": "测试博主",
                "title": "这是一条测试通知",
                "published_at": "2024-01-01 12:00:00",
                "like_count": 9999,
                "play_url": "https://www.douyin.com",
            },
            cfg,
        )
        return {"success": ok, "message": "发送成功" if ok else "发送失败，请检查配置"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
