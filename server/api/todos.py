#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
任务CRUD API
实现待办事项的增删改查，含权限检查
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid
from api.auth import require_auth, require_admin
from database import get_db
from shared.models import TodoItem

todos_bp = Blueprint('todos', __name__)


@todos_bp.route('', methods=['GET'])
@require_auth
def get_todos():
    """获取任务列表（管理员看全部，成员看自己的）"""
    user = request.user
    role = user.get('role')
    username = user.get('username')

    with get_db() as conn:
        if role == 'admin':
            # 管理员可以看到所有任务
            todos = conn.execute("""
                SELECT id, title, assignee, created_by, deadline, description,
                       progress, progress_updated_at, priority, status,
                       created_at, reminded_7day, reminded_3day, reminded_overdue
                FROM todos
                ORDER BY
                    CASE status
                        WHEN '已完成' THEN 1
                        WHEN '已取消' THEN 2
                        ELSE 0
                    END,
                    deadline IS NULL, deadline,
                    priority DESC
            """).fetchall()
        else:
            # 成员只能看到自己创建的或分配给自己的
            todos = conn.execute("""
                SELECT id, title, assignee, created_by, deadline, description,
                       progress, progress_updated_at, priority, status,
                       created_at, reminded_7day, reminded_3day, reminded_overdue
                FROM todos
                WHERE created_by = ? OR assignee = ?
                ORDER BY
                    CASE status
                        WHEN '已完成' THEN 1
                        WHEN '已取消' THEN 2
                        ELSE 0
                    END,
                    deadline IS NULL, deadline,
                    priority DESC
            """, (username, username)).fetchall()

        result = [dict(todo) for todo in todos]
        return jsonify({
            'success': True,
            'data': result,
            'count': len(result)
        })


@todos_bp.route('/<todo_id>', methods=['GET'])
@require_auth
def get_todo(todo_id):
    """获取单个任务详情"""
    user = request.user
    role = user.get('role')
    username = user.get('username')

    with get_db() as conn:
        todo = conn.execute(
            "SELECT * FROM todos WHERE id = ?", (todo_id,)
        ).fetchone()

        if not todo:
            return jsonify({
                'success': False,
                'message': '任务不存在'
            }), 404

        # 权限检查
        if role != 'admin' and todo['created_by'] != username and todo['assignee'] != username:
            return jsonify({
                'success': False,
                'message': '无权访问此任务'
            }), 403

        return jsonify({
            'success': True,
            'data': dict(todo)
        })


@todos_bp.route('', methods=['POST'])
@require_auth
def create_todo():
    """创建任务"""
    data = request.get_json()
    user = request.user
    username = user.get('username')
    role = user.get('role')

    # 验证必填字段
    if not data.get('title'):
        return jsonify({
            'success': False,
            'message': '任务标题不能为空'
        }), 400

    # 生成任务ID（使用完整UUID避免碰撞）
    todo_id = str(uuid.uuid4())

    # 处理分配
    assignee = data.get('assignee')
    if role != 'admin' and assignee and assignee != username:
        return jsonify({
            'success': False,
            'message': '成员只能将任务分配给自己或不分配'
        }), 403

    # 如果管理员没有指定assignee，默认为创建者
    if not assignee:
        assignee = username

    # 当前时间
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db() as conn:
        try:
            conn.execute("""
                INSERT INTO todos (
                    id, title, assignee, created_by, deadline, description,
                    progress, progress_updated_at, priority, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                todo_id,
                data['title'],
                assignee,
                username,
                data.get('deadline'),
                data.get('description', ''),
                data.get('progress', ''),
                data.get('progress_updated_at') if data.get('progress') else now,
                data.get('priority', 2),
                data.get('status', '待处理'),
                now
            ))

            # 查询创建的任务
            todo = conn.execute(
                "SELECT * FROM todos WHERE id = ?", (todo_id,)
            ).fetchone()

            return jsonify({
                'success': True,
                'message': '任务创建成功',
                'data': dict(todo)
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'创建失败: {str(e)}'
            }), 500


@todos_bp.route('/<todo_id>', methods=['PUT'])
@require_auth
def update_todo(todo_id):
    """更新任务"""
    data = request.get_json()
    user = request.user
    role = user.get('role')
    username = user.get('username')

    with get_db() as conn:
        # 查询任务
        todo = conn.execute(
            "SELECT * FROM todos WHERE id = ?", (todo_id,)
        ).fetchone()

        if not todo:
            return jsonify({
                'success': False,
                'message': '任务不存在'
            }), 404

        # 权限检查
        if role != 'admin' and todo['created_by'] != username and todo['assignee'] != username:
            return jsonify({
                'success': False,
                'message': '无权修改此任务'
            }), 403

        # 成员只能修改自己创建的任务的状态和进度，或分配给自己的任务的状态和进度
        if role != 'admin':
            if todo['assignee'] == username:
                # 只能修改状态和进度
                allowed_fields = {'status', 'progress', 'progress_updated_at'}
                for key in data.keys():
                    if key not in allowed_fields:
                        return jsonify({
                            'success': False,
                            'message': f'成员只能修改任务状态和进度，不能修改{key}'
                        }), 403

        # 构建更新SQL
        update_fields = []
        update_values = []

        for key, value in data.items():
            if key in ['title', 'assignee', 'deadline', 'description', 'progress', 'priority', 'status']:
                update_fields.append(f"{key} = ?")
                update_values.append(value)
            elif key == 'progress_updated_at' and value:
                update_fields.append("progress_updated_at = ?")
                update_values.append(value)

        if not update_fields:
            return jsonify({
                'success': False,
                'message': '没有要更新的字段'
            }), 400

        update_values.append(todo_id)

        sql = f"UPDATE todos SET {', '.join(update_fields)} WHERE id = ?"

        try:
            conn.execute(sql, update_values)

            # 查询更新后的任务
            updated_todo = conn.execute(
                "SELECT * FROM todos WHERE id = ?", (todo_id,)
            ).fetchone()

            return jsonify({
                'success': True,
                'message': '任务更新成功',
                'data': dict(updated_todo)
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'更新失败: {str(e)}'
            }), 500


@todos_bp.route('/<todo_id>', methods=['DELETE'])
@require_auth
def delete_todo(todo_id):
    """删除任务（需要管理员密码）"""
    user = request.user
    data = request.get_json() or {}
    admin_password = data.get('admin_password')

    if not admin_password:
        return jsonify({'success': False, 'message': '需要管理员密码才能删除任务'}), 403

    # 验证管理员密码
    from api.auth import hash_password
    with get_db() as conn:
        admin = conn.execute(
            "SELECT password_hash FROM users WHERE role = 'admin' LIMIT 1"
        ).fetchone()

        if not admin or admin['password_hash'] != hash_password(admin_password):
            return jsonify({'success': False, 'message': '管理员密码错误'}), 401

    with get_db() as conn:
        todo = conn.execute(
            "SELECT * FROM todos WHERE id = ?", (todo_id,)
        ).fetchone()

        if not todo:
            return jsonify({'success': False, 'message': '任务不存在'}), 404

        # 仅管理员可删除
        if user.get('role') != 'admin':
            return jsonify({'success': False, 'message': '只有管理员可以删除任务'}), 403

        try:
            conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
            return jsonify({'success': True, 'message': '任务删除成功'})
        except Exception as e:
            return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500


@todos_bp.route('/batch', methods=['POST'])
@require_auth
def batch_update():
    """批量更新任务状态"""
    data = request.get_json()
    todo_ids = data.get('todo_ids', [])
    status = data.get('status')

    if not todo_ids:
        return jsonify({
            'success': False,
            'message': '请指定要更新的任务'
        }), 400

    if not status:
        return jsonify({
            'success': False,
            'message': '请指定目标状态'
        }), 400

    user = request.user
    role = user.get('role')
    username = user.get('username')

    with get_db() as conn:
        updated = []
        failed = []

        for todo_id in todo_ids:
            # 查询任务
            todo = conn.execute(
                "SELECT * FROM todos WHERE id = ?", (todo_id,)
            ).fetchone()

            if not todo:
                failed.append({'id': todo_id, 'reason': '任务不存在'})
                continue

            # 权限检查
            if role != 'admin' and todo['created_by'] != username and todo['assignee'] != username:
                failed.append({'id': todo_id, 'reason': '无权修改'})
                continue

            try:
                conn.execute(
                    "UPDATE todos SET status = ? WHERE id = ?",
                    (status, todo_id)
                )
                updated.append(todo_id)
            except Exception as e:
                failed.append({'id': todo_id, 'reason': str(e)})

        return jsonify({
            'success': True,
            'message': f'批量更新完成：成功{len(updated)}个，失败{len(failed)}个',
            'data': {
                'updated': updated,
                'failed': failed
            }
        })


@todos_bp.route('/reminders/pending', methods=['GET'])
@require_auth
def get_pending_reminders():
    """获取当前用户的待提醒任务"""
    user = request.user
    role = user.get('role')
    username = user.get('username')

    with get_db() as conn:
        # 获取需要提醒的任务（根据角色过滤）
        if role == 'admin':
            # 管理员可以看到所有待提醒任务
            query = """
                SELECT id, title, assignee, deadline, status, priority,
                       reminded_7day, reminded_3day, reminded_overdue
                FROM todos
                WHERE deadline IS NOT NULL
                AND status NOT IN ('已完成', '已取消')
                ORDER BY deadline
            """
            todos = conn.execute(query).fetchall()
        else:
            # 成员只能看到分配给自己的或自己创建的待提醒任务
            query = """
                SELECT id, title, assignee, deadline, status, priority,
                       reminded_7day, reminded_3day, reminded_overdue
                FROM todos
                WHERE deadline IS NOT NULL
                AND status NOT IN ('已完成', '已取消')
                AND (assignee = ? OR created_by = ?)
                ORDER BY deadline
            """
            todos = conn.execute(query, (username, username)).fetchall()

        # 计算需要提醒的任务
        now = datetime.now()
        pending = []

        for todo in todos:
            try:
                deadline = datetime.strptime(todo['deadline'], '%Y-%m-%d')
            except ValueError:
                continue

            days_until = (deadline - now).days

            # 检查各种提醒类型
            remind_types = []
            if days_until < 0 and not todo['reminded_overdue']:
                remind_types.append({
                    'type': 'overdue',
                    'label': '【已逾期】',
                    'message': f"已逾期 {abs(days_until)} 天！"
                })
            if 0 <= days_until <= 3 and not todo['reminded_3day']:
                remind_types.append({
                    'type': '3day',
                    'label': '【紧急提醒】',
                    'message': f"距离截止还有 {days_until} 天！"
                })
            if 0 < days_until <= 7 and not todo['reminded_7day']:
                remind_types.append({
                    'type': '7day',
                    'label': '【提醒】',
                    'message': f"距离截止还有 {days_until} 天"
                })

            for remind_info in remind_types:
                pending.append({
                    'todo_id': todo['id'],
                    'title': todo['title'],
                    'assignee': todo['assignee'] or '未分配',
                    'deadline': todo['deadline'],
                    'remind_type': remind_info['type'],
                    'label': remind_info['label'],
                    'message': f"{remind_info['label']} {todo['title']}: {remind_info['message']}",
                    'priority': todo['priority']
                })

        return jsonify({
            'success': True,
            'data': pending,
            'count': len(pending)
        })


@todos_bp.route('/reminders/<todo_id>/<remind_type>/acknowledge', methods=['POST'])
@require_auth
def acknowledge_reminder(todo_id, remind_type):
    """确认已收到提醒（标记提醒状态）"""
    user = request.user
    role = user.get('role')
    username = user.get('username')

    with get_db() as conn:
        # 查询任务
        todo = conn.execute(
            "SELECT * FROM todos WHERE id = ?", (todo_id,)
        ).fetchone()

        if not todo:
            return jsonify({
                'success': False,
                'message': '任务不存在'
            }), 404

        # 权限检查
        if role != 'admin' and todo['assignee'] != username and todo['created_by'] != username:
            return jsonify({
                'success': False,
                'message': '无权操作'
            }), 403

        # 更新提醒标志
        field_map = {
            '7day': 'reminded_7day',
            '3day': 'reminded_3day',
            'overdue': 'reminded_overdue'
        }

        if remind_type not in field_map:
            return jsonify({
                'success': False,
                'message': '无效的提醒类型'
            }), 400

        field = field_map[remind_type]
        conn.execute(f"UPDATE todos SET {field} = 1 WHERE id = ?", (todo_id,))

        return jsonify({
            'success': True,
            'message': '提醒已确认'
        })
