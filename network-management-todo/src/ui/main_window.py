#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
主窗口
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
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
from ui.settings_dialog import SettingsDialog
from ui.progress_dialog import ProgressDialog


class TodoApp:
    """待办事项应用"""

    def __init__(self, root=None, data_manager=None, performance_optimizer=None):
        """
        初始化待办事项应用

        Args:
            root: 父窗口（可选，用于客户端模式）
            data_manager: 数据管理器（可选，用于客户端模式）
            performance_optimizer: 性能优化器（可选，用于客户端模式）
        """
        # 根窗口（传入或创建）
        self.root = root if root else tk.Tk()

        # 数据管理器（传入或创建）
        self.data_manager = data_manager if data_manager else DataManager()

        # 性能优化器（仅客户端模式）
        self.performance_optimizer = performance_optimizer

        # 提醒服务（仅单机模式）
        self.reminder_service = None
        if not performance_optimizer:  # 单机模式
            self.reminder_service = ReminderService(self.data_manager)

        # 系统托盘
        self.tray_icon = None
        self.tray_running = False
        self.is_hidden = False

        # Toast通知器
        if HAS_TOAST:
            self.toaster = ToastNotifier()

        # 先隐藏窗口（仅单机模式需要）
        if not root:  # 单机模式，创建了自己的root
            self.root.withdraw()

        self._setup_window()
        self._setup_styles()
        self._create_widgets()
        self._setup_bindings()
        self._setup_tray()
        self._setup_reminder()

        # 加载数据
        self._refresh_list()

        # 显示窗口
        self.root.deiconify()

        # 启动时检查（仅单机模式）
        if self.reminder_service and self.data_manager.get_config("check_on_start", True):
            self.root.after(1000, self.reminder_service.force_check)
    
    def _setup_window(self):
        """设置窗口"""
        # 客户端模式跳过窗口设置（由父窗口管理）
        if self.performance_optimizer:
            # 只设置窗口关闭处理
            self.root.protocol("WM_DELETE_WINDOW", self._on_close)
            return

        # 单机模式：设置窗口属性
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
            icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icon.ico")
            self.root.iconbitmap(icon_path)
        except Exception:
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

        ttk.Separator(left_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)

        ttk.Button(
            left_frame,
            text="⚙️ 设置",
            style="Action.TButton",
            command=self._open_settings
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

        # 绑定进度列点击事件
        self.tree.bind('<Button-1>', self._on_tree_click)
        
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
        self.root.bind("<Control-comma>", lambda e: self._open_settings())
        
        # 窗口移动和大小改变
        self.root.bind("<Configure>", self._on_configure)
    
    def _setup_tray(self):
        """设置系统托盘（仅单机模式）"""
        if not HAS_TRAY:
            return

        # 客户端模式不使用系统托盘
        if self.performance_optimizer:
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
        """设置提醒服务（仅单机模式）"""
        if self.reminder_service:
            self.reminder_service.register_callback(self._on_reminder)
            self.reminder_service.start()
    
    def _on_reminder(self, todo: TodoItem, remind_type: str, message: str):
        """提醒回调"""
        # 刷新列表显示
        self.root.after(0, self._refresh_list)
        
        # 播放提示音
        if self.data_manager.get_config("sound_enabled", True):
            try:
                import winsound
                winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
            except Exception:
                pass
        
        # 显示Toast通知
        if HAS_TOAST and self.data_manager.get_config("toast_enabled", True):
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
        
        # 如果窗口隐藏且需要弹出
        if self.is_hidden and self.data_manager.get_config("popup_enabled", True):
            self.root.after(0, self._show_window)
    
    def _refresh_list(self):
        """刷新列表"""
        # 清空列表
        for item in self.tree.get_children():
            self.tree.delete(item)

        # 一次获取所有数据，后续统计复用
        all_todos = self.data_manager.get_all_todos()
        todos = list(all_todos)

        # 是否显示已完成
        show_completed = self.data_manager.get_config("show_completed", True)

        # 应用筛选
        filter_value = self.filter_var.get()
        if filter_value == "即将到期":
            todos = [t for t in todos if t.get_urgency_level() in ["warning", "urgent", "overdue"]
                    and t.status not in [Status.COMPLETED.value, Status.CANCELLED.value]]
        elif filter_value != "全部":
            todos = [t for t in todos if t.status == filter_value]
        elif not show_completed:
            todos = [t for t in todos if t.status not in [Status.COMPLETED.value, Status.CANCELLED.value]]

        # 预计算 days_until_deadline 避免重复调用
        todo_days = {t.id: t.days_until_deadline() for t in todos}

        # 按截止时间和优先级排序
        def sort_key(t):
            days = todo_days.get(t.id, 9999)
            if days is None:
                days = 9999
            return (t.status == Status.COMPLETED.value, days, -t.priority)

        todos.sort(key=sort_key)

        # 填充列表
        for idx, todo in enumerate(todos, 1):
            # 获取进度更新文本（截断过长的文本）
            progress_text = "-"
            if todo.progress:
                progress_text = todo.progress[:15] + "..." if len(todo.progress) > 15 else todo.progress

            values = (
                idx,
                todo.title,
                todo.assignee or "-",
                todo.deadline or "-",
                progress_text,
                todo.status,
                PRIORITY_NAMES.get(todo.priority, "中")
            )

            # 确定标签
            if todo.status in (Status.COMPLETED.value, Status.CANCELLED.value):
                tag = "completed"
            else:
                tag = todo.get_urgency_level()

            self.tree.insert("", tk.END, iid=todo.id, values=values, tags=(tag,))

        # 从同一份数据派生统计
        active = [t for t in all_todos
                  if t.status not in [Status.COMPLETED.value, Status.CANCELLED.value]]
        urgent = [t for t in active if t.get_urgency_level() in ["urgent", "overdue"]]

        stats_text = f"共 {len(all_todos)} 项 | 待处理 {len(active)} 项"
        if urgent:
            stats_text += f" | ⚠️ 紧急 {len(urgent)} 项"
        self.stats_label.configure(text=stats_text)
    
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
        """删除待办（需要管理员密码）"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择一个待办事项")
            return

        # 弹出管理员密码确认
        password = simpledialog.askstring(
            "管理员验证",
            "删除任务需要管理员密码：",
            show='*',
            parent=self.root
        )
        if not password:
            return

        # 验证管理员密码
        if hasattr(self.data_manager, 'verify_admin_password'):
            if not self.data_manager.verify_admin_password(password):
                messagebox.showerror("错误", "管理员密码错误", parent=self.root)
                return

        if messagebox.askyesno("确认", "确定要删除选中的待办事项吗？"):
            todo_id = selection[0]
            success = self.data_manager.delete_todo(todo_id, admin_password=password)
            if success:
                self._refresh_list()
                self.status_label.configure(text="已删除待办事项")
            else:
                messagebox.showerror("删除失败", "无法删除任务，请检查网络连接", parent=self.root)
    
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

    def _open_settings(self):
        """打开设置"""
        def on_settings_saved():
            self._refresh_list()
            # 重启提醒服务以应用新设置（仅单机模式）
            if self.reminder_service:
                self.reminder_service.restart(root=self.root)
            self.status_label.configure(text="设置已更新")

        SettingsDialog(self.root, self.data_manager, callback=on_settings_saved)

    def _on_tree_click(self, event):
        """处理Treeview点击事件"""
        # 获取点击的列和项目
        region = self.tree.identify_region(event.x, event.y)
        if not region:
            return

        if region != 'cell':
            return

        # 获取点击的项目
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return

        # 获取点击的列
        column = self.tree.identify_column(event.x)
        if not column:
            return

        # 检查是否点击了进度列
        col_name = self.tree.column(column)['id']
        if col_name == 'progress':
            # 获取任务
            todo = self.data_manager.get_todo_by_id(item_id)
            if todo:
                from ui.progress_dialog import ProgressDialog
                ProgressDialog(
                    self.root,
                    todo,
                    self._update_progress_callback
                )

    def _update_progress_callback(self, todo_id: str, new_progress: str):
        """更新进度的回调"""
        # 调用API更新进度
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        success = self.data_manager.update_todo(
            todo_id,
            progress=new_progress,
            progress_updated_at=now
        )

        if success:
            self._refresh_list()
            self.status_label.configure(text="进度已更新")
        else:
            messagebox.showerror("更新失败", "无法更新进度，请检查网络连接", parent=self.root)

    def _on_configure(self, event):
        """窗口配置改变"""
        if event.widget == self.root:
            if hasattr(self, '_configure_after_id'):
                self.root.after_cancel(self._configure_after_id)
            self._configure_after_id = self.root.after(500, self._save_window_geometry)

    def _save_window_geometry(self):
        """保存窗口位置和大小"""
        self.data_manager.set_config("window_x", self.root.winfo_x())
        self.data_manager.set_config("window_y", self.root.winfo_y())
        self.data_manager.set_config("window_width", self.root.winfo_width())
        self.data_manager.set_config("window_height", self.root.winfo_height())
    
    def _on_close(self):
        """窗口关闭"""
        # 客户端模式直接关闭窗口
        if self.performance_optimizer:
            self.root.destroy()
            return

        # 单机模式：最小化到托盘或退出
        minimize_to_tray = self.data_manager.get_config("minimize_to_tray", True)

        if HAS_TRAY and minimize_to_tray and self.tray_icon:
            # 最小化到托盘
            self.root.withdraw()
            self.is_hidden = True

            # 启动托盘图标(如果还没启动)
            if not self.tray_running:
                import threading
                self.tray_running = True
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
        # 单机模式需要保存数据和停止服务
        if not self.performance_optimizer:
            # 保存数据
            if hasattr(self.data_manager, 'save'):
                self.data_manager.save()

            # 停止提醒服务
            if self.reminder_service:
                self.reminder_service.stop()

            # 停止托盘图标
            if self.tray_icon and self.tray_running:
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