from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, String, Text, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Creator(Base):
    """博主/采集目标"""
    __tablename__ = "creators"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    user_url: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    sec_user_id: Mapped[Optional[str]] = mapped_column(String(200))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    follower_count: Mapped[Optional[int]] = mapped_column(Integer)
    interval_min: Mapped[int] = mapped_column(Integer, default=60, comment="采集间隔（分钟）")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    download_video: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否下载视频文件")
    priority: Mapped[int] = mapped_column(Integer, default=1, comment="采集优先级 (0:低, 1:中, 2:高)")
    is_fast_mode: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否开启秒删抢拍模式")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    videos: Mapped[list["Video"]] = relationship("Video", back_populates="creator")
    crawl_logs: Mapped[list["CrawlLog"]] = relationship("CrawlLog", back_populates="creator")


class Video(Base):
    """视频记录"""
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    creator_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("creators.id"))
    source_type: Mapped[str] = mapped_column(String(50), default="creator", comment="creator | keyword")
    aweme_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, comment="抖音视频唯一ID")
    title: Mapped[Optional[str]] = mapped_column(String(500))
    desc: Mapped[Optional[str]] = mapped_column(Text)
    duration: Mapped[Optional[int]] = mapped_column(Integer, comment="视频时长（秒）")
    cover_url: Mapped[Optional[str]] = mapped_column(String(1000))
    play_url: Mapped[Optional[str]] = mapped_column(String(1000), comment="无水印播放链接")
    like_count: Mapped[Optional[int]] = mapped_column(Integer)
    comment_count: Mapped[Optional[int]] = mapped_column(Integer)
    share_count: Mapped[Optional[int]] = mapped_column(Integer)
    collect_count: Mapped[Optional[int]] = mapped_column(Integer)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    local_path: Mapped[Optional[str]] = mapped_column(String(500))
    downloaded: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_processed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    creator: Mapped[Optional["Creator"]] = relationship("Creator", back_populates="videos")
    ai_summary: Mapped[Optional["AISummary"]] = relationship("AISummary", back_populates="video", uselist=False)


class AISummary(Base):
    """AI 总结记录"""
    __tablename__ = "ai_summaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    aweme_id: Mapped[str] = mapped_column(String(100), ForeignKey("videos.aweme_id"), unique=True)
    transcript: Mapped[Optional[str]] = mapped_column(Text, comment="语音转文字结果")
    summary: Mapped[Optional[str]] = mapped_column(Text, comment="AI 总结内容")
    keywords: Mapped[Optional[str]] = mapped_column(Text, comment="关键词 JSON")
    model: Mapped[Optional[str]] = mapped_column(String(100), comment="使用的 AI 模型")
    status: Mapped[str] = mapped_column(String(50), default="pending", comment="pending|processing|done|failed")
    error_msg: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=func.now())

    video: Mapped["Video"] = relationship("Video", back_populates="ai_summary")


class NotificationConfig(Base):
    """通知渠道配置"""
    __tablename__ = "notification_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel: Mapped[str] = mapped_column(String(50), comment="feishu | email | wechat_mp | telegram")
    name: Mapped[str] = mapped_column(String(100), comment="配置别名")
    config_json: Mapped[str] = mapped_column(Text, comment="渠道特定配置 JSON")
    events: Mapped[str] = mapped_column(Text, default='["new_video"]', comment="订阅事件列表 JSON")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class CrawlLog(Base):
    """采集任务日志"""
    __tablename__ = "crawl_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    creator_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("creators.id"))
    source_type: Mapped[str] = mapped_column(String(50), default="creator")
    run_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    new_count: Mapped[int] = mapped_column(Integer, default=0)
    total_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(50), comment="success | failed | running")
    error_msg: Mapped[Optional[str]] = mapped_column(Text)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)

    creator: Mapped[Optional["Creator"]] = relationship("Creator", back_populates="crawl_logs")
class SystemSetting(Base):
    """系统全局设置"""
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, comment="设置项键名")
    value: Mapped[str] = mapped_column(Text, nullable=False, comment="设置项内容")
    description: Mapped[Optional[str]] = mapped_column(String(200))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class User(Base):
    """用户信息"""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user", comment="admin | user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class LoginLog(Base):
    """登录日志"""
    __tablename__ = "login_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(50))
    location: Mapped[Optional[str]] = mapped_column(String(100))
    user_agent: Mapped[Optional[str]] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(20), comment="success | failed")
    error_msg: Mapped[Optional[str]] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class PlatformAccount(Base):
    """多平台采集账号池"""
    __tablename__ = "platform_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(50), nullable=False, comment="douyin | xhs")
    username: Mapped[str] = mapped_column(String(100), nullable=False, comment="账号备注名")
    cookie: Mapped[str] = mapped_column(Text, nullable=False)
    proxy_url: Mapped[Optional[str]] = mapped_column(String(500), comment="绑定的固定代理")
    ua: Mapped[Optional[str]] = mapped_column(String(500), comment="绑定的 User-Agent")
    status: Mapped[str] = mapped_column(String(50), default="active", comment="active|expired|banned")
    fail_count: Mapped[int] = mapped_column(Integer, default=0)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, comment="用于轮询调度")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
