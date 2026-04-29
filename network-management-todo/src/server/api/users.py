#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
用户管理API
仅管理员可调用，用于管理成员账户
"""

import hashlib
from flask import Blueprint, request, jsonify
from api.auth import require_auth, require_admin, hash_password
from database import get_db

users_bp = Blueprint('users', __name__)


@users_bp.route('', methods=['GET'])
@require_admin
def get_users():
    """获取用户列表（仅管理员）"""
    with get_db() as conn:
        users = conn.execute("""
            SELECT id, username, display_name, role, ip_address, created_at
            FROM users
            ORDER BY created_at DESC
        """).fetchall()

        result = [dict(user) for user in users]
        return jsonify({
            'success': True,
            'data': result,
            'count': len(result)
        })


@users_bp.route('', methods=['POST'])
@require_admin
def create_user():
    """创建用户（仅管理员）"""
    data = request.get_json()

    # 验证必填字段
    required_fields = ['username', 'password', 'display_name', 'ip_address']
    for field in required_fields:
        if not data.get(field):
            return jsonify({
                'success': False,
                'message': f'{field} 不能为空'
            }), 400

    # 验证角色
    role = data.get('role', 'member')
    if role not in ['admin', 'member']:
        return jsonify({
            'success': False,
            'message': '角色必须是 admin 或 member'
        }), 400

    with get_db() as conn:
        # 检查用户名是否已存在
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (data['username'],)
        ).fetchone()

        if existing:
            return jsonify({
                'success': False,
                'message': '用户名已存在'
            }), 400

        # 检查IP是否已被使用
        existing_ip = conn.execute(
            "SELECT id FROM users WHERE ip_address = ?",
            (data['ip_address'],)
        ).fetchone()

        if existing_ip:
            return jsonify({
                'success': False,
                'message': f"IP地址 {data['ip_address']} 已被用户使用"
            }), 400

        # 创建用户
        password_hash = hash_password(data['password'])
        try:
            conn.execute("""
                INSERT INTO users (username, password_hash, display_name, role, ip_address)
                VALUES (?, ?, ?, ?, ?)
            """, (
                data['username'],
                password_hash,
                data['display_name'],
                role,
                data['ip_address']
            ))

            # 查询创建的用户
            user = conn.execute(
                "SELECT id, username, display_name, role, ip_address, created_at FROM users WHERE username = ?",
                (data['username'],)
            ).fetchone()

            return jsonify({
                'success': True,
                'message': '用户创建成功',
                'data': dict(user)
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'创建失败: {str(e)}'
            }), 500


@users_bp.route('/<int:user_id>', methods=['PUT'])
@require_admin
def update_user(user_id):
    """更新用户信息（仅管理员）"""
    data = request.get_json()

    with get_db() as conn:
        # 查询用户
        user = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()

        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404

        # 不能修改自己的角色为非管理员
        if user['id'] == request.user.get('user_id'):
            if data.get('role') and data.get('role') != 'admin':
                return jsonify({
                    'success': False,
                    'message': '不能将自己降级为普通成员'
                }), 400

        # 构建更新SQL
        update_fields = []
        update_values = []

        for key, value in data.items():
            if key in ['display_name', 'role', 'ip_address']:
                update_fields.append(f"{key} = ?")
                update_values.append(value)
            elif key == 'password':
                update_fields.append("password_hash = ?")
                update_values.append(hash_password(value))

        if not update_fields:
            return jsonify({
                'success': False,
                'message': '没有要更新的字段'
            }), 400

        # 如果修改IP，检查是否冲突
        if 'ip_address' in data:
            existing_ip = conn.execute(
                "SELECT id FROM users WHERE ip_address = ? AND id != ?",
                (data['ip_address'], user_id)
            ).fetchone()

            if existing_ip:
                return jsonify({
                    'success': False,
                    'message': f"IP地址 {data['ip_address']} 已被其他用户使用"
                }), 400

        update_values.append(user_id)

        try:
            sql = f"UPDATE users SET {', '.join(update_fields)} WHERE id = ?"
            conn.execute(sql, update_values)

            # 查询更新后的用户
            updated_user = conn.execute(
                "SELECT id, username, display_name, role, ip_address, created_at FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()

            return jsonify({
                'success': True,
                'message': '用户更新成功',
                'data': dict(updated_user)
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'更新失败: {str(e)}'
            }), 500


@users_bp.route('/<int:user_id>', methods=['DELETE'])
@require_admin
def delete_user(user_id):
    """删除用户（仅管理员）"""
    with get_db() as conn:
        # 查询用户
        user = conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ).fetchone()

        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404

        # 不能删除自己
        if user['id'] == request.user.get('user_id'):
            return jsonify({
                'success': False,
                'message': '不能删除自己的账户'
            }), 400

        # 检查是否有任务分配给该用户
        todos_count = conn.execute(
            "SELECT COUNT(*) as count FROM todos WHERE assignee = ? OR created_by = ?",
            (user['username'], user['username'])
        ).fetchone()['count']

        if todos_count > 0:
            return jsonify({
                'success': False,
                'message': f'该用户有 {todos_count} 个关联任务，无法删除'
            }), 400

        try:
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            return jsonify({
                'success': True,
                'message': '用户删除成功'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'删除失败: {str(e)}'
            }), 500


@users_bp.route('/check-ip', methods=['POST'])
@require_admin
def check_ip_available():
    """检查IP是否可用（仅管理员）"""
    data = request.get_json()
    ip_address = data.get('ip_address')

    if not ip_address:
        return jsonify({
            'success': False,
            'message': 'IP地址不能为空'
        }), 400

    with get_db() as conn:
        existing = conn.execute(
            "SELECT id, username, display_name FROM users WHERE ip_address = ?",
            (ip_address,)
        ).fetchone()

        if existing:
            return jsonify({
                'success': True,
                'available': False,
                'message': f"IP已被 {existing['display_name']} 使用",
                'user': dict(existing)
            })
        else:
            return jsonify({
                'success': True,
                'available': True,
                'message': 'IP地址可用'
            })
