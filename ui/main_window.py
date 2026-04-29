#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
主窗口
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Windows 任务栏图标支持
try:
    from win10toast import ToastNotifier
    HAS_TOAST = True
except ImportError:
    HAS_TOAST = False

try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False

from core.data_manager import DataManager
from core.reminder import ReminderService
from core.models import TodoItem, Status
from ui.styles import COLORS, FONTS, SIZES, COLUMNS, PRIORITY_NAMES
from ui.todo_editor import TodoEditor


class TodoApp:
    """待办事项应用"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.data_manager = DataManager()
        self.reminder_service = ReminderService(self.data_manager)
        
        # 系统托盘
        self.tray_icon = None
        self.is_hidden = False
        
        # Toast通知器
        if HAS_TOAST:
            self.toaster = ToastNotifier()
        
        self._setup_window()
        self._setup_styles()
        self._create_widgets()
        self._setup_bindings()
        self._setup_tray()
        self._setup_reminder()
        
        # 加载数据
        self._refresh_list()
    
    def _setup_window(self):
        """设置窗口"""
        self.root.title("📋 待办事项提醒")
        
        # 获取保存的窗口位置和大小
        x = self.data_manager.get_config("window_x", 100)
        y = self.data_manager.get_config("window_y", 100)
        w = self.data_manager.get_config("window_width", 750)
        h = self.data_manager.get_config("window_height", 500)
        
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.minsize(SIZES["min_width"], SIZES["min_height"])
        
        # 设置背景色
        self.root.configure(bg=COLORS["bg_primary"])
        
        # 透明度
        opacity = self.data_manager.get_config("opacity", 0.95)
        self.root.attributes('-alpha', opacity)
        
        # 置顶
        if self.data_manager.get_config("always_on_top", False):
            self.root.attributes('-topmost', True)
        
        # 窗口关闭处理
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # 设置图标
        self._set_icon()
    
    def _set_icon(self):
        """设置窗口图标"""
        try:
            # 尝试加载图标文件
            icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass
    
    def _setup_styles(self):
        """设置样式"""
        style = ttk.Style()
        
        # 配置Treeview样式
        style.configure(
            "Todo.Treeview",
            background=COLORS["bg_secondary"],
            foreground=COLORS["text_normal"],
            fieldbackground=COLORS["bg_secondary"],
            rowheight=SIZES["row_height"],
            font=FONTS["normal"]
        )
        
        style.configure(
            "Todo.Treeview.Heading",
            background=COLORS["bg_header"],
            foreground=COLORS["text_normal"],
            font=FONTS["header"]
        )
        
        style.map("Todo.Treeview",
            background=[("selected", COLORS["selection"])],
            foreground=[("selected", COLORS["text_normal"])]
        )
        
        # 按钮样式
        style.configure(
            "Action.TButton",
            padding=5,
            font=FONTS["normal"]
        )
    
    def _create_widgets(self):
        """创建控件"""
        # 工具栏
        self._create_toolbar()
        
        # 列表区域
        self._create_list_area()
        
        # 状态栏
        self._create_statusbar()
    
    def _create_toolbar(self):
        """创建工具栏"""
        toolbar = ttk.Frame(self.root, padding=10)
        toolbar.pack(fill=tk.X)
        
        # 左侧按钮
        left_frame = ttk.Frame(toolbar)
        left_frame.pack(side=tk.LEFT)
        
        ttk.Button(
            left_frame, 
            text="➕ 新建",
            style="Action.TButton",
            command=self._add_todo
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            left_frame,
            text="✏️ 编辑",
            style="Action.TButton", 
            command=self._edit_todo
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            left_frame,
            text="🗑️ 删除",
            style="Action.TButton",
            command=self._delete_todo
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(left_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
        
        ttk.Button(
            left_frame,
            text="✅ 完成",
            style="Action.TButton",
            command=self._mark_completed
        ).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(
            left_frame,
            text="🔄 刷新",
            style="Action.TButton",
            command=self._refresh_list
        ).pack(side=tk.LEFT, padx=2)
        
        # 右侧控件
        right_frame = ttk.Frame(toolbar)
        right_frame.pack(side=tk.RIGHT)
        
        # 筛选
        ttk.Label(right_frame, text="筛选:").pack(side=tk.LEFT, padx=5)
        self.filter_var = tk.StringVar(value="全部")
        filter_combo = ttk.Combobox(
            right_frame,
            textvariable=self.filter_var,
            values=["全部", "待处理", "进行中", "已完成", "已取消", "即将到期"],
            state="readonly",
            width=10
        )
        filter_combo.pack(side=tk.LEFT, padx=2)
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_list())
        
        # 置顶切换
        self.topmost_var = tk.BooleanVar(value=self.data_manager.get_config("always_on_top", False))
        ttk.Checkbutton(
            right_frame,
            text="📌 置顶",
            variable=self.topmost_var,
            command=self._toggle_topmost
        ).pack(side=tk.LEFT, padx=10)
    
    def _create_list_area(self):
        """创建列表区域"""
        list_frame = ttk.Frame(self.root, padding=10)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建Treeview
        columns = list(COLUMNS.keys())
        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            style="Todo.Treeview",
            selectmode="browse"
        )
        
        # 配置列
        for col, config in COLUMNS.items():
            self.tree.heading(col, text=config["text"], anchor=config["anchor"])
            self.tree.column(col, width=config["width"], anchor=config["anchor"])
        
        # 滚动条
        vsb = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        hsb = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # 布局
        self.tree.grid(row=0, column=0, sticky=tk.NSEW)
        vsb.grid(row=0, column=1, sticky=tk.NS)
        hsb.grid(row=1, column=0, sticky=tk.EW)
        
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # 双击编辑
        self.tree.bind("<Double-1>", lambda e: self._edit_todo())
        
        # 创建标签样式
        self.tree.tag_configure("overdue", foreground=COLORS["text_urgent"], font=FONTS["urgent"])
        self.tree.tag_configure("urgent", foreground=COLORS["text_urgent"], font=FONTS["urgent"])
        self.tree.tag_configure("warning", foreground=COLORS["text_warning"])
        self.tree.tag_configure("completed", foreground=COLORS["text_completed"])
        self.tree.tag_configure("normal", foreground=COLORS["text_normal"])
    
    def _create_statusbar(self):
        """创建状态栏"""
        statusbar = ttk.Frame(self.root)
        statusbar.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = ttk.Label(
            statusbar, 
            text="就绪",
            font=FONTS["small"],
            padding=5
        )
        self.status_label.pack(side=tk.LEFT)
        
        # 统计信息
        self.stats_label = ttk.Label(
            statusbar,
            text="",
            font=FONTS["small"],
            padding=5
        )
        self.stats_label.pack(side=tk.RIGHT)
    
    def _setup_bindings(self):
        """设置事件绑定"""
        # 快捷键
        self.root.bind("<Control-n>", lambda e: self._add_todo())
        self.root.bind("<Delete>", lambda e: self._delete_todo())
        self.root.bind("<F5>", lambda e: self._refresh_list())
        self.root.bind("<Return>", lambda e: self._edit_todo())
        
        # 窗口移动和大小改变
        self.root.bind("<Configure>", self._on_configure)
    
    def _setup_tray(self):
        """设置系统托盘"""
        if not HAS_TRAY:
            return
        
        # 创建托盘图标
        def create_image():
            """创建托盘图标图像"""
            size = 64
            image = Image.new('RGB', (size, size), color='#FFD700')
            draw = ImageDraw.Draw(image)
            # 画一个简单的勾
            draw.rectangle([10, 10, 54, 54], outline='#333333', width=3)
            draw.line([20, 35, 30, 45, 50, 20], fill='#228B22', width=4)
            return image
        
        menu = pystray.Menu(
            pystray.MenuItem("显示", self._show_window, default=True),
            pystray.MenuItem("新建待办", self._add_todo),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", self._quit_app)
        )
        
        self.tray_icon = pystray.Icon(
            "todo_reminder",
            create_image(),
            "待办事项提醒",
            menu
        )
    
    def _setup_reminder(self):
        """设置提醒服务"""
        self.reminder_service.register_callback(self._on_reminder)
        self.reminder_service.start()
    
    def _on_reminder(self, todo: TodoItem, remind_type: str, message: str):
        """提醒回调"""
        # 刷新列表显示
        self.root.after(0, self._refresh_list)
        
        # 显示Toast通知
        if HAS_TOAST:
            try:
                title = "待办事项提醒"
                if remind_type == "overdue":
                    title = "⚠️ 事项已逾期!"
                elif remind_type == "3day":
                    title = "⚡ 紧急提醒!"
                
                self.toaster.show_toast(
                    title,
                    message,
                    duration=5,
                    threaded=True
                )
            except Exception as e:
                print(f"Toast通知失败: {e}")
        
        # 如果窗口隐藏，显示出来
        if self.is_hidden:
            self.root.after(0, self._show_window)
    
    def _refresh_list(self):
        """刷新列表"""
        # 清空列表
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 获取数据
        todos = self.data_manager.get_all_todos()
        
        # 应用筛选
        filter_value = self.filter_var.get()
        if filter_value == "即将到期":
            todos = [t for t in todos if t.get_urgency_level() in ["warning", "urgent", "overdue"]
                    and t.status not in [Status.COMPLETED.value, Status.CANCELLED.value]]
        elif filter_value != "全部":
            todos = [t for t in todos if t.status == filter_value]
        
        # 按截止时间和优先级排序
        def sort_key(t):
            days = t.days_until_deadline()
            if days is None:
                days = 9999
            return (t.status == Status.COMPLETED.value, days, -t.priority)
        
        todos.sort(key=sort_key)
        
        # 填充列表
        for idx, todo in enumerate(todos, 1):
            days = todo.days_until_deadline()
            days_text = f"{days}天" if days is not None else "-"
            if days is not None and days < 0:
                days_text = f"逾期{abs(days)}天"
            
            values = (
                idx,
                todo.title,
                todo.assignee or "-",
                todo.deadline or "-",
                days_text,
                todo.status,
                PRIORITY_NAMES.get(todo.priority, "中")
            )
            
            # 确定标签
            if todo.status == Status.COMPLETED.value:
                tag = "completed"
            elif todo.status == Status.CANCELLED.value:
                tag = "completed"
            else:
                tag = todo.get_urgency_level()
            
            self.tree.insert("", tk.END, iid=todo.id, values=values, tags=(tag,))
        
        # 更新统计
        total = len(self.data_manager.get_all_todos())
        active = len(self.data_manager.get_active_todos())
        self.stats_label.configure(text=f"共 {total} 项 | 待处理 {active} 项")
    
    def _add_todo(self):
        """添加待办"""
        def callback(todo):
            self.data_manager.add_todo(todo)
            self._refresh_list()
            self.status_label.configure(text="已添加新待办事项")
        
        TodoEditor(self.root, callback=callback)
    
    def _edit_todo(self):
        """编辑待办"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一个待办事项")
            return
        
        todo_id = selection[0]
        todo = self.data_manager.get_todo_by_id(todo_id)
        
        if not todo:
            return
        
        def callback(updated_todo):
            self.data_manager.update_todo(
                todo_id,
                title=updated_todo.title,
                assignee=updated_todo.assignee,
                deadline=updated_todo.deadline,
                priority=updated_todo.priority,
                status=updated_todo.status,
                description=updated_todo.description,
                reminded_7day=updated_todo.reminded_7day,
                reminded_3day=updated_todo.reminded_3day,
                reminded_overdue=updated_todo.reminded_overdue
            )
            self._refresh_list()
            self.status_label.configure(text="已更新待办事项")
        
        TodoEditor(self.root, todo=todo, callback=callback)
    
    def _delete_todo(self):
        """删除待办"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一个待办事项")
            return
        
        if messagebox.askyesno("确认", "确定要删除选中的待办事项吗？"):
            todo_id = selection[0]
            self.data_manager.delete_todo(todo_id)
            self._refresh_list()
            self.status_label.configure(text="已删除待办事项")
    
    def _mark_completed(self):
        """标记完成"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一个待办事项")
            return
        
        todo_id = selection[0]
        self.data_manager.update_todo(todo_id, status=Status.COMPLETED.value)
        self._refresh_list()
        self.status_label.configure(text="已标记为完成")
    
    def _toggle_topmost(self):
        """切换置顶"""
        topmost = self.topmost_var.get()
        self.root.attributes('-topmost', topmost)
        self.data_manager.set_config("always_on_top", topmost)
    
    def _on_configure(self, event):
        """窗口配置改变"""
        if event.widget == self.root:
            # 保存窗口位置和大小
            self.data_manager.set_config("window_x", self.root.winfo_x())
            self.data_manager.set_config("window_y", self.root.winfo_y())
            self.data_manager.set_config("window_width", self.root.winfo_width())
            self.data_manager.set_config("window_height", self.root.winfo_height())
    
    def _on_close(self):
        """窗口关闭"""
        if HAS_TRAY and self.tray_icon:
            # 最小化到托盘
            self.root.withdraw()
            self.is_hidden = True
            
            # 启动托盘图标(如果还没启动)
            if not self.tray_icon._running:
                import threading
                threading.Thread(target=self.tray_icon.run, daemon=True).start()
        else:
            self._quit_app()
    
    def _show_window(self, icon=None, item=None):
        """显示窗口"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.is_hidden = False
    
    def _quit_app(self, icon=None, item=None):
        """退出应用"""
        # 保存数据
        self.data_manager.save()
        
        # 停止提醒服务
        self.reminder_service.stop()
        
        # 停止托盘图标
        if self.tray_icon:
            self.tray_icon.stop()
        
        # 退出主循环
        self.root.quit()
        self.root.destroy()
    
    def run(self):
        """运行应用"""
        self.root.mainloop()


if __name__ == "__main__":
    app = TodoApp()
    app.run()