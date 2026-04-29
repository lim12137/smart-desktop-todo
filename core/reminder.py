#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
提醒服务模块
"""

import threading
from typing import Callable, List, Tuple
from datetime import datetime
from core.data_manager import DataManager
from core.models import TodoItem, Status


class ReminderService:
    """提醒服务"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self._running = False
        self._timer = None
        self._callbacks: List[Callable] = []
    
    def register_callback(self, callback: Callable):
        """注册提醒回调"""
        self._callbacks.append(callback)
    
    def start(self):
        """启动提醒服务"""
        self._running = True
        self._check_reminders()
    
    def stop(self):
        """停止提醒服务"""
        self._running = False
        if self._timer:
            self._timer.cancel()
    
    def _check_reminders(self):
        """检查提醒"""
        if not self._running:
            return
            
        if self.data_manager.get_config("reminder_enabled", True):
            reminders = self._get_pending_reminders()
            for todo, remind_type, message in reminders:
                self._trigger_reminder(todo, remind_type, message)
            
        # 设置下次检查
        interval = self.data_manager.get_config("reminder_interval", 60)
        self._timer = threading.Timer(interval, self._check_reminders)
        self._timer.daemon = True
        self._timer.start()
    
    def _get_pending_reminders(self) -> List[Tuple[TodoItem, str, str]]:
        """获取待处理的提醒"""
        reminders = []
        todos = self.data_manager.get_active_todos()
        
        for todo in todos:
            days = todo.days_until_deadline()
            if days is None:
                continue
            
            # 已逾期
            if days < 0 and not todo.reminded_overdue:
                reminders.append((
                    todo, 
                    "overdue",
                    f"【已逾期】{todo.title}\n负责人: {todo.assignee}\n已逾期 {abs(days)} 天！"
                ))
            # 3天内到期
            elif 0 <= days <= 3 and not todo.reminded_3day:
                reminders.append((
                    todo,
                    "3day", 
                    f"【紧急提醒】{todo.title}\n负责人: {todo.assignee}\n距离截止还有 {days} 天！"
                ))
            # 7天内到期
            elif 3 < days <= 7 and not todo.reminded_7day:
                reminders.append((
                    todo,
                    "7day",
                    f"【提醒】{todo.title}\n负责人: {todo.assignee}\n距离截止还有 {days} 天"
                ))
        
        return reminders
    
    def _trigger_reminder(self, todo: TodoItem, remind_type: str, message: str):
        """触发提醒"""
        # 标记已提醒
        self.data_manager.mark_reminded(todo.id, remind_type)
        
        # 调用回调
        for callback in self._callbacks:
            try:
                callback(todo, remind_type, message)
            except Exception as e:
                print(f"提醒回调执行失败: {e}")
    
    def check_now(self) -> List[Tuple[TodoItem, str, str]]:
        """立即检查一次（不触发提醒，仅返回结果）"""
        return self._get_pending_reminders()