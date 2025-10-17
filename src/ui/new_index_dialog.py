"""
新建索引对话框

允许用户指定索引名称和保存位置
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from pathlib import Path
from typing import Optional, Tuple


class NewIndexDialog:
    """
    新建索引对话框

    功能:
    1. 输入索引名称
    2. 选择索引数据库保存位置
    3. 选择要索引的目录
    """

    def __init__(self, parent, default_index_dir: str = ""):
        """
        初始化对话框

        Args:
            parent: 父窗口
            default_index_dir: 默认索引目录
        """
        self.parent = parent
        self.default_index_dir = default_index_dir or str(Path.home() / "Documents" / "SearchIndexes")

        self.result = None  # (index_name, db_path, indexed_dirs)

        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("新建索引")
        self.dialog.geometry("600x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (400 // 2)
        self.dialog.geometry(f"600x400+{x}+{y}")

        self._create_widgets()

    def _create_widgets(self):
        """创建控件"""
        # 主框架
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        title_label = ttk.Label(
            main_frame,
            text="指定索引名称:",
            font=("Arial", 12, "bold")
        )
        title_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))

        # 索引名称输入框
        name_frame = ttk.Frame(main_frame)
        name_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))

        ttk.Label(name_frame, text="我的索引:", font=("Arial", 10)).pack(
            side=tk.LEFT, padx=(0, 10)
        )

        self.name_entry = ttk.Entry(name_frame, font=("Arial", 10))
        self.name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.name_entry.insert(0, "我的文档")
        self.name_entry.focus()

        # 索引数据库路径
        db_label = ttk.Label(
            main_frame,
            text="索引数据库的路径:",
            font=("Arial", 10)
        )
        db_label.grid(row=2, column=0, sticky=tk.W, pady=(0, 5))

        # 路径选择框架
        path_frame = ttk.Frame(main_frame)
        path_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        # 下拉框和浏览按钮
        self.path_combobox = ttk.Combobox(path_frame, font=("Arial", 9))
        self.path_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        # 设置默认路径
        default_path = str(Path(self.default_index_dir) / "Indexes")
        self.path_combobox.set(default_path)
        self.path_combobox['values'] = [
            default_path,
            str(Path.home() / "Documents" / "Indexes"),
            "C:\\Indexes",
            "D:\\Indexes"
        ]

        # 浏览按钮
        browse_btn = ttk.Button(
            path_frame,
            text="📁 浏览...",
            command=self._browse_path,
            width=12
        )
        browse_btn.pack(side=tk.LEFT)

        # 更改按钮
        change_btn = ttk.Button(
            path_frame,
            text="更改...",
            command=self._browse_path,
            width=10
        )
        change_btn.pack(side=tk.LEFT, padx=(5, 0))

        # 成功提示
        success_frame = ttk.Frame(main_frame)
        success_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 20))

        self.success_label = ttk.Label(
            success_frame,
            text="",
            font=("Arial", 9),
            foreground="green"
        )
        self.success_label.pack(side=tk.LEFT)

        # 下一步选项
        options_label = ttk.Label(
            main_frame,
            text="你是否想下一次:",
            font=("Arial", 10)
        )
        options_label.grid(row=5, column=0, sticky=tk.W, pady=(10, 5))

        # 单选按钮
        self.next_action = tk.StringVar(value="立刻索引")

        rb1 = ttk.Radiobutton(
            main_frame,
            text="立刻索引库",
            variable=self.next_action,
            value="立刻索引"
        )
        rb1.grid(row=6, column=0, sticky=tk.W, padx=(20, 0))

        rb2 = ttk.Radiobutton(
            main_frame,
            text="附后索引库",
            variable=self.next_action,
            value="附后索引"
        )
        rb2.grid(row=7, column=0, sticky=tk.W, padx=(20, 0))

        rb3 = ttk.Radiobutton(
            main_frame,
            text="设置高级设置",
            variable=self.next_action,
            value="高级设置"
        )
        rb3.grid(row=8, column=0, sticky=tk.W, padx=(20, 0))

        # 底部按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=9, column=0, columnspan=3, sticky=(tk.E, tk.S), pady=(20, 0))

        # 估计按钮
        estimate_btn = ttk.Button(
            button_frame,
            text="🔍 估计",
            command=self._estimate_size,
            width=12
        )
        estimate_btn.pack(side=tk.LEFT, padx=5)

        # 计算近似的索引大小...
        estimate_label = ttk.Label(
            button_frame,
            text="计算近似的索引大小...",
            font=("Arial", 8),
            foreground="gray"
        )
        estimate_label.pack(side=tk.LEFT, padx=10)

        # 后退按钮
        back_btn = ttk.Button(
            button_frame,
            text="⬅ 后退",
            command=self._back,
            width=10
        )
        back_btn.pack(side=tk.LEFT, padx=5)

        # 准备就绪按钮
        ready_btn = ttk.Button(
            button_frame,
            text="准备就绪 ➡",
            command=self._ready,
            width=12
        )
        ready_btn.pack(side=tk.LEFT, padx=5)

        # 取消按钮
        cancel_btn = ttk.Button(
            button_frame,
            text="✖ 取消",
            command=self._cancel,
            width=10
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)

        # 配置网格权重
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(8, weight=1)

    def _browse_path(self):
        """浏览选择路径"""
        initial_dir = self.path_combobox.get()
        if not os.path.exists(initial_dir):
            initial_dir = str(Path.home() / "Documents")

        selected_dir = filedialog.askdirectory(
            parent=self.dialog,
            title="选择索引数据库保存位置",
            initialdir=initial_dir
        )

        if selected_dir:
            self.path_combobox.set(selected_dir)

    def _estimate_size(self):
        """估计索引大小"""
        # 这里可以实现估计逻辑
        messagebox.showinfo(
            "估计大小",
            "索引大小估计功能将在选择要索引的目录后可用。",
            parent=self.dialog
        )

    def _back(self):
        """后退"""
        self.result = None
        self.dialog.destroy()

    def _ready(self):
        """准备就绪 - 创建索引"""
        index_name = self.name_entry.get().strip()
        db_dir = self.path_combobox.get().strip()

        # 验证
        if not index_name:
            messagebox.showwarning(
                "警告",
                "请输入索引名称",
                parent=self.dialog
            )
            self.name_entry.focus()
            return

        if not db_dir:
            messagebox.showwarning(
                "警告",
                "请选择索引数据库保存位置",
                parent=self.dialog
            )
            return

        # 创建数据库路径
        try:
            db_dir_path = Path(db_dir)
            db_dir_path.mkdir(parents=True, exist_ok=True)

            # 数据库文件名
            db_file = db_dir_path / f"{index_name}.db"

            # 检查是否已存在
            if db_file.exists():
                response = messagebox.askyesno(
                    "确认",
                    f"索引 '{index_name}' 已存在。\n是否覆盖?",
                    parent=self.dialog
                )
                if not response:
                    return

            # 根据用户选择的下一步操作
            next_action = self.next_action.get()

            if next_action == "立刻索引":
                # 让用户选择要索引的目录
                indexed_dir = filedialog.askdirectory(
                    parent=self.dialog,
                    title="选择要索引的目录"
                )

                if not indexed_dir:
                    return

                indexed_dirs = [indexed_dir]

            elif next_action == "附后索引":
                # 稍后索引,不选择目录
                indexed_dirs = []

            else:  # 高级设置
                # 打开高级设置对话框
                messagebox.showinfo(
                    "提示",
                    "高级设置功能将在索引创建后可用。\n请使用菜单 '编辑 → 设置' 进行配置。",
                    parent=self.dialog
                )
                indexed_dirs = []

            # 设置结果
            self.result = (index_name, str(db_file), indexed_dirs)

            # 显示成功消息
            self.success_label.config(
                text=f"✓ 索引 '{index_name}' 创建成功!"
            )

            # 关闭对话框
            self.dialog.after(500, self.dialog.destroy)

        except Exception as e:
            messagebox.showerror(
                "错误",
                f"创建索引失败: {e}",
                parent=self.dialog
            )

    def _cancel(self):
        """取消"""
        self.result = None
        self.dialog.destroy()

    def show(self) -> Optional[Tuple[str, str, list]]:
        """
        显示对话框

        Returns:
            tuple: (index_name, db_path, indexed_dirs) 或 None
        """
        self.dialog.wait_window()
        return self.result


def show_new_index_dialog(parent, default_index_dir: str = "") -> Optional[Tuple[str, str, list]]:
    """
    显示新建索引对话框

    Args:
        parent: 父窗口
        default_index_dir: 默认索引目录

    Returns:
        tuple: (index_name, db_path, indexed_dirs) 或 None
    """
    dialog = NewIndexDialog(parent, default_index_dir)
    return dialog.show()
