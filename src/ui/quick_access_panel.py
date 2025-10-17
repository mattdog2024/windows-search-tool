"""
快捷访问面板

Story 2.6: 搜索历史和快捷功能
- 显示最近打开的文件
- 收藏常用文件
- 快速访问
"""

import tkinter as tk
from tkinter import ttk
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class QuickAccessPanel(ttk.Frame):
    """
    快捷访问面板

    功能:
    1. 显示最近打开的文件
    2. 显示收藏的文件
    3. 快速访问和打开
    """

    def __init__(self, parent, on_file_open: Optional[Callable] = None):
        """
        初始化快捷访问面板

        Args:
            parent: 父窗口
            on_file_open: 文件打开回调
        """
        super().__init__(parent)

        self.on_file_open = on_file_open

        # 数据存储
        self.recent_files_path = "recent_files.json"
        self.favorites_path = "favorites.json"

        self.recent_files: List[Dict[str, Any]] = []
        self.favorites: List[Dict[str, Any]] = []

        # 创建 UI
        self._create_widgets()

        # 加载数据
        self._load_data()

        logger.info("Quick access panel initialized")

    def _create_widgets(self):
        """创建控件"""
        # 标题
        title_label = ttk.Label(
            self,
            text="快捷访问",
            font=("Arial", 11, "bold")
        )
        title_label.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # 使用 Notebook 创建选项卡
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 最近文件页
        self._create_recent_tab()

        # 收藏文件页
        self._create_favorites_tab()

    def _create_recent_tab(self):
        """创建最近文件页"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="最近")

        # 列表框
        self.recent_listbox = tk.Listbox(
            frame,
            font=("Arial", 9),
            activestyle='none'
        )
        self.recent_listbox.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # 滚动条
        scrollbar = ttk.Scrollbar(
            frame,
            orient=tk.VERTICAL,
            command=self.recent_listbox.yview
        )
        self.recent_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定事件
        self.recent_listbox.bind('<Double-1>', self._on_recent_double_click)
        self.recent_listbox.bind('<Button-3>', self._show_recent_context_menu)

        # 创建右键菜单
        self.recent_context_menu = tk.Menu(self, tearoff=0)
        self.recent_context_menu.add_command(
            label="打开",
            command=self._open_recent_file
        )
        self.recent_context_menu.add_command(
            label="添加到收藏",
            command=self._add_to_favorites_from_recent
        )
        self.recent_context_menu.add_separator()
        self.recent_context_menu.add_command(
            label="从列表移除",
            command=self._remove_recent_file
        )

    def _create_favorites_tab(self):
        """创建收藏文件页"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="收藏")

        # 列表框
        self.favorites_listbox = tk.Listbox(
            frame,
            font=("Arial", 9),
            activestyle='none'
        )
        self.favorites_listbox.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # 滚动条
        scrollbar = ttk.Scrollbar(
            frame,
            orient=tk.VERTICAL,
            command=self.favorites_listbox.yview
        )
        self.favorites_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 绑定事件
        self.favorites_listbox.bind('<Double-1>', self._on_favorite_double_click)
        self.favorites_listbox.bind('<Button-3>', self._show_favorites_context_menu)

        # 创建右键菜单
        self.favorites_context_menu = tk.Menu(self, tearoff=0)
        self.favorites_context_menu.add_command(
            label="打开",
            command=self._open_favorite_file
        )
        self.favorites_context_menu.add_separator()
        self.favorites_context_menu.add_command(
            label="取消收藏",
            command=self._remove_favorite_file
        )

    def add_recent_file(self, file_path: str, file_name: str = ""):
        """
        添加最近文件

        Args:
            file_path: 文件路径
            file_name: 文件名
        """
        if not file_name:
            file_name = Path(file_path).name

        # 检查是否已存在
        existing = [f for f in self.recent_files if f['path'] == file_path]
        if existing:
            # 移除旧记录
            self.recent_files = [f for f in self.recent_files if f['path'] != file_path]

        # 添加到开头
        self.recent_files.insert(0, {
            'path': file_path,
            'name': file_name,
            'timestamp': datetime.now().isoformat()
        })

        # 限制数量
        self.recent_files = self.recent_files[:20]

        # 更新显示
        self._update_recent_display()

        # 保存
        self._save_recent_files()

        logger.debug(f"Added recent file: {file_path}")

    def add_favorite(self, file_path: str, file_name: str = ""):
        """
        添加收藏文件

        Args:
            file_path: 文件路径
            file_name: 文件名
        """
        if not file_name:
            file_name = Path(file_path).name

        # 检查是否已收藏
        if any(f['path'] == file_path for f in self.favorites):
            logger.warning(f"File already in favorites: {file_path}")
            return

        # 添加收藏
        self.favorites.append({
            'path': file_path,
            'name': file_name,
            'timestamp': datetime.now().isoformat()
        })

        # 更新显示
        self._update_favorites_display()

        # 保存
        self._save_favorites()

        logger.debug(f"Added favorite: {file_path}")

    def _update_recent_display(self):
        """更新最近文件显示"""
        self.recent_listbox.delete(0, tk.END)

        for item in self.recent_files:
            self.recent_listbox.insert(tk.END, item['name'])

    def _update_favorites_display(self):
        """更新收藏文件显示"""
        self.favorites_listbox.delete(0, tk.END)

        for item in self.favorites:
            self.favorites_listbox.insert(tk.END, item['name'])

    def _on_recent_double_click(self, event):
        """最近文件双击事件"""
        self._open_recent_file()

    def _on_favorite_double_click(self, event):
        """收藏文件双击事件"""
        self._open_favorite_file()

    def _open_recent_file(self):
        """打开最近文件"""
        selection = self.recent_listbox.curselection()

        if selection:
            index = selection[0]
            file_info = self.recent_files[index]
            file_path = file_info['path']

            if self.on_file_open:
                self.on_file_open(file_path)

    def _open_favorite_file(self):
        """打开收藏文件"""
        selection = self.favorites_listbox.curselection()

        if selection:
            index = selection[0]
            file_info = self.favorites[index]
            file_path = file_info['path']

            if self.on_file_open:
                self.on_file_open(file_path)

    def _add_to_favorites_from_recent(self):
        """从最近文件添加到收藏"""
        selection = self.recent_listbox.curselection()

        if selection:
            index = selection[0]
            file_info = self.recent_files[index]
            self.add_favorite(file_info['path'], file_info['name'])

    def _remove_recent_file(self):
        """移除最近文件"""
        selection = self.recent_listbox.curselection()

        if selection:
            index = selection[0]
            del self.recent_files[index]
            self._update_recent_display()
            self._save_recent_files()

    def _remove_favorite_file(self):
        """移除收藏文件"""
        selection = self.favorites_listbox.curselection()

        if selection:
            index = selection[0]
            del self.favorites[index]
            self._update_favorites_display()
            self._save_favorites()

    def _show_recent_context_menu(self, event):
        """显示最近文件右键菜单"""
        # 选择点击的项
        index = self.recent_listbox.nearest(event.y)
        self.recent_listbox.selection_clear(0, tk.END)
        self.recent_listbox.selection_set(index)

        self.recent_context_menu.post(event.x_root, event.y_root)

    def _show_favorites_context_menu(self, event):
        """显示收藏文件右键菜单"""
        # 选择点击的项
        index = self.favorites_listbox.nearest(event.y)
        self.favorites_listbox.selection_clear(0, tk.END)
        self.favorites_listbox.selection_set(index)

        self.favorites_context_menu.post(event.x_root, event.y_root)

    def _load_data(self):
        """加载数据"""
        self._load_recent_files()
        self._load_favorites()

    def _load_recent_files(self):
        """加载最近文件"""
        try:
            path = Path(self.recent_files_path)

            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    self.recent_files = json.load(f)

                self._update_recent_display()
                logger.info(f"Loaded {len(self.recent_files)} recent files")

        except Exception as e:
            logger.error(f"Failed to load recent files: {e}")
            self.recent_files = []

    def _load_favorites(self):
        """加载收藏"""
        try:
            path = Path(self.favorites_path)

            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    self.favorites = json.load(f)

                self._update_favorites_display()
                logger.info(f"Loaded {len(self.favorites)} favorites")

        except Exception as e:
            logger.error(f"Failed to load favorites: {e}")
            self.favorites = []

    def _save_recent_files(self):
        """保存最近文件"""
        try:
            path = Path(self.recent_files_path)

            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.recent_files, f, ensure_ascii=False, indent=2)

            logger.debug("Recent files saved")

        except Exception as e:
            logger.error(f"Failed to save recent files: {e}")

    def _save_favorites(self):
        """保存收藏"""
        try:
            path = Path(self.favorites_path)

            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.favorites, f, ensure_ascii=False, indent=2)

            logger.debug("Favorites saved")

        except Exception as e:
            logger.error(f"Failed to save favorites: {e}")
