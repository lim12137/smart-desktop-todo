#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
登录对话框
IP自动识别，用户登录，Token存储
"""

import tkinter as tk
from tkinter import ttk, messagebox
import socket
import json
import os
from pathlib import Path


class LoginDialog(tk.Toplevel):
    """登录对话框"""

    def __init__(self, parent, on_login_success, server_url="http://localhost:5000"):
        super().__init__(parent)
        self.parent = parent
        self.on_login_success = on_login_success
        self.server_url = server_url
        self.result = None

        # 先隐藏窗口，防止闪烁
        self.withdraw()

        self._setup_window()
        self._create_widgets()
        self._detect_ip()
        self._load_saved_config()

        # 模态对话框
        self.transient(parent)
        self.grab_set()

        # 居中显示
        self._center_window()
        self.deiconify()
        self.focus_set()
        self.username_entry.focus_set()
        self.wait_window()

    def _setup_window(self):
        """设置窗口"""
        self.title("登录 - 待办事项提醒")
        self.resizable(False, False)
        self.configure(bg='#F0F0F0')
        self.geometry("400x350")

    def _create_widgets(self):
        """创建控件"""
        # 主框架
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = ttk.Label(
            main_frame,
            text="📋 待办事项提醒",
            font=('Microsoft YaHei UI', 16, 'bold')
        )
        title_label.pack(pady=(0, 20))

        # IP地址显示
        ip_frame = ttk.Frame(main_frame)
        ip_frame.pack(fill=tk.X, pady=10)

        ttk.Label(ip_frame, text="您的IP地址：").pack(side=tk.LEFT)
        self.ip_label = ttk.Label(ip_frame, text="正在检测...", font=('Consolas', 10))
        self.ip_label.pack(side=tk.LEFT, padx=10)

        ttk.Button(
            ip_frame,
            text="刷新",
            command=self._detect_ip,
            width=8
        ).pack(side=tk.LEFT, padx=5)

        # 用户名
        ttk.Label(main_frame, text="用户名：").pack(anchor=tk.W, pady=(10, 5))
        self.username_var = tk.StringVar()
        self.username_entry = ttk.Entry(main_frame, textvariable=self.username_var, width=30)
        self.username_entry.pack(fill=tk.X, pady=5)

        # 密码
        ttk.Label(main_frame, text="密码：").pack(anchor=tk.W, pady=(10, 5))
        self.password_var = tk.StringVar()
        self.password_entry = ttk.Entry(
            main_frame,
            textvariable=self.password_var,
            show='*',
            width=30
        )
        self.password_entry.pack(fill=tk.X, pady=5)

        # 记住密码
        self.remember_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            main_frame,
            text="记住登录状态",
            variable=self.remember_var
        ).pack(anchor=tk.W, pady=10)

        # 分隔线
        ttk.Separator(main_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=20)

        # 服务器设置
        server_frame = ttk.LabelFrame(main_frame, text="服务器设置", padding=10)
        server_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(server_frame, text="服务器地址：").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.server_var = tk.StringVar(value=self.server_url)
        server_entry = ttk.Entry(server_frame, textvariable=self.server_var, width=25)
        server_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        server_frame.columnconfigure(1, weight=1)

        ttk.Button(
            server_frame,
            text="连接测试",
            command=self._test_connection,
            width=10
        ).grid(row=1, column=1, sticky=tk.E, pady=5)

        # 登录按钮
        login_btn = ttk.Button(
            main_frame,
            text="登录",
            command=self._login,
            width=20
        )
        login_btn.pack(pady=15)

        # 状态标签
        self.status_label = ttk.Label(main_frame, text="请输入用户名和密码", foreground='#666')
        self.status_label.pack(pady=10)

        # 绑定回车键
        self.bind('<Return>', lambda e: self._login())

    def _detect_ip(self):
        """检测本地IP地址"""
        self.status_label.config(text="正在检测IP...", foreground='#666')
        self.update()

        try:
            # 获取本地IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()

            self.ip_label.config(text=local_ip)
            self.status_label.config(text="IP检测完成", foreground='#006400')

        except Exception as e:
            self.ip_label.config(text="IP检测失败")
            self.status_label.config(text=f"IP检测失败: {str(e)}", foreground='#8B0000')

    def _load_saved_config(self):
        """加载保存的配置"""
        config_file = os.path.join(os.path.expanduser('~'), '.todo_reminder_client')
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    self.server_var.set(config.get('server_url', self.server_url))
                    if config.get('remember', False):
                        self.username_var.set(config.get('username', ''))
                        self.remember_var.set(True)
                        self.password_var.set(config.get('password', ''))
            except:
                pass

    def _save_config(self):
        """保存配置"""
        config_file = os.path.join(os.path.expanduser('~'), '.todo_reminder_client')
        config = {
            'server_url': self.server_var.get(),
            'remember': self.remember_var.get(),
            'username': self.username_var.get() if self.remember_var.get() else '',
            'password': self.password_var.get() if self.remember_var.get() else ''
        }
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def _test_connection(self):
        """测试服务器连接"""
        server_url = self.server_var.get().strip()
        if not server_url:
            messagebox.showwarning("提示", "请输入服务器地址", parent=self)
            return

        self.status_label.config(text="正在连接服务器...", foreground='#666')
        self.update()

        try:
            import requests
            response = requests.get(f"{server_url.rstrip('/')}/api/health", timeout=5)
            if response.status_code == 200:
                self.status_label.config(text="服务器连接成功！", foreground='#006400')
            else:
                self.status_label.config(text="服务器响应异常", foreground='#8B0000')
        except Exception as e:
            self.status_label.config(text=f"连接失败: {str(e)}", foreground='#8B0000')

    def _login(self):
        """登录"""
        username = self.username_var.get().strip()
        password = self.password_var.get().strip()
        server_url = self.server_var.get().strip()

        if not username or not password:
            messagebox.showwarning("提示", "请输入用户名和密码", parent=self)
            return

        if not server_url:
            messagebox.showwarning("提示", "请输入服务器地址", parent=self)
            return

        self.status_label.config(text="正在登录...", foreground='#666')
        self.update()

        try:
            from client.api_client import APIClient

            client = APIClient(server_url)
            result = client.login(username, password)

            if result.get('success'):
                # 保存配置
                if self.remember_var.get():
                    self._save_config()

                # 回调
                self.result = {
                    'success': True,
                    'user': result['user'],
                    'token': result['token'],
                    'server_url': server_url
                }

                if self.on_login_success:
                    self.on_login_success(self.result)

                self.destroy()
            else:
                self.status_label.config(text=result.get('message', '登录失败'), foreground='#8B0000')
                messagebox.showerror("登录失败", result.get('message', '登录失败'), parent=self)

        except Exception as e:
            self.status_label.config(text=f"登录异常: {str(e)}", foreground='#8B0000')
            messagebox.showerror("登录异常", f"登录过程中发生错误：\n{str(e)}", parent=self)

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
