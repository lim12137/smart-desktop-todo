#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
待办事项编辑对话框
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date, timedelta
from tkcalendar import DateEntry
from core.models import TodoItem, Priority, Status
from ui.styles import COLORS, FONTS, STATUS_OPTIONS, PRIORITY_OPTIONS


class TodoEditor(tk.Toplevel):
    """待办事项编辑对话框"""
    
    def __init__(self, parent, todo: TodoItem = None, callback=None):
        super().__init__(parent)
        self.parent = parent
        self.todo = todo
        self.callback = callback
        self.result = None
        
        # 先隐藏窗口，防止闪烁
        self.withdraw()
        
        self._setup_window()
        self._create_widgets()
        self._load_data()
        
        # 模态对话框
        self.transient(parent)
        self.grab_set()
        
        # 计算位置并显示
        self._center_window()
        
        # 显示窗口
        self.deiconify()
        self.focus_set()
        self.title_entry.focus_set()
    
    def _setup_window(self):
        """设置窗口"""
        title = "编辑待办事项" if self.todo else "新建待办事项"
        self.title(title)
        self.configure(bg=COLORS["bg_primary"])
        self.resizable(False, False)
        
        # 设置最小尺寸
        self.minsize(400, 380)
    
    def _create_widgets(self):
        """创建控件"""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        ttk.Label(main_frame, text="事项标题:", font=FONTS["normal"]).grid(
            row=0, column=0, sticky=tk.W, pady=5)
        self.title_var = tk.StringVar()
        self.title_entry = ttk.Entry(main_frame, textvariable=self.title_var, width=40)
        self.title_entry.grid(row=0, column=1, columnspan=2, sticky=tk.EW, pady=5)
        
        # 责任人
        ttk.Label(main_frame, text="责任人:", font=FONTS["normal"]).grid(
            row=1, column=0, sticky=tk.W, pady=5)
        self.assignee_var = tk.StringVar()
        self.assignee_entry = ttk.Entry(main_frame, textvariable=self.assignee_var, width=20)
        self.assignee_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # 截止时间
        ttk.Label(main_frame, text="截止时间:", font=FONTS["normal"]).grid(
            row=2, column=0, sticky=tk.W, pady=5)
        
        date_frame = ttk.Frame(main_frame)
        date_frame.grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        self.deadline_var = tk.StringVar()
        self.date_entry = DateEntry(
            date_frame,
            textvariable=self.deadline_var,
            width=15,
            date_pattern='yyyy-mm-dd',
            locale='zh_CN'
        )
        self.date_entry.pack(side=tk.LEFT)
        
        self.no_deadline_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            date_frame, 
            text="无截止时间",
            variable=self.no_deadline_var,
            command=self._toggle_deadline
        ).pack(side=tk.LEFT, padx=10)
        
        # 优先级
        ttk.Label(main_frame, text="优先级:", font=FONTS["normal"]).grid(
            row=3, column=0, sticky=tk.W, pady=5)
        self.priority_var = tk.StringVar(value="中")
        priority_combo = ttk.Combobox(
            main_frame, 
            textvariable=self.priority_var,
            values=PRIORITY_OPTIONS,
            state="readonly",
            width=10
        )
        priority_combo.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # 状态
        ttk.Label(main_frame, text="状态:", font=FONTS["normal"]).grid(
            row=4, column=0, sticky=tk.W, pady=5)
        self.status_var = tk.StringVar(value="待处理")
        status_combo = ttk.Combobox(
            main_frame,
            textvariable=self.status_var,
            values=STATUS_OPTIONS,
            state="readonly",
            width=10
        )
        status_combo.grid(row=4, column=1, sticky=tk.W, pady=5)
        
        # 描述
        ttk.Label(main_frame, text="描述:", font=FONTS["normal"]).grid(
            row=5, column=0, sticky=tk.NW, pady=5)
        
        desc_frame = ttk.Frame(main_frame)
        desc_frame.grid(row=5, column=1, columnspan=2, sticky=tk.EW, pady=5)
        
        self.desc_text = tk.Text(desc_frame, width=35, height=5, font=FONTS["normal"])
        self.desc_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(desc_frame, orient=tk.VERTICAL, command=self.desc_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.desc_text.configure(yscrollcommand=scrollbar.set)
        
        # 按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=6, column=0, columnspan=3, pady=20)
        
        ttk.Button(btn_frame, text="保存", command=self._save, width=10).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="取消", command=self.destroy, width=10).pack(side=tk.LEFT, padx=10)
        
        # 配置列权重
        main_frame.columnconfigure(1, weight=1)
    
    def _toggle_deadline(self):
        """切换截止时间启用状态"""
        if self.no_deadline_var.get():
            self.date_entry.configure(state='disabled')
        else:
            self.date_entry.configure(state='normal')
    
    def _load_data(self):
        """加载数据"""
        if self.todo:
            self.title_var.set(self.todo.title)
            self.assignee_var.set(self.todo.assignee)

            # 保存原始截止时间用于比较
            self._old_deadline = self.todo.deadline

            if self.todo.deadline:
                self.deadline_var.set(self.todo.deadline)
                self.no_deadline_var.set(False)
            else:
                self.no_deadline_var.set(True)
                self._toggle_deadline()

            # 优先级
            priority_map = {1: "低", 2: "中", 3: "高", 4: "紧急"}
            self.priority_var.set(priority_map.get(self.todo.priority, "中"))

            self.status_var.set(self.todo.status)
            self.desc_text.insert("1.0", self.todo.description)
        else:
            # 默认截止时间为7天后
            default_date = date.today() + timedelta(days=7)
            self.deadline_var.set(default_date.strftime("%Y-%m-%d"))
    
    def _save(self):
        """保存"""
        title = self.title_var.get().strip()
        if not title:
            messagebox.showwarning("提示", "请输入事项标题！", parent=self)
            self.title_entry.focus_set()
            return
        
        # 获取截止时间
        deadline = None
        if not self.no_deadline_var.get():
            deadline = self.deadline_var.get()
        
        # 优先级映射
        priority_map = {"低": 1, "中": 2, "高": 3, "紧急": 4}
        priority = priority_map.get(self.priority_var.get(), 2)
        
        if self.todo:
            # 更新
            self.todo.title = title
            self.todo.assignee = self.assignee_var.get().strip()
            self.todo.deadline = deadline
            self.todo.priority = priority
            self.todo.status = self.status_var.get()
            self.todo.description = self.desc_text.get("1.0", tk.END).strip()
            
            # 如果截止时间改变，重置提醒标记
            old_deadline = getattr(self, '_old_deadline', None)
            if old_deadline != deadline:
                self.todo.reminded_7day = False
                self.todo.reminded_3day = False
                self.todo.reminded_overdue = False
            
            self.result = self.todo
        else:
            # 新建
            self.result = TodoItem(
                title=title,
                assignee=self.assignee_var.get().strip(),
                deadline=deadline,
                priority=priority,
                status=self.status_var.get(),
                description=self.desc_text.get("1.0", tk.END).strip()
            )
        
        if self.callback:
            self.callback(self.result)
        
        self.destroy()
    
    def _center_window(self):
        """居中显示窗口"""
        # 更新窗口以获取正确尺寸
        self.update_idletasks()
        
        # 获取窗口尺寸
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        
        # 获取父窗口位置和尺寸
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # 计算居中位置
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        
        # 确保不超出屏幕
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = max(0, min(x, screen_width - width))
        y = max(0, min(y, screen_height - height))
        
        # 直接设置位置
        self.geometry(f"{width}x{height}+{x}+{y}")