"""
应用控制器 - 连接 UI 和核心功能

负责:
1. 初始化核心组件
2. 处理 UI 事件
3. 协调搜索和索引操作
"""

import logging
import json
import threading
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class AppController:
    """
    应用控制器

    连接 MainWindow 和核心搜索/索引功能
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        初始化控制器

        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path or "search_index.db"
        self.current_index_name = "默认索引"

        # 核心组件(延迟加载)
        self.db_manager = None
        self.index_manager = None
        self.search_engine = None
        self.semantic_search = None

        # UI
        self.main_window = None

        # 最近索引列表
        self.recent_indexes_file = "recent_indexes.json"
        self.recent_indexes = self._load_recent_indexes()

        logger.info("App controller initialized")

    def initialize_components(self):
        """初始化核心组件"""
        try:
            from src.data.db_manager import DBManager
            from src.core.index_manager import IndexManager
            from src.core.search_engine import SearchEngine

            # 初始化数据库
            self.db_manager = DBManager(self.db_path)
            logger.info(f"Database initialized: {self.db_path}")

            # 初始化索引管理器 (传入 db_path,它使用单例模式会自己创建 DBManager)
            self.index_manager = IndexManager(db_path=self.db_path)
            logger.info("Index manager initialized")

            # 初始化搜索引擎 (传入 db_manager 实例)
            self.search_engine = SearchEngine(db_manager=self.db_manager)
            logger.info("Search engine initialized")

        except Exception as e:
            logger.error(f"Failed to initialize components: {e}")
            raise

    def initialize_ui(self):
        """初始化 UI"""
        from src.ui.main_window import MainWindow

        self.main_window = MainWindow()

        # 设置回调
        self.main_window.set_search_callback(self.handle_search)
        self.main_window.set_index_callback(self.handle_index)
        self.main_window.set_settings_callback(self.handle_settings)
        self.main_window.set_new_index_callback(self.handle_new_index)
        self.main_window.set_open_index_callback(self.handle_open_index)
        self.main_window.set_content_preview_callback(self.handle_content_preview)

        # 设置数据库管理器引用(用于预览面板从数据库读取内容)
        self.main_window.set_db_manager(self.db_manager)

        # 更新窗口标题显示当前索引
        self.main_window.root.title(f"Windows Search Tool - {self.current_index_name}")

        logger.info("UI initialized")

    def handle_search(self, query: str, mode: str = "fts") -> List[Dict[str, Any]]:
        """
        处理搜索请求

        Args:
            query: 搜索查询
            mode: 搜索模式 ('fts', 'semantic', 'hybrid')

        Returns:
            搜索结果列表
        """
        logger.info(f"Handling search: query='{query}', mode='{mode}'")

        try:
            if mode == "fts":
                # 全文搜索
                response = self.search_engine.search(query, limit=100)
                # SearchResponse.results 包含 SearchResult 列表
                return [self._search_result_to_dict(r) for r in response.results]

            elif mode == "semantic":
                # 语义搜索
                if not self.semantic_search:
                    logger.warning("Semantic search not initialized")
                    return []

                results = self.semantic_search.search(query, top_k=100)
                return [r.to_dict() for r in results]

            elif mode == "hybrid":
                # 混合搜索
                response = self.search_engine.search(query, limit=50)
                fts_dicts = [self._search_result_to_dict(r) for r in response.results]

                if self.semantic_search:
                    semantic_results = self.semantic_search.search(query, top_k=50)

                    from src.ai.semantic_search import combine_search_results
                    combined = combine_search_results(
                        fts_dicts,
                        semantic_results,
                        keyword_weight=0.5,
                        semantic_weight=0.5,
                        top_k=100
                    )
                    return combined
                else:
                    return fts_dicts

            else:
                logger.error(f"Unknown search mode: {mode}")
                return []

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    def _search_result_to_dict(self, result) -> Dict[str, Any]:
        """将 SearchResult 转换为字典"""
        return {
            'id': result.id,
            'file_path': result.file_path,
            'file_name': result.file_name,
            'snippet': result.snippet,
            'score': abs(result.rank),  # 转换为正数
            'similarity_score': abs(result.rank),
            'file_size': result.metadata.get('file_size', 0),
            'file_type': result.metadata.get('file_type', ''),
            'modified_at': result.metadata.get('modified_at', '')
        }

    def handle_index(self, directory: str):
        """
        处理索引请求（在后台线程中执行）

        Args:
            directory: 要索引的目录
        """
        logger.info(f"Handling index request for: {directory}")

        # 禁用索引按钮，防止重复索引
        self.main_window.set_status("准备索引...")

        def index_worker():
            """后台索引工作线程"""
            try:
                # 定义进度回调（使用 after 方法在主线程更新 GUI）
                def progress_callback(current: int, total: int, current_file: str):
                    """更新进度条和状态"""
                    if total > 0:
                        percentage = int((current / total) * 100)
                        file_name = current_file.split('\\')[-1] if current_file else ""

                        # 在主线程中更新 GUI
                        self.main_window.root.after(0, lambda: self._update_progress(
                            current, total, percentage, file_name
                        ))

                # 执行索引 (使用 create_index_parallel 方法)
                stats = self.index_manager.create_index_parallel(
                    paths=[directory],
                    num_workers=4,
                    progress_callback=progress_callback
                )

                logger.info(f"Indexing completed: {stats}")

                # 在主线程中显示完成统计
                self.main_window.root.after(0, lambda: self._finish_indexing(stats))

            except Exception as e:
                logger.error(f"Indexing failed: {e}")
                # 在主线程中显示错误
                self.main_window.root.after(0, lambda: self._indexing_error(str(e)))

        # 启动后台线程
        thread = threading.Thread(target=index_worker, daemon=True)
        thread.start()

    def _update_progress(self, current: int, total: int, percentage: int, file_name: str):
        """
        更新进度（在主线程中调用）

        Args:
            current: 当前进度
            total: 总数
            percentage: 百分比
            file_name: 当前文件名
        """
        # 更新状态栏
        self.main_window.set_status(
            f"正在索引: {current}/{total} ({percentage}%) - {file_name}"
        )

        # 更新进度条
        self.main_window.update_progress_bar(percentage)

    def _finish_indexing(self, stats):
        """
        索引完成（在主线程中调用）

        Args:
            stats: 索引统计信息
        """
        self.main_window.set_status(
            f"索引完成! 总计: {stats.total_files} 个文件, "
            f"成功: {stats.indexed_files}, 失败: {stats.failed_files}, "
            f"耗时: {stats.elapsed_time:.2f}秒"
        )
        self.main_window.update_progress_bar(0)  # 隐藏进度条

    def _indexing_error(self, error_msg: str):
        """
        索引错误（在主线程中调用）

        Args:
            error_msg: 错误信息
        """
        from tkinter import messagebox
        messagebox.showerror("错误", f"索引失败: {error_msg}")
        self.main_window.set_status("索引失败")
        self.main_window.update_progress_bar(0)  # 隐藏进度条

    def handle_settings(self):
        """
        处理设置对话框

        显示设置对话框并应用配置
        """
        logger.info("Opening settings dialog")

        try:
            from src.ui.settings_dialog import show_settings
            from src.utils.config import get_config

            config = get_config()

            # 显示设置对话框
            result = show_settings(self.main_window.root, config)

            if result:
                logger.info("Settings saved successfully")
                self.main_window.set_status("设置已保存")
            else:
                logger.info("Settings dialog cancelled")

        except Exception as e:
            logger.error(f"Failed to open settings: {e}")
            raise

    def handle_content_preview(self, doc_id: int, file_path: str, search_query: str = ""):
        """
        处理内容预览

        Args:
            doc_id: 文档 ID
            file_path: 文件路径
            search_query: 搜索关键词
        """
        logger.info(f"Opening content preview: {file_path}")

        try:
            from src.ui.content_preview_dialog import show_content_preview

            show_content_preview(
                self.main_window.root,
                self.db_manager,
                doc_id,
                file_path,
                search_query
            )

        except Exception as e:
            logger.error(f"Failed to open content preview: {e}")
            from tkinter import messagebox
            messagebox.showerror("错误", f"打开预览失败: {e}")

    def run(self):
        """运行应用"""
        try:
            # 初始化组件
            self.initialize_components()

            # 初始化 UI
            self.initialize_ui()

            # 运行主窗口
            self.main_window.run()

        except Exception as e:
            logger.error(f"Application failed: {e}")
            raise

    def shutdown(self):
        """关闭应用"""
        logger.info("Shutting down application")

        # 保存最近索引列表
        self._save_recent_indexes()

        if self.db_manager:
            self.db_manager.close()

        if self.main_window:
            self.main_window.quit()

    def handle_new_index(self):
        """
        处理新建索引请求

        显示新建索引对话框,创建新的索引数据库
        """
        logger.info("Opening new index dialog")

        try:
            from src.ui.new_index_dialog import show_new_index_dialog

            # 显示对话框
            result = show_new_index_dialog(self.main_window.root)

            if result:
                index_name, db_path, indexed_dirs = result

                # 切换到新的索引
                self._switch_index(index_name, db_path)

                # 如果选择了立刻索引
                if indexed_dirs:
                    for directory in indexed_dirs:
                        self.handle_index(directory)
                else:
                    self.main_window.set_status(f"索引 '{index_name}' 创建成功,可以开始添加目录")

                # 添加到最近索引
                self._add_to_recent_indexes(index_name, db_path)

        except Exception as e:
            logger.error(f"Failed to create new index: {e}")
            from tkinter import messagebox
            messagebox.showerror("错误", f"创建索引失败: {e}")

    def handle_open_index(self):
        """
        处理打开索引请求

        显示打开索引对话框,加载现有索引数据库
        """
        logger.info("Opening open index dialog")

        try:
            from src.ui.open_index_dialog import show_open_index_dialog

            # 显示对话框
            db_path = show_open_index_dialog(self.main_window.root, self.recent_indexes)

            if db_path:
                # 获取索引名称
                index_name = Path(db_path).stem

                # 切换到新的索引
                self._switch_index(index_name, db_path)

                # 添加到最近索引
                self._add_to_recent_indexes(index_name, db_path)

                # 显示索引统计
                stats = self.db_manager.get_statistics()
                doc_count = stats.get('total_documents', 0)
                self.main_window.set_status(
                    f"已打开索引 '{index_name}', 包含 {doc_count} 个文档"
                )

        except Exception as e:
            logger.error(f"Failed to open index: {e}")
            from tkinter import messagebox
            messagebox.showerror("错误", f"打开索引失败: {e}")

    def _switch_index(self, index_name: str, db_path: str):
        """
        切换到新的索引

        Args:
            index_name: 索引名称
            db_path: 数据库路径
        """
        logger.info(f"Switching to index: {index_name} ({db_path})")

        try:
            # 关闭当前数据库
            if self.db_manager:
                self.db_manager.close()

            # 更新路径和名称
            self.db_path = db_path
            self.current_index_name = index_name

            # 重新初始化组件
            self.initialize_components()

            # 更新主窗口的数据库管理器引用
            if self.main_window:
                self.main_window.set_db_manager(self.db_manager)

            # 更新窗口标题
            self.main_window.root.title(f"Windows Search Tool - {index_name}")

            logger.info(f"Successfully switched to index: {index_name}")

        except Exception as e:
            logger.error(f"Failed to switch index: {e}")
            raise

    def _load_recent_indexes(self) -> list:
        """
        加载最近使用的索引列表

        Returns:
            list: 最近索引列表
        """
        try:
            recent_file = Path(self.recent_indexes_file)
            if recent_file.exists():
                with open(recent_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data)} recent indexes")
                    return data
        except Exception as e:
            logger.error(f"Failed to load recent indexes: {e}")

        return []

    def _save_recent_indexes(self):
        """保存最近使用的索引列表"""
        try:
            with open(self.recent_indexes_file, 'w', encoding='utf-8') as f:
                json.dump(self.recent_indexes, f, ensure_ascii=False, indent=2)
                logger.info("Recent indexes saved")
        except Exception as e:
            logger.error(f"Failed to save recent indexes: {e}")

    def _add_to_recent_indexes(self, index_name: str, db_path: str):
        """
        添加到最近索引列表

        Args:
            index_name: 索引名称
            db_path: 数据库路径
        """
        # 移除已存在的相同路径
        self.recent_indexes = [
            idx for idx in self.recent_indexes
            if idx.get('path') != db_path
        ]

        # 添加到开头
        self.recent_indexes.insert(0, {
            'name': index_name,
            'path': db_path,
            'last_used': datetime.now().isoformat()
        })

        # 限制数量
        self.recent_indexes = self.recent_indexes[:10]

        # 保存
        self._save_recent_indexes()

        logger.info(f"Added to recent indexes: {index_name}")
