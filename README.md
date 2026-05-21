# Smart Desktop Todo - 智能桌面待办事项提醒系统

基于 Python + tkinter 的桌面待办事项管理应用，支持单机模式和 C/S 多用户协作模式。

## 功能特性

- **待办事项管理** — 创建、编辑、删除、状态跟踪
- **智能提醒** — 根据截止日期自动提醒（7天/3天/逾期）
- **优先级分类** — 低/中/高/紧急四级优先级
- **系统托盘** — 最小化到托盘，后台运行
- **Toast 通知** — Windows 系统原生弹窗提醒
- **C/S 多用户** — 客户端-服务器架构，支持团队协作
- **IP 自动识别** — 局域网内自动识别身份，管理员密码登录

## 项目结构

```
├── main.py                # 单机模式入口
├── start_client.py        # 客户端启动脚本
├── start_server.py        # 服务端启动脚本
├── build.py               # PyInstaller 打包脚本
├── core/                  # 核心逻辑（单机模式）
│   ├── models.py          # 数据模型
│   ├── data_manager.py    # 数据管理
│   └── reminder.py        # 提醒服务
├── ui/                    # 界面模块
│   ├── main_window.py     # 主窗口
│   ├── todo_editor.py     # 编辑对话框
│   ├── settings_window.py # 设置窗口
│   └── styles.py          # 样式定义
├── client/                # 客户端模块（C/S 模式）
│   ├── main.py            # 客户端入口
│   ├── api_client.py      # API 通信
│   ├── connect_dialog.py  # 连接对话框
│   ├── login_dialog.py    # 登录对话框
│   ├── cache.py           # 本地缓存
│   ├── performance.py     # 性能优化
│   └── reminder_poller.py # 提醒轮询
├── server/                # 服务端模块（C/S 模式）
│   ├── app.py             # Flask 应用
│   ├── database.py        # SQLite 数据库
│   ├── reminder_service.py# 后台提醒服务
│   └── api/               # REST API
│       ├── auth.py        # 认证
│       ├── todos.py       # 任务管理
│       └── users.py       # 用户管理
└── shared/                # 共享模块
    └── models.py          # 通用数据模型
```

## 快速开始

### 环境要求

- Python 3.7+
- Windows 系统（系统托盘和 Toast 通知功能依赖 Windows）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 单机模式

```bash
python main.py
```

### C/S 多用户模式

启动服务端：

```bash
python start_server.py
```

启动客户端：

```bash
python start_client.py
```

### 打包为可执行文件

```bash
python build.py
```

## 技术栈

| 组件 | 技术 |
|------|------|
| 客户端 UI | tkinter, tkcalendar |
| 服务端 | Flask, Flask-CORS |
| 认证 | PyJWT + IP 识别 |
| 数据库 | SQLite |
| 通知 | pystray, win10toast |
| 打包 | PyInstaller |

## License

MIT
