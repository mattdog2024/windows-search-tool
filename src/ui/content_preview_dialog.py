"""
内容预览对话框

显示文档内容并高亮搜索关键词
支持从数据库读取内容（即使文件已被删除）
"""

import tkinter as tk
from tkinter import ttk, messagebox
import re
import os
from pathlib import Path
from typing import Optional


class ContentPreviewDialog:
    """
    内容预览对话框

    功能:
    1. 从数据库读取文档内容
    2. 高亮显示搜索关键词
    3. 支持文件已删除的情况
    4. 显示文件元数据
    """

    def __init__(self, parent, db_manager, doc_id: int, file_path: str, search_query: str = ""):
        """
        初始化对话框

        Args:
            parent: 父窗口
            db_manager: 数据库管理器
            doc_id: 文档 ID
            file_path: 文件路径
            search_query: 搜索关键词
        """
        self.parent = parent
        self.db_manager = db_manager
        self.doc_id = doc_id
        self.file_path = file_path
        self.search_query = search_query

        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"内容预览 - {Path(file_path).name}")
        self.dialog.geometry("900x700")
        self.dialog.transient(parent)

        # 居中显示
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (700 // 2)
        self.dialog.geometry(f"900x700+{x}+{y}")

        self._create_widgets()
        self._load_content()

    def _create_widgets(self):
        """创建控件"""
        # 主框架
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 工具栏
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill=tk.X, pady=(0, 5))

        # 文件信息
        info_frame = ttk.Frame(toolbar)
        info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.file_exists_label = ttk.Label(
            info_frame,
            text="",
            font=("Arial", 9),
            foreground="gray"
        )
        self.file_exists_label.pack(side=tk.LEFT, padx=(0, 10))

        self.search_info_label = ttk.Label(
            info_frame,
            text="",
            font=("Arial", 9),
            foreground="blue"
        )
        self.search_info_label.pack(side=tk.LEFT)

        # 按钮
        button_frame = ttk.Frame(toolbar)
        button_frame.pack(side=tk.RIGHT)

        ttk.Button(
            button_frame,
            text="📄 打开原文件",
            command=self._open_original_file,
            width=15
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            button_frame,
            text="📂 打开所在文件夹",
            command=self._open_folder,
            width=18
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            button_frame,
            text="✖ 关闭",
            command=self.dialog.destroy,
            width=10
        ).pack(side=tk.LEFT, padx=2)

        # 文本框架
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        # 文本控件
        self.text_widget = tk.Text(
            text_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            padx=10,
            pady=10
        )
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 滚动条
        scrollbar = ttk.Scrollbar(
            text_frame,
            orient=tk.VERTICAL,
            command=self.text_widget.yview
        )
        self.text_widget.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 配置文本标签
        self.text_widget.tag_configure(
            "highlight",
            background="yellow",
            foreground="black",
            font=("Consolas", 10, "bold")
        )

        self.text_widget.tag_configure(
            "keyword",
            background="#FFD700",
            foreground="red",
            font=("Consolas", 11, "bold")
        )

        # 状态栏
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(5, 0))

        self.status_label = ttk.Label(
            status_frame,
            text="",
            font=("Arial", 9),
            foreground="gray"
        )
        self.status_label.pack(side=tk.LEFT)

    def _load_content(self):
        """加载文档内容"""
        try:
            # 检查文件是否存在
            file_exists = os.path.exists(self.file_path)

            if file_exists:
                self.file_exists_label.config(
                    text="✓ 文件存在",
                    foreground="green"
                )
            else:
                self.file_exists_label.config(
                    text="⚠ 文件已删除（显示数据库中的内容）",
                    foreground="orange"
                )

            # 从数据库读取内容
            content = self._get_content_from_database()

            if not content:
                # 如果数据库中没有内容，尝试从文件读取
                if file_exists:
                    content = self._get_content_from_file()
                else:
                    self.text_widget.insert(
                        tk.END,
                        "无法加载内容：文件不存在且数据库中没有保存内容。"
                    )
                    self.text_widget.config(state=tk.DISABLED)
                    return

            # 显示内容
            self.text_widget.insert(tk.END, content)

            # 高亮搜索关键词
            if self.search_query:
                self._highlight_keywords(content)

            # 禁用编辑
            self.text_widget.config(state=tk.DISABLED)

            # 更新状态
            lines = content.count('\n') + 1
            chars = len(content)
            self.status_label.config(
                text=f"共 {lines} 行, {chars} 个字符"
            )

        except Exception as e:
            messagebox.showerror(
                "错误",
                f"加载内容失败: {e}",
                parent=self.dialog
            )

    def _get_content_from_database(self) -> Optional[str]:
        """
        从数据库读取内容

        Returns:
            str: 文档内容
        """
        try:
            # 查询 FTS 表
            cursor = self.db_manager.connection.cursor()

            cursor.execute("""
                SELECT content
                FROM documents_fts
                WHERE rowid = ?
            """, (self.doc_id,))

            result = cursor.fetchone()

            if result and result['content']:
                return result['content']

            return None

        except Exception as e:
            print(f"从数据库读取内容失败: {e}")
            return None

    def _get_content_from_file(self) -> Optional[str]:
        """
        从文件读取内容

        Returns:
            str: 文件内容
        """
        try:
            # 尝试不同的编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']

            for encoding in encodings:
                try:
                    with open(self.file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                        return content
                except (UnicodeDecodeError, LookupError):
                    continue

            # 如果所有编码都失败，以二进制模式读取
            with open(self.file_path, 'rb') as f:
                raw_content = f.read()
                return raw_content.decode('utf-8', errors='replace')

        except Exception as e:
            print(f"从文件读取内容失败: {e}")
            return None

    def _highlight_keywords(self, content: str):
        """
        高亮显示关键词

        Args:
            content: 文档内容
        """
        if not self.search_query:
            return

        # 分割搜索查询为多个关键词
        keywords = self.search_query.strip().split()

        highlight_count = 0

        for keyword in keywords:
            if not keyword:
                continue

            # 不区分大小写搜索
            start_index = "1.0"

            while True:
                # 查找关键词
                pos = self.text_widget.search(
                    keyword,
                    start_index,
                    stopindex=tk.END,
                    nocase=True
                )

                if not pos:
                    break

                # 计算结束位置
                end_pos = f"{pos}+{len(keyword)}c"

                # 添加高亮标签
                self.text_widget.tag_add("keyword", pos, end_pos)

                highlight_count += 1

                # 移动到下一个位置
                start_index = end_pos

        # 更新搜索信息
        if highlight_count > 0:
            self.search_info_label.config(
                text=f"🔍 找到 {highlight_count} 处匹配: '{self.search_query}'"
            )

            # 滚动到第一个匹配位置
            first_match = self.text_widget.tag_ranges("keyword")
            if first_match:
                self.text_widget.see(first_match[0])

    def _open_original_file(self):
        """打开原始文件"""
        if not os.path.exists(self.file_path):
            messagebox.showwarning(
                "警告",
                "文件不存在，无法打开。",
                parent=self.dialog
            )
            return

        try:
            import os
            os.startfile(self.file_path)
        except Exception as e:
            messagebox.showerror(
                "错误",
                f"无法打开文件: {e}",
                parent=self.dialog
            )

    def _open_folder(self):
        """打开所在文件夹"""
        folder = os.path.dirname(self.file_path)

        if not os.path.exists(folder):
            messagebox.showwarning(
                "警告",
                "文件夹不存在。",
                parent=self.dialog
            )
            return

        try:
            import os
            os.startfile(folder)
        except Exception as e:
            messagebox.showerror(
                "错误",
                f"无法打开文件夹: {e}",
                parent=self.dialog
            )

    def show(self):
        """显示对话框"""
        self.dialog.wait_window()


def show_content_preview(parent, db_manager, doc_id: int, file_path: str, search_query: str = ""):
    """
    显示内容预览对话框

    Args:
        parent: 父窗口
        db_manager: 数据库管理器
        doc_id: 文档 ID
        file_path: 文件路径
        search_query: 搜索关键词
    """
    dialog = ContentPreviewDialog(parent, db_manager, doc_id, file_path, search_query)
    dialog.show()
