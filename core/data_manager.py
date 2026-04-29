#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据管理模块
"""

import json
import os
from typing import List, Optional
from pathlib import Path
from core.models import TodoItem


class DataManager:
    """数据管理器"""
    
    def __init__(self):
        # 数据存储在用户目录下
        self.data_dir = Path.home() / ".todo_reminder"
        self.data_file = self.data_dir / "todos.json"
        self.config_file = self.data_dir / "config.json"
        self._ensure_data_dir()
        self._todos: List[TodoItem] = []
        self._config: dict = {}
        self.load()
    
    def _ensure_data_dir(self):
        """确保数据目录存在"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def load(self):
        """加载数据"""
        # 加载待办事项
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._todos = [TodoItem.from_dict(item) for item in data]
            except Exception as e:
                print(f"加载数据失败: {e}")
                self._todos = []
        
        # 加载配置
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            except:
                self._config = self._default_config()
        else:
            self._config = self._default_config()
    
    def _default_config(self) -> dict:
        """默认配置"""
        return {
            "window_x": 100,
            "window_y": 100,
            "window_width": 700,
            "window_height": 500,
            "opacity": 0.95,
            "always_on_top": False,
            "auto_start": False,
            "reminder_enabled": True,
            "reminder_interval": 60  # 检查间隔(秒)
        }
    
    def save(self):
        """保存数据"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump([item.to_dict() for item in self._todos], f, 
                         ensure_ascii=False, indent=2)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存数据失败: {e}")
    
    def get_all_todos(self) -> List[TodoItem]:
        """获取所有待办事项"""
        return self._todos.copy()
    
    def get_active_todos(self) -> List[TodoItem]:
        """获取未完成的待办事项"""
        from core.models import Status
        return [t for t in self._todos if t.status not in 
                [Status.COMPLETED.value, Status.CANCELLED.value]]
    
    def add_todo(self, todo: TodoItem) -> bool:
        """添加待办事项"""
        self._todos.append(todo)
        self.save()
        return True
    
    def update_todo(self, todo_id: str, **kwargs) -> bool:
        """更新待办事项"""
        for todo in self._todos:
            if todo.id == todo_id:
                for key, value in kwargs.items():
                    if hasattr(todo, key):
                        setattr(todo, key, value)
                self.save()
                return True
        return False
    
    def delete_todo(self, todo_id: str) -> bool:
        """删除待办事项"""
        for i, todo in enumerate(self._todos):
            if todo.id == todo_id:
                del self._todos[i]
                self.save()
                return True
        return False
    
    def get_todo_by_id(self, todo_id: str) -> Optional[TodoItem]:
        """根据ID获取待办事项"""
        for todo in self._todos:
            if todo.id == todo_id:
                return todo
        return None
    
    def get_config(self, key: str, default=None):
        """获取配置"""
        return self._config.get(key, default)
    
    def set_config(self, key: str, value):
        """设置配置"""
        self._config[key] = value
        self.save()
    
    def mark_reminded(self, todo_id: str, remind_type: str):
        """标记已提醒"""
        todo = self.get_todo_by_id(todo_id)
        if todo:
            if remind_type == "7day":
                todo.reminded_7day = True
            elif remind_type == "3day":
                todo.reminded_3day = True
            elif remind_type == "overdue":
                todo.reminded_overdue = True
            self.save()