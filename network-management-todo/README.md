# 网络管理版待办提醒（独立整理）

本目录从 `todo_reminder` 项目中抽离“后期改造的联网管理模式”相关代码、文档、测试与发布产物，保持原项目不变。

## 目录结构

- `src/server`：Flask 服务端、API、数据库初始化
- `src/client`：联网客户端逻辑
- `src/ui`：Tkinter 界面
- `src/shared`：共享模型
- `src/core`：核心模型与提醒能力
- `scripts`：服务端/客户端启动脚本
- `tests`：集成测试脚本
- `docs`：中文说明和验证报告
- `release`：原 `dist` 打包产物

## 快速启动

```bash
pip install -r requirements.txt
python scripts/start_server.py
python scripts/start_client.py
```

## 集成测试

```bash
python tests/test_integration.py --server http://localhost:5000
```
