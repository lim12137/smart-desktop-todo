#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API客户端模块
封装与服务端的HTTP通信
"""

import requests
from typing import Optional, Dict, List, Any
from datetime import datetime
import json


class APIClient:
    """API客户端"""

    def __init__(self, server_url: str = "http://localhost:5000"):
        """
        初始化API客户端

        Args:
            server_url: 服务器地址，如 http://192.168.x.x:5000
        """
        self.server_url = server_url.rstrip('/')
        self.token: Optional[str] = None
        self.user: Optional[Dict] = None
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })

    def set_server(self, server_url: str):
        """设置服务器地址"""
        self.server_url = server_url.rstrip('/')

    def set_token(self, token: str):
        """设置认证Token"""
        self.token = token
        self.session.headers.update({
            'Authorization': f'Bearer {token}'
        })

    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        GET请求

        Args:
            endpoint: API端点，如 /api/todos
            params: 查询参数

        Returns:
            响应数据
        """
        url = f"{self.server_url}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'message': f'请求失败: {str(e)}'
            }

    def post(self, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """
        POST请求

        Args:
            endpoint: API端点
            data: 请求数据

        Returns:
            响应数据
        """
        url = f"{self.server_url}{endpoint}"
        try:
            response = self.session.post(url, json=data, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'message': f'请求失败: {str(e)}'
            }

    def put(self, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """
        PUT请求

        Args:
            endpoint: API端点
            data: 请求数据

        Returns:
            响应数据
        """
        url = f"{self.server_url}{endpoint}"
        try:
            response = self.session.put(url, json=data, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'message': f'请求失败: {str(e)}'
            }

    def delete(self, endpoint: str) -> Dict:
        """
        DELETE请求

        Args:
            endpoint: API端点

        Returns:
            响应数据
        """
        url = f"{self.server_url}{endpoint}"
        try:
            response = self.session.delete(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'message': f'请求失败: {str(e)}'
            }

    # ============ 认证相关 ============

    def connect(self, ip_address: str = None) -> Dict:
        """通过IP自动连接（成员无需密码）"""
        data = {}
        if ip_address:
            data['ip_address'] = ip_address
        response = self.post('/api/auth/connect', data)
        if response.get('success') and response.get('token'):
            self.set_token(response['token'])
            self.user = response.get('user')
        return response

    def login(self, password: str) -> Dict:
        """管理员密码登录"""
        response = self.post('/api/auth/login', {'password': password})
        if response.get('success'):
            self.set_token(response['token'])
            self.user = response['user']
        return response

    def verify_admin_password(self, password: str) -> bool:
        """验证管理员密码（用于删除等敏感操作）"""
        result = self.post('/api/auth/verify-admin-password', {'password': password})
        return result.get('success', False)

    def check_ip(self, ip_address: str) -> Dict:
        """
        检查IP是否可登录

        Args:
            ip_address: IP地址

        Returns:
            IP检查结果
        """
        return self.get('/api/auth/ip-check', params={'ip_address': ip_address})

    def get_current_user(self) -> Dict:
        """获取当前用户信息"""
        response = self.get('/api/auth/me')
        if response.get('success'):
            self.user = response['user']
        return response

    def is_authenticated(self) -> bool:
        """检查是否已认证"""
        return self.token is not None

    def logout(self):
        """登出"""
        self.token = None
        self.user = None
        self.session.headers.pop('Authorization', None)

    # ============ 任务相关 ============

    def get_todos(self) -> Dict:
        """获取任务列表"""
        return self.get('/api/todos')

    def get_todo(self, todo_id: str) -> Dict:
        """获取单个任务"""
        return self.get(f'/api/todos/{todo_id}')

    def create_todo(self, todo_data: Dict) -> Dict:
        """创建任务"""
        return self.post('/api/todos', todo_data)

    def update_todo(self, todo_id: str, todo_data: Dict) -> Dict:
        """更新任务"""
        return self.put(f'/api/todos/{todo_id}', todo_data)

    def delete_todo(self, todo_id: str, admin_password: str = None) -> Dict:
        """删除任务（需要管理员密码）"""
        data = {}
        if admin_password:
            data['admin_password'] = admin_password
        url = f'{self.server_url}/api/todos/{todo_id}'
        try:
            response = self.session.delete(url, json=data, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'success': False, 'message': f'请求失败: {str(e)}'}

    def batch_update_todos(self, todo_ids: List[str], status: str) -> Dict:
        """批量更新任务状态"""
        return self.post('/api/todos/batch', {
            'todo_ids': todo_ids,
            'status': status
        })

    # ============ 用户管理（仅管理员）=============

    def get_users(self) -> Dict:
        """获取用户列表"""
        return self.get('/api/users')

    def create_user(self, user_data: Dict) -> Dict:
        """创建用户"""
        return self.post('/api/users', user_data)

    def update_user(self, user_id: int, user_data: Dict) -> Dict:
        """更新用户"""
        return self.put(f'/api/users/{user_id}', user_data)

    def delete_user(self, user_id: int) -> Dict:
        """删除用户"""
        return self.delete(f'/api/users/{user_id}')

    def check_ip_available(self, ip_address: str) -> Dict:
        """检查IP是否可用（管理员）"""
        return self.post('/api/users/check-ip', {'ip_address': ip_address})

    # ============ 提醒相关 ============

    def get_pending_reminders(self) -> Dict:
        """获取待提醒任务列表"""
        return self.get('/api/todos/reminders/pending')

    def acknowledge_reminder(self, todo_id: str, remind_type: str) -> Dict:
        """确认已收到提醒"""
        return self.post(f'/api/todos/reminders/{todo_id}/{remind_type}/acknowledge', {})

    # ============ 健康检查 ============

    def health_check(self) -> bool:
        """检查服务器连接"""
        try:
            response = self.get('/api/health')
            return response.get('status') == 'healthy'
        except Exception:
            return False


# 全局API客户端实例（单例模式）
_api_client: Optional[APIClient] = None


def get_api_client() -> APIClient:
    """获取全局API客户端实例"""
    global _api_client
    if _api_client is None:
        # 尝试从本地配置读取服务器地址
        import os
        config_file = os.path.join(os.path.expanduser('~'), '.todo_reminder_client')
        server_url = "http://localhost:5000"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    server_url = config.get('server_url', server_url)
            except (json.JSONDecodeError, IOError):
                pass

        _api_client = APIClient(server_url)
    return _api_client


def reset_api_client():
    """重置全局API客户端"""
    global _api_client
    _api_client = None
