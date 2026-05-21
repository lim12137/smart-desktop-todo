#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
客户端提醒轮询器
定期从服务器获取待提醒任务
"""

import threading
import time
from typing import Callable, List
from client.api_client import get_api_client


class ReminderPoller:
    """客户端提醒轮询器"""

    def __init__(self, poll_interval: int = 300):
        """
        初始化提醒轮询器

        Args:
            poll_interval: 轮询间隔（秒），默认5分钟
        """
        self.poll_interval = poll_interval
        self._running = False
        self._thread = None
        self._callbacks: List[Callable] = []
        self._last_reminders: set = set()

    def register_callback(self, callback: Callable):
        """注册回调函数"""
        self._callbacks.append(callback)

    def start(self):
        """启动轮询"""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        print("提醒轮询器已启动")

    def stop(self):
        """停止轮询"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        print("提醒轮询器已停止")

    def _run_loop(self):
        """运行循环"""
        while self._running:
            try:
                self._check_reminders()
            except Exception as e:
                print(f"提醒检查出错: {e}")

            # 等待下一次检查
            for _ in range(self.poll_interval):
                if not self._running:
                    break
                time.sleep(1)

    def _check_reminders(self):
        """检查服务器上的待提醒任务"""
        api_client = get_api_client()

        if not api_client.is_authenticated():
            return

        try:
            result = api_client.get_pending_reminders()

            if result.get('success'):
                reminders = result.get('data', [])

                # 过滤出新提醒（使用todo_id和remind_type作为唯一标识）
                new_reminders = []
                for reminder in reminders:
                    reminder_key = f"{reminder['todo_id']}_{reminder['remind_type']}"
                    if reminder_key not in self._last_reminders:
                        new_reminders.append(reminder)
                        self._last_reminders.add(reminder_key)

                # 触发回调
                for reminder in new_reminders:
                    for callback in self._callbacks:
                        try:
                            callback(reminder)
                        except Exception as e:
                            print(f"回调执行失败: {e}")

                # 确认已收到的提醒
                for reminder in new_reminders:
                    try:
                        api_client.acknowledge_reminder(
                            reminder['todo_id'],
                            reminder['remind_type']
                        )
                    except Exception as e:
                        print(f"确认提醒失败: {e}")

        except Exception as e:
            print(f"获取提醒失败: {e}")

    def force_check(self):
        """强制立即检查一次"""
        threading.Thread(target=self._check_reminders, daemon=True).start()

    def restart(self, root=None):
        """重启轮询器（非阻塞）"""
        self.stop()
        if root:
            root.after(100, self.start)
        else:
            time.sleep(0.1)
            self.start()


# 全局提醒轮询器实例
_reminder_poller = None


def get_reminder_poller(poll_interval: int = 300) -> ReminderPoller:
    """
    获取全局提醒轮询器实例

    Args:
        poll_interval: 轮询间隔（秒），默认5分钟

    Returns:
        ReminderPoller实例
    """
    global _reminder_poller
    if _reminder_poller is None:
        _reminder_poller = ReminderPoller(poll_interval)
    return _reminder_poller
