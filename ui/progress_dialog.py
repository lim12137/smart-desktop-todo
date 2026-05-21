#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
进度详情对话框
显示和编辑任务进度说明
"""

import tkinter as tk
from tkinter import ttk, scrolledtext


class ProgressDialog(tk.Toplevel):
    """进度详情对话框"""

    def __init__(self, parent, todo, on_update_callback):
        super().__init__(parent)
        self.parent = parent
        self.todo = todo  # TodoItem对象
        self.on_update_callback = on_update_callback
        self.result = None

        # 先隐藏窗口，防止闪烁
        self.withdraw()

        self._setup_window()
        self._create_widgets()
        self._load_data()

        # 模态对话框
        self.transient(parent)
        self.grab_set()

        # 居中显示
        self._center_window()
        self.deiconify()
        self.focus_set()

    def _setup_window(self):
        """设置窗口"""
        self.title(f"任务进度 - {self.todo.title}")
        self.resizable(False, False)
        self.configure(bg='#F0F0F0')
        self.geometry("500x400")

    def _create_widgets(self):
        """创建控件"""
        # 主框架
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 任务信息
        info_frame = ttk.LabelFrame(main_frame, text="任务信息", padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(info_frame, text=f"任务：{self.todo.title}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"负责人：{self.todo.assignee or '未分配'}").pack(anchor=tk.W)

        if self.todo.progress_updated_at:
            ttk.Label(
                info_frame,
                text=f"更新时间：{self.todo.progress_updated_at}"
            ).pack(anchor=tk.W)
        else:
            ttk.Label(info_frame, text="更新时间：未更新").pack(anchor=tk.W)

        # 进度说明
        progress_frame = ttk.LabelFrame(main_frame, text="当前进度", padding=10)
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # 只读模式显示（初始）
        self.progress_text = scrolledtext.ScrolledText(
            progress_frame,
            width=50,
            height=10,
            font=('Microsoft YaHei UI', 10),
            wrap=tk.WORD,
            state='disabled'
        )
        self.progress_text.pack(fill=tk.BOTH, expand=True)

        # 按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        self.edit_btn = ttk.Button(
            btn_frame,
            text="编辑进度",
            command=self._toggle_edit,
            width=12
        )
        self.edit_btn.pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            btn_frame,
            text="关闭",
            command=self.destroy,
            width=12
        ).pack(side=tk.RIGHT)

    def _load_data(self):
        """加载数据"""
        # 显示进度说明
        self.progress_text.config(state='normal')
        if self.todo.progress:
            self.progress_text.insert("1.0", self.todo.progress)
        self.progress_text.config(state='disabled')

    def _toggle_edit(self):
        """切换编辑模式"""
        if self.edit_btn['text'] == '编辑进度':
            # 进入编辑模式
            self.progress_text.config(state='normal')
            self.progress_text.focus_set()
            self.edit_btn.config(text='保存')

            # 绑定Ctrl+Enter保存
            self.bind('<Control-Return>', lambda e: self._save_progress())
        else:
            # 保存进度
            self._save_progress()

    def _save_progress(self):
        """保存进度"""
        new_progress = self.progress_text.get("1.0", tk.END).strip()

        # 调用回调更新进度
        if self.on_update_callback:
            # 更新本地显示
            self.todo.progress = new_progress
            self._load_data()

            # 退出编辑模式
            self.progress_text.config(state='disabled')
            self.edit_btn.config(text='编辑进度')

            # 回调更新服务器
            self.on_update_callback(self.todo.id, new_progress)

    def _center_window(self):
        """居中显示窗口"""
        self.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = max(0, min(x, screen_width - width))
        y = max(0, min(y, screen_height - height))
        self.geometry(f"{width}x{height}+{x}+{y}")
