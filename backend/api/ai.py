import json
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from db.repository import VideoRepo, AISummaryRepo
from ai.registry import ai_registry

router = APIRouter(prefix="/api/ai", tags=["AI 总结"])


@router.post("/summarize/{aweme_id}")
async def trigger_summarize(
    aweme_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """触发单个视频的 AI 总结（异步后台执行）"""
    video_repo = VideoRepo(db)
    summary_repo = AISummaryRepo(db)

    video = await video_repo.get_by_aweme_id(aweme_id)
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    if not video.local_path:
        raise HTTPException(status_code=400, detail="视频尚未下载到本地，无法处理")

    # 创建处理记录
    await summary_repo.create_or_update(aweme_id, status="pending")
    await db.commit()

    background_tasks.add_task(_do_summarize, aweme_id, video.local_path, video.title or "")
    return {"message": "AI 总结任务已提交", "aweme_id": aweme_id}


async def _do_summarize(aweme_id: str, video_path: str, title: str):
    """后台执行 AI 总结"""
    from database import AsyncSessionLocal
    from loguru import logger
    from notifier.registry import notifier_registry
    from db.repository import NotificationRepo

    async with AsyncSessionLocal() as db:
        summary_repo = AISummaryRepo(db)
        video_repo = VideoRepo(db)

        try:
            await summary_repo.create_or_update(aweme_id, status="processing")
            await db.commit()

            processor = ai_registry.get_active()
            result = await processor.process(video_path, title=title)

            await summary_repo.create_or_update(
                aweme_id,
                transcript=result.get("transcript", ""),
                summary=result.get("summary", ""),
                keywords=json.dumps(result.get("keywords", []), ensure_ascii=False),
                model=result.get("model", ""),
                status="done",
                error_msg=None,
            )
            from sqlalchemy import update
            from db.models import Video
            await db.execute(update(Video).where(Video.aweme_id == aweme_id).values(ai_processed=True))
            await db.commit()
            logger.info(f"[AI] {aweme_id} 总结完成")

            # 通知
            notify_repo = NotificationRepo(db)
            notify_configs = await notify_repo.list_enabled_by_event("ai_summary_done")
            video = await video_repo.get_by_aweme_id(aweme_id)
            await notifier_registry.dispatch(
                "ai_summary_done",
                {"title": title, "summary": result.get("summary", ""), "aweme_id": aweme_id},
                notify_configs,
            )

        except Exception as e:
            logger.error(f"[AI] {aweme_id} 总结失败: {e}")
            await summary_repo.create_or_update(aweme_id, status="failed", error_msg=str(e))
            await db.commit()


@router.get("/summary/{aweme_id}")
async def get_summary(aweme_id: str, db: AsyncSession = Depends(get_db)):
    video_repo = VideoRepo(db)
    video = await video_repo.get_by_aweme_id(aweme_id)
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    if not video.ai_summary:
        return {"data": None, "message": "尚未生成 AI 总结"}

    s = video.ai_summary
    return {
        "data": {
            "aweme_id": aweme_id,
            "transcript": s.transcript,
            "summary": s.summary,
            "keywords": json.loads(s.keywords) if s.keywords else [],
            "model": s.model,
            "status": s.status,
            "error_msg": s.error_msg,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
    }


@router.get("/providers")
async def list_providers():
    """返回可用的 AI 处理器列表"""
    return {
        "data": ai_registry.list_providers(),
        "active": ai_registry.get_active().provider,
    }
