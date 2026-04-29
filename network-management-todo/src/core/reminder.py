#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
提醒服务模块
"""

import threading
from typing import Callable, List, Tuple, Dict
from datetime import datetime
from core.data_manager import DataManager
from core.models import TodoItem, Status

# 提醒类型到标签和描述模板的映射
REMIND_TEMPLATES = {
    "overdue": ("【已逾期】", "已逾期 {days} 天！"),
    "3day": ("【紧急提醒】", "距离截止还有 {days} 天！"),
    "7day": ("【提醒】", "距离截止还有 {days} 天"),
}

# remind_type 到 TodoItem 属性名的映射
REMIND_FIELDS = {
    "7day": "reminded_7day",
    "3day": "reminded_3day",
    "overdue": "reminded_overdue",
}


class ReminderService:

    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self._running = False
        self._timer = None
        self._callbacks: List[Callable] = []
        self._last_reminder_time: Dict[str, datetime] = {}
        self._restart_callback = None

    def register_callback(self, callback: Callable):
        self._callbacks.append(callback)

    def start(self):
        self._running = True
        self._schedule_next_check()

    def stop(self):
        self._running = False
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def restart(self, root=None):
        """重启提醒服务（非阻塞）"""
        self.stop()
        if root:
            self._restart_callback = root.after(100, self.start)
        else:
            import time
            time.sleep(0.1)
            self.start()

    def _schedule_next_check(self):
        if not self._running:
            return
        interval = self.data_manager.get_config("reminder_interval", 60)
        self._timer = threading.Timer(interval, self._check_and_schedule)
        self._timer.daemon = True
        self._timer.start()

    def _check_and_schedule(self):
        if not self._running:
            return
        self._do_check()
        self._schedule_next_check()

    def _do_check(self):
        if not self.data_manager.get_config("reminder_enabled", True):
            return
        reminders = self._get_pending_reminders()
        for todo, remind_type, message in reminders:
            self._trigger_reminder(todo, remind_type, message)

    def _should_remind(self, todo_id: str, remind_type: str,
                       already_reminded: bool, repeat_reminder: bool,
                       repeat_interval: float, now: datetime) -> bool:
        """判断是否需要发送提醒"""
        if not already_reminded:
            return True
        if not repeat_reminder:
            return False
        key = f"{todo_id}_{remind_type}"
        last_time = self._last_reminder_time.get(key)
        if last_time is None:
            return True
        return (now - last_time).total_seconds() >= repeat_interval

    def _build_message(self, todo: TodoItem, remind_type: str, days: int) -> str:
        """构建提醒消息"""
        label, detail_tpl = REMIND_TEMPLATES[remind_type]
        assignee = todo.assignee or '未指定'
        abs_days = abs(days) if remind_type == "overdue" else days
        return f"{label}{todo.title}\n负责人: {assignee}\n{detail_tpl.format(days=abs_days)}"

    def _get_pending_reminders(self) -> List[Tuple[TodoItem, str, str]]:
        reminders = []
        todos = self.data_manager.get_active_todos()

        remind_7day_enabled = self.data_manager.get_config("remind_7day_enabled", True)
        remind_3day_enabled = self.data_manager.get_config("remind_3day_enabled", True)
        remind_overdue_enabled = self.data_manager.get_config("remind_overdue_enabled", True)
        repeat_reminder = self.data_manager.get_config("repeat_reminder", False)
        repeat_interval = self.data_manager.get_config("repeat_interval", 30) * 60

        now = datetime.now()

        # 清理已不存在的提醒记录
        active_ids = {t.id for t in todos}
        self._last_reminder_time = {
            k: v for k, v in self._last_reminder_time.items()
            if k.split("_")[0] in active_ids
        }

        # 定义检查规则：(阈值范围, remind_type, 是否启用配置键)
        rules = [
            (lambda d: d < 0, "overdue", remind_overdue_enabled, "reminded_overdue"),
            (lambda d: 0 <= d <= 3, "3day", remind_3day_enabled, "reminded_3day"),
            (lambda d: 3 < d <= 7, "7day", remind_7day_enabled, "reminded_7day"),
        ]

        for todo in todos:
            days = todo.days_until_deadline()
            if days is None:
                continue

            for check_fn, remind_type, enabled, reminded_field in rules:
                if not enabled:
                    continue
                if not check_fn(days):
                    continue
                already = getattr(todo, reminded_field, False)
                if self._should_remind(todo.id, remind_type, already,
                                       repeat_reminder, repeat_interval, now):
                    reminders.append((todo, remind_type,
                                      self._build_message(todo, remind_type, days)))
                break  # 每条待办只匹配最高优先级的规则

        return reminders

    def _trigger_reminder(self, todo: TodoItem, remind_type: str, message: str):
        self.data_manager.mark_reminded(todo.id, remind_type)
        key = f"{todo.id}_{remind_type}"
        self._last_reminder_time[key] = datetime.now()
        for callback in self._callbacks:
            try:
                callback(todo, remind_type, message)
            except Exception as e:
                print(f"提醒回调执行失败: {e}")

    def check_now(self) -> List[Tuple[TodoItem, str, str]]:
        return self._get_pending_reminders()

    def force_check(self):
        self._do_check()
