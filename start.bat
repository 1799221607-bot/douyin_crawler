@echo off
title 抖音采集平台启动器
echo ==========================================
echo    🎬 抖音采集平台 - 一键启动脚本
echo ==========================================

:: 检查 Python 是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.9+ 
    pause
    exit
)

:: 进入后端目录
cd backend

:: 创建虚拟环境 (如果不存在)
if not exist venv (
    echo [1/3] 正在创建虚拟环境...
    python -m venv venv
)

:: 激活虚拟环境并安装依赖
echo [2/3] 正在检查/安装依赖...
call venv\Scripts\activate
pip install -r requirements.txt

:: 启动程序
echo [3/3] 正在启动服务...
echo 请在浏览器访问: http://localhost:8000
python main.py

pause
