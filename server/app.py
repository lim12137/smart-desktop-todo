#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flask服务器应用入口
待办事项提醒系统 - 服务端
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS
from datetime import timedelta

# 创建Flask应用
app = Flask(__name__)

# CORS配置 - 允许跨域请求
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# JWT配置
app.config['JWT_SECRET_KEY'] = 'todo-reminder-secret-key-2026'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['JWT_ALGORITHM'] = 'HS256'

# 注册路由
from api.auth import auth_bp
from api.todos import todos_bp
from api.users import users_bp

app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(todos_bp, url_prefix='/api/todos')
app.register_blueprint(users_bp, url_prefix='/api/users')

# 根路径健康检查
@app.route('/')
def index():
    return jsonify({
        'status': 'ok',
        'message': '待办事项提醒系统 - 服务端运行中',
        'version': '1.0.0'
    })

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy'})

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # 初始化数据库
    from database import init_db, DATABASE_PATH
    init_db()

    # 启动提醒服务
    from reminder_service import get_reminder_service
    reminder_service = get_reminder_service(check_interval=3600)  # 1小时检查一次
    reminder_service.start()

    # 启动服务器
    print("=" * 60)
    print("待办事项提醒系统 - 服务端启动")
    print("=" * 60)
    print(f"数据库: {DATABASE_PATH}")
    print("提醒服务: 已启动（1小时间隔）")
    print("API端点:")
    print("  - POST   /api/auth/login")
    print("  - GET    /api/auth/me")
    print("  - GET    /api/todos")
    print("  - POST   /api/todos")
    print("  - PUT    /api/todos/<id>")
    print("  - DELETE /api/todos/<id>")
    print("  - GET    /api/users")
    print("  - POST   /api/users")
    print("  - PUT    /api/users/<id>")
    print("  - DELETE /api/users/<id>")
    print("=" * 60)

    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    finally:
        # 停止提醒服务
        reminder_service.stop()
