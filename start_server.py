#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
服务端启动脚本
"""

import os
import sys

project_root = os.path.dirname(os.path.abspath(__file__))
server_dir = os.path.join(project_root, 'server')
sys.path.insert(0, project_root)
sys.path.insert(0, server_dir)

if __name__ == '__main__':
    from database import init_db, DATABASE_PATH
    from app import app
    from discovery import DiscoveryService

    init_db()

    discovery = DiscoveryService()
    discovery.start()

    print("=" * 60)
    print("待办事项提醒系统 - 服务端启动")
    print("=" * 60)
    print(f"数据库: {DATABASE_PATH}")
    print(f"UDP 广播: 已启动（端口 15432）")
    print("=" * 60)

    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    finally:
        discovery.stop()
