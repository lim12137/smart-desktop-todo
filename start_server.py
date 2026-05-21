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

    init_db()

    print("=" * 60)
    print("待办事项提醒系统 - 服务端启动")
    print("=" * 60)
    print(f"数据库: {DATABASE_PATH}")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5000, debug=False)
