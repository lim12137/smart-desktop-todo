@echo off
chcp 65001 >nul
echo =====================================
echo     测试待办事项提醒程序
echo =====================================

REM 检查可执行文件是否存在
if not exist "dist\待办事项提醒\待办事项提醒.exe" (
    echo 错误: 可执行文件不存在，请先运行打包
    pause
    exit /b 1
)

echo 启动应用程序...
echo 可执行文件路径: %cd%\dist\待办事项提醒\待办事项提醒.exe
echo.

REM 启动应用程序
start "" "%cd%\dist\待办事项提醒\待办事项提醒.exe"

echo.
echo 应用程序已启动！
echo 如果程序正常显示，说明打包成功。
echo.
echo 程序特性：
echo - 多文件格式（79MB）
echo - Python 3.11.3 环境
echo - 包含tkinter支持
echo - 包含所有必要的依赖
echo.
pause