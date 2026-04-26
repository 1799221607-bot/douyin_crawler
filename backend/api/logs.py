from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from db.repository import CrawlLogRepo

router = APIRouter(prefix="/api/logs", tags=["采集日志"])


def _log_to_dict(log) -> dict:
    return {
        "id": log.id,
        "creator_id": log.creator_id,
        "creator_name": log.creator.name if log.creator else None,
        "source_type": log.source_type,
        "run_at": log.run_at.isoformat() if log.run_at else None,
        "new_count": log.new_count,
        "total_count": log.total_count,
        "status": log.status,
        "error_msg": log.error_msg,
        "duration_ms": log.duration_ms,
    }


@router.get("")
async def list_logs(
    creator_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
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
