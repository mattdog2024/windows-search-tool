"""
索引管理器模块

提供文件扫描、索引创建和增量更新功能
"""

import os
import hashlib
import logging
import time
from pathlib import Path
from typing import List, Dict, Callable, Optional, Tuple
from dataclasses import dataclass, field
from multiprocessing import Pool, cpu_count

from ..data.db_manager import DBManager
from ..parsers.factory import ParserFactory
from ..utils.config import ConfigManager

logger = logging.getLogger(__name__)


@dataclass
class IndexStats:
    """
    索引统计信息

    Attributes:
        total_files: 扫描到的文件总数
        indexed_files: 成功索引的文件数
        failed_files: 索引失败的文件数
        skipped_files: 跳过的文件数
        total_size: 文件总大小(字节)
        elapsed_time: 索引耗时(秒)
        errors: 错误列表 [(文件路径, 错误信息)]
        added_files: 新增的文件数(增量索引)
        updated_files: 更新的文件数(增量索引)
        deleted_files: 删除的文件数(增量索引)
    """
    total_files: int = 0
    indexed_files: int = 0
    failed_files: int = 0
    skipped_files: int = 0
    total_size: int = 0
    elapsed_time: float = 0.0
    errors: List[Tuple[str, str]] = field(default_factory=list)
    added_files: int = 0
    updated_files: int = 0
    deleted_files: int = 0


# 进度回调类型: (已处理数量, 总数量, 当前文件路径) -> None
ProgressCallback = Callable[[int, int, str], None]


class IndexManager:
    """
    索引管理器

    负责文件扫描、内容提取、索引创建和增量更新
    采用单例模式防止多实例冲突
    """

    _instance = None

    def __new__(cls, db_path: Optional[str] = None):
        """
        单例模式实现

        Args:
            db_path: 数据库文件路径
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: Optional[str] = None):
        """
        初始化索引管理器

        Args:
            db_path: 数据库文件路径,如果为None则使用默认路径
        """
        # 避免重复初始化
        if self._initialized:
            return

        # 初始化配置管理器
        self.config = ConfigManager()

        # 初始化数据库管理器
        if db_path is None:
            # 使用默认数据库路径
            appdata = os.getenv('APPDATA', '')
            db_path = os.path.join(appdata, 'WindowsSearchTool', 'index.db')

        self.db = DBManager(db_path)

        # 初始化解析器工厂(使用全局工厂实例)
        from ..parsers.factory import get_parser_factory
        from ..parsers.text_parser import TextParser

        self.parser_factory = get_parser_factory()

        # 确保注册基本解析器(文本解析器)
        if not self.parser_factory.supports('test.txt'):
            self.parser_factory.register_parser(
                'text',
                ['.txt', '.md', '.csv', '.log', '.json', '.xml'],
                TextParser()
            )

        # 从配置加载参数
        self.max_file_size = self.config.get('indexing.max_file_size_mb', 100) * 1024 * 1024
        self.excluded_extensions = self.config.get('indexing.excluded_extensions', [])
        self.excluded_paths = self.config.get('indexing.excluded_paths', [])
        self.batch_size = self.config.get('indexing.batch_size', 100)
        self.parallel_workers = self.config.get('indexing.parallel_workers', cpu_count())

        self._initialized = True
        logger.info(f"IndexManager 初始化完成, 数据库路径: {db_path}")

    # ==================== 文件扫描功能 ====================

    def scan_directory(
        self,
        directory: str,
        recursive: bool = True
    ) -> List[Dict[str, any]]:
        """
        扫描目录,获取所有支持的文件

        Args:
            directory: 要扫描的目录路径
            recursive: 是否递归扫描子目录

        Returns:
            文件信息列表,每个元素包含:
            - path: 文件路径
            - size: 文件大小(字节)
            - modified: 修改时间(时间戳)
            - hash: 文件哈希值(SHA256)

        Example:
            >>> manager = IndexManager()
            >>> files = manager.scan_directory('E:/Documents')
            >>> print(f"找到 {len(files)} 个文件")
        """
        logger.info(f"开始扫描目录: {directory}, 递归={recursive}")

        if not os.path.exists(directory):
            logger.warning(f"目录不存在: {directory}")
            return []

        if not os.path.isdir(directory):
            logger.warning(f"不是有效的目录: {directory}")
            return []

        files = []

        try:
            if recursive:
                # 递归扫描
                for root, dirs, filenames in os.walk(directory):
                    # 过滤排除的目录
                    dirs[:] = [
                        d for d in dirs
                        if not self._is_excluded_path(os.path.join(root, d))
                    ]

                    # 处理文件
                    for filename in filenames:
                        file_path = os.path.join(root, filename)
                        file_info = self._process_file(file_path)
                        if file_info:
                            files.append(file_info)
            else:
                # 只扫描当前目录
                for entry in os.scandir(directory):
                    if entry.is_file():
                        file_info = self._process_file(entry.path)
                        if file_info:
                            files.append(file_info)

            logger.info(f"扫描完成: 找到 {len(files)} 个可索引文件")
            return files

        except Exception as e:
            logger.error(f"扫描目录失败: {directory}, 错误: {e}")
            return files

    def _process_file(self, file_path: str) -> Optional[Dict[str, any]]:
        """
        处理单个文件,获取文件信息

        Args:
            file_path: 文件路径

        Returns:
            文件信息字典,如果文件不应被索引则返回None
        """
        # 检查是否应该索引此文件
        if not self._should_index_file(file_path):
            return None

        try:
            # 获取文件信息
            stat = os.stat(file_path)

            file_info = {
                'path': file_path,
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'hash': self._calculate_file_hash(file_path)
            }

            return file_info

        except Exception as e:
            logger.warning(f"处理文件失败: {file_path}, 错误: {e}")
            return None

    def _should_index_file(self, file_path: str) -> bool:
        """
        检查文件是否应该被索引

        Args:
            file_path: 文件路径

        Returns:
            是否应该索引此文件
        """
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return False

        # 检查是否是符号链接
        if os.path.islink(file_path):
            logger.debug(f"跳过符号链接: {file_path}")
            return False

        # 检查是否是文件
        if not os.path.isfile(file_path):
            return False

        # 检查扩展名是否在排除列表中
        _, ext = os.path.splitext(file_path)
        ext_lower = ext.lower()
        if ext_lower in self.excluded_extensions:
            logger.debug(f"跳过排除的扩展名: {file_path}")
            return False

        # 检查是否是支持的格式
        if not self.parser_factory.supports(file_path):
            logger.debug(f"不支持的文件格式: {file_path}")
            return False

        # 检查路径是否在排除列表中
        if self._is_excluded_path(file_path):
            logger.debug(f"跳过排除的路径: {file_path}")
            return False

        # 检查文件大小
        try:
            size = os.path.getsize(file_path)
            if size > self.max_file_size:
                logger.debug(f"文件太大: {file_path} ({size} bytes)")
                return False

            # 跳过空文件
            if size == 0:
                logger.debug(f"跳过空文件: {file_path}")
                return False

        except Exception as e:
            logger.warning(f"检查文件大小失败: {file_path}, 错误: {e}")
            return False

        return True

    def _is_excluded_path(self, path: str) -> bool:
        """
        检查路径是否在排除列表中

        Args:
            path: 文件或目录路径

        Returns:
            是否应该排除此路径
        """
        path_lower = path.lower()

        for excluded in self.excluded_paths:
            excluded_lower = excluded.lower()

            # 支持通配符匹配
            if excluded_lower in path_lower:
                return True

        return False

    def _calculate_file_hash(self, file_path: str) -> str:
        """
        计算文件的 SHA256 哈希值

        Args:
            file_path: 文件路径

        Returns:
            文件的 SHA256 哈希值(十六进制字符串)
        """
        sha256_hash = hashlib.sha256()

        try:
            with open(file_path, 'rb') as f:
                # 分块读取,避免大文件内存溢出
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)

            return sha256_hash.hexdigest()

        except Exception as e:
            logger.error(f"计算文件哈希失败: {file_path}, 错误: {e}")
            return ""

    def list_files(
        self,
        directories: List[str],
        recursive: bool = True
    ) -> List[Dict[str, any]]:
        """
        扫描多个目录,获取所有支持的文件

        Args:
            directories: 要扫描的目录列表
            recursive: 是否递归扫描子目录

        Returns:
            文件信息列表

        Example:
            >>> manager = IndexManager()
            >>> files = manager.list_files(['E:/Documents', 'E:/Projects'])
            >>> print(f"总共找到 {len(files)} 个文件")
        """
        all_files = []

        for directory in directories:
            files = self.scan_directory(directory, recursive=recursive)
            all_files.extend(files)

        logger.info(f"扫描 {len(directories)} 个目录, 总共找到 {len(all_files)} 个文件")
        return all_files

    # ==================== 文件解析和索引创建功能 ====================

    def create_index(
        self,
        paths: List[str],
        progress_callback: Optional[ProgressCallback] = None,
        use_parallel: bool = False,
        num_workers: Optional[int] = None
    ) -> IndexStats:
        """
        创建完整索引

        扫描指定路径,解析文件内容并批量插入数据库。

        Args:
            paths: 要索引的目录或文件路径列表
            progress_callback: 进度回调函数 (已处理数量, 总数量, 当前文件路径)
            use_parallel: 是否使用多进程并行处理
            num_workers: 工作进程数(仅在 use_parallel=True 时有效)

        Returns:
            IndexStats: 索引统计信息

        Example:
            >>> def on_progress(processed, total, current):
            ...     print(f"进度: {processed}/{total} - {current}")
            >>> manager = IndexManager()
            >>> # 串行索引
            >>> stats = manager.create_index(['E:/Documents'], on_progress)
            >>> # 并行索引
            >>> stats = manager.create_index(['E:/Documents'], on_progress, use_parallel=True)
            >>> print(f"索引完成: {stats.indexed_files}/{stats.total_files}")
        """
        # 如果启用并行处理,委托给并行方法
        if use_parallel:
            return self.create_index_parallel(paths, num_workers, progress_callback)

        logger.info(f"开始创建索引: {len(paths)} 个路径")
        start_time = time.time()
        stats = IndexStats()

        try:
            # 1. 扫描文件列表
            files = self.list_files(paths, recursive=True)
            stats.total_files = len(files)

            if stats.total_files == 0:
                logger.warning("没有找到可索引的文件")
                stats.elapsed_time = time.time() - start_time
                return stats

            logger.info(f"找到 {stats.total_files} 个文件待索引")

            # 2. 遍历每个文件进行解析
            documents_batch = []
            processed_count = 0

            for file_info in files:
                # 解析文件
                parse_result = self._parse_file(file_info)

                if parse_result is None:
                    # 解析失败
                    stats.failed_files += 1
                    processed_count += 1
                    continue

                # 添加到批次
                documents_batch.append(parse_result)
                stats.total_size += file_info['size']
                processed_count += 1

                # 调用进度回调
                if progress_callback:
                    progress_callback(processed_count, stats.total_files, file_info['path'])

                # 批量插入
                if len(documents_batch) >= self.batch_size:
                    inserted_count = self._batch_insert(documents_batch)
                    stats.indexed_files += inserted_count
                    documents_batch.clear()

            # 3. 插入剩余的文档
            if documents_batch:
                inserted_count = self._batch_insert(documents_batch)
                stats.indexed_files += inserted_count

            # 4. 更新统计信息
            stats.elapsed_time = time.time() - start_time
            stats.skipped_files = stats.total_files - stats.indexed_files - stats.failed_files

            logger.info(
                f"索引创建完成: 总计={stats.total_files}, "
                f"成功={stats.indexed_files}, "
                f"失败={stats.failed_files}, "
                f"跳过={stats.skipped_files}, "
                f"耗时={stats.elapsed_time:.2f}秒"
            )

            return stats

        except Exception as e:
            logger.error(f"创建索引失败: {e}")
            stats.elapsed_time = time.time() - start_time
            raise

    def _parse_file(self, file_info: Dict[str, any]) -> Optional[Dict[str, any]]:
        """
        解析单个文件

        使用 ParserFactory 获取合适的解析器,解析文件内容。

        Args:
            file_info: 文件信息字典,包含 path, size, modified, hash 等字段

        Returns:
            文档数据字典,如果解析失败则返回 None
            字典包含以下字段:
            - file_path: 文件路径
            - file_name: 文件名
            - file_size: 文件大小
            - file_type: 文件类型(扩展名)
            - content_hash: 文件哈希值
            - created_at: 创建时间
            - modified_at: 修改时间
            - content: 文件内容(用于全文搜索)
            - metadata: 元数据字典
        """
        file_path = file_info['path']

        try:
            # 1. 获取解析器
            parser = self.parser_factory.get_parser(file_path)
            if parser is None:
                logger.warning(f"未找到合适的解析器: {file_path}")
                return None

            # 2. 解析文件
            result = parser.parse(file_path)

            if not result.success:
                logger.warning(f"解析失败: {file_path}, 错误: {result.error}")
                return None

            # 3. 提取文件信息
            _, ext = os.path.splitext(file_path)
            file_name = os.path.basename(file_path)

            # 4. 构建文档数据
            doc_data = {
                'file_path': file_path,
                'file_name': file_name,
                'file_size': file_info['size'],
                'file_type': ext.lstrip('.').lower() if ext else '',
                'content_hash': file_info['hash'],
                'created_at': None,  # SQLite 会使用默认值
                'modified_at': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file_info['modified'])),
                'content': result.content,
                'metadata': result.metadata
            }

            logger.debug(f"解析成功: {file_path}")
            return doc_data

        except Exception as e:
            logger.error(f"解析文件异常: {file_path}, 错误: {e}")
            return None

    def _batch_insert(self, documents: List[Dict[str, any]]) -> int:
        """
        批量插入文档到数据库

        Args:
            documents: 文档数据列表

        Returns:
            成功插入的文档数量
        """
        if not documents:
            return 0

        try:
            # 调用数据库管理器的批量插入方法
            doc_ids = self.db.batch_insert_documents(documents, batch_size=self.batch_size)

            logger.info(f"批量插入成功: {len(doc_ids)} 个文档")
            return len(doc_ids)

        except Exception as e:
            logger.error(f"批量插入失败: {e}")
            # 如果批量插入失败,尝试逐个插入
            success_count = 0
            for doc in documents:
                try:
                    self.db.insert_document(
                        file_path=doc['file_path'],
                        file_name=doc['file_name'],
                        content=doc['content'],
                        file_size=doc.get('file_size'),
                        file_type=doc.get('file_type'),
                        content_hash=doc.get('content_hash'),
                        created_at=doc.get('created_at'),
                        modified_at=doc.get('modified_at'),
                        metadata=doc.get('metadata')
                    )
                    success_count += 1
                except Exception as e2:
                    logger.error(f"插入单个文档失败: {doc['file_path']}, 错误: {e2}")

            logger.info(f"逐个插入完成: {success_count}/{len(documents)} 个文档")
            return success_count

    # ==================== 多进程并行处理功能 ====================

    def create_index_parallel(
        self,
        paths: List[str],
        num_workers: Optional[int] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> IndexStats:
        """
        使用多进程并行创建索引

        扫描指定路径,使用多进程并行解析文件内容并批量插入数据库。

        Args:
            paths: 要索引的目录或文件路径列表
            num_workers: 工作进程数,默认使用配置中的值或 CPU 核心数
            progress_callback: 进度回调函数 (已处理数量, 总数量, 当前文件路径)

        Returns:
            IndexStats: 索引统计信息

        Example:
            >>> def on_progress(processed, total, current):
            ...     print(f"进度: {processed}/{total} - {current}")
            >>> manager = IndexManager()
            >>> stats = manager.create_index_parallel(['E:/Documents'], num_workers=4, progress_callback=on_progress)
            >>> print(f"索引完成: {stats.indexed_files}/{stats.total_files}")
        """
        logger.info(f"开始并行创建索引: {len(paths)} 个路径")
        start_time = time.time()
        stats = IndexStats()

        # 确定工作进程数
        if num_workers is None:
            num_workers = self.parallel_workers

        try:
            # 1. 扫描文件列表
            files = self.list_files(paths, recursive=True)
            stats.total_files = len(files)

            if stats.total_files == 0:
                logger.warning("没有找到可索引的文件")
                stats.elapsed_time = time.time() - start_time
                return stats

            logger.info(f"找到 {stats.total_files} 个文件待索引,使用 {num_workers} 个工作进程")

            # 2. 使用多进程池并行解析文件
            parse_results = []
            processed_count = 0

            with Pool(processes=num_workers) as pool:
                # 提交所有解析任务
                async_results = []
                for file_info in files:
                    async_result = pool.apply_async(_parse_file_worker, (file_info,))
                    async_results.append((file_info, async_result))

                # 收集解析结果
                for file_info, async_result in async_results:
                    try:
                        # 等待解析完成(最多 30 秒)
                        parse_result = async_result.get(timeout=30)

                        if parse_result is not None:
                            parse_results.append(parse_result)
                            stats.total_size += file_info['size']
                        else:
                            # 解析失败
                            stats.failed_files += 1
                            stats.errors.append((file_info['path'], "解析返回 None"))

                    except Exception as e:
                        logger.error(f"获取解析结果失败: {file_info['path']}, 错误: {e}")
                        stats.failed_files += 1
                        stats.errors.append((file_info['path'], str(e)))

                    processed_count += 1

                    # 调用进度回调
                    if progress_callback:
                        progress_callback(processed_count, stats.total_files, file_info['path'])

            # 3. 批量插入数据库
            logger.info(f"并行解析完成,开始批量插入 {len(parse_results)} 个文档")

            # 分批插入
            batch_count = 0
            for i in range(0, len(parse_results), self.batch_size):
                batch = parse_results[i:i + self.batch_size]
                inserted_count = self._batch_insert(batch)
                stats.indexed_files += inserted_count
                batch_count += 1

            # 4. 更新统计信息
            stats.elapsed_time = time.time() - start_time
            stats.skipped_files = stats.total_files - stats.indexed_files - stats.failed_files

            logger.info(
                f"并行索引创建完成: 总计={stats.total_files}, "
                f"成功={stats.indexed_files}, "
                f"失败={stats.failed_files}, "
                f"跳过={stats.skipped_files}, "
                f"耗时={stats.elapsed_time:.2f}秒, "
                f"速度={stats.indexed_files / (stats.elapsed_time / 60):.1f}文件/分钟"
            )

            return stats

        except Exception as e:
            logger.error(f"并行创建索引失败: {e}")
            stats.elapsed_time = time.time() - start_time
            raise

    def _parse_files_parallel(
        self,
        files: List[Dict[str, any]],
        num_workers: Optional[int] = None,
        progress_callback: Optional[ProgressCallback] = None
    ) -> List[Dict[str, any]]:
        """
        使用多进程并行解析文件列表

        Args:
            files: 文件信息列表
            num_workers: 工作进程数
            progress_callback: 进度回调函数

        Returns:
            解析后的文档数据列表
        """
        if num_workers is None:
            num_workers = self.parallel_workers

        parse_results = []
        total = len(files)

        with Pool(processes=num_workers) as pool:
            # 提交所有解析任务
            async_results = []
            for file_info in files:
                async_result = pool.apply_async(_parse_file_worker, (file_info,))
                async_results.append((file_info, async_result))

            # 收集解析结果
            for i, (file_info, async_result) in enumerate(async_results, 1):
                try:
                    parse_result = async_result.get(timeout=30)

                    if parse_result is not None:
                        parse_results.append(parse_result)

                    # 调用进度回调
                    if progress_callback:
                        progress_callback(i, total, file_info['path'])

                except Exception as e:
                    logger.error(f"并行解析失败: {file_info['path']}, 错误: {e}")

        return parse_results


# ==================== 全局工作函数(用于多进程) ====================

def _parse_file_worker(file_info: Dict[str, any]) -> Optional[Dict[str, any]]:
    """
    多进程工作函数:解析单个文件

    该函数必须在顶层定义以便 pickle 序列化(multiprocessing 要求)。

    Args:
        file_info: 文件信息字典,包含 path, size, modified, hash 等字段

    Returns:
        文档数据字典,如果解析失败则返回 None
    """
    file_path = file_info['path']

    try:
        # 导入必要的模块(在工作进程中)
        from ..parsers.factory import get_parser_factory
        from ..parsers.text_parser import TextParser

        # 获取全局解析器工厂(确保在工作进程中注册解析器)
        factory = get_parser_factory()

        # 检查是否已注册解析器,如果没有则注册
        if not factory.supports(file_path):
            # 在工作进程中注册基本解析器
            factory.register_parser('text', ['.txt', '.md', '.csv', '.log', '.json', '.xml'], TextParser())

        # 获取解析器
        parser = factory.get_parser(file_path)
        if parser is None:
            return None

        # 解析文件
        result = parser.parse(file_path)

        if not result.success:
            return None

        # 提取文件信息
        _, ext = os.path.splitext(file_path)
        file_name = os.path.basename(file_path)

        # 构建文档数据
        doc_data = {
            'file_path': file_path,
            'file_name': file_name,
            'file_size': file_info['size'],
            'file_type': ext.lstrip('.').lower() if ext else '',
            'content_hash': file_info['hash'],
            'created_at': None,
            'modified_at': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file_info['modified'])),
            'content': result.content,
            'metadata': result.metadata
        }

        return doc_data

    except Exception as e:
        # 工作进程中的错误
        logger.error(f"工作进程解析失败: {file_path}, 错误: {e}")
        return None


# ==================== 增量索引扩展(IndexManager 类的方法) ====================
# 注意:以下方法应该添加到 IndexManager 类中,这里作为模块级函数是为了便于 Stream 协调

def _add_incremental_methods_to_index_manager():
    """
    将增量索引方法添加到 IndexManager 类

    这个函数用于动态添加方法到 IndexManager 类,
    以便与 Stream 4 的并行处理代码协调。
    """

    def refresh_index(
        self,
        paths: List[str],
        progress_callback: Optional[ProgressCallback] = None
    ) -> IndexStats:
        """
        增量更新索引

        扫描指定路径,通过比较文件哈希值检测文件变更,
        只索引新增和修改的文件,删除已不存在的文件。

        Args:
            paths: 要刷新索引的目录或文件路径列表
            progress_callback: 进度回调函数 (已处理数量, 总数量, 当前文件路径)

        Returns:
            IndexStats: 索引统计信息,包含新增、更新和删除的文件数量

        Example:
            >>> def on_progress(processed, total, current):
            ...     print(f"进度: {processed}/{total} - {current}")
            >>> manager = IndexManager()
            >>> stats = manager.refresh_index(['E:/Documents'], on_progress)
            >>> print(f"新增: {stats.added_files}, 更新: {stats.updated_files}, 删除: {stats.deleted_files}")
        """
        logger.info(f"开始增量索引: {len(paths)} 个路径")
        start_time = time.time()
        stats = IndexStats()

        try:
            # 1. 获取数据库中所有已索引的文件路径和哈希值
            db_files = self.db.get_all_file_paths()
            db_files_dict = {path: self.db.get_file_hash(path) for path in db_files}
            logger.info(f"数据库中已有 {len(db_files_dict)} 个文件")

            # 2. 扫描当前文件系统
            current_files = self.list_files(paths, recursive=True)
            stats.total_files = len(current_files)
            logger.info(f"当前文件系统中有 {stats.total_files} 个文件")

            # 3. 检测文件变更
            new_files, modified_files, deleted_file_paths = self._detect_changes(
                db_files_dict,
                current_files
            )

            logger.info(
                f"变更检测完成: 新增={len(new_files)}, "
                f"修改={len(modified_files)}, "
                f"删除={len(deleted_file_paths)}"
            )

            # 4. 处理新增的文件
            if new_files:
                logger.info(f"开始索引 {len(new_files)} 个新增文件")
                processed_count = 0
                documents_batch = []

                for file_info in new_files:
                    # 解析文件
                    parse_result = self._parse_file(file_info)

                    if parse_result is None:
                        stats.failed_files += 1
                        processed_count += 1
                        continue

                    documents_batch.append(parse_result)
                    stats.total_size += file_info['size']
                    processed_count += 1

                    # 调用进度回调
                    if progress_callback:
                        progress_callback(
                            processed_count,
                            len(new_files) + len(modified_files),
                            file_info['path']
                        )

                    # 批量插入
                    if len(documents_batch) >= self.batch_size:
                        inserted_count = self._batch_insert(documents_batch)
                        stats.added_files += inserted_count
                        documents_batch.clear()

                # 插入剩余的文档
                if documents_batch:
                    inserted_count = self._batch_insert(documents_batch)
                    stats.added_files += inserted_count

                logger.info(f"新增文件索引完成: {stats.added_files} 个")

            # 5. 处理修改的文件
            if modified_files:
                logger.info(f"开始更新 {len(modified_files)} 个修改的文件")
                processed_count = len(new_files)

                for file_info in modified_files:
                    # 解析文件
                    parse_result = self._parse_file(file_info)

                    if parse_result is None:
                        stats.failed_files += 1
                        processed_count += 1
                        continue

                    # 更新文档
                    success = self._update_document(file_info, parse_result)
                    if success:
                        stats.updated_files += 1
                        stats.total_size += file_info['size']
                    else:
                        stats.failed_files += 1

                    processed_count += 1

                    # 调用进度回调
                    if progress_callback:
                        progress_callback(
                            processed_count,
                            len(new_files) + len(modified_files),
                            file_info['path']
                        )

                logger.info(f"修改文件更新完成: {stats.updated_files} 个")

            # 6. 删除已删除文件的索引
            if deleted_file_paths:
                logger.info(f"开始删除 {len(deleted_file_paths)} 个已删除文件的索引")

                for file_path in deleted_file_paths:
                    success = self.db.delete_document_by_path(file_path, hard_delete=True)
                    if success:
                        stats.deleted_files += 1

                logger.info(f"删除文件索引完成: {stats.deleted_files} 个")

            # 7. 更新统计信息
            stats.indexed_files = stats.added_files + stats.updated_files
            stats.elapsed_time = time.time() - start_time

            logger.info(
                f"增量索引完成: "
                f"新增={stats.added_files}, "
                f"更新={stats.updated_files}, "
                f"删除={stats.deleted_files}, "
                f"失败={stats.failed_files}, "
                f"耗时={stats.elapsed_time:.2f}秒"
            )

            return stats

        except Exception as e:
            logger.error(f"增量索引失败: {e}")
            stats.elapsed_time = time.time() - start_time
            raise

    def _detect_changes(
        self,
        db_files_dict: Dict[str, str],
        current_files: List[Dict[str, any]]
    ) -> Tuple[List[Dict[str, any]], List[Dict[str, any]], List[str]]:
        """
        检测文件变更

        比较数据库中的文件和当前文件系统中的文件,
        检测新增、修改和删除的文件。

        Args:
            db_files_dict: 数据库中的文件字典 {文件路径: 哈希值}
            current_files: 当前文件系统中的文件列表

        Returns:
            (new_files, modified_files, deleted_file_paths):
            - new_files: 新增的文件列表
            - modified_files: 修改的文件列表
            - deleted_file_paths: 已删除的文件路径列表
        """
        new_files = []
        modified_files = []
        current_file_paths = set()

        # 遍历当前文件,检测新增和修改
        for file_info in current_files:
            file_path = file_info['path']
            file_hash = file_info['hash']
            current_file_paths.add(file_path)

            if file_path not in db_files_dict:
                # 新增的文件
                new_files.append(file_info)
                logger.debug(f"检测到新增文件: {file_path}")
            else:
                # 检查哈希值是否变化
                db_hash = db_files_dict[file_path]
                if db_hash != file_hash:
                    # 修改的文件
                    modified_files.append(file_info)
                    logger.debug(f"检测到修改文件: {file_path}")
                else:
                    # 文件未变化
                    logger.debug(f"文件未变化: {file_path}")

        # 检测已删除的文件
        db_file_paths = set(db_files_dict.keys())
        deleted_file_paths = list(db_file_paths - current_file_paths)

        for file_path in deleted_file_paths:
            logger.debug(f"检测到删除文件: {file_path}")

        return new_files, modified_files, deleted_file_paths

    def _update_document(
        self,
        file_info: Dict[str, any],
        doc_data: Dict[str, any]
    ) -> bool:
        """
        更新文档

        更新数据库中已有文档的内容、哈希值和修改时间。

        Args:
            file_info: 文件信息字典,包含 path, size, modified, hash 等字段
            doc_data: 文档数据字典,包含解析后的内容和元数据

        Returns:
            是否更新成功
        """
        file_path = file_info['path']

        try:
            # 获取文档 ID
            doc = self.db.get_document_by_path(file_path)
            if not doc:
                logger.warning(f"文档不存在,无法更新: {file_path}")
                return False

            doc_id = doc['id']

            # 更新文档
            success = self.db.update_document(
                document_id=doc_id,
                content=doc_data['content'],
                file_size=doc_data['file_size'],
                file_type=doc_data['file_type'],
                content_hash=doc_data['content_hash'],
                modified_at=doc_data['modified_at'],
                status='active',
                metadata=doc_data.get('metadata')
            )

            if success:
                logger.debug(f"文档更新成功: {file_path}")
            else:
                logger.warning(f"文档更新失败: {file_path}")

            return success

        except Exception as e:
            logger.error(f"更新文档异常: {file_path}, 错误: {e}")
            return False

    # 将方法添加到 IndexManager 类
    IndexManager.refresh_index = refresh_index
    IndexManager._detect_changes = _detect_changes
    IndexManager._update_document = _update_document


# 自动执行方法注册
_add_incremental_methods_to_index_manager()
