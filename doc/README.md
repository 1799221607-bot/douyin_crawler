# 🎬 抖音视频采集平台 - 快速上手指南

本指南将帮助您在本地环境（Windows）手动部署并运行该项目。

---

## 🛠️ 1. 环境准备

在开始之前，请确保您的电脑已安装以下工具：

1.  **Python 3.11+** (建议 3.11.9，请勿使用 3.14 等预览版)
    *   安装时务必勾选 `Add Python to PATH`。
2.  **Node.js 18+** (用于运行前端界面)
3.  **FFmpeg** (必须安装，否则视频无法合并)
    *   下载后将 `bin` 目录路径添加到系统环境变量 `PATH` 中。
    *   验证：在终端输入 `ffmpeg -version` 有输出即成功。

---

## ⚙️ 2. 配置文件设置

1.  进入项目根目录。
2.  确认存在 `.env` 文件（如果没有，请复制 `.env.example` 并重命名）。
3.  **关键配置项**：
    *   `COOKIE`: 抖音网页版的 Cookie（见下文获取方式）。
    *   `AI_PROVIDER`: 选择 `nvidia` / `glm` / `openai`。
    *   `OPENAI_API_KEY`: 对应的 AI 平台密钥。

### 如何获取抖音 Cookie？
1.  电脑浏览器打开 [douyin.com](https://www.douyin.com) 并登录。
2.  按 `F12` 打开开发者工具 -> `网络 (Network)` -> 刷新页面。
3.  点击任意请求，在 `请求标头 (Request Headers)` 中找到 `Cookie`。
4.  复制那一长串字符串到 `.env` 的 `COOKIE=` 后面。

---

## 🚀 3. 启动步骤

由于不使用 Docker，您需要打开 **两个终端窗口**。

### 窗口 A：启动后端 (FastAPI)
```powershell
cd backend
# 创建虚拟环境
python -m venv venv
# 激活环境
.\venv\Scripts\activate
# 安装依赖
pip install -r requirements.txt
# 启动
python main.py
```

### 窗口 B：启动前端 (Vue3)
```powershell
cd frontend
# 安装依赖
npm install
# 启动开发服务器
npm run dev
```

---

## 🖥️ 4. 访问系统

*   **前端地址**：[http://localhost:5173](http://localhost:5173)
*   **后端接口文档**：[http://localhost:8000/docs](http://localhost:8000/docs)

---

## ❓ 5. 常见问题排查

### Q: 提示 "Unsupported URL" 报错？
1.  确保博主主页链接正确（形如 `https://www.douyin.com/user/MS4wLjAB...`）。
2.  执行 `pip install -U yt-dlp` 更新解析引擎。
3.  检查 `.env` 中的 `COOKIE` 是否已过期（失效会导致解析失败）。

### Q: 视频下载后无法播放或没有声音？
*   请检查是否正确安装了 **FFmpeg**。如果没有它，系统无法将视频流和音频流合并。

### Q: 如何更新依赖？
*   后端：在 `venv` 激活状态下执行 `pip install -r requirements.txt`。
*   前端：执行 `npm install`。
