#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
服务端提醒服务
定期检查并发送提醒
"""

import threading
import time
from typing import List, Tuple
from datetime import datetime, timedelta
from database import get_db


# 提醒类型配置
REMINDER_CONFIGS = {
    "7day": {
        "days_threshold": 7,
        "field": "reminded_7day",
        "label": "【提醒】",
        "message_template": "距离截止还有 {days} 天"
    },
    "3day": {
        "days_threshold": 3,
        "field": "reminded_3day",
        "label": "【紧急提醒】",
        "message_template": "距离截止还有 {days} 天！"
    },
    "overdue": {
        "days_threshold": 0,
        "field": "reminded_overdue",
        "label": "【已逾期】",
        "message_template": "已逾期 {days} 天！"
    }
}


class ReminderService:
    """服务端提醒服务"""

    def __init__(self, check_interval: int = 3600):
        """
        初始化提醒服务

        Args:
            check_interval: 检查间隔（秒），默认1小时
        """
        self.check_interval = check_interval
        self._running = False
        self._thread = None
        self._callbacks = []

    def register_callback(self, callback):
        """注册回调函数"""
        self._callbacks.append(callback)

    def start(self):
        """启动提醒服务"""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        print("提醒服务已启动")

    def stop(self):
        """停止提醒服务"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        print("提醒服务已停止")

    def _run_loop(self):
        """运行循环"""
        while self._running:
            try:
                self._check_reminders()
            except Exception as e:
                print(f"提醒检查出错: {e}")

            # 等待下一次检查
            for _ in range(self.check_interval):
                if not self._running:
                    break
                time.sleep(1)

    def _check_reminders(self):
        """检查并发送提醒"""
        with get_db() as conn:
            try:
                reminders = self._get_pending_reminders(conn)

                for todo_id, remind_type, message, assignee, title in reminders:
                    self._mark_reminded(conn, todo_id, remind_type)

                    for callback in self._callbacks:
                        try:
                            callback({
                                'todo_id': todo_id,
                                'remind_type': remind_type,
                                'message': message,
                                'assignee': assignee,
                                'title': title
                            })
                        except Exception as e:
                            print(f"回调执行失败: {e}")

                    print(f"提醒已发送: [{remind_type}] {title} -> {assignee or '未分配'}")

            except Exception as e:
                print(f"提醒检查出错: {e}")

    def _get_pending_reminders(self, conn) -> List[Tuple]:
        """
        获取待发送的提醒

        Returns:
            List[(todo_id, remind_type, message, assignee, title)]
        """
        reminders = []
        now = datetime.now()

        # 查询需要提醒的任务
        query = """
            SELECT id, title, assignee, deadline, reminded_7day, reminded_3day, reminded_overdue
            FROM todos
            WHERE deadline IS NOT NULL
            AND status NOT IN ('已完成', '已取消')
        """
        cursor = conn.execute(query)

        for row in cursor.fetchall():
            todo_id, title, assignee, deadline_str, reminded_7day, reminded_3day, reminded_overdue = row

            try:
                deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
            except ValueError:
                continue

            days_until = (deadline - now).days

            # 检查各种提醒类型
            remind_flags = {
                '7day': bool(reminded_7day),
                '3day': bool(reminded_3day),
                'overdue': bool(reminded_overdue)
            }

            for remind_type, config in REMINDER_CONFIGS.items():
                already_reminded = remind_flags.get(remind_type, False)

                # 判断是否需要提醒
                should_remind = False
                if remind_type == "overdue":
                    should_remind = days_until < 0 and not already_reminded
                elif remind_type == "3day":
                    should_remind = 0 <= days_until <= 3 and not already_reminded
                elif remind_type == "7day":
                    should_remind = 0 < days_until <= 7 and not already_reminded

                if should_remind:
                    days = abs(days_until)
                    message = f"{config['label']} {title}: {config['message_template'].format(days=days)}"
                    reminders.append((todo_id, remind_type, message, assignee, title))

        return reminders

    def _mark_reminded(self, conn, todo_id: str, remind_type: str):
        """标记已提醒"""
        field_name = REMINDER_CONFIGS[remind_type]['field']
        update_query = f"UPDATE todos SET {field_name} = 1 WHERE id = ?"
        conn.execute(update_query, (todo_id,))

    def force_check(self):
        """强制立即检查一次"""
        threading.Thread(target=self._check_reminders, daemon=True).start()


# 全局提醒服务实例
_reminder_service = None


def get_reminder_service(check_interval: int = 3600) -> ReminderService:
    """
    获取全局提醒服务实例

    Args:
        check_interval: 检查间隔（秒），默认1小时

    Returns:
        ReminderService实例
    """
    global _reminder_service
    if _reminder_service is None:
        _reminder_service = ReminderService(check_interval)
    return _reminder_service
