import os
import re
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from db.repository import VideoRepo

router = APIRouter(prefix="/api/videos", tags=["视频管理"])


def _video_to_dict(v) -> dict:
    summary = None
    if v.ai_summary:
        summary = {
            "transcript": v.ai_summary.transcript,
            "summary": v.ai_summary.summary,
            "keywords": v.ai_summary.keywords,
            "status": v.ai_summary.status,
        }
    return {
        "id": v.id,
        "aweme_id": v.aweme_id,
        "creator_id": v.creator_id,
        "creator_name": v.creator.name if v.creator else "未知博主",
        "title": v.title,
        "desc": v.desc,
        "duration": v.duration,
        "cover_url": v.cover_url,
        "play_url": v.play_url,
        "like_count": v.like_count,
        "comment_count": v.comment_count,
        "share_count": v.share_count,
        "collect_count": v.collect_count,
        "published_at": v.published_at.isoformat() if v.published_at else None,
        "local_path": v.local_path,
        "downloaded": v.downloaded,
        "ai_processed": v.ai_processed,
        "created_at": v.created_at.isoformat() if v.created_at else None,
        "ai_summary": summary,
    }


@router.get("")
async def list_videos(
    creator_id: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None),
    downloaded: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    repo = VideoRepo(db)
    if creator_id:
        videos, total = await repo.list_by_creator(creator_id, page, page_size, downloaded)
    else:
        videos, total = await repo.list_all(page, page_size, keyword, downloaded)

    return {
        "data": [_video_to_dict(v) for v in videos],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/{aweme_id}")
async def get_video(aweme_id: str, db: AsyncSession = Depends(get_db)):
    repo = VideoRepo(db)
    video = await repo.get_by_aweme_id(aweme_id)
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")
    return {"data": _video_to_dict(video)}


@router.get("/{aweme_id}/stream")
async def stream_video(aweme_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    """
    本地视频流式播放接口（供前端 Plyr 播放器调用）。
    支持 Range 请求（断点续传），兼容 Chrome 的严格播放策略。
    """
    repo = VideoRepo(db)
    video = await repo.get_by_aweme_id(aweme_id)
    if not video or not video.local_path:
        raise HTTPException(status_code=404, detail="视频文件不存在")
    
    file_path = video.local_path
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"文件未找到: {file_path}")

    file_size = os.path.getsize(file_path)
    range_header = request.headers.get('Range')
    
    if range_header and isinstance(range_header, str):
        byte1, byte2 = 0, None
        match = re.search(r'bytes=(\d+)-(\d*)', range_header)
        if match:
            g = match.groups()
            byte1 = int(g[0])
            if g[1]:
                byte2 = int(g[1])
        
        if byte2 is None:
            byte2 = file_size - 1
            
        length = byte2 - byte1 + 1
        
        def file_iterator():
            with open(file_path, "rb") as f:
                f.seek(byte1)
                chunk_size = 1024 * 1024 # 1MB chunk
                remaining = length
                while remaining > 0:
                    read_size = min(chunk_size, remaining)
                    data = f.read(read_size)
                    if not data:
                        break
                    remaining -= len(data)
                    yield data

        headers = {
            "Content-Range": f"bytes {byte1}-{byte2}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(length),
        }
        return StreamingResponse(file_iterator(), status_code=206, headers=headers, media_type="video/mp4")
    
    else:
        def file_iterator():
            with open(file_path, "rb") as f:
                while chunk := f.read(1024 * 1024):
                    yield chunk
                    
        return StreamingResponse(
            file_iterator(), 
            headers={"Accept-Ranges": "bytes", "Content-Length": str(file_size)}, 
            media_type="video/mp4"
        )
