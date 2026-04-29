#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
共享数据模型
客户端和服务端都使用的通用数据结构
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class Role(Enum):
    """用户角色"""
    ADMIN = "admin"
    MEMBER = "member"


class Priority(Enum):
    """优先级"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class Status(Enum):
    """任务状态"""
    PENDING = "待处理"
    IN_PROGRESS = "进行中"
    COMPLETED = "已完成"
    CANCELLED = "已取消"


class ProgressCategory(Enum):
    """进度分类"""
    VERY_RECENT = "< 1天"
    RECENT = "< 7天"
    OLD = "> 7天"
    NEVER = "未更新"


@dataclass
class User:
    """用户数据模型"""
    id: int
    username: str
    display_name: str
    role: str  # 'admin' or 'member'
    ip_address: str
    created_at: str

    def to_dict(self) -> dict:
        """转换为字典（排除敏感信息）"""
        return {
            'id': self.id,
            'username': self.username,
            'display_name': self.display_name,
            'role': self.role,
            'ip_address': self.ip_address,
            'created_at': self.created_at
        }


@dataclass
class TodoItem:
    """待办事项数据模型"""
    id: str
    title: str
    created_by: str = ""
    assignee: Optional[str] = None
    deadline: Optional[str] = None
    description: str = ""
    progress: str = ""  # 进度说明
    progress_updated_at: Optional[str] = None  # 进度更新时间
    priority: int = Priority.MEDIUM.value
    status: str = Status.PENDING.value
    created_at: str = ""
    reminded_7day: bool = False
    reminded_3day: bool = False
    reminded_overdue: bool = False

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'assignee': self.assignee,
            'created_by': self.created_by,
            'deadline': self.deadline,
            'description': self.description,
            'progress': self.progress,
            'progress_updated_at': self.progress_updated_at,
            'priority': self.priority,
            'status': self.status,
            'created_at': self.created_at,
            'reminded_7day': self.reminded_7day,
            'reminded_3day': self.reminded_3day,
            'reminded_overdue': self.reminded_overdue
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'TodoItem':
        """从字典创建对象"""
        return cls(
            id=data.get('id', ''),
            title=data.get('title', ''),
            assignee=data.get('assignee'),
            created_by=data.get('created_by', ''),
            deadline=data.get('deadline'),
            description=data.get('description', ''),
            progress=data.get('progress', ''),
            progress_updated_at=data.get('progress_updated_at'),
            priority=data.get('priority', 2),
            status=data.get('status', '待处理'),
            created_at=data.get('created_at', ''),
            reminded_7day=data.get('reminded_7day', False),
            reminded_3day=data.get('reminded_3day', False),
            reminded_overdue=data.get('reminded_overdue', False)
        )

    def get_progress_category(self) -> str:
        """获取进度分类"""
        if not self.progress_updated_at:
            return ProgressCategory.NEVER.value

        try:
            updated_time = datetime.strptime(self.progress_updated_at, "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            delta = now - updated_time
            hours = delta.total_seconds() / 3600

            if hours < 24:
                return ProgressCategory.VERY_RECENT.value
            elif hours < 168:  # 7天
                return ProgressCategory.RECENT.value
            else:
                return ProgressCategory.OLD.value
        except (ValueError, TypeError):
            return ProgressCategory.NEVER.value

    def days_until_deadline(self) -> Optional[int]:
        """计算距离截止日期的天数"""
        if not self.deadline:
            return None
        try:
            deadline_date = datetime.strptime(self.deadline, "%Y-%m-%d").date()
            today = datetime.now().date()
            delta = deadline_date - today
            return delta.days
        except (ValueError, TypeError):
            return None

    def get_urgency_level(self) -> str:
        """获取紧急程度"""
        days = self.days_until_deadline()
        if days is None:
            return "normal"
        elif days < 0:
            return "overdue"
        elif days <= 3:
            return "urgent"
        elif days <= 7:
            return "warning"
        else:
            return "normal"


@dataclass
class LoginRequest:
    """登录请求"""
    username: str
    ip_address: str


@dataclass
class LoginResponse:
    """登录响应"""
    success: bool
    message: str
    token: Optional[str] = None
    user: Optional[dict] = None


@dataclass
class ApiResponse:
    """通用API响应"""
    success: bool
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None
