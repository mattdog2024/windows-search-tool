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
    """
    total_files: int = 0
    indexed_files: int = 0
    failed_files: int = 0
    skipped_files: int = 0
    total_size: int = 0
    elapsed_time: float = 0.0
    errors: List[Tuple[str, str]] = field(default_factory=list)


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

        # 初始化解析器工厂
        self.parser_factory = ParserFactory()

        # 从配置加载参数
        self.max_file_size = self.config.get('indexing.max_file_size_mb', 100) * 1024 * 1024
        self.excluded_extensions = self.config.get('indexing.excluded_extensions', [])
        self.excluded_paths = self.config.get('indexing.excluded_paths', [])
        self.batch_size = self.config.get('indexing.batch_size', 100)

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
