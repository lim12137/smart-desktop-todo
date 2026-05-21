#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
连接对话框（自动发现版）
自动扫描局域网服务器，合并连接和登录为一步
"""

import tkinter as tk
from tkinter import ttk, messagebox
import socket
import json
import os
import threading


BROADCAST_PORT = 15432
CONFIG_FILE = os.path.join(os.path.expanduser('~'), '.todo_reminder_client')


def discover_servers(timeout=3):
    """监听 UDP 广播，发现局域网内的服务器"""
    found = {}
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(("", BROADCAST_PORT))
    except Exception:
        return found

    sock.settimeout(timeout)
    deadline = socket.getdefaulttimeout()
    import time
    end_time = time.time() + timeout

    while time.time() < end_time:
        remaining = end_time - time.time()
        if remaining <= 0:
            break
        sock.settimeout(remaining)
        try:
            data, addr = sock.recvfrom(1024)
            info = json.loads(data.decode("utf-8"))
            key = f"{info['ip']}:{info['port']}"
            if key not in found:
                found[key] = info
        except socket.timeout:
            break
        except Exception:
            break

    sock.close()
    return found


def load_saved_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(server_url, token=None, user=None):
    data = {"server_url": server_url}
    if token:
        data["token"] = token
    if user:
        data["user"] = user
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class ConnectDialog(tk.Toplevel):
    """自动发现 + 一步登录"""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.result = None

        self.withdraw()
        self.title("连接 - 待办事项提醒")
        self.resizable(False, False)
        self.configure(bg='#F0F0F0')
        self.geometry("440x280")

        self._create_widgets()
        self._start_discovery()

        self.transient(parent)
        self.grab_set()
        self._center_window()
        self.deiconify()
        self.focus_set()
        self.wait_window()

    def _create_widgets(self):
        main = ttk.Frame(self, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main, text="📋 待办事项提醒",
                  font=('Microsoft YaHei UI', 16, 'bold')).pack(pady=(0, 12))

        # 服务器选择
        ttk.Label(main, text="服务器：").pack(anchor=tk.W)
        self.server_var = tk.StringVar()
        self.server_combo = ttk.Combobox(main, textvariable=self.server_var, width=40)
        self.server_combo.pack(fill=tk.X, pady=(0, 8))
        self.server_combo.bind("<<ComboboxSelected>>", lambda e: self._on_server_selected())

        # 管理员密码
        self.pwd_frame = ttk.Frame(main)
        self.pwd_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(self.pwd_frame, text="管理员密码：").pack(side=tk.LEFT)
        self.password_var = tk.StringVar()
        self.pwd_entry = ttk.Entry(self.pwd_frame, textvariable=self.password_var,
                                   show='*', width=20)
        self.pwd_entry.pack(side=tk.LEFT, padx=5)
        self.pwd_frame.pack_forget()  # 默认隐藏

        # 连接按钮
        self.connect_btn = ttk.Button(main, text="连接", command=self._connect, width=25)
        self.connect_btn.pack(pady=8)

        # 状态
        self.status_label = ttk.Label(main, text="正在扫描局域网...", foreground='#666',
                                      font=('Microsoft YaHei UI', 9))
        self.status_label.pack()

        self.bind('<Return>', lambda e: self._connect())

    def _start_discovery(self):
        saved = load_saved_config()

        def do_discover():
            servers = discover_servers(timeout=3)
            urls = []
            self._server_info = {}
            for key, info in servers.items():
                url = f"http://{info['ip']}:{info['port']}"
                urls.append(f"{info['name']} ({info['ip']}:{info['port']})")
                self._server_info[urls[-1]] = url

            self.after(0, lambda: self._on_discovery_done(urls, saved))

        self._server_info = {}
        threading.Thread(target=do_discover, daemon=True).start()

    def _on_discovery_done(self, urls, saved):
        if urls:
            self.server_combo['values'] = urls
            self.server_combo.current(0)
            self.status_label.configure(text=f"发现 {len(urls)} 个服务器", foreground='#006400')
            self._show_pwd_if_needed()
        else:
            # 没发现，用手动输入
            self.server_combo['values'] = []
            fallback = saved.get("server_url", "http://localhost:5000")
            self.server_var.set(fallback)
            self.server_combo.configure(postcommand=lambda: None)
            self.status_label.configure(text="未发现服务器，请手动输入地址", foreground='#8B0000')

        # 尝试自动重连
        saved_url = saved.get("server_url", "")
        saved_token = saved.get("token")
        saved_user = saved.get("user")
        if saved_url and saved_token and saved_user:
            self._auto_reconnect(saved_url, saved_token, saved_user)

    def _get_server_url(self):
        text = self.server_var.get().strip()
        if text in self._server_info:
            return self._server_info[text]
        if text.startswith("http"):
            return text.rstrip('/')
        return f"http://{text}"

    def _on_server_selected(self):
        self._show_pwd_if_needed()

    def _show_pwd_if_needed(self):
        """尝试通过 IP 检查当前身份，管理员则显示密码框"""
        import requests
        url = self._get_server_url()
        try:
            resp = requests.get(f"{url}/api/auth/ip-check", timeout=2)
            data = resp.json()
            if data.get("registered") and data.get("needs_password"):
                name = data["user"]["display_name"]
                self.pwd_frame.pack(fill=tk.X, pady=(0, 8), before=self.connect_btn)
                self.connect_btn.configure(text=f"登录 ({name})")
                self.pwd_entry.focus_set()
            else:
                self.pwd_frame.pack_forget()
                self.connect_btn.configure(text="连接")
        except Exception:
            pass

    def _auto_reconnect(self, server_url, token, user):
        """尝试用保存的 token 自动重连"""
        import requests
        try:
            resp = requests.get(f"{server_url}/api/auth/me",
                                headers={"Authorization": f"Bearer {token}"}, timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("success"):
                    self.result = {"token": token, "user": data["user"], "server_url": server_url}
                    self.status_label.configure(text=f"自动连接成功: {user.get('display_name', '')}",
                                                foreground='#006400')
                    self.after(500, self.destroy)
                    return
        except Exception:
            pass

    def _connect(self):
        import requests
        server_url = self._get_server_url()
        if not server_url:
            messagebox.showwarning("提示", "请选择或输入服务器地址", parent=self)
            return

        self.status_label.configure(text="正在连接...", foreground='#666')
        self.update()

        # 如果密码框可见 → 管理员登录
        if self.pwd_frame.winfo_manager():
            password = self.password_var.get().strip()
            if not password:
                messagebox.showwarning("提示", "请输入管理员密码", parent=self)
                return
            try:
                resp = requests.post(f"{server_url}/api/auth/login",
                                     json={"password": password}, timeout=5)
                data = resp.json()
                if data.get("success"):
                    self._on_success(data["token"], data["user"], server_url)
                else:
                    self.status_label.configure(text=data.get("message", "密码错误"), foreground='#8B0000')
            except Exception as e:
                self.status_label.configure(text=f"连接失败: {e}", foreground='#8B0000')
            return

        # 成员或未知身份 → 先尝试 IP 自动识别
        try:
            resp = requests.post(f"{server_url}/api/auth/connect", json={}, timeout=5)
            data = resp.json()

            if data.get("success") and data.get("token"):
                # 成员，直接进入
                self._on_success(data["token"], data["user"], server_url)
            elif data.get("needs_password"):
                # 管理员，显示密码框
                name = data["user"]["display_name"]
                self.pwd_frame.pack(fill=tk.X, pady=(0, 8), before=self.connect_btn)
                self.connect_btn.configure(text=f"登录 ({name})")
                self.pwd_entry.focus_set()
                self.status_label.configure(text=f"欢迎管理员 {name}，请输入密码", foreground='#006400')
            else:
                self.status_label.configure(text=data.get("message", "连接失败"), foreground='#8B0000')
        except Exception as e:
            self.status_label.configure(text=f"连接失败: {e}", foreground='#8B0000')

    def _on_success(self, token, user, server_url):
        self.result = {"token": token, "user": user, "server_url": server_url}
        save_config(server_url, token, user)
        self.destroy()

    def _center_window(self):
        self.update_idletasks()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        pw = self.parent.winfo_width()
        ph = self.parent.winfo_height()
        px = self.parent.winfo_rootx()
        py = self.parent.winfo_rooty()

        if pw < 100 or ph < 100:
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            x = (sw - w) // 2
            y = (sh - h) // 2
        else:
            x = px + (pw - w) // 2
            y = py + (ph - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")
