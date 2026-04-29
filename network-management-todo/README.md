# 网络管理版待办提醒（独立整理）

本目录是从 `todo_reminder` 项目中抽离出的联网管理子项目，包含服务端、客户端、测试与发布产物。

## 项目结构

- `src/server`：Flask 服务端（认证、用户、任务 API，SQLite）
- `src/client`：联网客户端逻辑（调用服务端 API）
- `src/ui`：Tkinter 界面层
- `src/core`：核心模型与提醒能力
- `src/shared`：共享数据模型
- `scripts`：启动脚本（服务端/客户端）
- `tests`：集成测试脚本
- `docs`：说明文档与测试报告
- `release`：历史打包产物

## 环境要求

- Windows 10/11
- Python 3.11（已验证）
- 网络连通到服务端地址（默认本机 `127.0.0.1:5000`）

推荐 Python：
- 首选：`C:\Users\hopemyl\Downloads\smart-desktop-todo\components\project\todo_reminder\venv\Scripts\python.exe`
- 备用：`D:\py311\python.exe`

## 安装依赖

> 不使用 `py -3`，直接调用明确 Python 路径。

```powershell
$env:PYTHONUTF8='1'
C:\Users\hopemyl\Downloads\smart-desktop-todo\components\project\todo_reminder\venv\Scripts\python.exe -m pip install -r requirements.txt
```

## 启动服务端

```powershell
C:\Users\hopemyl\Downloads\smart-desktop-todo\components\project\todo_reminder\venv\Scripts\python.exe scripts/start_server.py
```

默认监听：`http://0.0.0.0:5000`

## 启动客户端

```powershell
C:\Users\hopemyl\Downloads\smart-desktop-todo\components\project\todo_reminder\venv\Scripts\python.exe scripts/start_client.py
```

## 默认账号

- 管理员用户名：`admin`
- 管理员密码：`admin123`
- 默认管理员 IP：`127.0.0.1`

说明：该系统按 IP 识别身份，管理员需密码登录。

## API 健康检查

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:5000/api/health -Method GET
```

期望返回：`{"status":"healthy"}`

## 测试命令

### 1) 静态编译与导入验证

```powershell
C:\Users\hopemyl\Downloads\smart-desktop-todo\components\project\todo_reminder\venv\Scripts\python.exe -m compileall src
C:\Users\hopemyl\Downloads\smart-desktop-todo\components\project\todo_reminder\venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'src'); sys.path.insert(0,'src/server'); import app, client.api_client, core.models; print('IMPORT_OK')"
```

### 2) 集成测试脚本

```powershell
C:\Users\hopemyl\Downloads\smart-desktop-todo\components\project\todo_reminder\venv\Scripts\python.exe tests/test_integration.py --server http://127.0.0.1:5000
```

### 3) 核心 API E2E（登录、任务增查改删）

可参考 `docs` 报告中的命令与结果摘要。

## 停止进程

若服务端在后台启动，可按进程名或 PID 停止：

```powershell
Get-Process -Name python | Stop-Process -Force
# 或
Stop-Process -Id <PID> -Force
```

## 常见问题

### 1) `py` 启动器异常（例如 `py -3` 不可用）

绕过方式：不要使用 `py -3`，直接使用明确路径的 `python.exe`（见上文首选/备用路径）。

### 2) `pip install -r requirements.txt` 报编码错误（GBK/UnicodeDecodeError）

先设置 UTF-8 再安装：

```powershell
$env:PYTHONUTF8='1'
<python.exe> -m pip install -r requirements.txt
```

### 3) 删除任务失败

`DELETE /api/todos/{id}` 需要请求体包含管理员密码：

```json
{"admin_password":"admin123"}
```

否则会返回 `403`（业务限制，非系统故障）。
