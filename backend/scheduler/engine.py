import time
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger
from config import settings
from database import AsyncSessionLocal
from db.models import Creator
from db.repository import CreatorRepo, VideoRepo, CrawlLogRepo, NotificationRepo, SystemSettingRepo
from collector.registry import collector_registry
from notifier.registry import notifier_registry


class CrawlScheduler:
    """
    APScheduler 异步调度器封装。
    每个博主拥有独立的定时 Job，频率可动态调整，无需重启服务。
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")

    def start(self):
        self.scheduler.start()
        logger.info("[Scheduler] 调度器已启动")

    def stop(self):
        self.scheduler.shutdown(wait=False)

    async def load_all_creators(self):
        """服务启动时，从数据库加载所有启用的博主并注册定时任务"""
        async with AsyncSessionLocal() as db:
            repo = CreatorRepo(db)
            creators = await repo.get_enabled()
            for creator in creators:
                self.add_creator_job(creator)
            logger.info(f"[Scheduler] 已加载 {len(creators)} 个博主的采集任务")

    def add_creator_job(self, creator: Creator):
        """为博主添加或替换定时采集任务"""
        job_id = f"creator_{creator.id}"
        self.scheduler.add_job(
            func=crawl_creator_task,
            trigger=IntervalTrigger(minutes=creator.interval_min),
            args=[creator.id],
            id=job_id,
            replace_existing=True,
            next_run_time=datetime.now(),  # 注册后立即执行一次
        )
        logger.info(
            f"[Scheduler] 已注册任务: {creator.name} "
            f"(id={creator.id}, 间隔={creator.interval_min}min)"
        )

    def remove_creator_job(self, creator_id: int):
        job_id = f"creator_{creator_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
            logger.info(f"[Scheduler] 已移除任务: creator_id={creator_id}")

    def update_interval(self, creator_id: int, interval_min: int):
        """动态修改采集频率（立即生效，无需重启）"""
        job_id = f"creator_{creator_id}"
        job = self.scheduler.get_job(job_id)
        if job:
            job.reschedule(trigger=IntervalTrigger(minutes=interval_min))
            logger.info(f"[Scheduler] 已更新频率: creator_id={creator_id}, 新间隔={interval_min}min")

    def pause_creator(self, creator_id: int):
        job_id = f"creator_{creator_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.pause_job(job_id)

    def resume_creator(self, creator_id: int):
        job_id = f"creator_{creator_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.resume_job(job_id)

    def run_now(self, creator_id: int):
        """立即触发一次采集（不影响定时计划）"""
        self.scheduler.add_job(
            func=crawl_creator_task,
            args=[creator_id],
            id=f"creator_{creator_id}_manual_{int(time.time())}",
            replace_existing=False,
        )

    def get_job_status(self, creator_id: int) -> Optional[dict]:
        job_id = f"creator_{creator_id}"
        job = self.scheduler.get_job(job_id)
        if not job:
            return None
        return {
            "job_id": job_id,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "paused": job.next_run_time is None,
        }


# ─── 核心采集任务函数 ─────────────────────────────────────────────────────────

async def crawl_creator_task(creator_id: int):
    """
    单个博主的采集任务，包含：
    1. 获取视频列表（yt-dlp）
    2. 增量去重
    3. 入库 + 下载
    4. 触发通知
    """
    start_time = time.time()
    async with AsyncSessionLocal() as db:
        creator_repo = CreatorRepo(db)
        video_repo = VideoRepo(db)
        log_repo = CrawlLogRepo(db)
        notify_repo = NotificationRepo(db)
        setting_repo = SystemSettingRepo(db)

        creator = await creator_repo.get_by_id(creator_id)
        if not creator or not creator.enabled:
            return

        # 创建采集日志
        log = await log_repo.create(
            creator_id=creator_id,
            source_type="creator",
            status="running",
        )
        await db.commit()

        logger.info(f"[Task] 开始采集: {creator.name}")
        new_count = 0

        try:
            # 1. 获取视频列表
            collector = collector_registry.get("video")
            db_cookie = await setting_repo.get_value("dy_cookie")
            cookie = db_cookie if db_cookie else settings.cookie
            
            config = {
                "cookie": cookie,
                "proxy": settings.proxy,
                "download": creator.download_video,
                "download_dir": settings.download_dir,
            }
            target = {"user_url": creator.user_url, "creator_id": creator.id, "creator_name": creator.name}
            raw_videos = await collector.collect(target, config)

            if not raw_videos:
                logger.warning(f"[Task] {creator.name} 未获取到视频数据")
                await log_repo.update(log.id, status="success", new_count=0, total_count=0,
                                      duration_ms=int((time.time() - start_time) * 1000))
                await creator_repo.update_last_run(creator_id)
                await db.commit()
                return

            # 2. 增量去重
            aweme_ids = [v["aweme_id"] for v in raw_videos if v.get("aweme_id")]
            existing_ids = await video_repo.bulk_get_aweme_ids(aweme_ids)
            new_videos = [v for v in raw_videos if v["aweme_id"] not in existing_ids]

            logger.info(f"[Task] {creator.name}: 共{len(raw_videos)}条, 新增{len(new_videos)}条")

            # 3. 入库
            for v in new_videos:
                published_at = None
                if v.get("published_at"):
                    try:
                        published_at = datetime.fromisoformat(v["published_at"])
                    except Exception:
                        pass

                await video_repo.create(
                    creator_id=creator_id,
                    aweme_id=v["aweme_id"],
                    title=v.get("title", ""),
                    desc=v.get("desc", ""),
                    duration=v.get("duration"),
                    cover_url=v.get("cover_url"),
                    play_url=v.get("play_url"),
                    like_count=v.get("like_count"),
                    comment_count=v.get("comment_count"),
                    share_count=v.get("share_count"),
                    collect_count=v.get("collect_count"),
                    published_at=published_at,
                )
                new_count += 1

            await db.commit()

            # 4. 下载视频文件（入库后再下载，避免下载失败丢数据）
            if creator.download_video and new_videos:
                for v in new_videos:
                    if v.get("play_url"):
                        local_path = await collector.download_video(
                            aweme_id=v["aweme_id"],
                            play_url=v["play_url"],
                            creator_name=creator.name,
                            config=config,
                        )
                        if local_path:
                            await video_repo.update_downloaded(v["aweme_id"], local_path)
                await db.commit()

            # 5. 触发通知
            if new_count > 0:
                notify_configs = await notify_repo.list_enabled_by_event("new_video")
                for v in new_videos[:3]:  # 最多通知前3条，避免轰炸
                    payload = {**v, "creator_name": creator.name}
                    await notifier_registry.dispatch("new_video", payload, notify_configs)

            # 6. 更新日志
            await log_repo.update(
                log.id,
                status="success",
                new_count=new_count,
                total_count=len(raw_videos),
                duration_ms=int((time.time() - start_time) * 1000),
            )
            await creator_repo.update_last_run(creator_id)
            await db.commit()
            logger.info(f"[Task] {creator.name} 采集完成，新增 {new_count} 条")

        except Exception as e:
            logger.error(f"[Task] {creator.name} 采集失败: {e}")
            try:
                await log_repo.update(log.id, status="failed", error_msg=str(e),
                                      duration_ms=int((time.time() - start_time) * 1000))
                notify_configs = await notify_repo.list_enabled_by_event("crawl_error")
                await notifier_registry.dispatch(
                    "crawl_error",
                    {"creator_name": creator.name, "error_msg": str(e)},
                    notify_configs,
                )
                await db.commit()
            except Exception as inner_e:
                logger.error(f"[Task] 记录错误日志失败: {inner_e}")


# 全局调度器单例
crawler_scheduler = CrawlScheduler()
