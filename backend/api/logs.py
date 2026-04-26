from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db
from db.models import Creator, Video, CrawlLog
import traceback
from loguru import logger

router = APIRouter(prefix="/api/logs", tags=["采集日志"])


from datetime import timedelta

def _log_to_dict(log) -> dict:
    # 将数据库中的 UTC 时间转换为本地时间展示 (UTC+8)
    local_run_at = log.run_at
    if local_run_at:
        local_run_at = local_run_at + timedelta(hours=8)
    
    return {
        "id": log.id,
        "creator_id": log.creator_id,
        "creator_name": log.creator.name if log.creator else None,
        "source_type": log.source_type,
        "run_at": local_run_at.isoformat() if local_run_at else None,
        "new_count": log.new_count,
        "total_count": log.total_count,
        "status": log.status,
        "error_msg": log.error_msg,
        "duration_ms": log.duration_ms,
    }


@router.get("/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select, func
    from db.models import Creator, Video, CrawlLog
    try:
        creator_count = (await db.execute(select(func.count()).select_from(Creator))).scalar() or 0
        video_count = (await db.execute(select(func.count()).select_from(Video))).scalar() or 0
        downloaded_count = (await db.execute(select(func.count()).where(Video.downloaded == True))).scalar() or 0
        log_count = (await db.execute(select(func.count()).select_from(CrawlLog))).scalar() or 0
        
        # 今日新增统计（考虑北京时间偏移）
        today_new = (await db.execute(
            select(func.count())
            .select_from(Video)
            .where(func.date(Video.created_at, '+8 hours') >= func.date('now', 'localtime', 'start of day'))
        )).scalar() or 0
        
        return {
            "creator_count": creator_count,
            "video_count": video_count,
            "downloaded_count": downloaded_count,
            "log_count": log_count,
            "today_new": today_new,
        }
    except Exception as e:
        logger.error(f"❌ 统计接口异常: {e}")
        return {"creator_count": 0, "video_count": 0, "downloaded_count": 0, "log_count": 0, "today_new": 0}


@router.get("")
async def list_logs(
    creator_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    from db.repository import CrawlLogRepo
    repo = CrawlLogRepo(db)
    if creator_id:
        logs = await repo.list_by_creator(creator_id, limit=page_size)
        return {"data": [_log_to_dict(l) for l in logs], "total": len(logs)}
    logs, total = await repo.list_all(page, page_size)
    return {
        "data": [_log_to_dict(l) for l in logs],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
