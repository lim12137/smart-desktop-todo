#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
成员管理对话框
仅管理员可用，用于增删改团队成员
"""

import tkinter as tk
from tkinter import ttk, messagebox
from ui.styles import COLORS, FONTS


class UserManagementDialog(tk.Toplevel):

    def __init__(self, parent, data_manager):
        super().__init__(parent)
        self.parent = parent
        self.data_manager = data_manager

        self.withdraw()

        self.title("👥 成员管理")
        self.configure(bg=COLORS["bg_primary"])
        self.resizable(True, True)
        self.minsize(550, 400)
        self.geometry("600x450")

        self._create_widgets()
        self._load_users()

        self.transient(parent)
        self.grab_set()
        self._center_window()
        self.deiconify()
        self.focus_set()

    def _create_widgets(self):
        main = ttk.Frame(self, padding=15)
        main.pack(fill=tk.BOTH, expand=True)

        # 工具栏
        toolbar = ttk.Frame(main)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(toolbar, text="➕ 添加成员", command=self._add_user).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="✏️ 编辑", command=self._edit_user).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑️ 删除", command=self._delete_user).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔄 刷新", command=self._load_users).pack(side=tk.LEFT, padx=2)

        # 用户列表
        cols = ("username", "display_name", "role", "ip_address", "created_at")
        self.tree = ttk.Treeview(main, columns=cols, show="headings", selectmode="browse",
                                 height=15)

        self.tree.heading("username", text="用户名")
        self.tree.heading("display_name", text="显示名")
        self.tree.heading("role", text="角色")
        self.tree.heading("ip_address", text="IP 地址")
        self.tree.heading("created_at", text="注册时间")

        self.tree.column("username", width=80)
        self.tree.column("display_name", width=100)
        self.tree.column("role", width=60, anchor="center")
        self.tree.column("ip_address", width=130)
        self.tree.column("created_at", width=140)

        vsb = ttk.Scrollbar(main, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # 状态栏
        self.status_label = ttk.Label(self, text="就绪", font=FONTS["small"], padding=5)
        self.status_label.pack(fill=tk.X, side=tk.BOTTOM)

        # 双击编辑
        self.tree.bind("<Double-1>", lambda e: self._edit_user())

    def _load_users(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        users = self.data_manager.get_users()
        role_names = {"admin": "管理员", "member": "成员"}

        for u in users:
            self.tree.insert("", tk.END, iid=str(u["id"]), values=(
                u.get("username", ""),
                u.get("display_name", ""),
                role_names.get(u.get("role", ""), u.get("role", "")),
                u.get("ip_address", ""),
                (u.get("created_at") or "")[:19],
            ))

        self.status_label.configure(text=f"共 {len(users)} 个用户")

    def _get_selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("提示", "请先选择一个成员", parent=self)
            return None
        return sel[0]

    def _add_user(self):
        dialog = _UserFormDialog(self, title="添加成员")
        if dialog.result:
            success = self.data_manager.create_user(dialog.result)
            if success:
                self._load_users()
                self.status_label.configure(text=f"已添加成员: {dialog.result['display_name']}")
            else:
                messagebox.showerror("失败", "添加成员失败，用户名或IP可能已存在", parent=self)

    def _edit_user(self):
        uid = self._get_selected_id()
        if not uid:
            return

        values = self.tree.item(uid, "values")
        current = {
            "username": values[0],
            "display_name": values[1],
            "role": "admin" if values[2] == "管理员" else "member",
            "ip_address": values[3],
        }

        dialog = _UserFormDialog(self, title="编辑成员", user=current, edit_mode=True)
        if dialog.result:
            success = self.data_manager.update_user(int(uid), dialog.result)
            if success:
                self._load_users()
                self.status_label.configure(text=f"已更新成员: {dialog.result.get('display_name', '')}")
            else:
                messagebox.showerror("失败", "更新成员失败", parent=self)

    def _delete_user(self):
        uid = self._get_selected_id()
        if not uid:
            return

        values = self.tree.item(uid, "values")
        name = f"{values[1]} ({values[0]})"

        if not messagebox.askyesno("确认", f"确定要删除成员 {name} 吗？", parent=self):
            return

        success = self.data_manager.delete_user(int(uid))
        if success:
            self._load_users()
            self.status_label.configure(text=f"已删除成员: {name}")
        else:
            messagebox.showerror("失败", "删除失败，该成员可能有关联任务", parent=self)

    def _center_window(self):
        self.update_idletasks()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        pw = self.parent.winfo_width()
        ph = self.parent.winfo_height()
        px = self.parent.winfo_rootx()
        py = self.parent.winfo_rooty()

        if pw < 100 or ph < 100:
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            x = (sw - w) // 2
            y = (sh - h) // 2
        else:
            x = px + (pw - w) // 2
            y = py + (ph - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")


class _UserFormDialog(tk.Toplevel):
    """成员编辑/新建表单"""

    def __init__(self, parent, title="成员", user=None, edit_mode=False):
        super().__init__(parent)
        self.result = None
        self.edit_mode = edit_mode

        self.title(title)
        self.configure(bg=COLORS["bg_primary"])
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        main = ttk.Frame(self, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        row = 0
        # 用户名
        ttk.Label(main, text="用户名:", font=FONTS["normal"]).grid(row=row, column=0, sticky=tk.W, pady=5)
        self.username_var = tk.StringVar(value=user.get("username", "") if user else "")
        self.username_entry = ttk.Entry(main, textvariable=self.username_var, width=25)
        self.username_entry.grid(row=row, column=1, pady=5, padx=(10, 0))
        if edit_mode:
            self.username_entry.configure(state="readonly")
        row += 1

        # 显示名
        ttk.Label(main, text="显示名:", font=FONTS["normal"]).grid(row=row, column=0, sticky=tk.W, pady=5)
        self.display_var = tk.StringVar(value=user.get("display_name", "") if user else "")
        ttk.Entry(main, textvariable=self.display_var, width=25).grid(row=row, column=1, pady=5, padx=(10, 0))
        row += 1

        # 密码（新建时必填）
        ttk.Label(main, text="密码:", font=FONTS["normal"]).grid(row=row, column=0, sticky=tk.W, pady=5)
        self.password_var = tk.StringVar()
        pwd_entry = ttk.Entry(main, textvariable=self.password_var, show="*", width=25)
        pwd_entry.grid(row=row, column=1, pady=5, padx=(10, 0))
        if edit_mode:
            ttk.Label(main, text="留空则不修改", font=FONTS["small"]).grid(row=row, column=2, padx=5)
        row += 1

        # 角色
        ttk.Label(main, text="角色:", font=FONTS["normal"]).grid(row=row, column=0, sticky=tk.W, pady=5)
        self.role_var = tk.StringVar(value=user.get("role", "member") if user else "member")
        role_combo = ttk.Combobox(main, textvariable=self.role_var,
                                  values=["member", "admin"], state="readonly", width=10)
        role_combo.grid(row=row, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        row += 1

        # IP 地址
        ttk.Label(main, text="IP 地址:", font=FONTS["normal"]).grid(row=row, column=0, sticky=tk.W, pady=5)
        self.ip_var = tk.StringVar(value=user.get("ip_address", "") if user else "")
        ttk.Entry(main, textvariable=self.ip_var, width=25).grid(row=row, column=1, pady=5, padx=(10, 0))
        row += 1

        # 按钮
        btn_frame = ttk.Frame(main)
        btn_frame.grid(row=row, column=0, columnspan=3, pady=15)
        ttk.Button(btn_frame, text="保存", command=self._save, width=10).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="取消", command=self.destroy, width=10).pack(side=tk.LEFT, padx=10)

        # 居中
        self.update_idletasks()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        self.deiconify()
        self.focus_set()
        if not edit_mode:
            self.username_entry.focus_set()
        else:
            self.display_var.set(user.get("display_name", "") if user else "")

        self.wait_window()

    def _save(self):
        username = self.username_var.get().strip()
        display_name = self.display_var.get().strip()
        ip_address = self.ip_var.get().strip()
        role = self.role_var.get()
        password = self.password_var.get().strip()

        if not username:
            messagebox.showwarning("提示", "请输入用户名", parent=self)
            return
        if not display_name:
            messagebox.showwarning("提示", "请输入显示名", parent=self)
            return
        if not ip_address:
            messagebox.showwarning("提示", "请输入IP地址", parent=self)
            return
        if not self.edit_mode and not password:
            messagebox.showwarning("提示", "请输入密码", parent=self)
            return

        self.result = {
            "username": username,
            "display_name": display_name,
            "ip_address": ip_address,
            "role": role,
        }
        if password:
            self.result["password"] = password

        self.destroy()
