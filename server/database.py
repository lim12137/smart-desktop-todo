#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库模块
处理SQLite数据库连接、表创建和数据操作
"""

import sqlite3
import os
from datetime import datetime
from contextlib import contextmanager
import json

# 数据库路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(BASE_DIR, 'server', 'data', 'todo_reminder.db')

# 确保数据目录存在
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)


@contextmanager
def get_db():
    """获取数据库连接的上下文管理器"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """初始化数据库，创建所有表"""
    print(f"初始化数据库: {DATABASE_PATH}")

    with get_db() as conn:
        # 创建users表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                display_name TEXT NOT NULL,
                role TEXT NOT NULL,
                ip_address TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建todos表（扩展版）
        conn.execute("""
            CREATE TABLE IF NOT EXISTS todos (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                assignee TEXT,
                created_by TEXT NOT NULL,
                deadline DATE,
                description TEXT DEFAULT '',
                progress TEXT DEFAULT '',
                progress_updated_at TIMESTAMP,
                priority INTEGER DEFAULT 2,
                status TEXT DEFAULT '待处理',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reminded_7day BOOLEAN DEFAULT 0,
                reminded_3day BOOLEAN DEFAULT 0,
                reminded_overdue BOOLEAN DEFAULT 0,
                FOREIGN KEY (assignee) REFERENCES users(username),
                FOREIGN KEY (created_by) REFERENCES users(username)
            )
        """)

        # 创建索引
        conn.execute("CREATE INDEX IF NOT EXISTS idx_todos_assignee ON todos(assignee)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_todos_created_by ON todos(created_by)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_todos_status ON todos(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_todos_deadline ON todos(deadline)")

    # 创建默认管理员用户
    create_default_admin()


def create_default_admin():
    """创建默认管理员账户"""
    from api.auth import hash_password

    default_admin_ip = "127.0.0.1"
    default_admin = {
        'username': 'admin',
        'password': 'admin123',
        'display_name': '系统管理员',
        'role': 'admin',
        'ip_address': default_admin_ip
    }

    with get_db() as conn:
        existing = conn.execute(
            "SELECT * FROM users WHERE role = 'admin' LIMIT 1"
        ).fetchone()

        if not existing:
            password_hash = hash_password(default_admin['password'])
            conn.execute("""
                INSERT INTO users (username, password_hash, display_name, role, ip_address)
                VALUES (?, ?, ?, ?, ?)
            """, (
                default_admin['username'],
                password_hash,
                default_admin['display_name'],
                default_admin['role'],
                default_admin['ip_address']
            ))
            print(f"[OK] 创建默认管理员: username={default_admin['username']}, ip={default_admin_ip}")
        else:
            print("[OK] 管理员账户已存在")


def dict_factory(cursor, row):
    """将数据库行转换为字典"""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def get_connection():
    """获取数据库连接（用于非上下文管理器场景）"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = dict_factory
    return conn


if __name__ == '__main__':
    # 测试数据库初始化
    init_db()

    # 查询数据
    with get_db() as conn:
        print("\n=== 用户列表 ===")
        users = conn.execute("SELECT * FROM users").fetchall()
        for user in users:
            print(f"  {dict(user)}")

        print("\n=== 任务列表 ===")
        todos = conn.execute("SELECT * FROM todos").fetchall()
        for todo in todos:
            print(f"  {dict(todo)}")
