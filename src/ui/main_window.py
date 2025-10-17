"""
主窗口 - Windows Search Tool

Story 2.1: 设计并实现主窗口框架
- 现代化的 UI 设计
- 搜索框和结果展示
- 设置和索引管理
- 状态栏显示
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
from typing import Optional, Callable, List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class MainWindow:
    """
    主窗口类

    功能:
    1. 搜索界面
    2. 结果展示
    3. 索引管理
    4. 设置配置
    """

    def __init__(
        self,
        library_manager=None,
        title: str = "Windows Search Tool",
        width: int = 900,
        height: int = 600
    ):
        """
        初始化主窗口

        Args:
            library_manager: 索引库管理器实例
            title: 窗口标题
            width: 窗口宽度
            height: 窗口高度
        """
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry(f"{width}x{height}")

        # 设置最小窗口大小
        self.root.minsize(800, 500)

        # 索引库管理器
        self.library_manager = library_manager

        # 回调函数
        self.on_search_callback: Optional[Callable] = None
        self.on_index_callback: Optional[Callable] = None
        self.on_update_index_callback: Optional[Callable] = None  # 增量更新回调
        self.on_settings_callback: Optional[Callable] = None
        self.on_new_index_callback: Optional[Callable] = None
        self.on_open_index_callback: Optional[Callable] = None
        self.on_content_preview_callback: Optional[Callable] = None
        self.on_library_change_callback: Optional[Callable] = None  # 索引库变化回调

        # 当前搜索关键词
        self.current_search_query: str = ""

        # 组件
        self.search_entry: Optional[ttk.Combobox] = None  # 改为 Combobox 支持历史
        self.results_tree: Optional[ttk.Treeview] = None
        self.status_label: Optional[tk.Label] = None
        self.progress_bar: Optional[ttk.Progressbar] = None
        self.quick_access_panel = None
        self.preview_text: Optional[tk.Text] = None  # 预览文本框
        self.preview_info_label: Optional[ttk.Label] = None  # 预览信息标签
        self.preview_panel: Optional[ttk.Frame] = None  # 预览面板
        self.library_selector = None  # 索引库选择器

        # 数据库管理器引用(用于从数据库读取内容)
        self._db_manager_ref = None

        # 搜索过滤器
        self.search_filters: Dict[str, Any] = {}

        # 搜索历史
        from src.ui.search_history import get_search_history
        self.search_history = get_search_history()

        # 创建 UI
        self._create_menu()
        self._create_toolbar()
        self._create_main_area()  # 包含快捷访问面板和搜索/结果区域
        self._create_status_bar()

        # 绑定快捷键
        self._bind_shortcuts()

        logger.info("Main window initialized")

    def _create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件(F)", menu=file_menu)
        file_menu.add_command(label="新建索引...", command=self._new_index)
        file_menu.add_command(label="打开索引...", command=self._open_index)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.root.quit)

        # 编辑菜单
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="编辑(E)", menu=edit_menu)
        edit_menu.add_command(label="设置...", command=self._open_settings)

        # 视图菜单
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="视图(V)", menu=view_menu)
        view_menu.add_command(label="搜索历史...", command=self._show_search_history)
        view_menu.add_separator()
        view_menu.add_command(label="刷新", command=self._refresh)

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助(H)", menu=help_menu)
        help_menu.add_command(label="关于", command=self._show_about)

    def _create_toolbar(self):
        """创建工具栏"""
        toolbar_frame = ttk.Frame(self.root)
        toolbar_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # 索引按钮
        ttk.Button(
            toolbar_frame,
            text="📁 添加目录",
            command=self._add_directory
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            toolbar_frame,
            text="🔄 更新索引",
            command=self._update_index
        ).pack(side=tk.LEFT, padx=2)

        # 分隔符
        ttk.Separator(toolbar_frame, orient=tk.VERTICAL).pack(
            side=tk.LEFT,
            fill=tk.Y,
            padx=5
        )

        # 搜索模式
        ttk.Label(toolbar_frame, text="搜索模式:").pack(side=tk.LEFT, padx=5)

        self.search_mode = tk.StringVar(value="fts")
        ttk.Radiobutton(
            toolbar_frame,
            text="全文搜索",
            variable=self.search_mode,
            value="fts"
        ).pack(side=tk.LEFT, padx=2)

        ttk.Radiobutton(
            toolbar_frame,
            text="语义搜索",
            variable=self.search_mode,
            value="semantic"
        ).pack(side=tk.LEFT, padx=2)

        ttk.Radiobutton(
            toolbar_frame,
            text="混合搜索",
            variable=self.search_mode,
            value="hybrid"
        ).pack(side=tk.LEFT, padx=2)

    def _create_main_area(self):
        """创建主区域(包含快捷访问面板和搜索/结果区域)"""
        # 创建主容器
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # 左侧快捷访问面板
        from src.ui.quick_access_panel import QuickAccessPanel
        self.quick_access_panel = QuickAccessPanel(
            main_container,
            on_file_open=self._open_file_from_path
        )
        main_container.add(self.quick_access_panel, weight=0)

        # 右侧搜索和结果区域
        right_frame = ttk.Frame(main_container)
        main_container.add(right_frame, weight=1)

        # 在右侧框架中创建搜索区域和结果区域
        self._create_search_area_in_frame(right_frame)
        self._create_results_area_in_frame(right_frame)

    def _create_search_area_in_frame(self, parent):
        """在指定父框架中创建搜索区域"""
        # 索引库选择器（在搜索框上方）
        if self.library_manager:
            from src.ui.index_library_selector import IndexLibrarySelector
            self.library_selector = IndexLibrarySelector(
                parent,
                self.library_manager,
                on_selection_changed=self._on_library_selection_changed
            )
            self.library_selector.pack(side=tk.TOP, fill=tk.X, padx=10, pady=(5, 0))

        search_frame = ttk.Frame(parent)
        search_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

        # 搜索标签
        ttk.Label(search_frame, text="🔍 搜索:", font=("Arial", 11)).pack(
            side=tk.LEFT,
            padx=5
        )

        # 搜索输入框 (改为 Combobox 支持历史记录)
        self.search_entry = ttk.Combobox(search_frame, font=("Arial", 11))
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.search_entry.bind('<Return>', lambda e: self._perform_search())
        self.search_entry.bind('<KeyRelease>', self._on_search_key_release)
        self.search_entry.focus()

        # 加载搜索历史
        self._update_search_history_dropdown()

        # 搜索按钮
        ttk.Button(
            search_frame,
            text="搜索",
            command=self._perform_search
        ).pack(side=tk.LEFT, padx=5)

        # 高级搜索按钮
        ttk.Button(
            search_frame,
            text="高级搜索",
            command=self._advanced_search
        ).pack(side=tk.LEFT, padx=2)

        # 清空按钮
        ttk.Button(
            search_frame,
            text="清空",
            command=self._clear_search
        ).pack(side=tk.LEFT, padx=2)

    def _create_results_area_in_frame(self, parent):
        """在指定父框架中创建结果展示区域(包含结果列表和预览面板)"""
        results_frame = ttk.Frame(parent)
        results_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

        # 创建水平分隔窗口(左侧结果列表,右侧预览面板)
        paned_window = ttk.PanedWindow(results_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)

        # === 左侧:搜索结果列表 ===
        left_frame = ttk.Frame(paned_window)
        paned_window.add(left_frame, weight=2)

        # 标题
        ttk.Label(
            left_frame,
            text="搜索结果:",
            font=("Arial", 10, "bold")
        ).pack(side=tk.TOP, anchor=tk.W, pady=5)

        # 创建 Treeview 容器
        tree_frame = ttk.Frame(left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # 创建 Treeview（添加"索引库"列）
        columns = ("文件名", "路径", "索引库", "大小", "修改时间", "相似度")
        self.results_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="tree headings",
            selectmode="browse"
        )

        # 设置列
        self.results_tree.heading("#0", text="序号")
        self.results_tree.column("#0", width=50, minwidth=50)

        for col in columns:
            self.results_tree.heading(col, text=col)

        self.results_tree.column("文件名", width=200)
        self.results_tree.column("路径", width=250)
        self.results_tree.column("索引库", width=100)
        self.results_tree.column("大小", width=80)
        self.results_tree.column("修改时间", width=120)
        self.results_tree.column("相似度", width=80)

        # 滚动条
        scrollbar_y = ttk.Scrollbar(
            tree_frame,
            orient=tk.VERTICAL,
            command=self.results_tree.yview
        )
        scrollbar_x = ttk.Scrollbar(
            tree_frame,
            orient=tk.HORIZONTAL,
            command=self.results_tree.xview
        )

        self.results_tree.configure(
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set
        )

        # 布局
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        # 双击打开文件
        self.results_tree.bind('<Double-1>', self._open_file)

        # 选中项变化时更新预览
        self.results_tree.bind('<<TreeviewSelect>>', self._on_result_selected)

        # 右键菜单
        self._create_context_menu()

        # === 右侧:内容预览面板 ===
        right_frame = ttk.Frame(paned_window)
        paned_window.add(right_frame, weight=1)

        # 预览面板标题
        preview_header = ttk.Frame(right_frame)
        preview_header.pack(side=tk.TOP, fill=tk.X, pady=5)

        ttk.Label(
            preview_header,
            text="内容预览:",
            font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT)

        # 文件信息标签
        self.preview_info_label = ttk.Label(
            preview_header,
            text="",
            font=("Arial", 8),
            foreground="gray"
        )
        self.preview_info_label.pack(side=tk.LEFT, padx=10)

        # 预览文本框
        preview_text_frame = ttk.Frame(right_frame)
        preview_text_frame.pack(fill=tk.BOTH, expand=True)

        self.preview_text = tk.Text(
            preview_text_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#f8f8f8"
        )

        preview_scrollbar = ttk.Scrollbar(
            preview_text_frame,
            orient=tk.VERTICAL,
            command=self.preview_text.yview
        )
        self.preview_text.configure(yscrollcommand=preview_scrollbar.set)

        self.preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        preview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 配置文本高亮标签
        self.preview_text.tag_config("keyword", background="#ffff00", foreground="#000000")
        self.preview_text.tag_config("keyword_alt", background="#ffcccc", foreground="#000000")

        # 创建预览文本的右键菜单
        self.preview_context_menu = tk.Menu(self.root, tearoff=0)
        self.preview_context_menu.add_command(label="复制", command=self._copy_preview_text)
        self.preview_context_menu.add_command(label="全选", command=self._select_all_preview)

        # 绑定右键菜单
        self.preview_text.bind('<Button-3>', self._show_preview_context_menu)

        # 绑定快捷键用于复制和全选
        self.preview_text.bind('<Control-c>', lambda e: self._handle_preview_copy())
        self.preview_text.bind('<Control-a>', lambda e: self._handle_preview_select_all())

        # 禁用所有其他键盘输入（保护只读状态）
        def block_edit(event):
            # 允许的操作：Ctrl+C, Ctrl+A, 方向键, Home, End, PageUp, PageDown
            allowed_keys = ('Left', 'Right', 'Up', 'Down', 'Home', 'End', 'Prior', 'Next')
            # 检查是否是 Ctrl+C 或 Ctrl+A
            if event.state & 0x4:  # Ctrl 键按下
                if event.keysym in ('c', 'C', 'a', 'A'):
                    return  # 允许
            # 允许方向键等导航键
            if event.keysym in allowed_keys:
                return
            # 阻止其他所有键
            return 'break'

        self.preview_text.bind('<Key>', block_edit)

        # 存储预览文本组件的引用
        self.preview_panel = right_frame

    def _create_context_menu(self):
        """创建右键菜单"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="预览", command=self._preview_file)
        self.context_menu.add_command(label="打开", command=self._open_file)
        self.context_menu.add_command(label="打开所在文件夹", command=self._open_folder)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="添加到收藏", command=self._add_to_favorites)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="复制路径", command=self._copy_path)

        self.results_tree.bind('<Button-3>', self._show_context_menu)

    def _create_status_bar(self):
        """创建状态栏"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # 状态标签
        self.status_label = ttk.Label(
            status_frame,
            text="就绪",
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, pady=2)

        # 进度条 (改为确定模式，显示真实进度)
        self.progress_bar = ttk.Progressbar(
            status_frame,
            mode='determinate',
            length=200,
            maximum=100
        )
        self.progress_bar.pack(side=tk.RIGHT, padx=5, pady=2)
        self.progress_bar['value'] = 0  # 初始隐藏

    def _bind_shortcuts(self):
        """绑定快捷键"""
        # 搜索相关
        self.root.bind('<Control-f>', lambda e: self.search_entry.focus())
        self.root.bind('<Control-h>', lambda e: self._show_search_history())
        self.root.bind('<Escape>', lambda e: self._clear_search())

        # 索引相关
        self.root.bind('<Control-n>', lambda e: self._new_index())
        self.root.bind('<Control-o>', lambda e: self._open_index())
        self.root.bind('<Control-i>', lambda e: self._add_directory())

        # 视图相关
        self.root.bind('<F5>', lambda e: self._refresh())
        self.root.bind('<Control-comma>', lambda e: self._open_settings())

        # 文件操作
        self.root.bind('<Return>', lambda e: self._open_selected_file())
        # Ctrl+C 只在结果树有焦点时复制路径
        self.root.bind('<Control-c>', lambda e: self._copy_path() if self.root.focus_get() == self.results_tree else None)
        self.root.bind('<Control-d>', lambda e: self._add_to_favorites())

    def _update_search_history_dropdown(self):
        """更新搜索历史下拉列表"""
        recent = self.search_history.get_recent_searches(limit=20)
        queries = [item['query'] for item in recent]
        self.search_entry['values'] = queries

    def _on_library_selection_changed(self):
        """当索引库选择变化时的回调"""
        logger.info("Library selection changed")
        # 清除当前搜索结果（因为搜索范围变化了）
        self.clear_results()
        self._clear_preview()
        self.set_status(f"搜索范围已更新: {self.library_manager.get_selection_summary()}")

        # 通知控制器更新窗口标题
        if self.on_library_change_callback:
            self.on_library_change_callback()

    def _on_search_key_release(self, event):
        """搜索框按键释放事件 - 提供自动完成建议"""
        # 忽略特殊键
        if event.keysym in ('Return', 'Tab', 'Up', 'Down', 'Left', 'Right'):
            return

        current_text = self.search_entry.get()

        if len(current_text) >= 2:
            # 获取建议
            suggestions = self.search_history.get_suggestions(current_text, limit=10)

            if suggestions:
                self.search_entry['values'] = suggestions
            else:
                # 如果没有建议,显示最近搜索
                self._update_search_history_dropdown()

    def _show_search_history(self):
        """显示搜索历史对话框"""
        from src.ui.search_history_dialog import show_search_history_dialog

        selected_query = show_search_history_dialog(self.root, self.search_history)

        if selected_query:
            self.search_entry.set(selected_query)
            self._perform_search()

    # === 回调方法 ===

    def set_search_callback(self, callback: Callable):
        """设置搜索回调"""
        self.on_search_callback = callback

    def set_index_callback(self, callback: Callable):
        """设置索引回调"""
        self.on_index_callback = callback

    def set_update_index_callback(self, callback: Callable):
        """设置更新索引回调"""
        self.on_update_index_callback = callback

    def set_settings_callback(self, callback: Callable):
        """设置配置回调"""
        self.on_settings_callback = callback

    def set_new_index_callback(self, callback: Callable):
        """设置新建索引回调"""
        self.on_new_index_callback = callback

    def set_open_index_callback(self, callback: Callable):
        """设置打开索引回调"""
        self.on_open_index_callback = callback

    def set_content_preview_callback(self, callback: Callable):
        """设置内容预览回调"""
        self.on_content_preview_callback = callback

    def set_library_change_callback(self, callback: Callable):
        """设置索引库选择变化回调"""
        self.on_library_change_callback = callback

    def set_db_manager(self, db_manager):
        """
        设置数据库管理器引用(用于预览面板从数据库读取内容)

        Args:
            db_manager: 数据库管理器实例
        """
        self._db_manager_ref = db_manager

    # === 事件处理 ===

    def _perform_search(self):
        """执行搜索"""
        query = self.search_entry.get().strip()

        if not query:
            messagebox.showwarning("警告", "请输入搜索关键词")
            return

        mode = self.search_mode.get()

        # 保存当前搜索关键词
        self.current_search_query = query

        logger.info(f"Searching for: {query}, mode: {mode}")
        self.set_status(f"正在搜索: {query}")
        self.progress_bar.start()

        # 调用回调
        if self.on_search_callback:
            try:
                results = self.on_search_callback(query, mode)
                self.display_results(results)
                self.set_status(f"找到 {len(results)} 个结果")

                # 记录到搜索历史
                self.search_history.add_search(query, mode, len(results))
                self._update_search_history_dropdown()

            except Exception as e:
                logger.error(f"Search failed: {e}")
                messagebox.showerror("错误", f"搜索失败: {e}")
                self.set_status("搜索失败")
            finally:
                self.progress_bar.stop()
        else:
            self.progress_bar.stop()
            self.set_status("搜索功能未实现")

    def _advanced_search(self):
        """高级搜索"""
        from src.ui.advanced_search import show_advanced_search

        filters = show_advanced_search(self.root)

        if filters:
            # 将过滤条件保存,在搜索时使用
            self.search_filters = filters
            messagebox.showinfo("提示", f"已设置 {len(filters)} 个过滤条件")
        else:
            self.search_filters = {}

    def _clear_search(self):
        """清空搜索"""
        self.search_entry.delete(0, tk.END)
        self.clear_results()
        self.search_filters = {}
        self.set_status("就绪")

    def _add_directory(self):
        """添加目录到索引"""
        directory = filedialog.askdirectory(title="选择要索引的目录")

        if directory:
            logger.info(f"Adding directory to index: {directory}")

            if self.on_index_callback:
                try:
                    # 调用回调，后台线程会自己处理进度显示
                    self.on_index_callback(directory)
                except Exception as e:
                    logger.error(f"Indexing failed: {e}")
                    messagebox.showerror("错误", f"索引失败: {e}")
                    self.set_status("索引失败")
            else:
                self.set_status("索引功能未实现")

    def _update_index(self):
        """更新索引（增量更新）"""
        # 获取当前索引的所有目录
        response = messagebox.askyesno(
            "确认更新索引",
            "是否对当前索引库进行增量更新？\n\n"
            "增量更新会检测文件变化：\n"
            "- 添加新文件\n"
            "- 更新已修改的文件\n"
            "- 移除已删除的文件"
        )

        if response:
            # 调用更新索引回调（需要添加新的回调）
            if hasattr(self, 'on_update_index_callback') and self.on_update_index_callback:
                self.on_update_index_callback()
            else:
                # 兼容旧的实现：使用 on_index_callback
                messagebox.showinfo(
                    "提示",
                    "增量更新功能需要配置更新回调。\n"
                    "请使用 '添加目录' 功能重新索引。"
                )

    def _new_index(self):
        """新建索引"""
        if self.on_new_index_callback:
            self.on_new_index_callback()
        else:
            messagebox.showinfo("提示", "新建索引功能未实现")

    def _open_index(self):
        """打开索引"""
        if self.on_open_index_callback:
            self.on_open_index_callback()
        else:
            messagebox.showinfo("提示", "打开索引功能未实现")

    def _open_settings(self):
        """打开设置"""
        if self.on_settings_callback:
            self.on_settings_callback()
        else:
            messagebox.showinfo("提示", "设置功能开发中")

    def _refresh(self):
        """刷新"""
        self.set_status("刷新中...")
        # TODO: 实现刷新逻辑
        self.set_status("就绪")

    def _show_about(self):
        """显示关于信息"""
        about_text = """Windows Search Tool v0.1.0

智能文件内容索引和搜索系统

快捷键:
  Ctrl+F    - 聚焦搜索框
  Ctrl+H    - 搜索历史
  Esc       - 清空搜索
  Ctrl+I    - 添加目录索引
  F5        - 刷新
  Ctrl+,    - 打开设置
  Enter     - 打开选中文件/执行搜索
  Ctrl+C    - 复制路径
  Ctrl+D    - 添加到收藏

© 2025
"""
        messagebox.showinfo("关于", about_text)

    def _preview_file(self):
        """预览文件"""
        selection = self.results_tree.selection()
        if not selection:
            return

        item = self.results_tree.item(selection[0])
        file_path = item['values'][1]  # 路径列

        # 从 tags 中提取文档 ID
        tags = item.get('tags', [])
        doc_id = 0
        for tag in tags:
            if tag.startswith('doc_id:'):
                try:
                    doc_id = int(tag.split(':', 1)[1])
                    break
                except ValueError:
                    pass

        # 调用内容预览回调
        if self.on_content_preview_callback:
            try:
                self.on_content_preview_callback(
                    doc_id=doc_id,
                    file_path=file_path,
                    search_query=self.current_search_query
                )
            except Exception as e:
                logger.error(f"Failed to preview file: {e}")
                messagebox.showerror("错误", f"无法预览文件: {e}")
        else:
            # 兼容旧的预览功能
            try:
                from src.ui.preview_window import show_preview
                show_preview(self.root, file_path, self.current_search_query)
            except Exception as e:
                logger.error(f"Failed to preview file: {e}")
                messagebox.showerror("错误", f"无法预览文件: {e}")

    def _open_file(self, event=None):
        """打开文件"""
        selection = self.results_tree.selection()
        if not selection:
            return

        item = self.results_tree.item(selection[0])
        file_path = item['values'][1]  # 路径列

        try:
            import os
            os.startfile(file_path)

            # 添加到最近文件
            file_name = item['values'][0]  # 文件名列
            if self.quick_access_panel:
                self.quick_access_panel.add_recent_file(file_path, file_name)

        except Exception as e:
            logger.error(f"Failed to open file: {e}")
            messagebox.showerror("错误", f"无法打开文件: {e}")

    def _open_file_from_path(self, file_path: str):
        """
        从路径打开文件(快捷访问面板回调)

        Args:
            file_path: 文件路径
        """
        try:
            import os
            os.startfile(file_path)
        except Exception as e:
            logger.error(f"Failed to open file: {e}")
            messagebox.showerror("错误", f"无法打开文件: {e}")

    def _open_selected_file(self):
        """打开选中的文件(快捷键触发)"""
        # 检查是否有焦点在结果树上
        if self.root.focus_get() == self.results_tree:
            self._open_file()
        # 如果焦点在搜索框,执行搜索
        elif self.root.focus_get() == self.search_entry:
            self._perform_search()

    def _open_folder(self):
        """打开所在文件夹"""
        selection = self.results_tree.selection()
        if not selection:
            return

        item = self.results_tree.item(selection[0])
        file_path = item['values'][1]

        try:
            import os
            folder_path = os.path.dirname(file_path)
            os.startfile(folder_path)
        except Exception as e:
            logger.error(f"Failed to open folder: {e}")
            messagebox.showerror("错误", f"无法打开文件夹: {e}")

    def _copy_path(self):
        """复制路径"""
        selection = self.results_tree.selection()
        if not selection:
            return

        item = self.results_tree.item(selection[0])
        file_path = item['values'][1]

        self.root.clipboard_clear()
        self.root.clipboard_append(file_path)
        self.set_status(f"已复制路径: {file_path}")

    def _add_to_favorites(self):
        """添加到收藏"""
        selection = self.results_tree.selection()
        if not selection:
            return

        item = self.results_tree.item(selection[0])
        file_name = item['values'][0]  # 文件名列
        file_path = item['values'][1]  # 路径列

        if self.quick_access_panel:
            self.quick_access_panel.add_favorite(file_path, file_name)
            self.set_status(f"已添加到收藏: {file_name}")
            messagebox.showinfo("提示", f"已添加到收藏: {file_name}")

    def _show_context_menu(self, event):
        """显示右键菜单"""
        # 选择点击的项
        item = self.results_tree.identify_row(event.y)
        if item:
            self.results_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def _on_result_selected(self, event=None):
        """当选中搜索结果时,自动更新内容预览"""
        selection = self.results_tree.selection()
        if not selection:
            self._clear_preview()
            return

        item = self.results_tree.item(selection[0])
        file_path = item['values'][1]  # 路径列
        file_name = item['values'][0]  # 文件名列
        library_name = item['values'][2]  # 索引库列

        # 从 tags 中提取文档 ID
        tags = item.get('tags', [])
        doc_id = 0
        for tag in tags:
            if tag.startswith('doc_id:'):
                try:
                    doc_id = int(tag.split(':', 1)[1])
                    break
                except ValueError:
                    pass

        # 更新预览
        self._update_preview(doc_id, file_path, file_name, library_name)

    def _update_preview(self, doc_id: int, file_path: str, file_name: str, library_name: str = ""):
        """
        更新预览面板内容

        Args:
            doc_id: 文档 ID
            file_path: 文件路径
            file_name: 文件名
            library_name: 索引库名称
        """
        # 更新文件信息
        file_exists = Path(file_path).exists()
        status_text = f"{file_name} {'[存在]' if file_exists else '[已删除]'}"
        self.preview_info_label.config(
            text=status_text,
            foreground="green" if file_exists else "red"
        )

        # 获取内容
        content = self._get_file_content(doc_id, file_path, library_name)

        if content is None:
            self._show_preview_error("无法读取文件内容")
            return

        # 显示内容并高亮关键词
        self._display_preview_content(content)

    def _get_file_content(self, doc_id: int, file_path: str, library_name: str = "") -> Optional[str]:
        """
        获取文件内容(优先从数据库读取)

        Args:
            doc_id: 文档 ID
            file_path: 文件路径
            library_name: 索引库名称

        Returns:
            文件内容,或 None 如果无法读取
        """
        # 根据库名获取正确的数据库路径
        db_manager_to_use = None

        if library_name and self.library_manager:
            # 获取指定库的信息
            library = self.library_manager.get_library(library_name)
            if library:
                # 为这个库创建临时数据库连接
                from src.data.db_manager import DBManager
                try:
                    db_manager_to_use = DBManager(library.db_path)
                except Exception as e:
                    logger.warning(f"Failed to create db_manager for library '{library_name}': {e}")

        # 如果没有指定库名或获取失败,使用默认的 db_manager
        if not db_manager_to_use and hasattr(self, '_db_manager_ref') and self._db_manager_ref:
            db_manager_to_use = self._db_manager_ref

        # 尝试从数据库读取
        if db_manager_to_use:
            try:
                cursor = db_manager_to_use.connection.cursor()
                cursor.execute("""
                    SELECT content
                    FROM documents_fts
                    WHERE rowid = ?
                """, (doc_id,))
                result = cursor.fetchone()

                # 如果是临时创建的连接,关闭它
                if library_name and db_manager_to_use != self._db_manager_ref:
                    db_manager_to_use.close()

                if result and result['content']:
                    content = result['content']
                    # 限制预览大小
                    if len(content) > 50000:  # 50KB
                        content = content[:50000] + "\n\n... [内容过长,已截断,仅显示前50000字符]"
                    return content
            except Exception as e:
                # 如果是临时创建的连接,确保关闭
                if library_name and db_manager_to_use and db_manager_to_use != self._db_manager_ref:
                    try:
                        db_manager_to_use.close()
                    except:
                        pass
                logger.warning(f"Failed to read from database: {e}")

        # 如果数据库读取失败，只对纯文本文件尝试从文件系统读取
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            return "[文件不存在]"

        # 检查文件扩展名,只对纯文本文件尝试读取
        file_ext = file_path_obj.suffix.lower()
        text_extensions = {'.txt', '.log', '.md', '.py', '.js', '.java', '.cpp', '.h', '.cs', '.xml', '.json', '.yml', '.yaml', '.ini', '.cfg', '.conf'}

        if file_ext not in text_extensions:
            return f"[{file_ext} 文件不支持直接预览,请从数据库查看提取的文本内容]"

        # 尝试从文件系统读取纯文本文件
        try:
            # 尝试多种编码
            for encoding in ['utf-8', 'gbk', 'gb2312', 'latin-1']:
                try:
                    with open(file_path_obj, 'r', encoding=encoding) as f:
                        content = f.read()
                        # 限制预览大小
                        if len(content) > 50000:  # 50KB
                            content = content[:50000] + "\n\n... [内容过长,已截断,仅显示前50000字符]"
                        return content
                except (UnicodeDecodeError, UnicodeError):
                    continue

            return "[无法解码文件内容,请检查文件编码]"

        except Exception as e:
            logger.error(f"Failed to read file: {e}")
            return f"[读取文件失败: {e}]"

    def _display_preview_content(self, content: str):
        """
        在预览面板中显示内容并高亮关键词

        Args:
            content: 文件内容
        """
        # 清空现有内容
        self.preview_text.delete(1.0, tk.END)

        # 插入内容
        self.preview_text.insert(1.0, content)

        # 高亮关键词
        if self.current_search_query:
            keywords = self.current_search_query.strip().split()
            for i, keyword in enumerate(keywords):
                tag_name = "keyword" if i % 2 == 0 else "keyword_alt"
                start_index = "1.0"
                while True:
                    pos = self.preview_text.search(
                        keyword,
                        start_index,
                        stopindex=tk.END,
                        nocase=True
                    )
                    if not pos:
                        break
                    end_pos = f"{pos}+{len(keyword)}c"
                    self.preview_text.tag_add(tag_name, pos, end_pos)
                    start_index = end_pos

            # 滚动到第一个匹配
            first_keyword = keywords[0] if keywords else ""
            if first_keyword:
                pos = self.preview_text.search(
                    first_keyword,
                    "1.0",
                    stopindex=tk.END,
                    nocase=True
                )
                if pos:
                    self.preview_text.see(pos)

    def _show_preview_error(self, message: str):
        """
        在预览面板显示错误信息

        Args:
            message: 错误信息
        """
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(1.0, f"错误: {message}")

    def _clear_preview(self):
        """清空预览面板"""
        self.preview_info_label.config(text="")
        self.preview_text.delete(1.0, tk.END)

    def _handle_preview_copy(self):
        """处理 Ctrl+C 复制快捷键"""
        try:
            # 获取选中的文本
            selected_text = self.preview_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selected_text:
                self.root.clipboard_clear()
                self.root.clipboard_append(selected_text)
                self.set_status(f"已复制 {len(selected_text)} 个字符")
                return 'break'  # 阻止默认行为
        except tk.TclError:
            # 没有选中文本，不复制
            pass
        return 'break'

    def _handle_preview_select_all(self):
        """处理 Ctrl+A 全选快捷键"""
        self.preview_text.tag_add(tk.SEL, "1.0", tk.END)
        self.preview_text.mark_set(tk.INSERT, "1.0")
        self.preview_text.see(tk.INSERT)
        return 'break'  # 阻止默认行为

    def _copy_preview_text(self):
        """复制预览文本中选中的内容（右键菜单）"""
        try:
            # 获取选中的文本
            selected_text = self.preview_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selected_text:
                self.root.clipboard_clear()
                self.root.clipboard_append(selected_text)
                self.set_status(f"已复制 {len(selected_text)} 个字符")
        except tk.TclError:
            # 如果没有选中文本，复制全部内容
            all_text = self.preview_text.get(1.0, tk.END)
            self.root.clipboard_clear()
            self.root.clipboard_append(all_text)
            self.set_status("已复制全部预览内容")

    def _select_all_preview(self):
        """全选预览文本（右键菜单）"""
        self.preview_text.tag_add(tk.SEL, "1.0", tk.END)
        self.preview_text.mark_set(tk.INSERT, "1.0")
        self.preview_text.see(tk.INSERT)

    def _show_preview_context_menu(self, event):
        """显示预览文本的右键菜单"""
        self.preview_context_menu.post(event.x_root, event.y_root)

    # === 公共方法 ===

    def display_results(self, results: List[Dict[str, Any]]):
        """
        显示搜索结果

        Args:
            results: 结果列表
        """
        # 清空现有结果
        self.clear_results()

        # 添加结果
        for i, result in enumerate(results, 1):
            doc_id = result.get('id', 0)
            file_name = result.get('file_name', '')
            file_path = result.get('file_path', '')
            library_name = result.get('library_name', '')  # 获取库名
            file_size = result.get('file_size', 0)
            modified_at = result.get('modified_at', '')
            similarity = result.get('similarity_score', result.get('score', ''))

            # 格式化大小
            size_str = self._format_size(file_size)

            # 格式化相似度
            similarity_str = f"{similarity:.2f}" if isinstance(similarity, (int, float)) else str(similarity)

            # 插入结果,使用 tags 存储文档 ID（添加库名列）
            item_id = self.results_tree.insert(
                '',
                'end',
                text=str(i),
                values=(file_name, file_path, library_name, size_str, modified_at, similarity_str),
                tags=(f'doc_id:{doc_id}',)
            )

        logger.info(f"Displayed {len(results)} results")

    def clear_results(self):
        """清空结果"""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

    def set_status(self, message: str):
        """设置状态栏消息"""
        self.status_label.config(text=message)
        logger.debug(f"Status: {message}")

    def show_progress(self, start: bool = True):
        """显示/隐藏进度条"""
        if start:
            self.progress_bar.start()
        else:
            self.progress_bar.stop()

    def update_progress_bar(self, percentage: int):
        """
        更新进度条

        Args:
            percentage: 进度百分比 (0-100)
        """
        if percentage <= 0:
            self.progress_bar['value'] = 0
        elif percentage >= 100:
            self.progress_bar['value'] = 100
        else:
            self.progress_bar['value'] = percentage

        # 强制刷新
        self.root.update_idletasks()

    def run(self):
        """运行应用"""
        logger.info("Starting main window")
        self.root.mainloop()

    def quit(self):
        """退出应用"""
        self.root.quit()

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 ** 2:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 ** 3:
            return f"{size_bytes / (1024 ** 2):.1f} MB"
        else:
            return f"{size_bytes / (1024 ** 3):.1f} GB"
