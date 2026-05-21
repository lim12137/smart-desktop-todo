@echo off
chcp 65001 >nul
title 待办事项提醒系统 - 客户端

echo ============================================================
echo 待办事项提醒系统 - 客户端启动
echo ============================================================
echo.

REM 切换到项目目录
cd /d "%~dp0"

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.7+
    pause
    exit /b 1
)

REM 检查依赖是否安装
echo 检查依赖...
python -c "import requests, tkinter" >nul 2>&1
if errorlevel 1 (
    echo 安装依赖中...
    pip install requests
    if errorlevel 1 (
        echo 错误: 依赖安装失败
        pause
        exit /b 1
    )
)

REM 启动客户端
echo.
echo 启动客户端...
echo.
python start_client.py

pause
