from datetime import datetime
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from db.repository import AccountRepo
from db.models import PlatformAccount

class AccountManager:
    """
    账号池管理器，负责账号的轮询获取和状态反馈
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AccountRepo(db)

    async def get_account_for_task(self, platform: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        获取一个可用的账号信息
        返回: (cookie, proxy_url, user_agent)
        """
        account = await self.repo.get_next_available(platform)
        if not account:
            logger.warning(f"[AccountManager] {platform} 账号池中无可用账号！")
            # 触发通知：账号池枯竭
            await self._notify_account_issue(platform, "账号池已空，无法执行采集任务")
            return None, None, None
        
        # 更新最后使用时间，实现轮询
        await self.repo.update_last_used(account.id)
        
        logger.info(f"[AccountManager] 为任务分配账号: {account.username} (ID: {account.id})")
        return account.cookie, account.proxy_url, account.ua

    async def report_status(self, account_cookie: str, platform: str, success: bool, error_msg: Optional[str] = None):
        """
        反馈账号执行结果，用于故障隔离
        """
        # 简单起见，通过 Cookie 匹配账号
        from sqlalchemy import select
        from db.models import PlatformAccount
        
        result = await self.db.execute(
            select(PlatformAccount).where(PlatformAccount.cookie == account_cookie)
        )
        account = result.scalar_one_or_none()
        
        if not account:
            return

        if success:
            if account.fail_count > 0:
                await self.repo.update(account.id, fail_count=0)
        else:
            new_fail_count = account.fail_count + 1
            update_data = {"fail_count": new_fail_count}
            
            # 如果连续失败超过 5 次，标记为失效
            if new_fail_count >= 5:
                logger.error(f"[AccountManager] 账号 {account.username} 连续失败次数过多，已自动下线")
                update_data["status"] = "error"
                # 触发通知：账号异常下线
                await self._notify_account_issue(platform, f"账号 {account.username} 连续失败 5 次，已自动下线")
            
            await self.repo.update(account.id, **update_data)
        
        await self.db.flush()

    async def _notify_account_issue(self, platform: str, message: str):
        """发送账号异常通知"""
        try:
            from db.repository import NotificationRepo
            from notifier.registry import notifier_registry
            notify_repo = NotificationRepo(self.db)
            configs = await notify_repo.list_enabled_by_event("account_expired")
            if configs:
                await notifier_registry.dispatch(
                    "account_expired",
                    {"platform": platform, "message": message, "time": datetime.now().isoformat()},
                    configs
                )
        except Exception as e:
            logger.error(f"[AccountManager] 发送账号异常通知失败: {e}")
