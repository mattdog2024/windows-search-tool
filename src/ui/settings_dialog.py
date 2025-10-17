"""
设置对话框

Story 2.5: 设置对话框
- 索引配置
- 搜索配置
- OCR 配置
- 界面配置
"""

import tkinter as tk
from tkinter import ttk, filedialog
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SettingsDialog:
    """
    应用设置对话框

    提供各种配置选项
    """

    def __init__(self, parent, config_manager):
        """
        初始化对话框

        Args:
            parent: 父窗口
            config_manager: 配置管理器
        """
        self.parent = parent
        self.config = config_manager
        self.result = False

        # 创建窗口
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("设置")
        self.dialog.geometry("600x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_widgets()
        self._load_settings()

    def _create_widgets(self):
        """创建控件"""
        # 主框架
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 使用 Notebook 创建选项卡
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)

        # 索引设置页
        self._create_index_tab(notebook)

        # 搜索设置页
        self._create_search_tab(notebook)

        # OCR 设置页
        self._create_ocr_tab(notebook)

        # 界面设置页
        self._create_ui_tab(notebook)

        # 按钮框架
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
            text="应用",
            command=self._apply
        ).pack(side=tk.RIGHT, padx=5)

    def _create_index_tab(self, notebook):
        """创建索引设置页"""
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="索引")

        # 并行工作进程数
        ttk.Label(frame, text="并行工作进程数:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.parallel_workers = ttk.Spinbox(frame, from_=1, to=16, width=10)
        self.parallel_workers.grid(row=0, column=1, sticky=tk.W, padx=5)

        # 批处理大小
        ttk.Label(frame, text="批处理大小:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.batch_size = ttk.Spinbox(frame, from_=10, to=1000, increment=10, width=10)
        self.batch_size.grid(row=1, column=1, sticky=tk.W, padx=5)

        # 最大文件大小
        ttk.Label(frame, text="最大文件大小 (MB):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.max_file_size = ttk.Entry(frame, width=15)
        self.max_file_size.grid(row=2, column=1, sticky=tk.W, padx=5)

        # 排除扩展名
        ttk.Label(frame, text="排除扩展名:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.excluded_extensions = tk.Text(frame, width=40, height=3)
        self.excluded_extensions.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(frame, text="(用逗号分隔, 如: .exe,.dll)", font=("Arial", 8)).grid(
            row=4, column=1, sticky=tk.W, padx=5
        )

        # 排除路径
        ttk.Label(frame, text="排除路径:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.excluded_paths = tk.Text(frame, width=40, height=3)
        self.excluded_paths.grid(row=5, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(frame, text="(每行一个路径)", font=("Arial", 8)).grid(
            row=6, column=1, sticky=tk.W, padx=5
        )

    def _create_search_tab(self, notebook):
        """创建搜索设置页"""
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="搜索")

        # 每页结果数
        ttk.Label(frame, text="每页结果数:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.results_per_page = ttk.Spinbox(frame, from_=10, to=200, increment=10, width=10)
        self.results_per_page.grid(row=0, column=1, sticky=tk.W, padx=5)

        # 摘要长度
        ttk.Label(frame, text="摘要片段长度:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.snippet_length = ttk.Spinbox(frame, from_=50, to=500, increment=50, width=10)
        self.snippet_length.grid(row=1, column=1, sticky=tk.W, padx=5)

        # 缓存大小
        ttk.Label(frame, text="搜索缓存大小:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.cache_size = ttk.Spinbox(frame, from_=10, to=1000, increment=10, width=10)
        self.cache_size.grid(row=2, column=1, sticky=tk.W, padx=5)

        # 默认搜索模式
        ttk.Label(frame, text="默认搜索模式:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.default_search_mode = ttk.Combobox(
            frame,
            values=["全文搜索", "语义搜索", "混合搜索"],
            width=15,
            state="readonly"
        )
        self.default_search_mode.grid(row=3, column=1, sticky=tk.W, padx=5)

    def _create_ocr_tab(self, notebook):
        """创建 OCR 设置页"""
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="OCR")

        # Tesseract 路径
        ttk.Label(frame, text="Tesseract 路径:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.tesseract_path = ttk.Entry(frame, width=40)
        self.tesseract_path.grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Button(
            frame,
            text="浏览...",
            command=self._browse_tesseract
        ).grid(row=0, column=2, padx=5)

        # 置信度阈值
        ttk.Label(frame, text="置信度阈值 (%):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.ocr_confidence = ttk.Spinbox(frame, from_=0, to=100, increment=5, width=10)
        self.ocr_confidence.grid(row=1, column=1, sticky=tk.W, padx=5)

        # 支持语言
        ttk.Label(frame, text="支持语言:").grid(row=2, column=0, sticky=tk.W, pady=5)
        lang_frame = ttk.Frame(frame)
        lang_frame.grid(row=2, column=1, sticky=tk.W, padx=5)

        self.lang_chi = tk.BooleanVar(value=True)
        self.lang_eng = tk.BooleanVar(value=True)

        ttk.Checkbutton(lang_frame, text="中文 (chi_sim)", variable=self.lang_chi).pack(anchor=tk.W)
        ttk.Checkbutton(lang_frame, text="英文 (eng)", variable=self.lang_eng).pack(anchor=tk.W)

    def _create_ui_tab(self, notebook):
        """创建界面设置页"""
        frame = ttk.Frame(notebook, padding=10)
        notebook.add(frame, text="界面")

        # 主题
        ttk.Label(frame, text="界面主题:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.theme = ttk.Combobox(
            frame,
            values=["浅色", "深色"],
            width=15,
            state="readonly"
        )
        self.theme.grid(row=0, column=1, sticky=tk.W, padx=5)

        # 字体大小
        ttk.Label(frame, text="字体大小:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.font_size = ttk.Spinbox(frame, from_=8, to=20, width=10)
        self.font_size.grid(row=1, column=1, sticky=tk.W, padx=5)

    def _browse_tesseract(self):
        """浏览 Tesseract 路径"""
        path = filedialog.askopenfilename(
            title="选择 Tesseract 可执行文件",
            filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")]
        )
        if path:
            self.tesseract_path.delete(0, tk.END)
            self.tesseract_path.insert(0, path)

    def _load_settings(self):
        """加载当前设置"""
        # 索引设置
        self.parallel_workers.set(self.config.get('indexing.parallel_workers', 4))
        self.batch_size.set(self.config.get('indexing.batch_size', 100))
        self.max_file_size.insert(0, str(self.config.get('indexing.max_file_size_mb', 100)))

        excluded_exts = self.config.get('indexing.excluded_extensions', [])
        self.excluded_extensions.insert('1.0', ','.join(excluded_exts))

        excluded_paths = self.config.get('indexing.excluded_paths', [])
        self.excluded_paths.insert('1.0', '\n'.join(excluded_paths))

        # 搜索设置
        self.results_per_page.set(self.config.get('search.results_per_page', 20))
        self.snippet_length.set(self.config.get('search.snippet_length', 100))
        self.cache_size.set(self.config.get('search.cache_size', 100))
        self.default_search_mode.set("全文搜索")

        # OCR 设置
        tesseract = self.config.get('ocr.tesseract_path', '')
        if tesseract:
            self.tesseract_path.insert(0, tesseract)
        self.ocr_confidence.set(self.config.get('ocr.confidence_threshold', 60))

        # 界面设置
        self.theme.set("浅色")
        self.font_size.set(10)

    def _apply(self):
        """应用设置"""
        try:
            # 保存索引设置
            self.config.set('indexing.parallel_workers', int(self.parallel_workers.get()))
            self.config.set('indexing.batch_size', int(self.batch_size.get()))
            self.config.set('indexing.max_file_size_mb', int(self.max_file_size.get()))

            # 排除扩展名
            exts_text = self.excluded_extensions.get('1.0', tk.END).strip()
            exts = [e.strip() for e in exts_text.split(',') if e.strip()]
            self.config.set('indexing.excluded_extensions', exts)

            # 排除路径
            paths_text = self.excluded_paths.get('1.0', tk.END).strip()
            paths = [p.strip() for p in paths_text.split('\n') if p.strip()]
            self.config.set('indexing.excluded_paths', paths)

            # 保存搜索设置
            self.config.set('search.results_per_page', int(self.results_per_page.get()))
            self.config.set('search.snippet_length', int(self.snippet_length.get()))
            self.config.set('search.cache_size', int(self.cache_size.get()))

            # 保存 OCR 设置
            tesseract = self.tesseract_path.get().strip()
            if tesseract:
                self.config.set('ocr.tesseract_path', tesseract)
            self.config.set('ocr.confidence_threshold', int(self.ocr_confidence.get()))

            # 保存配置文件
            self.config.save()

            self.result = True
            logger.info("Settings saved successfully")

        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            tk.messagebox.showerror("错误", f"保存设置失败: {e}")

    def _ok(self):
        """确定按钮"""
        self._apply()
        self.dialog.destroy()

    def _cancel(self):
        """取消按钮"""
        self.dialog.destroy()

    def show(self) -> bool:
        """
        显示对话框

        Returns:
            是否保存了设置
        """
        self.dialog.wait_window()
        return self.result


def show_settings(parent, config_manager) -> bool:
    """
    显示设置对话框

    Args:
        parent: 父窗口
        config_manager: 配置管理器

    Returns:
        是否保存了设置
    """
    dialog = SettingsDialog(parent, config_manager)
    return dialog.show()
