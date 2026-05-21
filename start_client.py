#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
客户端启动脚本
成员通过IP自动识别，管理员需密码
"""

import os
import sys

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

if __name__ == '__main__':
    from client.main import main
    main()
