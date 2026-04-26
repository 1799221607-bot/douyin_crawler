# 支持小红书采集功能实现计划

该计划旨在扩展当前的采集架构，使其支持小红书（Xiaohongshu）图文和视频的采集。由于小红书的风控机制较严，我们将利用已安装的 `DrissionPage` 的**网络请求监听（Network Interception）**功能，通过模拟真实浏览器访问主页并拦截后端 API 返回的 JSON 数据来实现稳定采集。

## 核心确认事项

> [!IMPORTANT]
> 1. **数据库结构变更**：我们需要对现有的 `Creator`（博主）和 `Video`（原视频表，将更名为更通用的概念，或增加字段）进行字段扩展。这会触发数据库结构的变更。
> 2. **浏览器自动化要求**：小红书的采集将强依赖于桌面弹出的 Chrome/Edge 浏览器窗口（`DrissionPage`）。采集小红书时，系统会自动打开一个隐式或显式窗口来滑动页面并拦截数据。
> 3. **需要登录**：和抖音类似，小红书采集需要您事先在弹出的浏览器中登录一次小红书网页版（后续可自动复用本地浏览器状态或提取 Cookie）。

## 开放性问题探讨

> [!WARNING]
> 1. **历史数据兼容**：为了兼容旧的抖音数据，我计划在 `Video` 表中新增 `platform` (平台) 和 `post_type` (帖子类型: video/image) 以及 `images` (图片列表 JSON) 字段，而不是彻底重命名表名。您是否同意这种向后兼容的做法？
> 2. **小红书下载限制**：小红书图文包含多张图片（可能无水印），而视频则可能较难获取无水印直链。对于小红书，默认下载模式是将所有图片下载到本地文件夹，视频则尝试下载，这样可以吗？

## 预期修改内容

### 数据库层 (Database Layer)
#### [MODIFY] backend/db/models.py
- `Creator` 表增加字段：
  - `platform`: 平台类型（默认 `'douyin'`，可选 `'xhs'`）
- `Video` 表（保持表名不变以防现有数据丢失，但作为通用的“帖子”表使用）增加字段：
  - `platform`: 平台类型（默认 `'douyin'`）
  - `post_type`: 内容类型（默认 `'video'`，可选 `'image'`）
  - `images`: JSON 字符串，用于存储小红书图文的图片 URL 列表

### 采集器层 (Collector Layer)
#### [NEW] backend/collector/xhs_collector.py
- 实现 `XhsCollector` 继承自 `BaseCollector`。
- **采集逻辑**：使用 `DrissionPage` 访问小红书用户主页，使用 `.listen.start('api/sns/web/v1/user_posted')` 拦截数据包。
- 自动向下滚动页面以触发分页加载，直到获取到所有需要的笔记元数据。
- 提取笔记的 `note_id`、标题、描述、点赞/收藏数、图片列表/视频链接。

#### [MODIFY] backend/collector/registry.py
- 注册新的 `xhs_collector`。

### 调度器层 (Scheduler Layer)
#### [MODIFY] backend/scheduler/engine.py
- 在 `crawl_creator_task` 中，根据 `creator.platform` 动态选择调用 `video` (抖音) 采集器还是 `xhs` (小红书) 采集器。
- 修改存储逻辑，以适配新加入的 `post_type` 和 `images` 字段。

### 前端层 (Frontend Layer)
#### [MODIFY] frontend/src/views/Creators.vue
- 添加平台选择器（抖音/小红书）。
- 列表页增加平台 Icon 区分。

#### [MODIFY] frontend/src/views/Videos.vue
- 修改卡片展示逻辑：如果 `post_type === 'image'`，则展示图片轮播图（Carousel）而不是视频播放器。
- 添加平台徽章。

## 验证计划

### 自动化/手动测试
1. **数据库迁移测试**：重启后端，检查是否自动生成新字段，且不影响旧数据。
2. **小红书采集测试**：在页面上添加一个小红书博主，观察 `DrissionPage` 是否正确打开页面并拦截到笔记列表。
3. **前端渲染测试**：验证小红书图文笔记的展示是否正常（多图轮播）、抖音视频播放是否依然正常。
4. **下载测试**：验证小红书的无水印图片/视频能否正确下载到本地对应的文件夹中。
