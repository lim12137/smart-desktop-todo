@echo off
chcp 65001 >nul
cd /d "%~dp0"
D:\py311\python.exe start_client.py
if %errorlevel% neq 0 (
    echo.
    echo 客户端启动失败，错误代码: %errorlevel%
    pause
)
