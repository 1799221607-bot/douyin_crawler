
import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
try:
    from backend.database import AsyncSessionLocal
    from backend.db.models import Video
except ImportError:
    from database import AsyncSessionLocal
    from db.models import Video

async def fix_video_times():
    print("开始检查并修复视频时间偏移...")
    async with AsyncSessionLocal() as session:
        # 查询所有视频
        result = await session.execute(select(Video))
        videos = result.scalars().all()
        
        now = datetime.now()
        count = 0
        
        for video in videos:
            if video.published_at:
                # 如果时间处于未来，说明被错误地加了 8 小时
                if video.published_at > now + timedelta(hours=1):
                    print(f"检测到异常时间: {video.title[:20]} -> {video.published_at}")
                    # 减去 8 小时
                    video.published_at = video.published_at - timedelta(hours=8)
                    count += 1
        
        if count > 0:
            await session.commit()
            print(f"修复完成！共处理 {count} 条记录。")
        else:
            print("未检测到需要修复的数据。")

if __name__ == "__main__":
    # 注意：确保在 backend 目录下运行
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    asyncio.run(fix_video_times())
