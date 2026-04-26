# 多平台账号池与高频抢拍采集系统实施方案

## 1. 目标概述
本项目旨在构建一个高稳定性、可扩展的账号管理与采集系统。解决单账号易封禁、多平台难管理以及“秒删”视频抓取不及时的问题。

## 2. 核心组件设计

### 2.1 账号池管理器 (Account Pool Manager)
*   **多平台支持**：通过接口化设计支持 Douyin, XHS, Weibo 等。
*   **账号接力 (Account Relay)**：实现轮询调度算法。如果博主 A 需要 1 分钟采集一次，系统将从池中循环调取不同账号，确保单个账号的访问频率处于安全阈值。
*   **环境指纹绑定**：Cookie 必须与获取时的 User-Agent 强绑定，并在请求时完整还原。

### 2.2 代理绑定策略 (Static Proxy Binding)
*   **独享出口**：每个账号可绑定一个固定代理 URL。
*   **自动漂移**：若代理失效，系统支持将账号自动迁移至备用代理池。

### 2.3 高频抢拍系统 (Instant Catch)
*   **博主分级**：`High` 优先级博主进入“快车道”调度。
*   **轻量采样**：高频探测时仅拉取最新 1 条视频 ID，发现不一致后才触发全量数据拉取。

---

## 3. 数据库模型变更

### 3.1 [NEW] `PlatformAccount`
| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `platform` | String | 平台名 (douyin/xhs) |
| `username` | String | 账号名称/备注 |
| `cookie` | Text | 原始 Cookie 字符串 |
| `proxy_url` | String | 绑定的代理 (http://...) |
| `ua` | String | 绑定的 User-Agent |
| `status` | String | active/expired/banned/error |
| `last_used_at` | DateTime | 实现负载均衡的关键 |
| `fail_count` | Integer | 连续失败次数，用于自动标记失效 |

### 3.2 [UPDATE] `Creator`
*   新增 `priority`: `int` (0: Low, 1: Normal, 2: High)
*   新增 `is_fast_mode`: `bool` (是否开启秒删抢拍)

---

## 4. 接口与逻辑流

### 4.1 获取可用账号流程
1.  系统向账号池请求：`get_valid_account(platform="douyin")`。
2.  池管理器执行 SQL：`ORDER BY last_used_at ASC` 找出最久未用的有效账号。
3.  返回账号、Cookie、代理及 UA。
4.  执行采集，并根据结果调用 `report_success()` 或 `report_failure()`。

### 4.2 高频探测流程
1.  每 X 分钟触发探测任务。
2.  通过 `FastProbe` 仅请求第一条视频 ID。
3.  若 ID 未在 `Video` 表中出现，立即推入“极速下载队列”。

---

## 5. 验证计划

### 5.1 自动化测试
*   验证 10 个账号轮询采集 1 个博主时，各账号的访问间隔是否符合预期。
*   模拟代理失效情况，检查系统是否能正确拦截请求并记录日志。

### 5.2 手动验证
*   在前端手动添加 5 个抖音测试账号，观察“账号池”看板中的状态切换。
*   发布测试视频并迅速删除，验证系统是否能在 2 分钟内完成抓取存档。

---

## 6. 用户评审要点 (User Review Required)
> [!IMPORTANT]
> **代理成本**：高频采集建议配合付费代理使用，系统已预留 `proxy_url` 接口。
> **验证码处理**：本系统暂不包含全自动打码（如滑块验证），当账号需要手动验证时，会通过飞书/邮件发出告警，引导管理员手动干预。
