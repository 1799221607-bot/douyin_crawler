# 抖音视频采集平台 — 完整实现方案（扩展性重评估版）

## 背景与目标

构建一个**可长期演进**的抖音内容采集平台，不仅支持当前需求（定时采集最新视频），
还需为以下后续扩展提供干净的插件扩展点：

| 扩展方向 | 扩展点设计 |
|----------|------------|
| 关键词检索采集 | `Collector` 插件接口，新增 `KeywordCollector` |
| 采集评论/点赞/收藏 | `DataType` 枚举扩展 + 独立 Collector |
| 微信/邮箱/飞书通知 | `Notifier` 插件接口，每个渠道实现一个类 |
| 视频播放 | 前端集成 `Plyr.js`，后端流式代理接口 |
| 视频 AI 总结 | `AIProcessor` 插件接口，异步队列执行 |

---

## 技术选型（扩展性优先）

| 层级 | 技术 | 理由 |
|------|------|------|
| **后端框架** | `FastAPI` | 高性能，自动 OpenAPI 文档，异步友好 |
| **数据库** | `SQLite → PostgreSQL` | 开发用 SQLite，生产可无缝迁移 |
| **ORM + 迁移** | `SQLAlchemy 2.0` + `Alembic` | 迁移脚本管理，结构演进安全 |
| **异步任务队列** | `Celery` + `Redis` | AI总结、通知等耗时操作异步化 |
| **定时调度** | `APScheduler`（内嵌 FastAPI）| 动态增删任务，频率实时调整 |
| **视频采集** | `yt-dlp` | 稳定、持续更新 |
| **前端框架** | `Vue3` + `Vite` | 现代化，组件复用性好 |
| **UI 组件库** | `Element Plus` | 国内生态完善，文档丰富 |
| **视频播放器** | `Plyr.js` | 轻量，支持自定义样式 |
| **AI 总结** | `OpenAI Whisper`（语音转文字）+ `GPT-4o`（总结）| 可替换为本地模型 |
| **通知** | 插件式（飞书/邮箱/微信公众号）| 每个渠道独立实现 |

---

## 系统架构图

```
┌──────────────────────────────────────────────────────────────────┐
│                        前端 Vue3 Web UI                          │
│  Dashboard | 博主管理 | 视频库(播放) | 任务日志 | 通知配置 | AI总结 │
└────────────────────────────┬─────────────────────────────────────┘
                             │ REST API / WebSocket
┌────────────────────────────▼─────────────────────────────────────┐
│                      FastAPI 后端                                 │
│                                                                  │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────┐ │
│  │  APScheduler│  │  API Routers  │  │   Plugin Registry       │ │
│  │  动态调度器  │  │  /creators   │  │   (Collector/Notifier/  │ │
│  │  每博主独立  │  │  /videos     │  │    AIProcessor 插件管理) │ │
│  │  Job        │  │  /tasks      │  └─────────────────────────┘ │
│  └──────┬──────┘  └──────────────┘                              │
│         │ 触发                                                    │
│  ┌──────▼──────────────────────────────────────────────────────┐ │
│  │              Collector 插件层（可扩展）                       │ │
│  │  VideoCollector | KeywordCollector* | CommentCollector*     │ │
│  └──────────────────────────┬────────────────────────────────┘  │
│                             │                                    │
│  ┌──────────────────────────▼────────────────────────────────┐  │
│  │                    yt-dlp 下载引擎                          │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────┬────────────────────┬───────────────────────┘
                      │                    │
       ┌──────────────▼──┐        ┌────────▼────────────────────┐
       │   SQLite/PgSQL  │        │  Celery Worker + Redis      │
       │  creators       │        │  ┌──────────────────────┐   │
       │  videos         │        │  │ AIProcessorTask      │   │
       │  comments*      │        │  │ (Whisper + GPT总结)  │   │
       │  crawl_logs     │        │  └──────────────────────┘   │
       │  notifications  │        │  ┌──────────────────────┐   │
       └─────────────────┘        │  │ NotifierTask         │   │
                                  │  │ (飞书/邮箱/微信)     │   │
                                  │  └──────────────────────┘   │
                                  └─────────────────────────────┘

* 标注为后续扩展模块
```

---

## 插件接口设计（扩展性核心）

### Collector 插件接口
```python
# collector/base.py
from abc import ABC, abstractmethod

class BaseCollector(ABC):
    """所有采集器的基类，新增采集类型只需继承此类"""
    
    @property
    @abstractmethod
    def collector_type(self) -> str:
        """采集器类型标识, e.g. 'video', 'keyword', 'comment'"""
        pass

    @abstractmethod
    async def collect(self, target: dict, config: dict) -> list[dict]:
        """
        执行采集，返回原始数据列表
        target: {'url': ..., 'sec_user_id': ..., 'keyword': ...}
        config: {'download': True, 'max_count': 50, ...}
        """
        pass

# 当前实现
class VideoCollector(BaseCollector):
    collector_type = "video"
    async def collect(self, target, config): ...

# 后续扩展示例（不改动现有代码）
class KeywordCollector(BaseCollector):
    collector_type = "keyword"
    async def collect(self, target, config): ...

class CommentCollector(BaseCollector):
    collector_type = "comment"
    async def collect(self, target, config): ...
```

### Notifier 插件接口
```python
# notifier/base.py
from abc import ABC, abstractmethod

class BaseNotifier(ABC):
    """所有通知渠道的基类，新增渠道只需继承此类"""
    
    @property
    @abstractmethod
    def channel(self) -> str:
        """渠道标识: 'feishu', 'email', 'wechat_mp', 'telegram'"""
        pass

    @abstractmethod
    async def send(self, event: str, payload: dict, config: dict) -> bool:
        """
        发送通知
        event: 'new_video' | 'crawl_error' | 'ai_summary_done'
        payload: 事件数据
        config: 渠道配置（webhook/token/邮箱地址等）
        """
        pass

# 当前实现
class FeishuNotifier(BaseNotifier):
    channel = "feishu"
    async def send(self, event, payload, config): ...

class EmailNotifier(BaseNotifier):
    channel = "email"
    async def send(self, event, payload, config): ...

# 后续扩展（无需修改现有代码）
class WechatMpNotifier(BaseNotifier):
    channel = "wechat_mp"
    async def send(self, event, payload, config): ...
```

### AIProcessor 插件接口
```python
# ai/base.py
class BaseAIProcessor(ABC):
    @abstractmethod
    async def process(self, video: dict) -> dict:
        """处理视频，返回 AI 结果"""
        pass

class WhisperGPTProcessor(BaseAIProcessor):
    """Whisper 转录 + GPT-4o 总结"""
    async def process(self, video):
        transcript = await self.transcribe(video['local_path'])
        summary = await self.summarize(transcript)
        return {'transcript': transcript, 'summary': summary}
```

---

## 数据库设计（支持后续扩展）

```sql
-- 博主/采集目标表
CREATE TABLE creators (
    id            INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    user_url      TEXT NOT NULL UNIQUE,
    sec_user_id   TEXT,
    avatar_url    TEXT,
    follower_count INTEGER,
    interval_min  INTEGER DEFAULT 60,   -- 采集间隔（分钟）
    enabled       BOOLEAN DEFAULT 1,
    created_at    DATETIME,
    last_run_at   DATETIME
);

-- 关键词采集任务表（后续扩展）
CREATE TABLE keyword_tasks (
    id            INTEGER PRIMARY KEY,
    keyword       TEXT NOT NULL,
    interval_min  INTEGER DEFAULT 60,
    enabled       BOOLEAN DEFAULT 1,
    created_at    DATETIME
);

-- 视频表
CREATE TABLE videos (
    id            INTEGER PRIMARY KEY,
    source_type   TEXT DEFAULT 'creator',  -- 'creator' | 'keyword'
    source_id     INTEGER,                 -- creator_id or keyword_task_id
    aweme_id      TEXT UNIQUE NOT NULL,    -- 去重唯一键
    title         TEXT,
    desc          TEXT,
    duration      INTEGER,
    cover_url     TEXT,
    play_url      TEXT,                    -- 无水印播放链接
    like_count    INTEGER,
    comment_count INTEGER,
    share_count   INTEGER,
    collect_count INTEGER,                 -- 收藏数
    published_at  DATETIME,
    local_path    TEXT,
    downloaded    BOOLEAN DEFAULT 0,
    ai_processed  BOOLEAN DEFAULT 0,
    created_at    DATETIME
);

-- 评论表（后续扩展）
CREATE TABLE comments (
    id            INTEGER PRIMARY KEY,
    aweme_id      TEXT,
    comment_id    TEXT UNIQUE,
    content       TEXT,
    like_count    INTEGER,
    user_nickname TEXT,
    created_at    DATETIME
);

-- AI 总结表
CREATE TABLE ai_summaries (
    id            INTEGER PRIMARY KEY,
    aweme_id      TEXT UNIQUE,
    transcript    TEXT,                    -- 语音转文字
    summary       TEXT,                   -- AI 总结
    keywords      TEXT,                   -- 关键词（JSON）
    model         TEXT,                   -- 使用的模型
    created_at    DATETIME
);

-- 通知渠道配置表
CREATE TABLE notification_configs (
    id            INTEGER PRIMARY KEY,
    channel       TEXT NOT NULL,          -- 'feishu' | 'email' | 'wechat_mp'
    name          TEXT,                   -- 配置名称
    config        TEXT,                   -- JSON 存储渠道特定配置
    events        TEXT,                   -- 订阅的事件列表（JSON）
    enabled       BOOLEAN DEFAULT 1,
    created_at    DATETIME
);

-- 采集日志表
CREATE TABLE crawl_logs (
    id            INTEGER PRIMARY KEY,
    source_type   TEXT,
    source_id     INTEGER,
    run_at        DATETIME,
    new_count     INTEGER,
    status        TEXT,                   -- 'success' | 'failed'
    error_msg     TEXT,
    duration_ms   INTEGER
);
```

---

## 目录结构

```
douyin_crawler/
├── backend/
│   ├── main.py                     # FastAPI 启动入口
│   ├── config.py                   # 全局配置（pydantic-settings）
│   ├── database.py                 # SQLAlchemy engine & session
│   ├── alembic/                    # 数据库迁移脚本
│   │
│   ├── collector/                  # 采集插件
│   │   ├── base.py                 # BaseCollector 接口
│   │   ├── registry.py             # 插件注册表
│   │   ├── video_collector.py      # 博主视频采集（yt-dlp）
│   │   └── keyword_collector.py    # [后续] 关键词采集
│   │
│   ├── notifier/                   # 通知插件
│   │   ├── base.py                 # BaseNotifier 接口
│   │   ├── registry.py             # 插件注册表
│   │   ├── feishu.py               # 飞书 Webhook 通知
│   │   ├── email.py                # 邮件 SMTP 通知
│   │   └── wechat_mp.py            # [后续] 微信公众号通知
│   │
│   ├── ai/                         # AI 处理插件
│   │   ├── base.py                 # BaseAIProcessor 接口
│   │   ├── whisper_gpt.py          # Whisper + GPT 总结
│   │   └── tasks.py                # Celery 异步任务
│   │
│   ├── scheduler/
│   │   ├── engine.py               # APScheduler 封装
│   │   └── jobs.py                 # Job 定义
│   │
│   ├── api/
│   │   ├── creators.py             # 博主 CRUD
│   │   ├── videos.py               # 视频查询 + 流式代理
│   │   ├── tasks.py                # 任务管理
│   │   ├── notifications.py        # 通知配置
│   │   └── ai.py                   # AI 总结触发/查询
│   │
│   └── db/
│       ├── models.py               # SQLAlchemy 模型
│       └── repository.py           # 数据操作封装
│
├── frontend/                       # Vue3 + Vite
│   ├── src/
│   │   ├── views/
│   │   │   ├── Dashboard.vue       # 概览仪表盘
│   │   │   ├── Creators.vue        # 博主管理
│   │   │   ├── Videos.vue          # 视频库 + 播放器
│   │   │   ├── AISummary.vue       # AI 总结查看
│   │   │   ├── Notifications.vue   # 通知配置
│   │   │   └── Logs.vue            # 采集日志
│   │   └── components/
│   │       ├── VideoPlayer.vue     # Plyr.js 视频播放器
│   │       ├── CreatorCard.vue
│   │       └── NotifyChannelCard.vue
│
├── config.yaml                     # 用户配置文件
├── docker-compose.yml              # Redis + 应用一键启动
└── requirements.txt
```

---

## 分阶段实现计划

### 🚀 Phase 1：核心功能（当前实现）
> 目标：跑通完整链路，具备基本可用性

- [x] 项目骨架搭建（FastAPI + Vue3 + SQLite）
- [x] 数据库模型 + Alembic 迁移
- [x] yt-dlp VideoCollector 实现（含增量逻辑）
- [x] APScheduler 动态调度（频率可调）
- [x] 飞书/邮件 Notifier 实现
- [x] 基础 Web UI（博主管理、视频列表、日志）
- [x] 视频播放器集成（Plyr.js）

### 🔧 Phase 2：AI 能力
> 目标：为视频内容增加 AI 价值

- [ ] Celery + Redis 异步任务队列
- [ ] Whisper 语音转文字
- [ ] GPT-4o 视频内容总结
- [ ] AI 总结 Web UI 展示

### 🌐 Phase 3：扩展采集
> 目标：扩展数据维度

- [ ] 关键词搜索采集（KeywordCollector）
- [ ] 评论采集（CommentCollector）
- [ ] 点赞/收藏数据记录

### 📢 Phase 4：通知扩展
> 目标：接入更多推送渠道

- [ ] 微信公众号推送（需服务号）
- [ ] Telegram Bot 通知
