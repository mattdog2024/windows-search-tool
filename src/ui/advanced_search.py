"""
高级搜索对话框

Story 2.4: 高级搜索和过滤
- 文件类型过滤
- 日期范围过滤
- 文件大小过滤
- 路径过滤
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class AdvancedSearchDialog:
    """
    高级搜索对话框

    提供更多搜索过滤选项
    """

    def __init__(self, parent):
        """
        初始化对话框

        Args:
            parent: 父窗口
        """
        self.parent = parent
        self.result = None

        # 创建窗口
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("高级搜索")
        self.dialog.geometry("500x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_widgets()

    def _create_widgets(self):
        """创建控件"""
        # 主框架
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 文件类型过滤
        type_frame = ttk.LabelFrame(main_frame, text="文件类型", padding=10)
        type_frame.pack(fill=tk.X, pady=5)

        self.file_types = {}
        types = [
            ("文本文件", ["txt", "md", "log"]),
            ("Word 文档", ["docx", "doc"]),
            ("Excel 文档", ["xlsx", "xls"]),
            ("PowerPoint", ["pptx", "ppt"]),
            ("PDF 文档", ["pdf"]),
            ("代码文件", ["py", "java", "cpp", "js"])
        ]

        for i, (label, exts) in enumerate(types):
            var = tk.BooleanVar(value=True)
            self.file_types[tuple(exts)] = var
            cb = ttk.Checkbutton(type_frame, text=label, variable=var)
            cb.grid(row=i//2, column=i%2, sticky=tk.W, padx=5, pady=2)

        # 日期范围过滤
        date_frame = ttk.LabelFrame(main_frame, text="修改日期", padding=10)
        date_frame.pack(fill=tk.X, pady=5)

        self.date_range = tk.StringVar(value="all")
        date_options = [
            ("全部", "all"),
            ("最近一天", "1d"),
            ("最近一周", "1w"),
            ("最近一月", "1m"),
            ("最近一年", "1y"),
            ("自定义", "custom")
        ]

        for i, (label, value) in enumerate(date_options):
            rb = ttk.Radiobutton(
                date_frame,
                text=label,
                variable=self.date_range,
                value=value
            )
            rb.grid(row=i//3, column=i%3, sticky=tk.W, padx=5, pady=2)

        # 文件大小过滤
        size_frame = ttk.LabelFrame(main_frame, text="文件大小", padding=10)
        size_frame.pack(fill=tk.X, pady=5)

        # 最小大小
        ttk.Label(size_frame, text="最小:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.min_size = ttk.Entry(size_frame, width=15)
        self.min_size.grid(row=0, column=1, padx=5)
        ttk.Label(size_frame, text="KB").grid(row=0, column=2, sticky=tk.W)

        # 最大大小
        ttk.Label(size_frame, text="最大:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.max_size = ttk.Entry(size_frame, width=15)
        self.max_size.grid(row=1, column=1, padx=5)
        ttk.Label(size_frame, text="KB").grid(row=1, column=2, sticky=tk.W)

        # 路径过滤
        path_frame = ttk.LabelFrame(main_frame, text="路径过滤", padding=10)
        path_frame.pack(fill=tk.X, pady=5)

        ttk.Label(path_frame, text="包含路径:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.include_path = ttk.Entry(path_frame, width=40)
        self.include_path.grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(path_frame, text="排除路径:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.exclude_path = ttk.Entry(path_frame, width=40)
        self.exclude_path.grid(row=1, column=1, padx=5, pady=2)

        # 按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            button_frame,
            text="确定",
            command=self._ok
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="取消",
            command=self._cancel
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Button(
            button_frame,
            text="重置",
            command=self._reset
        ).pack(side=tk.LEFT, padx=5)

    def _ok(self):
        """确定按钮"""
        # 收集过滤条件
        filters = {}

        # 文件类型
        selected_types = []
        for exts, var in self.file_types.items():
            if var.get():
                selected_types.extend(exts)
        if selected_types:
            filters['file_types'] = selected_types

        # 日期范围
        date_range = self.date_range.get()
        if date_range != "all":
            if date_range == "1d":
                filters['modified_after'] = datetime.now() - timedelta(days=1)
            elif date_range == "1w":
                filters['modified_after'] = datetime.now() - timedelta(weeks=1)
            elif date_range == "1m":
                filters['modified_after'] = datetime.now() - timedelta(days=30)
            elif date_range == "1y":
                filters['modified_after'] = datetime.now() - timedelta(days=365)

        # 文件大小
        min_size = self.min_size.get().strip()
        if min_size:
            try:
                filters['min_size'] = int(min_size) * 1024  # KB to bytes
            except ValueError:
                pass

        max_size = self.max_size.get().strip()
        if max_size:
            try:
                filters['max_size'] = int(max_size) * 1024
            except ValueError:
                pass

        # 路径
        include = self.include_path.get().strip()
        if include:
            filters['include_path'] = include

        exclude = self.exclude_path.get().strip()
        if exclude:
            filters['exclude_path'] = exclude

        self.result = filters
        self.dialog.destroy()

    def _cancel(self):
        """取消按钮"""
        self.result = None
        self.dialog.destroy()

    def _reset(self):
        """重置按钮"""
        # 重置所有选项
        for var in self.file_types.values():
            var.set(True)

        self.date_range.set("all")
        self.min_size.delete(0, tk.END)
        self.max_size.delete(0, tk.END)
        self.include_path.delete(0, tk.END)
        self.exclude_path.delete(0, tk.END)

    def show(self) -> Optional[Dict[str, Any]]:
        """
        显示对话框并返回结果

        Returns:
            过滤条件字典,如果取消则返回 None
        """
        self.dialog.wait_window()
        return self.result


def show_advanced_search(parent) -> Optional[Dict[str, Any]]:
    """
    显示高级搜索对话框

    Args:
        parent: 父窗口

    Returns:
        过滤条件字典
    """
    dialog = AdvancedSearchDialog(parent)
    return dialog.show()
