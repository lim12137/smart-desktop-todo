#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
客户端主入口
成员通过IP自动识别，管理员需密码登录
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from client.connect_dialog import ConnectDialog
from client.data_manager import ClientDataManager
from client.performance import get_performance_optimizer
from client.reminder_poller import get_reminder_poller
from ui.main_window import TodoApp


class ClientApp:
    """客户端应用主类"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("待办事项提醒系统")
        self.root.geometry("1x1+0+0")
        self.root.overrideredirect(True)

        self.data_manager = ClientDataManager()
        self.performance_optimizer = None
        self.reminder_poller = None
        self.main_window = None

        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def run(self):
        self._show_connect_dialog()
        self.root.mainloop()

    def _show_connect_dialog(self):
        dlg = ConnectDialog(self.root)

        if dlg.result:
            token = dlg.result['token']
            user = dlg.result['user']
            server_url = dlg.result['server_url']

            self.data_manager.set_server(server_url)
            self.data_manager.api_client.set_token(token)
            self.data_manager._current_user = user
            self.data_manager._is_connected = True

            self.performance_optimizer = get_performance_optimizer(self.data_manager, self.root)
            self.reminder_poller = get_reminder_poller(poll_interval=300)

            self._create_main_window()

            # 恢复根窗口为正常显示
            self.root.overrideredirect(False)
            self.root.geometry("900x600")

            if self.main_window:
                self.reminder_poller.register_callback(self._on_reminder)
                self.reminder_poller.start()
        else:
            print("Connect dialog cancelled, exiting")
            self.root.destroy()

    def _create_main_window(self):
        if self.main_window:
            self.main_window.destroy()
        self.main_window = TodoApp(
            self.root,
            data_manager=self.data_manager,
            performance_optimizer=self.performance_optimizer
        )

    def _on_reminder(self, reminder: dict):
        message = reminder.get('message', '您有新的待办事项提醒')
        title = reminder.get('label', '待办事项提醒')
        self.root.after(0, lambda: self._show_reminder_ui(title, message))

    def _show_reminder_ui(self, title: str, message: str):
        if self.main_window and hasattr(self.main_window, 'status_label'):
            self.main_window.status_label.configure(text=message)
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception:
            pass
        messagebox.showwarning(title, message, parent=self.root)
        if self.main_window:
            self.main_window._refresh_list()

    def _on_closing(self):
        try:
            if self.performance_optimizer:
                self.performance_optimizer.destroy()
            if self.reminder_poller:
                self.reminder_poller.stop()
            if self.data_manager.is_connected():
                self.data_manager.logout()
        except Exception as e:
            print(f"清理资源时出错: {e}")
        finally:
            self.root.destroy()


def main():
    try:
        app = ClientApp()
        app.run()
    except Exception as e:
        import traceback
        traceback.print_exc()
        try:
            messagebox.showerror("错误", f"应用启动失败:\n{e}")
        except Exception:
            pass
        input("按回车键退出...")
        sys.exit(1)


if __name__ == "__main__":
    main()
