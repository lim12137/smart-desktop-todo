#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据模型定义
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from typing import Optional
from enum import Enum
import uuid


class Priority(Enum):
    """优先级"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class Status(Enum):
    """状态"""
    PENDING = "待处理"
    IN_PROGRESS = "进行中"
    COMPLETED = "已完成"
    CANCELLED = "已取消"


@dataclass
class TodoItem:
    """待办事项数据模型"""
    title: str
    assignee: str = ""
    deadline: Optional[str] = None  # 格式: YYYY-MM-DD
    description: str = ""
    priority: int = Priority.MEDIUM.value
    status: str = Status.PENDING.value
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    created_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    reminded_7day: bool = False
    reminded_3day: bool = False
    reminded_overdue: bool = False
    
    def days_until_deadline(self) -> Optional[int]:
        """计算距离截止日期的天数"""
        if not self.deadline:
            return None
        try:
            deadline_date = datetime.strptime(self.deadline, "%Y-%m-%d").date()
            today = date.today()
            return (deadline_date - today).days
        except:
            return None
    
    def get_urgency_level(self) -> str:
        """获取紧急程度"""
        days = self.days_until_deadline()
        if days is None:
            return "normal"
        if days < 0:
            return "overdue"
        elif days <= 3:
            return "urgent"
        elif days <= 7:
            return "warning"
        return "normal"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TodoItem':
        """从字典创建实例"""
        return cls(**data)