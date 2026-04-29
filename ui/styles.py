#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
样式配置
"""

# 颜色配置
COLORS = {
    "bg_primary": "#FFFACD",       # 主背景色 (柠檬绸)
    "bg_secondary": "#FFF8DC",      # 次要背景色
    "bg_header": "#F0E68C",         # 表头背景
    "text_normal": "#333333",       # 正常文字
    "text_warning": "#FF8C00",      # 警告文字 (橙色)
    "text_urgent": "#FF0000",       # 紧急文字 (红色)
    "text_completed": "#888888",    # 已完成文字
    "border": "#DEB887",            # 边框颜色
    "button_bg": "#FFE4B5",         # 按钮背景
    "button_hover": "#FFDAB9",      # 按钮悬停
    "selection": "#87CEEB",         # 选中颜色
}

# 字体配置
FONTS = {
    "title": ("Microsoft YaHei UI", 14, "bold"),
    "header": ("Microsoft YaHei UI", 10, "bold"),
    "normal": ("Microsoft YaHei UI", 10),
    "small": ("Microsoft YaHei UI", 9),
    "urgent": ("Microsoft YaHei UI", 10, "bold"),
}

# 尺寸配置
SIZES = {
    "padding": 10,
    "button_width": 80,
    "button_height": 30,
    "row_height": 28,
    "min_width": 600,
    "min_height": 400,
}

# 列配置
COLUMNS = {
    "index": {"text": "序号", "width": 50, "anchor": "center"},
    "title": {"text": "事项", "width": 200, "anchor": "w"},
    "assignee": {"text": "责任人", "width": 80, "anchor": "center"},
    "deadline": {"text": "截止时间", "width": 100, "anchor": "center"},
    "days_left": {"text": "剩余天数", "width": 80, "anchor": "center"},
    "status": {"text": "状态", "width": 80, "anchor": "center"},
    "priority": {"text": "优先级", "width": 70, "anchor": "center"},
}

PRIORITY_NAMES = {
    1: "低",
    2: "中",
    3: "高",
    4: "紧急"
}

STATUS_OPTIONS = ["待处理", "进行中", "已完成", "已取消"]
PRIORITY_OPTIONS = ["低", "中", "高", "紧急"]