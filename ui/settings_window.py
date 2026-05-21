#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
设置窗口模块
"""

import tkinter as tk
from tkinter import ttk, messagebox
from ui.styles import COLORS, FONTS


class SettingsWindow(tk.Toplevel):
    """设置窗口"""

    def __init__(self, parent, data_manager, callback=None):
        super().__init__(parent)
        self.parent = parent
        self.data_manager = data_manager
        self.callback = callback

        # 设置变量
        self.reminder_enabled_var = tk.BooleanVar()
        self.check_interval_var = tk.StringVar()
        self.warning_days_var = tk.StringVar()
        self.urgent_days_var = tk.StringVar()
        self.auto_show_var = tk.BooleanVar()

        self._setup_window()
        self._create_widgets()
        self._load_settings()

        # 窗口定位
        self._position_window()

        # 模态对话框
        self.transient(parent)
        self.grab_set()
        self.focus_set()

    def _setup_window(self):
        """设置窗口"""
        self.title("⚙️ 设置")
        self.configure(bg=COLORS["bg_primary"])
        self.resizable(False, False)

        # 设置最小尺寸
        self.minsize(450, 400)

    def _position_window(self):
        """窗口定位"""
        self.withdraw()  # 临时隐藏以避免闪烁
        self.update_idletasks()  # 确保窗口尺寸已计算

        # 获取屏幕尺寸以处理边界情况
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # 计算居中位置
        window_width = self.winfo_width()
        window_height = self.winfo_height()
        x = self.parent.winfo_x() + (self.parent.winfo_width() - window_width) // 2
        y = self.parent.winfo_y() + (self.parent.winfo_height() - window_height) // 2

        # 确保窗口在屏幕范围内
        x = max(0, min(x, screen_width - window_width))
        y = max(0, min(y, screen_height - window_height))

        # 设置位置后再显示
        self.geometry(f"+{x}+{y}")
        self.deiconify()

    def _create_widgets(self):
        """创建控件"""
        # 主容器
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 提醒设置组
        self._create_reminder_group(main_frame)

        # 界面设置组
        self._create_ui_group(main_frame)

        # 按钮区域
        self._create_buttons(main_frame)

    def _create_reminder_group(self, parent):
        """创建提醒设置组"""
        # 组标题
        group_frame = ttk.LabelFrame(parent, text="🔔 提醒设置", padding=10)
        group_frame.pack(fill=tk.X, pady=10)

        # 启用提醒
        ttk.Checkbutton(
            group_frame,
            text="启用提醒功能",
            variable=self.reminder_enabled_var,
            command=self._toggle_reminder_settings
        ).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)

        # 检查间隔
        ttk.Label(group_frame, text="检查间隔:").grid(row=1, column=0, sticky=tk.W, pady=5)
        interval_frame = ttk.Frame(group_frame)
        interval_frame.grid(row=1, column=1, sticky=tk.W, pady=5)

        self.check_interval_var.set("60")
        check_interval_combo = ttk.Combobox(
            interval_frame,
            textvariable=self.check_interval_var,
            values=["30", "60", "120", "300", "600"],
            state="readonly",
            width=8
        )
        check_interval_combo.pack(side=tk.LEFT)
        ttk.Label(interval_frame, text="秒").pack(side=tk.LEFT, padx=5)

        # 警告提醒天数
        ttk.Label(group_frame, text="警告提醒:").grid(row=2, column=0, sticky=tk.W, pady=5)
        warning_frame = ttk.Frame(group_frame)
        warning_frame.grid(row=2, column=1, sticky=tk.W, pady=5)

        self.warning_days_var.set("7")
        warning_combo = ttk.Combobox(
            warning_frame,
            textvariable=self.warning_days_var,
            values=["1", "2", "3", "5", "7", "10", "14"],
            state="readonly",
            width=8
        )
        warning_combo.pack(side=tk.LEFT)
        ttk.Label(warning_frame, text="天内").pack(side=tk.LEFT, padx=5)

        # 紧急提醒天数
        ttk.Label(group_frame, text="紧急提醒:").grid(row=3, column=0, sticky=tk.W, pady=5)
        urgent_frame = ttk.Frame(group_frame)
        urgent_frame.grid(row=3, column=1, sticky=tk.W, pady=5)

        self.urgent_days_var.set("3")
        urgent_combo = ttk.Combobox(
            urgent_frame,
            textvariable=self.urgent_days_var,
            values=["1", "2", "3", "5"],
            state="readonly",
            width=8
        )
        urgent_combo.pack(side=tk.LEFT)
        ttk.Label(urgent_frame, text="天内").pack(side=tk.LEFT, padx=5)

        # 配置列权重
        group_frame.columnconfigure(1, weight=1)

    def _create_ui_group(self, parent):
        """创建界面设置组"""
        # 组标题
        group_frame = ttk.LabelFrame(parent, text="🎨 界面设置", padding=10)
        group_frame.pack(fill=tk.X, pady=10)

        # 自动显示主窗口
        ttk.Checkbutton(
            group_frame,
            text="收到提醒时自动显示主窗口",
            variable=self.auto_show_var
        ).pack(anchor=tk.W, pady=5)

    def _create_buttons(self, parent):
        """创建按钮"""
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=20)

        ttk.Button(btn_frame, text="保存", command=self._save_settings, width=10).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy, width=10).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="重置", command=self._reset_settings, width=10).pack(side=tk.LEFT, padx=5)

    def _toggle_reminder_settings(self):
        """切换提醒设置启用状态"""
        enabled = self.reminder_enabled_var.get()
        # 这里可以添加启用/禁用子控件的逻辑

    def _load_settings(self):
        """加载设置"""
        # 加载提醒设置
        self.reminder_enabled_var.set(self.data_manager.get_config("reminder_enabled", True))
        self.check_interval_var.set(str(self.data_manager.get_config("reminder_interval", 60)))
        self.warning_days_var.set(str(self.data_manager.get_config("warning_days", 7)))
        self.urgent_days_var.set(str(self.data_manager.get_config("urgent_days", 3)))

        # 加载界面设置
        self.auto_show_var.set(self.data_manager.get_config("auto_show_on_reminder", True))

    def _save_settings(self):
        """保存设置"""
        try:
            # 验证输入
            check_interval = int(self.check_interval_var.get())
            warning_days = int(self.warning_days_var.get())
            urgent_days = int(self.urgent_days_var.get())

            if check_interval < 10:
                messagebox.showwarning("提示", "检查间隔不能小于10秒！", parent=self)
                return

            if urgent_days >= warning_days:
                messagebox.showwarning("提示", "紧急提醒天数必须小于警告提醒天数！", parent=self)
                return

            # 保存提醒设置
            self.data_manager.set_config("reminder_enabled", self.reminder_enabled_var.get())
            self.data_manager.set_config("reminder_interval", check_interval)
            self.data_manager.set_config("warning_days", warning_days)
            self.data_manager.set_config("urgent_days", urgent_days)

            # 保存界面设置
            self.data_manager.set_config("auto_show_on_reminder", self.auto_show_var.get())

            messagebox.showinfo("提示", "设置已保存！", parent=self)

            # 调用回调
            if self.callback:
                self.callback()

            self.destroy()

        except ValueError as e:
            messagebox.showerror("错误", f"保存设置失败：{str(e)}", parent=self)

    def _reset_settings(self):
        """重置设置"""
        if messagebox.askyesno("确认", "确定要重置所有设置为默认值吗？", parent=self):
            # 重置为默认值
            self.reminder_enabled_var.set(True)
            self.check_interval_var.set("60")
            self.warning_days_var.set("7")
            self.urgent_days_var.set("3")
            self.auto_show_var.set(True)