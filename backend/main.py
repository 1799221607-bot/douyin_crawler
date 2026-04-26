import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from config import settings
from database import init_db
from scheduler.engine import crawler_scheduler
from api import creators, videos, notifications, ai, logs, sys_settings as settings_api, auth, users


async def init_admin_user():
    """如果数据库中没有用户，创建一个默认管理员"""
    from database import AsyncSessionLocal
    from db.repository import UserRepo
    from utils.security import get_password_hash
    
    async with AsyncSessionLocal() as db:
        repo = UserRepo(db)
        users_list = await repo.list_all()
        if not users_list:
            logger.info("👥 正在创建初始管理员账号: admin / admin123")
            await repo.create(
                username="admin",
                hashed_password=get_password_hash("admin123"),
                role="admin"
            )
            await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── 启动 ──
    logger.info("🚀 抖音采集平台启动中...")
    await init_db()
    logger.info("✅ 数据库初始化完成")

    await init_admin_user()

    os.makedirs(settings.download_dir, exist_ok=True)

    crawler_scheduler.start()
    await crawler_scheduler.load_all_creators()
    logger.info("✅ 调度器启动完成")

    yield

    # ── 关闭 ──
    crawler_scheduler.stop()
    logger.info("👋 调度器已停止")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 路由
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(creators.router)
app.include_router(videos.router)
app.include_router(notifications.router)
app.include_router(ai.router)
app.include_router(logs.router)
app.include_router(settings_api.router)

# ── 托管前端静态文件 ──
# 假设前端 build 后的文件放在 backend/static 目录下
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    # 兜底路由：处理 Vue Router 的 History 模式，防止刷新页面 404
    @app.exception_handler(404)
    async def not_found_handler(request, exc):
        return FileResponse(os.path.join(static_dir, "index.html"))
else:
    logger.warning(f"⚠️ 静态文件目录不存在: {static_dir}，前端页面将无法通过此端口访问")


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": settings.app_version}


@app.get("/api/stats")
async def stats():
    """仪表盘概览数据"""
    from database import AsyncSessionLocal
    from sqlalchemy import select, func
    from db.models import Creator, Video, CrawlLog

    async with AsyncSessionLocal() as db:
        creator_count = (await db.execute(select(func.count()).select_from(Creator))).scalar()
        video_count = (await db.execute(select(func.count()).select_from(Video))).scalar()
        downloaded_count = (await db.execute(
            select(func.count()).where(Video.downloaded == True)
        )).scalar()
        log_count = (await db.execute(select(func.count()).select_from(CrawlLog))).scalar()
        today_new = (await db.execute(
            select(func.count()).where(
                func.date(Video.created_at) == func.date("now")
            )
        )).scalar()

    return {
        "creator_count": creator_count,
        "video_count": video_count,
        "downloaded_count": downloaded_count,
        "log_count": log_count,
        "today_new": today_new,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.debug)
