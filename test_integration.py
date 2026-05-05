#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
集成测试脚本
测试服务器和客户端的基本功能
"""

import sys
import os
import time
import requests
from datetime import datetime, timedelta
import io

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)


def test_server_health(base_url: str) -> bool:
    """测试服务器健康检查"""
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        return response.status_code == 200 and response.json().get('status') == 'healthy'
    except Exception as e:
        print(f"ERROR 服务器健康检查失败: {e}")
        return False


def test_admin_login(base_url: str, username: str, password: str) -> str:
    """测试管理员登录"""
    try:
        response = requests.post(f"{base_url}/api/auth/login", json={
            'username': username,
            'password': password
        }, timeout=5)

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                token = data.get('token') or data.get('data', {}).get('token')
                print("OK 登录成功")
                return token
            else:
                print(f"ERROR 登录失败: {data.get('message')}")
        else:
            print(f"ERROR 登录请求失败: {response.status_code}")
    except Exception as e:
        print(f"ERROR 登录异常: {e}")
    return None


def test_create_todo(base_url: str, token: str) -> str:
    """测试创建任务"""
    try:
        deadline = (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d')
        response = requests.post(f"{base_url}/api/todos",
            headers={'Authorization': f'Bearer {token}'},
            json={
                'title': '测试任务',
                'description': '这是一个集成测试任务',
                'deadline': deadline,
                'priority': 3,
                'status': '待处理'
            },
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                todo_id = data.get('data', {}).get('id')
                print(f"OK 创建任务成功: {todo_id}")
                return todo_id
            else:
                print(f"ERROR 创建任务失败: {data.get('message')}")
        else:
            print(f"ERROR 创建任务请求失败: {response.status_code}")
    except Exception as e:
        print(f"ERROR 创建任务异常: {e}")
    return None


def test_get_todos(base_url: str, token: str) -> bool:
    """测试获取任务列表"""
    try:
        response = requests.get(f"{base_url}/api/todos",
            headers={'Authorization': f'Bearer {token}'},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                todos = data.get('data', [])
                print(f"OK 获取任务列表成功: {len(todos)} 个任务")
                return True
            else:
                print(f"ERROR 获取任务列表失败: {data.get('message')}")
        else:
            print(f"ERROR 获取任务列表请求失败: {response.status_code}")
    except Exception as e:
        print(f"ERROR 获取任务列表异常: {e}")
    return False


def test_update_todo(base_url: str, token: str, todo_id: str) -> bool:
    """测试更新任务"""
    try:
        response = requests.put(f"{base_url}/api/todos/{todo_id}",
            headers={'Authorization': f'Bearer {token}'},
            json={
                'status': '进行中',
                'progress': '正在处理测试任务'
            },
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("OK 更新任务成功")
                return True
            else:
                print(f"ERROR 更新任务失败: {data.get('message')}")
        else:
            print(f"ERROR 更新任务请求失败: {response.status_code}")
    except Exception as e:
        print(f"ERROR 更新任务异常: {e}")
    return False


def test_delete_todo(base_url: str, token: str, todo_id: str) -> bool:
    """测试删除任务"""
    try:
        response = requests.delete(f"{base_url}/api/todos/{todo_id}",
            headers={'Authorization': f'Bearer {token}'},
            json={'admin_password': 'admin123'},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("OK 删除任务成功")
                return True
            else:
                print(f"ERROR 删除任务失败: {data.get('message')}")
        else:
            print(f"ERROR 删除任务请求失败: {response.status_code}")
    except Exception as e:
        print(f"ERROR 删除任务异常: {e}")
    return False


def test_get_users(base_url: str, token: str) -> bool:
    """测试获取用户列表（仅管理员）"""
    try:
        response = requests.get(f"{base_url}/api/users",
            headers={'Authorization': f'Bearer {token}'},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                users = data.get('data', [])
                print(f"OK 获取用户列表成功: {len(users)} 个用户")
                return True
            else:
                print(f"ERROR 获取用户列表失败: {data.get('message')}")
        else:
            print(f"ERROR 获取用户列表请求失败: {response.status_code}")
    except Exception as e:
        print(f"ERROR 获取用户列表异常: {e}")
    return False


def run_integration_tests(base_url: str = "http://localhost:5000"):
    """运行集成测试"""
    print("=" * 60)
    print("待办事项提醒系统 - 集成测试")
    print("=" * 60)
    print(f"服务器地址: {base_url}")
    print()

    # 测试服务器健康检查
    print("1. 测试服务器健康检查...")
    if not test_server_health(base_url):
        print("\nERROR 服务器未运行或无法访问，请先启动服务器")
        return False
    print()

    # 测试管理员登录
    print("2. 测试管理员登录...")
    token = test_admin_login(base_url, "admin", "admin123")
    if not token:
        print("\nERROR 登录失败，无法继续测试")
        return False
    print()

    # 测试获取用户列表
    print("3. 测试获取用户列表...")
    test_get_users(base_url, token)
    print()

    # 测试创建任务
    print("4. 测试创建任务...")
    todo_id = test_create_todo(base_url, token)
    if not todo_id:
        print("\n❌ 创建任务失败，跳过后续测试")
        return False
    print()

    # 测试获取任务列表
    print("5. 测试获取任务列表...")
    test_get_todos(base_url, token)
    print()

    # 测试更新任务
    print("6. 测试更新任务...")
    test_update_todo(base_url, token, todo_id)
    print()

    # 测试删除任务
    print("7. 测试删除任务...")
    test_delete_todo(base_url, token, todo_id)
    print()

    print("=" * 60)
    print("OK 集成测试完成")
    print("=" * 60)
    return True


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='待办事项提醒系统 - 集成测试')
    parser.add_argument('--server', default='http://localhost:5000',
                       help='服务器地址（默认: http://localhost:5000）')

    args = parser.parse_args()

    try:
        success = run_integration_tests(args.server)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n测试已中断")
        sys.exit(1)
