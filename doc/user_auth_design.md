# 用户管理与安全认证系统设计文档

本文档详细说明了抖音采集平台中用户管理模块的实现方案、安全设计及核心细节。

## 1. 总体设计目标
*   **安全性**：防御暴力破解、密码泄露及跨站请求攻击。
*   **审计性**：完整记录所有登录行为（包括 IP、地理位置、设备信息）。
*   **易扩展**：采用 JWT 无状态鉴权，方便未来支持多节点部署。

---

## 2. 安全防御架构

### 2.1 密码存储安全 (Bcrypt)
系统采用 `Bcrypt` 算法对用户密码进行加盐哈希处理。
*   **不可逆性**：即便数据库被窃取，攻击者也无法还原原始密码。
*   **抗彩虹表**：自动加盐机制确保相同密码的哈希值不同。

### 2.2 暴力破解防护 (Rate Limiting)
针对登录接口 (`/api/auth/login`) 应用了基于 IP 的频率限制：
*   **策略**：5 次尝试 / 每分钟。
*   **效果**：有效拦截自动化字典攻击和暴力撞库。

### 2.3 JWT 无状态认证
使用 JSON Web Token (JWT) 代替传统的 Session。
*   **Header 传递**：令牌通过 HTTP `Authorization: Bearer <token>` 头部传递，天然免受 CSRF（跨站请求伪造）攻击。
*   **过期控制**：默认有效期 24 小时，过期需重新登录。

---

## 3. 数据库模型设计

### 3.1 User 表
存储账号基础信息：
| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `username` | String | 唯一用户名 |
| `hashed_password` | String | Bcrypt 哈希值 |
| `role` | String | 角色 (admin/user) |
| `is_active` | Boolean | 账号启用状态 |

### 3.2 LoginLog 表
存储审计日志：
| 字段 | 类型 | 说明 |
| :--- | :--- | :--- |
| `ip_address` | String | 登录来源 IP |
| `location` | String | 地理位置（省份/城市） |
| `user_agent` | String | 浏览器与操作系统信息 |
| `status` | String | success / failed |
| `error_msg` | String | 失败原因（如密码错误） |

---

## 4. 核心逻辑细节

### 4.1 IP 定位实现
后端集成异步地理位置查询工具 (`backend/utils/ip_lookup.py`)：
*   调用 `ip-api.com` 接口获取中文归属地。
*   自动识别 `127.0.0.1` 为“本地回环”。

### 4.2 前端拦截体系
*   **请求拦截**：Axios 自动从 `localStorage` 获取 Token 并注入 Header。
*   **响应拦截**：当后端返回 `401 Unauthorized` 时，前端自动清除本地 Token 并重定向至登录页。
*   **导航守卫**：Vue Router 检查 `meta.public` 属性，阻止未登录用户进入后台页面。

### 4.3 初始管理员初始化
系统在 `main.py` 的 `lifespan` 阶段执行自检：
*   如果 `users` 表为空，自动创建 `admin` 账号。
*   默认密码：`admin123`（建议首次登录后立即修改）。

---

## 5. 维护与配置

### 5.1 修改加密密钥
在 `.env` 或 `config.py` 中修改 `SECRET_KEY`。修改后，所有已签发的 Token 将立即失效，所有用户需重新登录。

### 5.2 审计日志查看
管理员可以通过接口 `GET /api/auth/logs` 获取最近 50 条登录记录，前端已在布局组件中预留扩展位置。

---

## 6. 开发依赖清单
*   `passlib[bcrypt]`：密码加密。
*   `python-jose[cryptography]`：JWT 核心库。
*   `slowapi`：FastAPI 频率限制中间件。
*   `httpx`：异步 IP 定位请求。
*   `pinia`：前端状态持久化。
