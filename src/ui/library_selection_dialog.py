"""
索引库选择对话框

用于在添加目录时选择目标索引库
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, List


class LibrarySelectionDialog:
    """索引库选择对话框"""

    def __init__(self, parent, libraries: list, title: str = "选择索引库"):
        """
        初始化对话框

        Args:
            parent: 父窗口
            libraries: 索引库列表
            title: 对话框标题
        """
        self.parent = parent
        self.libraries = libraries
        self.selected_library = None

        self._create_dialog(title)

    def _create_dialog(self, title: str):
        """创建对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(title)
        self.dialog.geometry("500x450")
        self.dialog.resizable(False, False)

        # 设置为模态
        self.dialog.grab_set()

        # 标题说明
        title_frame = ttk.Frame(self.dialog)
        title_frame.pack(fill=tk.X, padx=20, pady=15)

        title_label = ttk.Label(
            title_frame,
            text="请选择要将目录添加到哪个索引库：",
            font=("Microsoft YaHei UI", 11, "bold")
        )
        title_label.pack(anchor=tk.W)

        instruction_label = ttk.Label(
            title_frame,
            text="目录中的文件将被索引到所选的库中",
            font=("Microsoft YaHei UI", 9),
            foreground="gray"
        )
        instruction_label.pack(anchor=tk.W, pady=(5, 0))

        # 分隔线
        separator1 = ttk.Separator(self.dialog, orient=tk.HORIZONTAL)
        separator1.pack(fill=tk.X, padx=20, pady=5)

        # 库列表区域（限制高度，不使用 expand）
        list_frame = ttk.Frame(self.dialog)
        list_frame.pack(fill=tk.X, padx=20, pady=5)

        # 创建 Listbox 显示库列表
        listbox_frame = ttk.Frame(list_frame)
        listbox_frame.pack(fill=tk.BOTH)

        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL)

        self.listbox = tk.Listbox(
            listbox_frame,
            font=("Microsoft YaHei UI", 10),
            yscrollcommand=scrollbar.set,
            selectmode=tk.SINGLE,
            height=6,  # 固定高度
            activestyle='dotbox',
            selectbackground='#0078D4',
            selectforeground='white'
        )

        scrollbar.config(command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 填充库列表
        for i, library in enumerate(self.libraries):
            # 显示格式：库名 (数据库路径)
            display_text = f"📚 {library.name}"
            if hasattr(library, 'doc_count') and library.doc_count > 0:
                display_text += f"  ({library.doc_count} 个文档)"

            self.listbox.insert(tk.END, display_text)

        # 默认选中第一个
        if self.libraries:
            self.listbox.selection_set(0)
            self.listbox.activate(0)

        # 双击选择
        self.listbox.bind('<Double-Button-1>', lambda e: self._on_confirm())

        # 详细信息区域
        info_frame = ttk.LabelFrame(self.dialog, text="所选库信息", padding=10)
        info_frame.pack(fill=tk.X, padx=20, pady=10)

        self.info_label = ttk.Label(
            info_frame,
            text="",
            font=("Microsoft YaHei UI", 9),
            foreground="#333",
            wraplength=440  # 限制宽度，自动换行
        )
        self.info_label.pack(fill=tk.X)

        # 绑定选择事件
        self.listbox.bind('<<ListboxSelect>>', self._on_selection_changed)

        # 初始显示第一个库的信息
        if self.libraries:
            self._update_info(0)

        # 分隔线
        separator2 = ttk.Separator(self.dialog, orient=tk.HORIZONTAL)
        separator2.pack(fill=tk.X, padx=20, pady=5)

        # 按钮区域 - 使用固定位置
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill=tk.X, padx=20, pady=15)

        ttk.Button(
            btn_frame,
            text="取消",
            command=self._on_cancel,
            width=12
        ).pack(side=tk.RIGHT, padx=5)

        confirm_btn = ttk.Button(
            btn_frame,
            text="确定",
            command=self._on_confirm,
            width=12
        )
        confirm_btn.pack(side=tk.RIGHT, padx=5)

        # 设置默认按钮样式（需要时可以添加）
        confirm_btn.focus_set()

        # 绑定键盘事件
        self.dialog.bind('<Return>', lambda e: self._on_confirm())
        self.dialog.bind('<Escape>', lambda e: self._on_cancel())

        # 居中显示
        self._center_dialog()

    def _center_dialog(self):
        """居中显示对话框"""
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def _on_selection_changed(self, event):
        """选择改变事件"""
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            self._update_info(index)

    def _update_info(self, index: int):
        """更新详细信息显示"""
        if 0 <= index < len(self.libraries):
            library = self.libraries[index]

            info_lines = []
            info_lines.append(f"库名称: {library.name}")
            info_lines.append(f"数据库: {library.db_path}")

            if hasattr(library, 'doc_count'):
                info_lines.append(f"文档数: {library.doc_count}")

            if hasattr(library, 'created'):
                info_lines.append(f"创建时间: {library.created[:10]}")

            self.info_label.config(text="\n".join(info_lines))

    def _on_confirm(self):
        """确认选择"""
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            self.selected_library = self.libraries[index]
        self.dialog.destroy()

    def _on_cancel(self):
        """取消选择"""
        self.selected_library = None
        self.dialog.destroy()

    def show(self) -> Optional[object]:
        """
        显示对话框并等待用户选择

        Returns:
            选中的索引库对象，如果取消则返回 None
        """
        self.dialog.wait_window()
        return self.selected_library


def show_library_selection_dialog(parent, libraries: list, title: str = "选择索引库"):
    """
    显示索引库选择对话框的便捷函数

    Args:
        parent: 父窗口
        libraries: 索引库列表
        title: 对话框标题

    Returns:
        选中的索引库对象，如果取消则返回 None
    """
    dialog = LibrarySelectionDialog(parent, libraries, title)
    return dialog.show()


# 测试代码
if __name__ == '__main__':
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

    from src.core.index_library_manager import IndexLibrary

    root = tk.Tk()
    root.withdraw()

    # 模拟索引库
    libs = [
        IndexLibrary(
            name="默认索引库",
            db_path="search_index.db",
            created="2025-10-17T14:45:48",
            last_used="2025-10-17T15:00:06",
            doc_count=748,
            size_bytes=2600000
        ),
        IndexLibrary(
            name="测试1",
            db_path="C:/Users/TV/Documents/测试1.db",
            created="2025-10-17T15:24:22",
            last_used="2025-10-17T15:46:00",
            doc_count=0,
            size_bytes=0
        ),
        IndexLibrary(
            name="工作文档",
            db_path="D:/Work/work_index.db",
            created="2025-10-17T10:00:00",
            last_used="2025-10-17T16:00:00",
            doc_count=1523,
            size_bytes=8500000
        ),
    ]

    selected = show_library_selection_dialog(root, libs, "选择目标索引库")

    if selected:
        print(f"用户选择了: {selected.name}")
    else:
        print("用户取消了选择")
