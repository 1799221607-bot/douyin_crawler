from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from db.repository import SystemSettingRepo

router = APIRouter(prefix="/api/settings", tags=["系统设置"])

class SettingUpdate(BaseModel):
    value: str
    description: str = None

@router.get("/{key}")
async def get_setting(key: str, db: AsyncSession = Depends(get_db)):
    repo = SystemSettingRepo(db)
    value = await repo.get_value(key)
    return {"key": key, "value": value}

@router.post("/auto-fetch")
async def auto_fetch_cookie(db: AsyncSession = Depends(get_db)):
    """触发浏览器自动化获取 Cookie"""
    try:
        from utils.cookie_fetcher import fetch_douyin_cookie_automated
        cookie_str = fetch_douyin_cookie_automated()
        repo = SystemSettingRepo(db)
        await repo.set_value("dy_cookie", cookie_str, "通过自动化窗口获取")
        await db.commit()
        return {"cookie": cookie_str, "message": "获取并同步成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{key}")
async def update_setting(key: str, body: SettingUpdate, db: AsyncSession = Depends(get_db)):
    repo = SystemSettingRepo(db)
    await repo.set_value(key, body.value, body.description)
    await db.commit()
    return {"message": f"设置 {key} 已更新"}
