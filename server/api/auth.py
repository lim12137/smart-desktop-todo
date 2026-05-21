#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
认证API
基于IP地址的用户识别，管理员密码登录
"""

import hashlib
import jwt
from functools import wraps
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from database import get_db, DATABASE_PATH

auth_bp = Blueprint('auth', __name__)

JWT_SECRET = 'todo-reminder-secret-key-2026-hmac-sha256-min32b!'
JWT_ALGORITHM = 'HS256'


def hash_password(password: str) -> str:
    """密码哈希（SHA256 + 固定盐）"""
    salt = "todo-reminder-salt-2026"
    return hashlib.sha256((salt + password).encode()).hexdigest()


def generate_token(user_id: int, username: str, role: str) -> str:
    """生成JWT Token"""
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> dict:
    """验证JWT Token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_client_ip() -> str:
    """获取客户端IP地址"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr


@auth_bp.route('/connect', methods=['POST'])
def connect():
    """客户端连接 - 通过IP自动识别身份"""
    client_ip = get_client_ip()
    data = request.get_json(silent=True) or {}
    reported_ip = data.get('ip_address', client_ip)

    with get_db() as conn:
        # 先按 IP 查找
        user = conn.execute(
            "SELECT * FROM users WHERE ip_address = ?",
            (client_ip,)
        ).fetchone()

        # IP 没匹配到，检查是否有管理员（管理员不绑定 IP）
        if not user:
            admin = conn.execute(
                "SELECT * FROM users WHERE role = 'admin' LIMIT 1"
            ).fetchone()
            if admin:
                return jsonify({
                    'success': True,
                    'needs_password': True,
                    'user': {
                        'id': admin['id'],
                        'username': admin['username'],
                        'display_name': admin['display_name'],
                        'role': admin['role']
                    }
                })

        if not user:
            return jsonify({
                'success': False,
                'message': f'未注册的客户端（IP: {client_ip}），请联系管理员添加',
                'code': 'UNREGISTERED'
            }), 403

        if user['role'] == 'admin':
            # 管理员需要密码登录
            return jsonify({
                'success': True,
                'needs_password': True,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'display_name': user['display_name'],
                    'role': user['role']
                }
            })
        else:
            # 成员直接通过，返回Token
            token = generate_token(user['id'], user['username'], user['role'])
            return jsonify({
                'success': True,
                'needs_password': False,
                'token': token,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'display_name': user['display_name'],
                    'role': user['role'],
                    'ip_address': user['ip_address']
                }
            })


@auth_bp.route('/login', methods=['POST'])
def login():
    """管理员密码登录"""
    data = request.get_json()
    password = data.get('password')

    if not password:
        return jsonify({'success': False, 'message': '请输入密码'}), 400

    with get_db() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE role = 'admin' LIMIT 1"
        ).fetchone()

        if not user:
            return jsonify({'success': False, 'message': '无管理员账户'}), 403

        if user['password_hash'] != hash_password(password):
            return jsonify({'success': False, 'message': '密码错误'}), 401

        token = generate_token(user['id'], user['username'], user['role'])
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'display_name': user['display_name'],
                'role': user['role']
            }
        })


@auth_bp.route('/verify-admin-password', methods=['POST'])
def verify_admin_password():
    """验证管理员密码（用于删除等敏感操作的二次确认）"""
    data = request.get_json()
    password = data.get('password')

    if not password:
        return jsonify({'success': False, 'message': '请输入密码'}), 400

    with get_db() as conn:
        admin = conn.execute(
            "SELECT * FROM users WHERE role = 'admin' LIMIT 1"
        ).fetchone()

        if not admin:
            return jsonify({'success': False, 'message': '无管理员账户'}), 500

        if admin['password_hash'] != hash_password(password):
            return jsonify({'success': False, 'message': '管理员密码错误'}), 401

        return jsonify({'success': True, 'message': '验证通过'})


@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """获取当前用户信息"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'success': False, 'message': '未提供认证Token'}), 401

    payload = verify_token(auth_header.split(' ')[1])
    if not payload:
        return jsonify({'success': False, 'message': 'Token无效或已过期'}), 401

    with get_db() as conn:
        user = conn.execute(
            "SELECT id, username, display_name, role, ip_address, created_at FROM users WHERE id = ?",
            (payload['user_id'],)
        ).fetchone()

        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404

        return jsonify({
            'success': True,
            'user': dict(user)
        })


@auth_bp.route('/ip-check', methods=['GET'])
def check_ip():
    """检查当前IP是否已注册"""
    client_ip = get_client_ip()

    with get_db() as conn:
        user = conn.execute(
            "SELECT id, username, display_name, role FROM users WHERE ip_address = ?",
            (client_ip,)
        ).fetchone()

        if user:
            return jsonify({
                'success': True,
                'registered': True,
                'needs_password': user['role'] == 'admin',
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'display_name': user['display_name'],
                    'role': user['role']
                }
            })
        else:
            return jsonify({
                'success': True,
                'registered': False,
                'message': f'此IP（{client_ip}）未注册，请联系管理员'
            })


def require_auth(f):
    """认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'message': '未提供认证Token'}), 401

        payload = verify_token(auth_header.split(' ')[1])
        if not payload:
            return jsonify({'success': False, 'message': 'Token无效或已过期'}), 401

        request.user = payload
        return f(*args, **kwargs)

    return decorated_function


def require_admin(f):
    """管理员权限装饰器"""
    @wraps(f)
    @require_auth
    def decorated_function(*args, **kwargs):
        if request.user.get('role') != 'admin':
            return jsonify({'success': False, 'message': '需要管理员权限'}), 403
        return f(*args, **kwargs)

    return decorated_function
