#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
桌面待办事项提醒程序
"""

import sys
import os

# 确保路径正确
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BASE_DIR)

from ui.main_window import TodoApp

def main():
    app = TodoApp()
    app.run()

if __name__ == "__main__":
    main()