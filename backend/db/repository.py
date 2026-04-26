from datetime import datetime
from typing import Optional
from sqlalchemy import select, update, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from db.models import Creator, Video, AISummary, NotificationConfig, CrawlLog, User, LoginLog, PlatformAccount


# ─── Creator ───────────────────────────────────────────────────────────────

class CreatorRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(self) -> list[Creator]:
        result = await self.db.execute(select(Creator).order_by(Creator.created_at.desc()))
        return result.scalars().all()

    async def get_by_id(self, creator_id: int) -> Optional[Creator]:
        result = await self.db.execute(select(Creator).where(Creator.id == creator_id))
        return result.scalar_one_or_none()

    async def get_enabled(self) -> list[Creator]:
        result = await self.db.execute(select(Creator).where(Creator.enabled == True))
        return result.scalars().all()

    async def create(self, **kwargs) -> Creator:
        creator = Creator(**kwargs)
        self.db.add(creator)
        await self.db.flush()
        await self.db.refresh(creator)
        return creator

    async def update(self, creator_id: int, **kwargs) -> Optional[Creator]:
        await self.db.execute(
            update(Creator).where(Creator.id == creator_id).values(**kwargs)
        )
        return await self.get_by_id(creator_id)

    async def delete(self, creator_id: int):
        creator = await self.get_by_id(creator_id)
        if creator:
            await self.db.delete(creator)

    async def update_last_run(self, creator_id: int):
        await self.db.execute(
            update(Creator).where(Creator.id == creator_id)
            .values(last_run_at=datetime.now())
        )


# ─── Video ─────────────────────────────────────────────────────────────────

class VideoRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def exists_by_aweme_id(self, aweme_id: str) -> bool:
        result = await self.db.execute(
            select(func.count()).where(Video.aweme_id == aweme_id)
        )
        return result.scalar() > 0

    async def bulk_get_aweme_ids(self, aweme_ids: list[str]) -> set[str]:
        """批量检查已存在的 aweme_id，用于增量去重"""
        result = await self.db.execute(
            select(Video.aweme_id).where(Video.aweme_id.in_(aweme_ids))
        )
        return set(result.scalars().all())

    async def create(self, **kwargs) -> Video:
        video = Video(**kwargs)
        self.db.add(video)
        await self.db.flush()
        await self.db.refresh(video)
        return video

    async def list_by_creator(
        self, creator_id: int, page: int = 1, page_size: int = 20, downloaded: Optional[bool] = None
    ) -> tuple[list[Video], int]:
        q = select(Video).where(Video.creator_id == creator_id)
        count_q = select(func.count()).where(Video.creator_id == creator_id)
        
        if downloaded is not None:
            q = q.where(Video.downloaded == downloaded)
            count_q = count_q.where(Video.downloaded == downloaded)

        total = (await self.db.execute(count_q)).scalar()
        result = await self.db.execute(
            q.order_by(Video.published_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .options(selectinload(Video.ai_summary), selectinload(Video.creator))
        )
        return result.scalars().all(), total

    async def list_all(
        self, page: int = 1, page_size: int = 20, keyword: Optional[str] = None, downloaded: Optional[bool] = None
    ) -> tuple[list[Video], int]:
        q = select(Video)
        count_q = select(func.count()).select_from(Video)
        
        if keyword:
            q = q.where(Video.title.contains(keyword))
            count_q = count_q.where(Video.title.contains(keyword))
            
        if downloaded is not None:
            q = q.where(Video.downloaded == downloaded)
            count_q = count_q.where(Video.downloaded == downloaded)

        total = (await self.db.execute(count_q)).scalar()
        result = await self.db.execute(
            q.order_by(Video.published_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .options(selectinload(Video.ai_summary), selectinload(Video.creator))
        )
        return result.scalars().all(), total

    async def update_downloaded(self, aweme_id: str, local_path: str):
        await self.db.execute(
            update(Video).where(Video.aweme_id == aweme_id)
            .values(downloaded=True, local_path=local_path)
        )

    async def get_by_aweme_id(self, aweme_id: str) -> Optional[Video]:
        result = await self.db.execute(
            select(Video)
            .where(Video.aweme_id == aweme_id)
            .options(selectinload(Video.ai_summary), selectinload(Video.creator))
        )
        return result.scalar_one_or_none()

    async def list_with_filters(
        self, filters: list, page: int = 1, page_size: int = 20
    ) -> tuple[list[Video], int]:
        """通用的多条件过滤查询"""
        q = select(Video)
        count_q = select(func.count()).select_from(Video)
        
        for f in filters:
            q = q.where(f)
            count_q = count_q.where(f)

        total = (await self.db.execute(count_q)).scalar()
        result = await self.db.execute(
            q.order_by(Video.created_at.desc()) # 按采集时间倒序，确保最新采集的在最前
            .offset((page - 1) * page_size)
            .limit(page_size)
            .options(selectinload(Video.ai_summary), selectinload(Video.creator))
        )
        return result.scalars().all(), total

    async def delete_by_aweme_id(self, aweme_id: str):
        video = await self.get_by_aweme_id(aweme_id)
        if video:
            await self.db.delete(video)


# ─── AISummary ─────────────────────────────────────────────────────────────

class AISummaryRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_or_update(self, aweme_id: str, **kwargs) -> AISummary:
        existing = await self.db.execute(
            select(AISummary).where(AISummary.aweme_id == aweme_id)
        )
        summary = existing.scalar_one_or_none()
        if summary:
            for k, v in kwargs.items():
                setattr(summary, k, v)
        else:
            summary = AISummary(aweme_id=aweme_id, **kwargs)
            self.db.add(summary)
        await self.db.flush()
        await self.db.refresh(summary)
        return summary


# ─── NotificationConfig ────────────────────────────────────────────────────

class NotificationRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(self) -> list[NotificationConfig]:
        result = await self.db.execute(select(NotificationConfig))
        return result.scalars().all()

    async def list_enabled_by_event(self, event: str) -> list[NotificationConfig]:
        result = await self.db.execute(
            select(NotificationConfig).where(NotificationConfig.enabled == True)
        )
        configs = result.scalars().all()
        return [c for c in configs if event in c.events]

    async def get_by_id(self, config_id: int) -> Optional[NotificationConfig]:
        result = await self.db.execute(
            select(NotificationConfig).where(NotificationConfig.id == config_id)
        )
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> NotificationConfig:
        config = NotificationConfig(**kwargs)
        self.db.add(config)
        await self.db.flush()
        await self.db.refresh(config)
        return config

    async def update(self, config_id: int, **kwargs) -> Optional[NotificationConfig]:
        await self.db.execute(
            update(NotificationConfig).where(NotificationConfig.id == config_id).values(**kwargs)
        )
        return await self.get_by_id(config_id)

    async def delete(self, config_id: int):
        config = await self.get_by_id(config_id)
        if config:
            await self.db.delete(config)


# ─── CrawlLog ──────────────────────────────────────────────────────────────

class CrawlLogRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **kwargs) -> CrawlLog:
        log = CrawlLog(**kwargs)
        self.db.add(log)
        await self.db.flush()
        await self.db.refresh(log)
        return log

    async def update(self, log_id: int, **kwargs):
        await self.db.execute(
            update(CrawlLog).where(CrawlLog.id == log_id).values(**kwargs)
        )

    async def list_by_creator(self, creator_id: int, limit: int = 20) -> list[CrawlLog]:
        result = await self.db.execute(
            select(CrawlLog).where(CrawlLog.creator_id == creator_id)
            .order_by(CrawlLog.run_at.desc()).limit(limit)
        )
        return result.scalars().all()

    async def list_all(self, page: int = 1, page_size: int = 30) -> tuple[list[CrawlLog], int]:
        total = (await self.db.execute(select(func.count()).select_from(CrawlLog))).scalar()
        result = await self.db.execute(
            select(CrawlLog).order_by(CrawlLog.run_at.desc())
            .offset((page - 1) * page_size).limit(page_size)
            .options(selectinload(CrawlLog.creator))
        )
        return result.scalars().all(), total


# ─── SystemSetting ─────────────────────────────────────────────────────────

class SystemSettingRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_value(self, key: str, default: str = "") -> str:
        from db.models import SystemSetting
        result = await self.db.execute(select(SystemSetting).where(SystemSetting.key == key))
        setting = result.scalar_one_or_none()
        return setting.value if setting else default

    async def set_value(self, key: str, value: str, description: Optional[str] = None):
        from db.models import SystemSetting
        existing = await self.db.execute(select(SystemSetting).where(SystemSetting.key == key))
        setting = existing.scalar_one_or_none()
        if setting:
            setting.value = value
            if description:
                setting.description = description
        else:
            setting = SystemSetting(key=key, value=value, description=description)
            self.db.add(setting)
        await self.db.flush()


# ─── User ──────────────────────────────────────────────────────────────────

class UserRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> User:
        user = User(**kwargs)
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def list_all(self) -> list[User]:
        result = await self.db.execute(select(User))
        return result.scalars().all()

    async def update(self, user_id: int, **kwargs):
        await self.db.execute(
            update(User).where(User.id == user_id).values(**kwargs)
        )

    async def delete(self, user_id: int):
        user = await self.get_by_id(user_id)
        if user:
            await self.db.delete(user)


# ─── LoginLog ──────────────────────────────────────────────────────────────

class LoginLogRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **kwargs) -> LoginLog:
        log = LoginLog(**kwargs)
        self.db.add(log)
        await self.db.flush()
        return log

    async def list_latest(self, limit: int = 50) -> list[LoginLog]:
        result = await self.db.execute(
            select(LoginLog).order_by(LoginLog.created_at.desc()).limit(limit)
        )
        return result.scalars().all()


# ─── PlatformAccount ──────────────────────────────────────────────────────

class AccountRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_platform(self, platform: str) -> list[PlatformAccount]:
        result = await self.db.execute(
            select(PlatformAccount).where(PlatformAccount.platform == platform)
        )
        return result.scalars().all()

    async def get_by_id(self, account_id: int) -> Optional[PlatformAccount]:
        result = await self.db.execute(
            select(PlatformAccount).where(PlatformAccount.id == account_id)
        )
        return result.scalar_one_or_none()

    async def get_next_available(self, platform: str) -> Optional[PlatformAccount]:
        """
        核心调度算法：获取最久未使用的有效账号实现轮询
        """
        result = await self.db.execute(
            select(PlatformAccount)
            .where(PlatformAccount.platform == platform)
            .where(PlatformAccount.status == "active")
            .order_by(PlatformAccount.last_used_at.asc().nulls_first())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> PlatformAccount:
        account = PlatformAccount(**kwargs)
        self.db.add(account)
        await self.db.flush()
        await self.db.refresh(account)
        return account

    async def update(self, account_id: int, **kwargs) -> Optional[PlatformAccount]:
        await self.db.execute(
            update(PlatformAccount).where(PlatformAccount.id == account_id).values(**kwargs)
        )
        return await self.get_by_id(account_id)

    async def update_last_used(self, account_id: int):
        await self.db.execute(
            update(PlatformAccount)
            .where(PlatformAccount.id == account_id)
            .values(last_used_at=datetime.now())
        )

    async def delete(self, account_id: int):
        account = await self.get_by_id(account_id)
        if account:
            await self.db.delete(account)

