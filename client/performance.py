#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
客户端性能优化模块
异步加载、分页、批量操作
"""

import tkinter as tk
from concurrent.futures import ThreadPoolExecutor
from typing import Callable, List


class AsyncLoader:
    """异步加载器"""

    def __init__(self, max_workers: int = 3):
        """
        初始化异步加载器

        Args:
            max_workers: 最大工作线程数
        """
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.pending_futures = []

    def submit(self, func: Callable, *args, **kwargs):
        """
        提交异步任务

        Args:
            func: 要执行的函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            Future对象
        """
        return self.executor.submit(func, *args, **kwargs)

    def shutdown(self):
        """关闭线程池"""
        self.executor.shutdown(wait=True)


class LoadingIndicator:
    """加载指示器"""

    def __init__(self, parent, message: str = "加载中..."):
        """
        初始化加载指示器

        Args:
            parent: 父窗口
            message: 显示消息
        """
        self.parent = parent
        self.top = tk.Toplevel(parent)
        self.top.title("")
        self.top.resizable(False, False)
        self.top.configure(bg='#F0F0F0')
        self.top.geometry("200x80")

        # 居中显示
        self.top.transient(parent)
        label = tk.Label(
            self.top,
            text=message,
            bg='#F0F0F0',
            font=('Microsoft YaHei UI', 10)
        )
        label.pack(expand=True)

        # 居中于父窗口
        self._center()

    def _center(self):
        """居中显示"""
        self.top.update_idletasks()
        width = self.top.winfo_reqwidth()
        height = self.top.winfo_reqheight()
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        x = parent_x + (parent_width - width) // 2
        y = parent_y + (parent_height - height) // 2
        self.top.geometry(f"+{x}+{y}")

    def destroy(self):
        """销毁指示器"""
        self.top.destroy()

    def set_message(self, message: str):
        """设置消息"""
        for widget in self.top.winfo_children():
            if isinstance(widget, tk.Label):
                widget.config(text=message)


class PerformanceOptimizer:
    """性能优化器"""

    def __init__(self, data_manager, root_window=None):
        """
        初始化性能优化器

        Args:
            data_manager: 数据管理器实例
            root_window: 根窗口对象（可选）
        """
        self.data_manager = data_manager
        self.root_window = root_window
        self.async_loader = AsyncLoader()
        self._loading_indicator = None

    def async_get_todos(self, callback: Callable):
        """
        异步获取任务列表

        Args:
            callback: 完成后的回调函数
        """
        if self._loading_indicator:
            return

        self._loading_indicator = LoadingIndicator(self.root_window, "正在加载任务...")

        def load_task():
            todos = self.data_manager.get_all_todos()
            return todos

        future = self.async_loader.submit(load_task)

        def on_done(future):
            try:
                todos = future.result()
                # 使用 root_window.after 确保在主线程执行回调
                if callback and self.root_window:
                    self.root_window.after(0, lambda: callback(todos))
            except Exception as e:
                print(f"异步加载失败: {e}")
            finally:
                # 在主线程销毁指示器
                if self._loading_indicator and self.root_window:
                    indicator = self._loading_indicator
                    self._loading_indicator = None
                    self.root_window.after(0, lambda: indicator.destroy())

        future.add_done_callback(on_done)

    def batch_update_todo_status(self, todo_ids: List[str], status: str, callback: Callable):
        """
        批量更新任务状态（减少网络请求）

        Args:
            todo_ids: 任务ID列表
            status: 目标状态
            callback: 完成后的回调函数
        """
        if self._loading_indicator:
            return

        self._loading_indicator = LoadingIndicator(self.root_window, "正在批量更新...")

        def batch_task():
            success = self.data_manager.batch_update_status(todo_ids, status)
            return success

        future = self.async_loader.submit(batch_task)

        def on_done(future):
            try:
                success = future.result()
                if callback and self.root_window:
                    self.root_window.after(0, lambda: callback(success))
            except Exception as e:
                print(f"批量更新失败: {e}")
            finally:
                if self._loading_indicator and self.root_window:
                    indicator = self._loading_indicator
                    self._loading_indicator = None
                    self.root_window.after(0, lambda: indicator.destroy())

        future.add_done_callback(on_done)

    def destroy(self):
        """清理资源"""
        self.async_loader.shutdown()


# 全局性能优化器实例
_performance_optimizer = None


def get_performance_optimizer(data_manager, root_window=None):
    """
    获取全局性能优化器实例

    Args:
        data_manager: 数据管理器实例
        root_window: 根窗口对象（可选）

    Returns:
        PerformanceOptimizer实例
    """
    global _performance_optimizer
    if _performance_optimizer is None:
        _performance_optimizer = PerformanceOptimizer(data_manager, root_window)
    elif root_window:
        _performance_optimizer.root_window = root_window
    return _performance_optimizer
