@echo off
chcp 65001 >nul
echo =====================================
echo    待办事项提醒程序 - 打包工具
echo =====================================

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python环境，请先安装Python
    pause
    exit /b 1
)

REM 检查PyInstaller
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo 正在安装PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo 错误: PyInstaller安装失败
        pause
        exit /b 1
    )
)

REM 检查必要文件
if not exist "main.py" (
    echo 错误: 请在项目根目录运行此脚本
    pause
    exit /b 1
)

if not exist "build.spec" (
    echo 错误: 找不到 build.spec 文件
    pause
    exit /b 1
)

REM 清理旧文件
echo 正在清理旧文件...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
for /r %%i in (*.pyc) do del "%%i" 2>nul
for /d %%i in (__pycache__) do rmdir /s /q "%%i" 2>nul

REM 开始打包
echo 开始打包...
pyinstaller build.spec

if errorlevel 1 (
    echo 错误: 打包失败
    pause
    exit /b 1
)

echo.
echo ✅ 打包完成！
echo 输出目录: %cd%\dist\待办事项提醒\
echo.
if exist "dist\待办事项提醒\待办事项提醒.exe" (
    echo 可执行文件: dist\待办事项提醒\待办事项提醒.exe
    echo 文件大小:
    dir "dist\待办事项提醒\待办事项提醒.exe" | find "待办事项提醒.exe"
)
echo.
echo 按任意键打开输出目录...
pause >nul
if exist "dist\待办事项提醒" (
    explorer "dist\待办事项提醒"
)

pause