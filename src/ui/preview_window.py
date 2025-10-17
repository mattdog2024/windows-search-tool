"""
文档预览窗口

Story 2.3: 搜索结果预览功能
- 显示文档内容
- 语法高亮
- 搜索关键词高亮
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PreviewWindow:
    """
    文档预览窗口

    显示搜索结果的文档内容预览
    """

    def __init__(self, parent, file_path: str, search_query: str = ""):
        """
        初始化预览窗口

        Args:
            parent: 父窗口
            file_path: 文件路径
            search_query: 搜索关键词(用于高亮)
        """
        self.parent = parent
        self.file_path = file_path
        self.search_query = search_query.lower()

        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title(f"预览 - {file_path.split('\\')[-1]}")
        self.window.geometry("800x600")

        self._create_widgets()
        self._load_content()

    def _create_widgets(self):
        """创建控件"""
        # 工具栏
        toolbar = ttk.Frame(self.window)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # 文件路径标签
        path_label = ttk.Label(
            toolbar,
            text=f"文件: {self.file_path}",
            font=("Arial", 9)
        )
        path_label.pack(side=tk.LEFT, padx=5)

        # 关闭按钮
        close_btn = ttk.Button(
            toolbar,
            text="关闭",
            command=self.window.destroy
        )
        close_btn.pack(side=tk.RIGHT, padx=5)

        # 文本区域
        text_frame = ttk.Frame(self.window)
        text_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 使用 ScrolledText
        self.text_widget = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            padx=10,
            pady=10
        )
        self.text_widget.pack(fill=tk.BOTH, expand=True)

        # 配置标签样式
        self.text_widget.tag_configure(
            "highlight",
            background="yellow",
            foreground="black"
        )

    def _load_content(self):
        """加载文件内容"""
        try:
            # 尝试读取文件
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 插入内容
            self.text_widget.insert(tk.END, content)

            # 高亮搜索关键词
            if self.search_query:
                self._highlight_keywords()

            # 设置为只读
            self.text_widget.config(state=tk.DISABLED)

        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                with open(self.file_path, 'r', encoding='gbk') as f:
                    content = f.read()
                self.text_widget.insert(tk.END, content)
                if self.search_query:
                    self._highlight_keywords()
                self.text_widget.config(state=tk.DISABLED)
            except Exception as e:
                self.text_widget.insert(
                    tk.END,
                    f"无法读取文件(二进制格式或不支持的编码)\n\n错误: {e}"
                )
                self.text_widget.config(state=tk.DISABLED)

        except Exception as e:
            logger.error(f"Failed to load file: {e}")
            self.text_widget.insert(
                tk.END,
                f"加载文件失败: {e}"
            )
            self.text_widget.config(state=tk.DISABLED)

    def _highlight_keywords(self):
        """高亮显示搜索关键词"""
        if not self.search_query:
            return

        # 获取文本内容
        content = self.text_widget.get("1.0", tk.END).lower()

        # 查找所有匹配位置
        start_index = "1.0"
        while True:
            # 搜索关键词
            pos = self.text_widget.search(
                self.search_query,
                start_index,
                stopindex=tk.END,
                nocase=True
            )

            if not pos:
                break

            # 计算结束位置
            end_pos = f"{pos}+{len(self.search_query)}c"

            # 应用高亮标签
            self.text_widget.tag_add("highlight", pos, end_pos)

            # 移动到下一个位置
            start_index = end_pos

        logger.info(f"Highlighted keyword: {self.search_query}")


def show_preview(parent, file_path: str, search_query: str = ""):
    """
    显示文档预览窗口

    Args:
        parent: 父窗口
        file_path: 文件路径
        search_query: 搜索关键词
    """
    PreviewWindow(parent, file_path, search_query)
