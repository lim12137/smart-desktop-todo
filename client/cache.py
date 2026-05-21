#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
本地缓存模块
客户端本地SQLite缓存，减少网络请求
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from contextlib import contextmanager

# 缓存数据库路径
CACHE_DB = os.path.join(os.path.expanduser('~'), '.todo_reminder_cache.db')


@contextmanager
def get_cache_db():
    """获取缓存数据库连接"""
    conn = sqlite3.connect(CACHE_DB)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_cache():
    """初始化缓存数据库"""
    with get_cache_db() as conn:
        # 创建todos缓存表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cached_todos (
                id TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建users缓存表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cached_users (
                id INTEGER PRIMARY KEY,
                data TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建配置表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cache_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)


def set_todos_cache(todos: List[Dict]):
    """缓存任务列表"""
    with get_cache_db() as conn:
        conn.execute("DELETE FROM cached_todos")
        for todo in todos:
            conn.execute(
                "INSERT INTO cached_todos (id, data) VALUES (?, ?)",
                (todo['id'], json.dumps(todo, ensure_ascii=False))
            )


def get_todos_cache() -> Optional[List[Dict]]:
    """获取缓存的任务列表"""
    with get_cache_db() as conn:
        rows = conn.execute("SELECT data FROM cached_todos ORDER BY updated_at DESC").fetchall()
        if rows:
            return [json.loads(row['data']) for row in rows]
    return None


def set_user_cache(user: Dict):
    """缓存用户信息"""
    with get_cache_db() as conn:
        conn.execute("DELETE FROM cached_users WHERE id = ?", (user['id'],))
        conn.execute(
            "INSERT INTO cached_users (id, data) VALUES (?, ?)",
            (user['id'], json.dumps(user, ensure_ascii=False))
        )


def get_users_cache() -> Optional[List[Dict]]:
    """获取缓存的用户列表"""
    with get_cache_db() as conn:
        rows = conn.execute("SELECT data FROM cached_users ORDER BY updated_at DESC").fetchall()
        if rows:
            return [json.loads(row['data']) for row in rows]
    return None


def get_user_cache(user_id: int) -> Optional[Dict]:
    """获取单个缓存的用户"""
    with get_cache_db() as conn:
        row = conn.execute(
            "SELECT data FROM cached_users WHERE id = ?", (user_id,)
        ).fetchone()
        if row:
            return json.loads(row['data'])
    return None


def invalidate_cache(cache_type: str = 'all'):
    """失效缓存"""
    with get_cache_db() as conn:
        if cache_type == 'all' or cache_type == 'todos':
            conn.execute("DELETE FROM cached_todos")
        if cache_type == 'all' or cache_type == 'users':
            conn.execute("DELETE FROM cached_users")


def set_config(key: str, value: str):
    """设置配置"""
    with get_cache_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO cache_config (key, value) VALUES (?, ?)",
            (key, value)
        )


def get_config(key: str, default: str = '') -> str:
    """获取配置"""
    with get_cache_db() as conn:
        row = conn.execute(
            "SELECT value FROM cache_config WHERE key = ?", (key,)
        ).fetchone()
        if row:
            return row['value']
    return default


def is_cache_valid(cache_type: str = 'todos', max_age_minutes: int = 5) -> bool:
    """
    检查缓存是否有效

    Args:
        cache_type: 缓存类型
        max_age_minutes: 最大缓存时间（分钟）

    Returns:
        缓存是否有效
    """
    with get_cache_db() as conn:
        if cache_type == 'todos':
            row = conn.execute(
                "SELECT updated_at FROM cached_todos ORDER BY updated_at DESC LIMIT 1"
            ).fetchone()
        elif cache_type == 'users':
            row = conn.execute(
                "SELECT updated_at FROM cached_users ORDER BY updated_at DESC LIMIT 1"
            ).fetchone()
        else:
            return False

        if not row:
            return False

        try:
            updated_at = datetime.strptime(row['updated_at'], "%Y-%m-%d %H:%M:%S")
            age = datetime.now() - updated_at
            return age.total_seconds() < max_age_minutes * 60
        except (ValueError, TypeError):
            return False


if __name__ == '__main__':
    # 测试缓存
    init_cache()

    # 测试设置和获取
    test_todos = [
        {'id': '1', 'title': '测试任务1'},
        {'id': '2', 'title': '测试任务2'}
    ]
    set_todos_cache(test_todos)
    cached = get_todos_cache()
    print(f"缓存测试: {cached}")
