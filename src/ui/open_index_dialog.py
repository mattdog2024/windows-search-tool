"""
打开索引对话框

允许用户打开现有的索引数据库
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from pathlib import Path
from typing import Optional
from datetime import datetime


class OpenIndexDialog:
    """
    打开索引对话框

    功能:
    1. 浏览选择现有的索引数据库文件
    2. 显示最近使用的索引
    3. 验证索引文件有效性
    """

    def __init__(self, parent, recent_indexes: list = None):
        """
        初始化对话框

        Args:
            parent: 父窗口
            recent_indexes: 最近使用的索引列表
        """
        self.parent = parent
        self.recent_indexes = recent_indexes or []

        self.result = None  # 选中的数据库路径

        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("打开索引")
        self.dialog.geometry("650x450")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (650 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (450 // 2)
        self.dialog.geometry(f"650x450+{x}+{y}")

        self._create_widgets()
        self._load_recent_indexes()

    def _create_widgets(self):
        """创建控件"""
        # 主框架
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = ttk.Label(
            main_frame,
            text="打开现有索引",
            font=("Arial", 13, "bold")
        )
        title_label.pack(anchor=tk.W, pady=(0, 15))

        # 最近使用的索引
        recent_label = ttk.Label(
            main_frame,
            text="最近使用的索引:",
            font=("Arial", 10)
        )
        recent_label.pack(anchor=tk.W, pady=(0, 5))

        # 列表框架
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # 创建 Treeview
        columns = ("名称", "路径", "大小", "最后使用")
        self.index_tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        # 设置列
        self.index_tree.heading("名称", text="索引名称")
        self.index_tree.heading("路径", text="路径")
        self.index_tree.heading("大小", text="大小")
        self.index_tree.heading("最后使用", text="最后使用")

        self.index_tree.column("名称", width=150)
        self.index_tree.column("路径", width=250)
        self.index_tree.column("大小", width=80)
        self.index_tree.column("最后使用", width=120)

        # 滚动条
        scrollbar = ttk.Scrollbar(
            list_frame,
            orient=tk.VERTICAL,
            command=self.index_tree.yview
        )
        self.index_tree.configure(yscrollcommand=scrollbar.set)

        # 布局
        self.index_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 双击打开
        self.index_tree.bind('<Double-1>', lambda e: self._open_selected())

        # 或者浏览
        browse_frame = ttk.Frame(main_frame)
        browse_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(
            browse_frame,
            text="或者浏览索引文件:",
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=(0, 10))

        self.path_entry = ttk.Entry(browse_frame, font=("Arial", 9))
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        browse_btn = ttk.Button(
            browse_frame,
            text="📁 浏览...",
            command=self._browse_file,
            width=12
        )
        browse_btn.pack(side=tk.LEFT)

        # 底部按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        # 左侧信息
        info_label = ttk.Label(
            button_frame,
            text="提示: 双击列表中的索引即可打开",
            font=("Arial", 8),
            foreground="gray"
        )
        info_label.pack(side=tk.LEFT)

        # 右侧按钮
        btn_container = ttk.Frame(button_frame)
        btn_container.pack(side=tk.RIGHT)

        # 打开按钮
        open_btn = ttk.Button(
            btn_container,
            text="✓ 打开",
            command=self._open_selected,
            width=12
        )
        open_btn.pack(side=tk.LEFT, padx=5)

        # 取消按钮
        cancel_btn = ttk.Button(
            btn_container,
            text="✖ 取消",
            command=self._cancel,
            width=10
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)

    def _load_recent_indexes(self):
        """加载最近使用的索引"""
        for index_info in self.recent_indexes:
            db_path = index_info.get('path', '')
            name = index_info.get('name', Path(db_path).stem)
            last_used = index_info.get('last_used', '')

            # 检查文件是否存在
            if not os.path.exists(db_path):
                continue

            # 获取文件大小
            try:
                size_bytes = os.path.getsize(db_path)
                if size_bytes < 1024:
                    size_str = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    size_str = f"{size_bytes / 1024:.1f} KB"
                else:
                    size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
            except:
                size_str = "未知"

            # 格式化时间
            if last_used:
                try:
                    dt = datetime.fromisoformat(last_used)
                    time_str = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    time_str = last_used
            else:
                time_str = ""

            # 插入到树
            self.index_tree.insert(
                '',
                'end',
                values=(name, db_path, size_str, time_str),
                tags=(db_path,)
            )

    def _browse_file(self):
        """浏览选择索引文件"""
        file_path = filedialog.askopenfilename(
            parent=self.dialog,
            title="选择索引数据库文件",
            filetypes=[
                ("SQLite 数据库", "*.db"),
                ("所有文件", "*.*")
            ],
            initialdir=str(Path.home() / "Documents")
        )

        if file_path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, file_path)

            # 验证文件
            if self._validate_index(file_path):
                self.result = file_path
                self.dialog.destroy()

    def _open_selected(self):
        """打开选中的索引"""
        # 首先检查是否从列表选择
        selection = self.index_tree.selection()
        if selection:
            item = self.index_tree.item(selection[0])
            db_path = item['values'][1]  # 路径列

            if self._validate_index(db_path):
                self.result = db_path
                self.dialog.destroy()
            return

        # 否则检查路径输入框
        db_path = self.path_entry.get().strip()
        if db_path:
            if self._validate_index(db_path):
                self.result = db_path
                self.dialog.destroy()
            return

        # 没有选择
        messagebox.showwarning(
            "警告",
            "请选择一个索引或输入索引文件路径",
            parent=self.dialog
        )

    def _validate_index(self, db_path: str) -> bool:
        """
        验证索引文件

        Args:
            db_path: 数据库文件路径

        Returns:
            bool: 是否有效
        """
        if not os.path.exists(db_path):
            messagebox.showerror(
                "错误",
                f"索引文件不存在:\n{db_path}",
                parent=self.dialog
            )
            return False

        if not db_path.endswith('.db'):
            response = messagebox.askyesno(
                "确认",
                f"选择的文件不是 .db 文件。\n是否仍要打开?",
                parent=self.dialog
            )
            if not response:
                return False

        # 可以添加更多验证逻辑,比如检查是否是有效的SQLite数据库
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 检查是否有 documents 表
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='documents'"
            )
            if not cursor.fetchone():
                conn.close()
                messagebox.showerror(
                    "错误",
                    "这不是一个有效的搜索索引数据库。\n缺少 documents 表。",
                    parent=self.dialog
                )
                return False

            conn.close()
            return True

        except Exception as e:
            messagebox.showerror(
                "错误",
                f"无法打开索引文件:\n{e}",
                parent=self.dialog
            )
            return False

    def _cancel(self):
        """取消"""
        self.result = None
        self.dialog.destroy()

    def show(self) -> Optional[str]:
        """
        显示对话框

        Returns:
            str: 选中的数据库路径,或 None
        """
        self.dialog.wait_window()
        return self.result


def show_open_index_dialog(parent, recent_indexes: list = None) -> Optional[str]:
    """
    显示打开索引对话框

    Args:
        parent: 父窗口
        recent_indexes: 最近使用的索引列表

    Returns:
        str: 选中的数据库路径,或 None
    """
    dialog = OpenIndexDialog(parent, recent_indexes)
    return dialog.show()
