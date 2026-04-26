from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from db.repository import CreatorRepo
from scheduler.engine import crawler_scheduler

router = APIRouter(prefix="/api/creators", tags=["博主管理"])


class CreatorCreate(BaseModel):
    name: str
    user_url: str
    interval_min: int = 60
    download_video: bool = True
    enabled: bool = True


class CreatorUpdate(BaseModel):
    name: Optional[str] = None
    user_url: Optional[str] = None
    interval_min: Optional[int] = None
    download_video: Optional[bool] = None
    enabled: Optional[bool] = None


from datetime import timedelta

def _to_dict(c) -> dict:
    status = crawler_scheduler.get_job_status(c.id)
    
    # 转换为本地时间 (UTC+8)
    created_at = c.created_at + timedelta(hours=8) if c.created_at else None
    last_run_at = c.last_run_at + timedelta(hours=8) if c.last_run_at else None
    
    return {
        "id": c.id,
        "name": c.name,
        "user_url": c.user_url,
        "sec_user_id": c.sec_user_id,
        "avatar_url": c.avatar_url,
        "follower_count": c.follower_count,
        "interval_min": c.interval_min,
        "enabled": c.enabled,
        "download_video": c.download_video,
        "created_at": created_at.isoformat() if created_at else None,
        "last_run_at": last_run_at.isoformat() if last_run_at else None,
        "next_run_at": status["next_run"] if status else None,
        "job_paused": status["paused"] if status else True,
    }


@router.get("")
async def list_creators(db: AsyncSession = Depends(get_db)):
    repo = CreatorRepo(db)
    creators = await repo.list_all()
    return {"data": [_to_dict(c) for c in creators]}


@router.post("", status_code=201)
async def create_creator(body: CreatorCreate, db: AsyncSession = Depends(get_db)):
    repo = CreatorRepo(db)
    creator = await repo.create(**body.model_dump())
    await db.commit()
    await db.refresh(creator)
    if creator.enabled:
        crawler_scheduler.add_creator_job(creator)
    return {"data": _to_dict(creator)}


@router.put("/{creator_id}")
async def update_creator(creator_id: int, body: CreatorUpdate, db: AsyncSession = Depends(get_db)):
    repo = CreatorRepo(db)
    creator = await repo.get_by_id(creator_id)
    if not creator:
        raise HTTPException(status_code=404, detail="博主不存在")

    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    creator = await repo.update(creator_id, **update_data)
    await db.commit()

    # 同步更新调度器
    if "interval_min" in update_data:
        crawler_scheduler.update_interval(creator_id, creator.interval_min)
    if "enabled" in update_data:
        if creator.enabled:
            crawler_scheduler.add_creator_job(creator)
        else:
            crawler_scheduler.remove_creator_job(creator_id)

    return {"data": _to_dict(creator)}


@router.delete("/{creator_id}")
async def delete_creator(creator_id: int, db: AsyncSession = Depends(get_db)):
    repo = CreatorRepo(db)
    creator = await repo.get_by_id(creator_id)
    if not creator:
        raise HTTPException(status_code=404, detail="博主不存在")
    crawler_scheduler.remove_creator_job(creator_id)
    await repo.delete(creator_id)
    await db.commit()
    return {"message": "已删除"}


@router.post("/{creator_id}/run-now")
async def run_now(creator_id: int, db: AsyncSession = Depends(get_db)):
    repo = CreatorRepo(db)
    creator = await repo.get_by_id(creator_id)
    if not creator:
        raise HTTPException(status_code=404, detail="博主不存在")
    crawler_scheduler.run_now(creator_id)
    return {"message": "采集任务已触发"}


@router.post("/{creator_id}/pause")
async def pause_creator(creator_id: int):
    crawler_scheduler.pause_creator(creator_id)
    return {"message": "已暂停"}


@router.post("/{creator_id}/resume")
async def resume_creator(creator_id: int):
    crawler_scheduler.resume_creator(creator_id)
    return {"message": "已恢复"}
