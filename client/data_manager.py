#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
客户端数据管理器
使用API客户端与服务器通信，替代本地文件操作
"""

from typing import List, Optional, Dict
from datetime import datetime
import json
import os
from client.api_client import get_api_client
from client.cache import (
    get_todos_cache, set_todos_cache, is_cache_valid,
    set_config, get_config, invalidate_cache
)
from shared.models import TodoItem, Priority, Status


class ClientDataManager:
    """客户端数据管理器"""

    def __init__(self):
        """初始化客户端数据管理器"""
        self.api_client = get_api_client()
        self._current_user = None
        self._is_connected = False

    def set_server(self, server_url: str):
        """设置服务器地址"""
        self.api_client.set_server(server_url)

    def connect(self) -> dict:
        """
        通过IP自动连接

        Returns:
            {'success': bool, 'needs_password': bool, 'user': dict}
        """
        result = self.api_client.connect()
        if result.get('success') and result.get('token'):
            self._current_user = result['user']
            self._is_connected = True
            invalidate_cache()
        return result

    def login(self, password: str) -> bool:
        """管理员密码登录"""
        result = self.api_client.login(password)
        if result.get('success'):
            self._current_user = result['user']
            self._is_connected = True
            invalidate_cache()
            return True
        return False

    def verify_admin_password(self, password: str) -> bool:
        """验证管理员密码"""
        return self.api_client.verify_admin_password(password)

    def logout(self):
        """登出"""
        self.api_client.logout()
        self._current_user = None
        self._is_connected = False
        invalidate_cache()

    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._is_connected and self.api_client.is_authenticated()

    def get_current_user(self) -> Optional[Dict]:
        """获取当前用户信息"""
        return self._current_user

    def get_all_todos(self) -> List[TodoItem]:
        """获取所有任务（带缓存）"""
        # 检查缓存
        if is_cache_valid('todos', max_age_minutes=1):
            cached = get_todos_cache()
            if cached:
                return [TodoItem.from_dict(item) for item in cached]

        # 从服务器获取
        result = self.api_client.get_todos()
        if result.get('success'):
            todos_data = result.get('data', [])
            # 更新缓存
            set_todos_cache(todos_data)
            return [TodoItem.from_dict(item) for item in todos_data]

        return []

    def get_active_todos(self) -> List[TodoItem]:
        """获取未完成的待办事项"""
        all_todos = self.get_all_todos()
        return [
            t for t in all_todos
            if t.status not in [Status.COMPLETED.value, Status.CANCELLED.value]
        ]

    def add_todo(self, todo: TodoItem) -> bool:
        """添加待办事项"""
        if not self.is_connected():
            return False

        todo_dict = todo.to_dict()
        result = self.api_client.create_todo(todo_dict)

        if result.get('success'):
            # 清除缓存
            invalidate_cache('todos')
            return True
        return False

    def update_todo(self, todo_id: str, **kwargs) -> bool:
        """更新待办事项"""
        if not self.is_connected():
            return False

        # 权限检查由服务端处理
        result = self.api_client.update_todo(todo_id, kwargs)

        if result.get('success'):
            # 清除缓存
            invalidate_cache('todos')
            return True
        return False

    def delete_todo(self, todo_id: str, admin_password: str = None) -> bool:
        """删除待办事项（需要管理员密码）"""
        if not self.is_connected():
            return False

        result = self.api_client.delete_todo(todo_id, admin_password=admin_password)

        if result.get('success'):
            invalidate_cache('todos')
            return True
        return False

    def get_todo_by_id(self, todo_id: str) -> Optional[TodoItem]:
        """根据ID获取待办事项"""
        if not self.is_connected():
            return None

        result = self.api_client.get_todo(todo_id)

        if result.get('success'):
            return TodoItem.from_dict(result['data'])
        return None

    def get_config(self, key: str, default=None):
        """获取配置"""
        return get_config(key, default)

    def set_config(self, key: str, value):
        """设置配置"""
        set_config(key, str(value))

    def mark_reminded(self, todo_id: str, remind_type: str):
        """标记已提醒"""
        # 需要更新对应的提醒标志
        todo = self.get_todo_by_id(todo_id)
        if todo:
            update_data = {}
            if remind_type == "7day":
                update_data['reminded_7day'] = True
            elif remind_type == "3day":
                update_data['reminded_3day'] = True
            elif remind_type == "overdue":
                update_data['reminded_overdue'] = True

            if update_data:
                return self.update_todo(todo_id, **update_data)
        return False

    def batch_update_status(self, todo_ids: List[str], status: str) -> bool:
        """批量更新任务状态"""
        if not self.is_connected():
            return False

        result = self.api_client.batch_update_todos(todo_ids, status)

        if result.get('success'):
            # 清除缓存
            invalidate_cache('todos')
            return True
        return False

    # ============ 用户管理（仅管理员）=============

    def get_users(self) -> List[Dict]:
        """获取用户列表（仅管理员）"""
        if not self.is_connected():
            return []

        result = self.api_client.get_users()
        if result.get('success'):
            return result.get('data', [])
        return []

    def create_user(self, user_data: Dict) -> bool:
        """创建用户（仅管理员）"""
        if not self.is_connected():
            return False

        result = self.api_client.create_user(user_data)
        return result.get('success', False)

    def update_user(self, user_id: int, user_data: Dict) -> bool:
        """更新用户（仅管理员）"""
        if not self.is_connected():
            return False

        result = self.api_client.update_user(user_id, user_data)
        return result.get('success', False)

    def delete_user(self, user_id: int) -> bool:
        """删除用户（仅管理员）"""
        if not self.is_connected():
            return False

        result = self.api_client.delete_user(user_id)
        return result.get('success', False)
