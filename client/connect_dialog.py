#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
连接对话框
IP自动识别身份，管理员需输入密码，成员直接进入
"""

import tkinter as tk
from tkinter import ttk, messagebox
import socket
import json
import os


class ConnectDialog(tk.Toplevel):
    """连接对话框"""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.result = None  # {'token', 'user', 'server_url'}

        self.withdraw()

        self._setup_window()
        self._create_widgets()
        self._detect_ip()
        self._load_saved_config()

        self.transient(parent)
        self.grab_set()
        self._center_window()
        self.deiconify()
        self.focus_set()
        self.wait_window()

    def _setup_window(self):
        self.title("连接 - 待办事项提醒")
        self.resizable(False, False)
        self.configure(bg='#F0F0F0')
        self.geometry("420x320")

    def _create_widgets(self):
        main = ttk.Frame(self, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        # 标题
        ttk.Label(main, text="📋 待办事项提醒",
                  font=('Microsoft YaHei UI', 16, 'bold')).pack(pady=(0, 15))

        # IP显示
        ip_frame = ttk.Frame(main)
        ip_frame.pack(fill=tk.X, pady=5)
        ttk.Label(ip_frame, text="本机IP：").pack(side=tk.LEFT)
        self.ip_label = ttk.Label(ip_frame, text="检测中...", font=('Consolas', 10))
        self.ip_label.pack(side=tk.LEFT, padx=5)

        # 服务器地址
        ttk.Label(main, text="服务器地址：").pack(anchor=tk.W, pady=(10, 2))
        self.server_var = tk.StringVar(value="http://localhost:5000")
        ttk.Entry(main, textvariable=self.server_var, width=35).pack(fill=tk.X)

        # 管理员密码（初始隐藏）
        self.pwd_frame = ttk.Frame(main)
        # 不先pack，连接后根据身份决定是否显示
        ttk.Label(self.pwd_frame, text="管理员密码：").pack(side=tk.LEFT)
        self.password_var = tk.StringVar()
        ttk.Entry(self.pwd_frame, textvariable=self.password_var,
                  show='*', width=20).pack(side=tk.LEFT, padx=5)

        # 连接按钮
        self.connect_btn = ttk.Button(main, text="连接", command=self._connect, width=20)
        self.connect_btn.pack(pady=15)

        # 状态
        self.status_label = ttk.Label(main, text="输入服务器地址后点击连接", foreground='#666')
        self.status_label.pack(pady=5)

        self.bind('<Return>', lambda e: self._connect())

    def _detect_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            self.ip_label.config(text=ip)
        except Exception:
            self.ip_label.config(text="检测失败")

    def _load_saved_config(self):
        config_file = os.path.join(os.path.expanduser('~'), '.todo_reminder_client')
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    self.server_var.set(config.get('server_url', 'http://localhost:5000'))
            except (json.JSONDecodeError, IOError):
                pass

    def _save_config(self):
        config_file = os.path.join(os.path.expanduser('~'), '.todo_reminder_client')
        with open(config_file, 'w') as f:
            json.dump({'server_url': self.server_var.get().strip()}, f, indent=2)

    def _test_connection(self, server_url):
        """测试服务器是否可达"""
        import requests
        try:
            resp = requests.get(f"{server_url}/api/health", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    def _connect(self):
        server_url = self.server_var.get().strip().rstrip('/')
        if not server_url:
            messagebox.showwarning("提示", "请输入服务器地址", parent=self)
            return

        self.status_label.config(text="正在连接...", foreground='#666')
        self.update()

        # 先测试连通性
        if not self._test_connection(server_url):
            self.status_label.config(text="无法连接到服务器", foreground='#8B0000')
            return

        import requests

        # 如果密码框已显示，说明是管理员登录
        if self.pwd_frame.winfo_manager():
            password = self.password_var.get().strip()
            if not password:
                messagebox.showwarning("提示", "请输入管理员密码", parent=self)
                return
            try:
                resp = requests.post(f"{server_url}/api/auth/login",
                                     json={'password': password}, timeout=10)
                data = resp.json()
                if data.get('success'):
                    self._on_success(data['token'], data['user'], server_url)
                else:
                    self.status_label.config(text=data.get('message', '密码错误'), foreground='#8B0000')
            except Exception as e:
                self.status_label.config(text=f"连接异常: {e}", foreground='#8B0000')
            return

        # 首次连接，通过IP自动识别
        try:
            resp = requests.post(f"{server_url}/api/auth/connect",
                                 json={'ip_address': self.ip_label.cget('text')}, timeout=10)
            data = resp.json()

            if not data.get('success'):
                self.status_label.config(text=data.get('message', '连接失败'), foreground='#8B0000')
                return

            if data.get('needs_password'):
                # 管理员身份，显示密码框
                self.status_label.config(
                    text=f"欢迎管理员 {data['user']['display_name']}，请输入密码",
                    foreground='#006400')
                self.pwd_frame.pack(fill=tk.X, pady=(5, 0), before=self.connect_btn)
                self.connect_btn.config(text="登录")
                self.password_var.set('')
                self.focus_set()
                # 找到密码输入框并聚焦
                for child in self.pwd_frame.winfo_children():
                    if isinstance(child, ttk.Entry):
                        child.focus_set()
                        break
            else:
                # 成员身份，直接进入
                self._on_success(data['token'], data['user'], server_url)

        except Exception as e:
            self.status_label.config(text=f"连接异常: {e}", foreground='#8B0000')

    def _on_success(self, token, user, server_url):
        self.result = {
            'token': token,
            'user': user,
            'server_url': server_url
        }
        self._save_config()
        self.destroy()

    def _center_window(self):
        self.update_idletasks()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        pw = self.parent.winfo_width()
        ph = self.parent.winfo_height()
        px = self.parent.winfo_rootx()
        py = self.parent.winfo_rooty()

        # 父窗口太小则屏幕居中
        if pw < 100 or ph < 100:
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            x = (sw - w) // 2
            y = (sh - h) // 2
        else:
            x = px + (pw - w) // 2
            y = py + (ph - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
