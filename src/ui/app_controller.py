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

        # 索引库管理器
        from src.core.index_library_manager import IndexLibraryManager
        self.library_manager = IndexLibraryManager(config_file='indexes.json')

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

        self.main_window = MainWindow(library_manager=self.library_manager)

        # 设置回调
        self.main_window.set_search_callback(self.handle_search)
        self.main_window.set_index_callback(self.handle_index)
        self.main_window.set_update_index_callback(self.handle_update_index)  # 增量更新
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
        处理搜索请求（支持多库搜索）

        Args:
            query: 搜索查询
            mode: 搜索模式 ('fts', 'semantic', 'hybrid')

        Returns:
            搜索结果列表
        """
        logger.info(f"Handling search: query='{query}', mode='{mode}'")

        try:
            # 获取启用的索引库
            enabled_libraries = self.library_manager.get_enabled_libraries()

            if not enabled_libraries:
                logger.warning("No enabled libraries for search")
                return []

            all_results = []

            # 对每个启用的库进行搜索
            for library in enabled_libraries:
                try:
                    # 为每个库创建独立的数据库连接和搜索引擎
                    from src.data.db_manager import DBManager
                    from src.core.search_engine import SearchEngine

                    db_manager = DBManager(library.db_path)
                    search_engine = SearchEngine(db_manager=db_manager)

                    if mode == "fts":
                        # 全文搜索
                        response = search_engine.search(query, limit=100)
                        library_results = [
                            self._search_result_to_dict(r, library.name)
                            for r in response.results
                        ]
                        all_results.extend(library_results)

                    elif mode == "semantic":
                        # 语义搜索（暂不支持多库）
                        if library.db_path == self.db_path and self.semantic_search:
                            results = self.semantic_search.search(query, top_k=100)
                            library_results = [r.to_dict() for r in results]
                            # 添加库名
                            for r in library_results:
                                r['library_name'] = library.name
                            all_results.extend(library_results)

                    elif mode == "hybrid":
                        # 混合搜索
                        response = search_engine.search(query, limit=50)
                        library_results = [
                            self._search_result_to_dict(r, library.name)
                            for r in response.results
                        ]
                        all_results.extend(library_results)

                    # 关闭数据库连接
                    db_manager.close()

                    # 更新库的统计信息（最后使用时间）
                    self.library_manager.update_library_stats(
                        library.name,
                        doc_count=library.doc_count,
                        size_bytes=library.size_bytes
                    )

                except Exception as e:
                    logger.error(f"Search failed for library '{library.name}': {e}")
                    continue

            # 按分数排序所有结果
            all_results.sort(key=lambda x: x.get('score', 0), reverse=True)

            # 去重（基于文件路径，规范化路径格式）
            import os
            seen_paths = set()
            unique_results = []
            for result in all_results:
                file_path = result.get('file_path', '')
                if file_path:
                    # 规范化路径（统一斜杠方向，解析 . 和 ..）
                    normalized_path = os.path.normpath(file_path).lower()
                    if normalized_path not in seen_paths:
                        seen_paths.add(normalized_path)
                        unique_results.append(result)

            logger.info(f"Search returned {len(all_results)} results, {len(unique_results)} unique")

            # 返回前 100 条结果
            return unique_results[:100]

        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise

    def _search_result_to_dict(self, result, library_name: str = "") -> Dict[str, Any]:
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
            'modified_at': result.metadata.get('modified_at', ''),
            'library_name': library_name  # 添加库名
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
        # 清除搜索缓存（因为索引已更新，旧的搜索结果可能已过期）
        if self.search_engine:
            self.search_engine.clear_cache()
            logger.info("搜索缓存已清除（索引更新后）")

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

    def handle_update_index(self):
        """
        处理增量更新索引请求（在后台线程中执行）

        检测文件变化并更新索引
        """
        logger.info("Handling update index request")

        self.main_window.set_status("准备更新索引...")

        def update_worker():
            """后台增量更新工作线程"""
            try:
                # 定义进度回调
                def progress_callback(current: int, total: int, current_file: str):
                    """更新进度条和状态"""
                    if total > 0:
                        percentage = int((current / total) * 100)
                        file_name = current_file.split('\\')[-1] if current_file else ""

                        # 在主线程中更新 GUI
                        self.main_window.root.after(0, lambda: self._update_progress(
                            current, total, percentage, f"检查: {file_name}"
                        ))

                # 获取数据库中所有已索引的文件路径
                cursor = self.db_manager.connection.cursor()
                cursor.execute("""
                    SELECT DISTINCT file_path
                    FROM documents
                    WHERE status = 'active'
                """)

                rows = cursor.fetchall()

                if not rows:
                    # 没有已索引的文件
                    def show_no_files():
                        from tkinter import messagebox
                        messagebox.showinfo(
                            "提示",
                            "当前索引库中没有文件。\n请先使用 '添加目录' 功能进行索引。"
                        )
                        self.main_window.set_status("索引库为空")
                        self.main_window.update_progress_bar(0)

                    self.main_window.root.after(0, show_no_files)
                    return

                # 提取所有唯一的根目录
                import os
                unique_dirs = set()
                for row in rows:
                    file_path = row['file_path']
                    # 提取文件所在目录
                    dir_path = os.path.dirname(file_path)
                    # 尝试找到更高层的目录（简单方法：使用前几层）
                    parts = dir_path.split(os.sep)
                    if len(parts) > 3:
                        # 使用前3层作为根目录（例如 E:\索引测试\2025年警示教育）
                        root_dir = os.sep.join(parts[:4])
                    else:
                        root_dir = dir_path
                    unique_dirs.add(root_dir)

                # 将目录集合转换为列表
                paths_to_refresh = list(unique_dirs)

                logger.info(f"发现 {len(paths_to_refresh)} 个目录需要刷新: {paths_to_refresh}")

                # 使用 refresh_index 对所有文件进行检查
                stats = self.index_manager.refresh_index(
                    paths=paths_to_refresh,
                    progress_callback=progress_callback
                )

                logger.info(f"Index update completed: {stats}")

                # 在主线程中显示完成统计
                def finish_update():
                    self.main_window.set_status(
                        f"更新完成! "
                        f"新增: {stats.added_files}, "
                        f"更新: {stats.updated_files}, "
                        f"删除: {stats.deleted_files}, "
                        f"耗时: {stats.elapsed_time:.2f}秒"
                    )
                    self.main_window.update_progress_bar(0)

                    # 清除搜索缓存
                    if self.search_engine:
                        self.search_engine.clear_cache()
                        logger.info("搜索缓存已清除（增量更新后）")

                self.main_window.root.after(0, finish_update)

            except Exception as e:
                logger.error(f"Index update failed: {e}")
                # 在主线程中显示错误
                self.main_window.root.after(0, lambda: self._indexing_error(str(e)))

        # 启动后台线程
        thread = threading.Thread(target=update_worker, daemon=True)
        thread.start()

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
