"""
多索引库更新进度对话框

显示多个索引库的更新进度，每个索引库独立显示状态和进度条
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Callable, Optional
from dataclasses import dataclass
from enum import Enum


class UpdateStatus(Enum):
    """更新状态枚举"""
    WAITING = "等待中"
    CHECKING = "检查目录"
    UPDATING = "更新中"
    COMPLETED = "完成"
    SKIPPED = "已跳过"
    ERROR = "错误"


@dataclass
class LibraryUpdateState:
    """索引库更新状态"""
    library_name: str
    status: UpdateStatus = UpdateStatus.WAITING
    progress: int = 0  # 0-100
    current_file: str = ""
    total_files: int = 0
    processed_files: int = 0
    added: int = 0
    updated: int = 0
    deleted: int = 0
    error_message: str = ""
    directory_exists: bool = True


class MultiIndexUpdateDialog:
    """多索引库更新进度对话框"""

    def __init__(self, parent, libraries: list, on_close: Optional[Callable] = None):
        """
        初始化对话框

        Args:
            parent: 父窗口
            libraries: 索引库列表
            on_close: 关闭回调
        """
        self.parent = parent
        self.libraries = libraries
        self.on_close = on_close

        # 初始化状态字典
        self.states: Dict[str, LibraryUpdateState] = {}
        for lib in libraries:
            self.states[lib.name] = LibraryUpdateState(library_name=lib.name)

        # UI 组件字典
        self.status_labels: Dict[str, ttk.Label] = {}
        self.progress_bars: Dict[str, ttk.Progressbar] = {}
        self.detail_labels: Dict[str, ttk.Label] = {}

        self._create_dialog()

    def _create_dialog(self):
        """创建对话框窗口"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("索引库更新进度")
        self.dialog.geometry("700x500")
        self.dialog.resizable(True, True)

        # 设置为模态对话框
        self.dialog.grab_set()

        # 标题
        title_frame = ttk.Frame(self.dialog)
        title_frame.pack(fill=tk.X, padx=10, pady=10)

        title_label = ttk.Label(
            title_frame,
            text=f"正在更新 {len(self.libraries)} 个索引库",
            font=("Microsoft YaHei UI", 12, "bold")
        )
        title_label.pack(side=tk.LEFT)

        # 总体进度
        overall_frame = ttk.LabelFrame(self.dialog, text="总体进度", padding=10)
        overall_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.overall_progress = ttk.Progressbar(
            overall_frame,
            mode='determinate',
            length=660
        )
        self.overall_progress.pack(fill=tk.X)

        self.overall_label = ttk.Label(
            overall_frame,
            text="准备开始...",
            font=("Microsoft YaHei UI", 9)
        )
        self.overall_label.pack(fill=tk.X, pady=(5, 0))

        # 分隔线
        separator = ttk.Separator(self.dialog, orient=tk.HORIZONTAL)
        separator.pack(fill=tk.X, padx=10, pady=5)

        # 各索引库进度区域（可滚动）
        canvas_frame = ttk.Frame(self.dialog)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 创建 Canvas 和 Scrollbar
        self.canvas = tk.Canvas(canvas_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 为每个索引库创建进度显示
        for i, library in enumerate(self.libraries):
            self._create_library_progress_widget(library, i)

        # 底部按钮区
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        self.close_btn = ttk.Button(
            btn_frame,
            text="关闭",
            command=self._on_close,
            state=tk.DISABLED  # 初始禁用
        )
        self.close_btn.pack(side=tk.RIGHT)

        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def _create_library_progress_widget(self, library, index: int):
        """为单个索引库创建进度显示组件"""
        # 库名框架
        lib_frame = ttk.LabelFrame(
            self.scrollable_frame,
            text=library.name,
            padding=10
        )
        lib_frame.pack(fill=tk.X, pady=5)

        # 状态行
        status_frame = ttk.Frame(lib_frame)
        status_frame.pack(fill=tk.X, pady=(0, 5))

        status_label = ttk.Label(
            status_frame,
            text="● 等待中",
            font=("Microsoft YaHei UI", 9),
            foreground="gray"
        )
        status_label.pack(side=tk.LEFT)
        self.status_labels[library.name] = status_label

        # 进度条
        progress_bar = ttk.Progressbar(
            lib_frame,
            mode='determinate',
            length=640
        )
        progress_bar.pack(fill=tk.X, pady=(0, 5))
        self.progress_bars[library.name] = progress_bar

        # 详细信息
        detail_label = ttk.Label(
            lib_frame,
            text="",
            font=("Microsoft YaHei UI", 8),
            foreground="gray"
        )
        detail_label.pack(fill=tk.X)
        self.detail_labels[library.name] = detail_label

    def update_library_status(
        self,
        library_name: str,
        status: UpdateStatus,
        progress: int = 0,
        current_file: str = "",
        total_files: int = 0,
        processed_files: int = 0,
        stats: Optional[dict] = None,
        error_message: str = "",
        directory_exists: bool = True
    ):
        """
        更新索引库状态

        Args:
            library_name: 索引库名称
            status: 更新状态
            progress: 进度百分比 (0-100)
            current_file: 当前处理的文件
            total_files: 总文件数
            processed_files: 已处理文件数
            stats: 统计信息字典 {added, updated, deleted}
            error_message: 错误消息
            directory_exists: 目录是否存在
        """
        if library_name not in self.states:
            return

        state = self.states[library_name]
        state.status = status
        state.progress = progress
        state.current_file = current_file
        state.total_files = total_files
        state.processed_files = processed_files
        state.error_message = error_message
        state.directory_exists = directory_exists

        if stats:
            state.added = stats.get('added', 0)
            state.updated = stats.get('updated', 0)
            state.deleted = stats.get('deleted', 0)

        # 更新 UI
        self._update_library_ui(library_name)
        self._update_overall_progress()

    def _update_library_ui(self, library_name: str):
        """更新单个索引库的 UI 显示"""
        state = self.states[library_name]
        status_label = self.status_labels[library_name]
        progress_bar = self.progress_bars[library_name]
        detail_label = self.detail_labels[library_name]

        # 状态颜色映射
        status_colors = {
            UpdateStatus.WAITING: ("gray", "●"),
            UpdateStatus.CHECKING: ("blue", "◉"),
            UpdateStatus.UPDATING: ("orange", "◉"),
            UpdateStatus.COMPLETED: ("green", "✓"),
            UpdateStatus.SKIPPED: ("gray", "○"),
            UpdateStatus.ERROR: ("red", "✗"),
        }

        color, symbol = status_colors.get(state.status, ("black", "●"))

        # 更新状态标签
        if state.status == UpdateStatus.SKIPPED:
            status_text = f"{symbol} {state.status.value} - 索引目录不存在，保留原有内容"
        elif state.status == UpdateStatus.ERROR:
            status_text = f"{symbol} {state.status.value} - {state.error_message}"
        else:
            status_text = f"{symbol} {state.status.value}"

        status_label.config(text=status_text, foreground=color)

        # 更新进度条
        progress_bar['value'] = state.progress

        # 更新详细信息
        if state.status == UpdateStatus.UPDATING and state.current_file:
            detail_text = f"处理中: {state.current_file}"
            if state.total_files > 0:
                detail_text += f" ({state.processed_files}/{state.total_files})"
        elif state.status == UpdateStatus.COMPLETED:
            # 检查是否是空库（没有任何变化）
            if state.added == 0 and state.updated == 0 and state.deleted == 0:
                detail_text = "空索引库，无需更新"
            else:
                detail_text = f"新增: {state.added} | 更新: {state.updated} | 删除: {state.deleted}"
        elif state.status == UpdateStatus.SKIPPED:
            detail_text = "已跳过 - 目录不存在"
        else:
            detail_text = ""

        detail_label.config(text=detail_text)

    def _update_overall_progress(self):
        """更新总体进度"""
        total = len(self.states)
        completed = sum(
            1 for s in self.states.values()
            if s.status in (UpdateStatus.COMPLETED, UpdateStatus.SKIPPED, UpdateStatus.ERROR)
        )

        overall_progress = int((completed / total) * 100) if total > 0 else 0
        self.overall_progress['value'] = overall_progress

        # 更新总体标签
        active_states = [
            s for s in self.states.values()
            if s.status == UpdateStatus.UPDATING
        ]

        if active_states:
            self.overall_label.config(
                text=f"正在更新: {active_states[0].library_name} | 总进度: {completed}/{total}"
            )
        elif completed == total:
            self.overall_label.config(text=f"✓ 全部完成 ({completed}/{total})")
            self.close_btn.config(state=tk.NORMAL)  # 启用关闭按钮
        else:
            self.overall_label.config(text=f"进度: {completed}/{total}")

    def mark_completed(self):
        """标记更新完成"""
        self.close_btn.config(state=tk.NORMAL)

    def _on_close(self):
        """关闭对话框"""
        if self.on_close:
            self.on_close()
        self.dialog.destroy()

    def show(self):
        """显示对话框"""
        self.dialog.deiconify()


# 测试代码
if __name__ == '__main__':
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

    import time
    from src.core.index_library_manager import IndexLibrary

    root = tk.Tk()
    root.withdraw()

    # 模拟索引库
    libs = [
        IndexLibrary(
            name="测试索引库1",
            db_path="test1.db",
            created="2025-01-01",
            last_used="2025-01-01"
        ),
        IndexLibrary(
            name="测试索引库2",
            db_path="test2.db",
            created="2025-01-01",
            last_used="2025-01-01"
        ),
        IndexLibrary(
            name="测试索引库3",
            db_path="test3.db",
            created="2025-01-01",
            last_used="2025-01-01"
        ),
    ]

    dialog = MultiIndexUpdateDialog(root, libs)
    dialog.show()

    # 模拟更新过程
    def simulate_updates():
        # 索引库1 - 正常更新
        dialog.update_library_status("测试索引库1", UpdateStatus.CHECKING)
        root.after(500, lambda: dialog.update_library_status(
            "测试索引库1", UpdateStatus.UPDATING, 30, "file1.txt", 10, 3
        ))
        root.after(1000, lambda: dialog.update_library_status(
            "测试索引库1", UpdateStatus.UPDATING, 60, "file2.txt", 10, 6
        ))
        root.after(1500, lambda: dialog.update_library_status(
            "测试索引库1", UpdateStatus.COMPLETED, 100, "", 10, 10,
            stats={'added': 2, 'updated': 5, 'deleted': 1}
        ))

        # 索引库2 - 目录不存在，跳过
        root.after(1600, lambda: dialog.update_library_status(
            "测试索引库2", UpdateStatus.CHECKING
        ))
        root.after(2000, lambda: dialog.update_library_status(
            "测试索引库2", UpdateStatus.SKIPPED, directory_exists=False
        ))

        # 索引库3 - 正常更新
        root.after(2100, lambda: dialog.update_library_status(
            "测试索引库3", UpdateStatus.UPDATING, 50, "file3.txt", 5, 2
        ))
        root.after(2500, lambda: dialog.update_library_status(
            "测试索引库3", UpdateStatus.COMPLETED, 100, "", 5, 5,
            stats={'added': 1, 'updated': 3, 'deleted': 0}
        ))

    simulate_updates()
    root.mainloop()
