#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
设置对话框
"""

import tkinter as tk
from tkinter import ttk, messagebox
from ui.styles import COLORS, FONTS


class SettingsDialog(tk.Toplevel):
    """设置对话框"""
    
    def __init__(self, parent, data_manager, callback=None):
        super().__init__(parent)
        self.parent = parent
        self.data_manager = data_manager
        self.callback = callback
        
        # 先隐藏窗口，防止闪烁
        self.withdraw()
        
        self._setup_window()
        self._create_widgets()
        self._load_settings()
        
        # 模态对话框
        self.transient(parent)
        self.grab_set()
        
        # 计算位置并显示
        self._center_window()
        
        # 显示窗口
        self.deiconify()
        self.focus_set()
    
    def _setup_window(self):
        """设置窗口"""
        self.title("⚙️ 设置")
        self.configure(bg=COLORS["bg_primary"])
        self.resizable(False, False)
    
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
    
    def _create_widgets(self):
        """创建控件"""
        # 使用Notebook创建标签页
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 提醒设置标签页
        reminder_frame = self._create_reminder_tab()
        notebook.add(reminder_frame, text="提醒设置")
        
        # 外观设置标签页
        appearance_frame = self._create_appearance_tab()
        notebook.add(appearance_frame, text="外观设置")
        
        # 通用设置标签页
        general_frame = self._create_general_tab()
        notebook.add(general_frame, text="通用设置")
        
        # 按钮区域
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="保存", command=self._save, width=10).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="取消", command=self.destroy, width=10).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="恢复默认", command=self._reset_defaults, width=10).pack(side=tk.LEFT, padx=5)
    
    def _create_reminder_tab(self):
        """创建提醒设置标签页"""
        frame = ttk.Frame(self, padding=20)
        
        # 启用提醒
        self.reminder_enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            frame,
            text="启用提醒功能",
            variable=self.reminder_enabled_var,
            command=self._toggle_reminder_options
        ).grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=10)
        
        # 提醒选项容器
        self.reminder_options_frame = ttk.LabelFrame(frame, text="提醒规则", padding=15)
        self.reminder_options_frame.grid(row=1, column=0, columnspan=3, sticky=tk.EW, pady=10)
        
        # 7天提醒
        row = 0
        ttk.Label(self.reminder_options_frame, text="提前7天提醒:", font=FONTS["normal"]).grid(
            row=row, column=0, sticky=tk.W, pady=8)
        
        self.remind_7day_enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.reminder_options_frame,
            text="启用",
            variable=self.remind_7day_enabled_var
        ).grid(row=row, column=1, sticky=tk.W, padx=10)
        
        # 3天提醒
        row = 1
        ttk.Label(self.reminder_options_frame, text="提前3天提醒:", font=FONTS["normal"]).grid(
            row=row, column=0, sticky=tk.W, pady=8)
        
        self.remind_3day_enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.reminder_options_frame,
            text="启用",
            variable=self.remind_3day_enabled_var
        ).grid(row=row, column=1, sticky=tk.W, padx=10)
        
        # 逾期提醒
        row = 2
        ttk.Label(self.reminder_options_frame, text="逾期提醒:", font=FONTS["normal"]).grid(
            row=row, column=0, sticky=tk.W, pady=8)
        
        self.remind_overdue_enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            self.reminder_options_frame,
            text="启用",
            variable=self.remind_overdue_enabled_var
        ).grid(row=row, column=1, sticky=tk.W, padx=10)
        
        # 分隔线
        ttk.Separator(self.reminder_options_frame, orient=tk.HORIZONTAL).grid(
            row=3, column=0, columnspan=3, sticky=tk.EW, pady=15)
        
        # 检查间隔
        row = 4
        ttk.Label(self.reminder_options_frame, text="检查间隔:", font=FONTS["normal"]).grid(
            row=row, column=0, sticky=tk.W, pady=8)
        
        interval_frame = ttk.Frame(self.reminder_options_frame)
        interval_frame.grid(row=row, column=1, columnspan=2, sticky=tk.W, padx=10)
        
        self.check_interval_var = tk.StringVar(value="60")
        interval_spinbox = ttk.Spinbox(
            interval_frame,
            textvariable=self.check_interval_var,
            from_=10,
            to=3600,
            width=8
        )
        interval_spinbox.pack(side=tk.LEFT)
        ttk.Label(interval_frame, text="秒").pack(side=tk.LEFT, padx=5)
        
        # 重复提醒
        row = 5
        ttk.Label(self.reminder_options_frame, text="重复提醒:", font=FONTS["normal"]).grid(
            row=row, column=0, sticky=tk.W, pady=8)
        
        self.repeat_reminder_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self.reminder_options_frame,
            text="每次检查时重复提醒未处理事项",
            variable=self.repeat_reminder_var
        ).grid(row=row, column=1, columnspan=2, sticky=tk.W, padx=10)
        
        # 重复提醒间隔
        row = 6
        ttk.Label(self.reminder_options_frame, text="重复间隔:", font=FONTS["normal"]).grid(
            row=row, column=0, sticky=tk.W, pady=8)
        
        repeat_frame = ttk.Frame(self.reminder_options_frame)
        repeat_frame.grid(row=row, column=1, columnspan=2, sticky=tk.W, padx=10)
        
        self.repeat_interval_var = tk.StringVar(value="30")
        repeat_spinbox = ttk.Spinbox(
            repeat_frame,
            textvariable=self.repeat_interval_var,
            from_=5,
            to=1440,
            width=8
        )
        repeat_spinbox.pack(side=tk.LEFT)
        ttk.Label(repeat_frame, text="分钟 (仅当重复提醒启用时生效)").pack(side=tk.LEFT, padx=5)
        
        # Toast通知设置
        toast_frame = ttk.LabelFrame(frame, text="通知方式", padding=15)
        toast_frame.grid(row=2, column=0, columnspan=3, sticky=tk.EW, pady=10)
        
        self.toast_enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            toast_frame,
            text="Windows Toast 气泡通知",
            variable=self.toast_enabled_var
        ).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.sound_enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            toast_frame,
            text="提示音",
            variable=self.sound_enabled_var
        ).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.popup_enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            toast_frame,
            text="弹出主窗口",
            variable=self.popup_enabled_var
        ).grid(row=2, column=0, sticky=tk.W, pady=5)
        
        return frame
    
    def _create_appearance_tab(self):
        """创建外观设置标签页"""
        frame = ttk.Frame(self, padding=20)
        
        # 透明度
        row = 0
        ttk.Label(frame, text="窗口透明度:", font=FONTS["normal"]).grid(
            row=row, column=0, sticky=tk.W, pady=10)
        
        opacity_frame = ttk.Frame(frame)
        opacity_frame.grid(row=row, column=1, sticky=tk.EW, pady=10)
        
        self.opacity_var = tk.DoubleVar(value=0.95)
        opacity_scale = ttk.Scale(
            opacity_frame,
            from_=0.5,
            to=1.0,
            variable=self.opacity_var,
            orient=tk.HORIZONTAL,
            length=200,
            command=self._preview_opacity
        )
        opacity_scale.pack(side=tk.LEFT)
        
        self.opacity_label = ttk.Label(opacity_frame, text="95%", width=5)
        self.opacity_label.pack(side=tk.LEFT, padx=10)
        
        # 窗口置顶
        row = 1
        self.always_on_top_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frame,
            text="窗口始终置顶",
            variable=self.always_on_top_var
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        # 显示已完成事项
        row = 2
        self.show_completed_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            frame,
            text="显示已完成事项",
            variable=self.show_completed_var
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        # 颜色设置说明
        row = 3
        color_frame = ttk.LabelFrame(frame, text="紧急程度颜色说明", padding=15)
        color_frame.grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=20)
        
        colors_info = [
            ("正常 (>7天)", COLORS["text_normal"], "正常显示"),
            ("警告 (3-7天)", COLORS["text_warning"], "橙色显示"),
            ("紧急 (≤3天)", COLORS["text_urgent"], "红色加粗"),
            ("逾期", COLORS["text_urgent"], "红色加粗+通知"),
        ]
        
        for i, (label, color, desc) in enumerate(colors_info):
            tk.Label(
                color_frame,
                text="■",
                fg=color,
                font=("Arial", 14)
            ).grid(row=i, column=0, padx=5, pady=3)
            ttk.Label(color_frame, text=f"{label}: {desc}").grid(
                row=i, column=1, sticky=tk.W, padx=10, pady=3)
        
        return frame
    
    def _create_general_tab(self):
        """创建通用设置标签页"""
        frame = ttk.Frame(self, padding=20)
        
        # 开机自启
        row = 0
        self.auto_start_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frame,
            text="开机自动启动",
            variable=self.auto_start_var
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        # 最小化到托盘
        row = 1
        self.minimize_to_tray_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            frame,
            text="关闭窗口时最小化到系统托盘",
            variable=self.minimize_to_tray_var
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        # 启动时检查提醒
        row = 2
        self.check_on_start_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            frame,
            text="启动时立即检查提醒",
            variable=self.check_on_start_var
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        # 数据备份
        row = 3
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=2, sticky=tk.EW, pady=20)
        
        row = 4
        data_frame = ttk.LabelFrame(frame, text="数据管理", padding=15)
        data_frame.grid(row=row, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        ttk.Button(
            data_frame,
            text="导出数据",
            command=self._export_data,
            width=15
        ).grid(row=0, column=0, padx=10, pady=5)
        
        ttk.Button(
            data_frame,
            text="导入数据",
            command=self._import_data,
            width=15
        ).grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Button(
            data_frame,
            text="清空所有数据",
            command=self._clear_data,
            width=15
        ).grid(row=0, column=2, padx=10, pady=5)
        
        # 版本信息
        row = 5
        ttk.Label(
            frame,
            text="待办事项提醒 v1.0.0",
            font=FONTS["small"],
            foreground="gray"
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=30)
        
        return frame
    
    def _toggle_reminder_options(self):
        """切换提醒选项启用状态"""
        enabled = self.reminder_enabled_var.get()
        state = "normal" if enabled else "disabled"
        
        for child in self.reminder_options_frame.winfo_children():
            try:
                child.configure(state=state)
            except:
                pass
    
    def _preview_opacity(self, value):
        """预览透明度"""
        opacity = float(value)
        self.opacity_label.configure(text=f"{int(opacity*100)}%")
        self.parent.attributes('-alpha', opacity)
    
    def _load_settings(self):
        """加载设置"""
        dm = self.data_manager
        
        # 提醒设置
        self.reminder_enabled_var.set(dm.get_config("reminder_enabled", True))
        self.remind_7day_enabled_var.set(dm.get_config("remind_7day_enabled", True))
        self.remind_3day_enabled_var.set(dm.get_config("remind_3day_enabled", True))
        self.remind_overdue_enabled_var.set(dm.get_config("remind_overdue_enabled", True))
        self.check_interval_var.set(str(dm.get_config("reminder_interval", 60)))
        self.repeat_reminder_var.set(dm.get_config("repeat_reminder", False))
        self.repeat_interval_var.set(str(dm.get_config("repeat_interval", 30)))
        
        # 通知设置
        self.toast_enabled_var.set(dm.get_config("toast_enabled", True))
        self.sound_enabled_var.set(dm.get_config("sound_enabled", True))
        self.popup_enabled_var.set(dm.get_config("popup_enabled", True))
        
        # 外观设置
        self.opacity_var.set(dm.get_config("opacity", 0.95))
        self.opacity_label.configure(text=f"{int(self.opacity_var.get()*100)}%")
        self.always_on_top_var.set(dm.get_config("always_on_top", False))
        self.show_completed_var.set(dm.get_config("show_completed", True))
        
        # 通用设置
        self.auto_start_var.set(dm.get_config("auto_start", False))
        self.minimize_to_tray_var.set(dm.get_config("minimize_to_tray", True))
        self.check_on_start_var.set(dm.get_config("check_on_start", True))
        
        # 更新UI状态
        self._toggle_reminder_options()
    
    def _save(self):
        """保存设置"""
        try:
            # 验证输入
            interval = int(self.check_interval_var.get())
            if interval < 10:
                messagebox.showwarning("提示", "检查间隔不能小于10秒", parent=self)
                return
            
            repeat_interval = int(self.repeat_interval_var.get())
            if repeat_interval < 5:
                messagebox.showwarning("提示", "重复间隔不能小于5分钟", parent=self)
                return
        except ValueError:
            messagebox.showwarning("提示", "请输入有效的数字", parent=self)
            return
        
        dm = self.data_manager
        
        # 保存提醒设置
        dm.set_config("reminder_enabled", self.reminder_enabled_var.get())
        dm.set_config("remind_7day_enabled", self.remind_7day_enabled_var.get())
        dm.set_config("remind_3day_enabled", self.remind_3day_enabled_var.get())
        dm.set_config("remind_overdue_enabled", self.remind_overdue_enabled_var.get())
        dm.set_config("reminder_interval", interval)
        dm.set_config("repeat_reminder", self.repeat_reminder_var.get())
        dm.set_config("repeat_interval", repeat_interval)
        
        # 保存通知设置
        dm.set_config("toast_enabled", self.toast_enabled_var.get())
        dm.set_config("sound_enabled", self.sound_enabled_var.get())
        dm.set_config("popup_enabled", self.popup_enabled_var.get())
        
        # 保存外观设置
        dm.set_config("opacity", self.opacity_var.get())
        dm.set_config("always_on_top", self.always_on_top_var.get())
        dm.set_config("show_completed", self.show_completed_var.get())
        
        # 保存通用设置
        dm.set_config("auto_start", self.auto_start_var.get())
        dm.set_config("minimize_to_tray", self.minimize_to_tray_var.get())
        dm.set_config("check_on_start", self.check_on_start_var.get())
        
        # 应用设置
        self.parent.attributes('-alpha', self.opacity_var.get())
        self.parent.attributes('-topmost', self.always_on_top_var.get())
        
        # 处理开机自启
        self._set_auto_start(self.auto_start_var.get())
        
        # 回调
        if self.callback:
            self.callback()
        
        messagebox.showinfo("提示", "设置已保存", parent=self)
        self.destroy()
    
    def _reset_defaults(self):
        """恢复默认设置"""
        if messagebox.askyesno("确认", "确定要恢复默认设置吗？", parent=self):
            # 提醒设置
            self.reminder_enabled_var.set(True)
            self.remind_7day_enabled_var.set(True)
            self.remind_3day_enabled_var.set(True)
            self.remind_overdue_enabled_var.set(True)
            self.check_interval_var.set("60")
            self.repeat_reminder_var.set(False)
            self.repeat_interval_var.set("30")
            
            # 通知设置
            self.toast_enabled_var.set(True)
            self.sound_enabled_var.set(True)
            self.popup_enabled_var.set(True)
            
            # 外观设置
            self.opacity_var.set(0.95)
            self.opacity_label.configure(text="95%")
            self.always_on_top_var.set(False)
            self.show_completed_var.set(True)
            
            # 通用设置
            self.auto_start_var.set(False)
            self.minimize_to_tray_var.set(True)
            self.check_on_start_var.set(True)
            
            self._toggle_reminder_options()
            self.parent.attributes('-alpha', 0.95)
    
    def _set_auto_start(self, enabled):
        """设置开机自启"""
        try:
            import winreg
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            app_name = "TodoReminder"
            
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
            
            if enabled:
                import sys
                import os
                exe_path = sys.executable
                if getattr(sys, 'frozen', False):
                    exe_path = sys.executable
                else:
                    exe_path = f'"{sys.executable}" "{os.path.abspath("main.py")}"'
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exe_path)
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except FileNotFoundError:
                    pass
            
            winreg.CloseKey(key)
        except Exception as e:
            print(f"设置开机自启失败: {e}")
    
    def _export_data(self):
        """导出数据"""
        from tkinter import filedialog
        import json
        import shutil
        
        file_path = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
            title="导出数据"
        )
        
        if file_path:
            try:
                shutil.copy(self.data_manager.data_file, file_path)
                messagebox.showinfo("提示", f"数据已导出到:\n{file_path}", parent=self)
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {e}", parent=self)
    
    def _import_data(self):
        """导入数据"""
        from tkinter import filedialog
        import json
        import shutil
        
        file_path = filedialog.askopenfilename(
            parent=self,
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")],
            title="导入数据"
        )
        
        if file_path:
            if messagebox.askyesno("确认", "导入将覆盖现有数据，是否继续？", parent=self):
                try:
                    # 验证文件格式
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    shutil.copy(file_path, self.data_manager.data_file)
                    self.data_manager.load()
                    
                    if self.callback:
                        self.callback()
                    
                    messagebox.showinfo("提示", "数据导入成功", parent=self)
                except Exception as e:
                    messagebox.showerror("错误", f"导入失败: {e}", parent=self)
    
    def _clear_data(self):
        """清空数据"""
        if messagebox.askyesno("警告", "确定要清空所有待办事项吗？\n此操作不可恢复！", parent=self):
            if messagebox.askyesno("再次确认", "真的要清空吗？", parent=self):
                self.data_manager._todos = []
                self.data_manager.save()
                
                if self.callback:
                    self.callback()
                
                messagebox.showinfo("提示", "数据已清空", parent=self)