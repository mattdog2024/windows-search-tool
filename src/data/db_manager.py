"""
SQLite FTS5 数据库管理器

此模块提供 SQLite 数据库的管理功能,包括:
- 数据库模式创建和初始化
- 性能优化配置 (WAL, cache_size 等)
- 连接管理和事务支持
"""

import sqlite3
import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Any, Generator
from datetime import datetime

logger = logging.getLogger(__name__)


class DBManager:
    """
    SQLite 数据库管理器

    提供数据库初始化、连接管理、性能优化配置等功能。
    使用 FTS5 全文搜索引擎提供高性能的文档内容检索。

    Attributes:
        db_path: 数据库文件路径
        connection: SQLite 数据库连接对象
    """

    def __init__(self, db_path: str):
        """
        初始化数据库管理器

        Args:
            db_path: 数据库文件路径

        Raises:
            sqlite3.Error: 数据库初始化失败
        """
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self._init_database()

    def _init_database(self) -> None:
        """
        初始化数据库

        创建数据库连接,配置性能优化参数,创建数据库模式。

        Raises:
            sqlite3.Error: 数据库初始化失败
        """
        try:
            # 确保数据库目录存在
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)

            # 创建数据库连接
            self.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False
            )
            self.connection.row_factory = sqlite3.Row

            logger.info(f"数据库连接已建立: {self.db_path}")

            # 配置性能优化
            self._configure_performance()

            # 创建数据库模式
            self._create_schema()

            logger.info("数据库初始化完成")

        except sqlite3.Error as e:
            logger.error(f"数据库初始化失败: {e}")
            raise

    def _configure_performance(self) -> None:
        """
        配置性能优化参数

        设置以下 PRAGMA 参数优化性能:
        - journal_mode=WAL: 提高并发性能
        - synchronous=NORMAL: 平衡性能和安全性
        - cache_size=-64000: 64MB 缓存
        - temp_store=MEMORY: 内存临时存储
        - mmap_size=268435456: 256MB 内存映射

        Raises:
            sqlite3.Error: 配置失败
        """
        cursor = self.connection.cursor()

        try:
            # WAL 模式提高并发性能
            cursor.execute("PRAGMA journal_mode=WAL")

            # 平衡性能和数据安全
            cursor.execute("PRAGMA synchronous=NORMAL")

            # 64MB 缓存 (负数表示 KB)
            cursor.execute("PRAGMA cache_size=-64000")

            # 内存临时存储
            cursor.execute("PRAGMA temp_store=MEMORY")

            # 256MB 内存映射
            cursor.execute("PRAGMA mmap_size=268435456")

            self.connection.commit()

            logger.info("数据库性能优化配置完成")

        except sqlite3.Error as e:
            logger.error(f"性能配置失败: {e}")
            raise

    def _create_schema(self) -> None:
        """
        创建数据库模式

        创建以下表和索引:
        - documents: 文档主表
        - documents_fts: FTS5 全文搜索表
        - document_metadata: 文档元数据表
        - document_summaries: AI 生成的摘要表
        - index_config: 索引配置表
        - 各种性能优化索引

        Raises:
            sqlite3.Error: 创建模式失败
        """
        cursor = self.connection.cursor()

        try:
            # 创建文档主表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL UNIQUE,
                    file_name TEXT NOT NULL,
                    file_size INTEGER,
                    file_type TEXT,
                    content_hash TEXT,
                    created_at DATETIME,
                    modified_at DATETIME,
                    indexed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active'
                )
            """)

            # 创建 FTS5 全文搜索表
            # 使用 porter 词干提取, unicode61 分词器, 移除音调符号
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                    content,
                    content_rowid=id,
                    tokenize='porter unicode61 remove_diacritics 2'
                )
            """)

            # 创建文档元数据表 (键值对存储)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS document_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT,
                    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE,
                    UNIQUE(document_id, key)
                )
            """)

            # 创建 AI 摘要表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS document_summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER NOT NULL UNIQUE,
                    summary TEXT,
                    key_points TEXT,
                    entities TEXT,
                    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
                )
            """)

            # 创建索引配置表 (键值对存储)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS index_config (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            # 创建性能优化索引
            self._create_indexes(cursor)

            self.connection.commit()

            logger.info("数据库模式创建完成")

        except sqlite3.Error as e:
            logger.error(f"创建数据库模式失败: {e}")
            raise

    def _create_indexes(self, cursor: sqlite3.Cursor) -> None:
        """
        创建性能优化索引

        为常用查询字段创建索引,提高查询性能。

        Args:
            cursor: 数据库游标

        Raises:
            sqlite3.Error: 创建索引失败
        """
        indexes = [
            # documents 表索引
            "CREATE INDEX IF NOT EXISTS idx_documents_file_path ON documents(file_path)",
            "CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents(file_type)",
            "CREATE INDEX IF NOT EXISTS idx_documents_modified_at ON documents(modified_at)",
            "CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status)",

            # document_metadata 表索引
            "CREATE INDEX IF NOT EXISTS idx_metadata_document_id ON document_metadata(document_id)",
            "CREATE INDEX IF NOT EXISTS idx_metadata_key ON document_metadata(key)",
        ]

        for index_sql in indexes:
            cursor.execute(index_sql)

        logger.info("数据库索引创建完成")

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Cursor, None, None]:
        """
        事务上下文管理器

        提供事务支持,自动提交或回滚。

        Yields:
            sqlite3.Cursor: 数据库游标

        Raises:
            sqlite3.Error: 事务执行失败

        Example:
            >>> with db.transaction() as cursor:
            ...     cursor.execute("INSERT INTO ...")
        """
        cursor = self.connection.cursor()
        try:
            yield cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logger.error(f"事务失败,已回滚: {e}")
            raise

    def check_integrity(self) -> bool:
        """
        检查数据库完整性

        Returns:
            bool: True 表示数据库完整,False 表示数据库损坏
        """
        try:
            cursor = self.connection.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]

            if result == "ok":
                logger.info("数据库完整性检查通过")
                return True
            else:
                logger.error(f"数据库完整性检查失败: {result}")
                return False

        except sqlite3.Error as e:
            logger.error(f"数据库完整性检查失败: {e}")
            return False

    def vacuum(self) -> None:
        """
        压缩数据库

        清理未使用的空间,优化数据库文件大小。

        Raises:
            sqlite3.Error: 压缩失败
        """
        try:
            self.connection.execute("VACUUM")
            logger.info("数据库压缩完成")
        except sqlite3.Error as e:
            logger.error(f"数据库压缩失败: {e}")
            raise

    def backup(self, backup_path: str) -> None:
        """
        备份数据库

        Args:
            backup_path: 备份文件路径

        Raises:
            sqlite3.Error: 备份失败
        """
        try:
            # 确保备份目录存在
            backup_dir = Path(backup_path).parent
            backup_dir.mkdir(parents=True, exist_ok=True)

            # 创建备份连接
            backup_conn = sqlite3.connect(backup_path)

            # 执行备份
            with backup_conn:
                self.connection.backup(backup_conn)

            backup_conn.close()

            logger.info(f"数据库备份完成: {backup_path}")

        except sqlite3.Error as e:
            logger.error(f"数据库备份失败: {e}")
            raise

    def get_db_info(self) -> dict[str, Any]:
        """
        获取数据库信息

        Returns:
            dict: 包含数据库各种信息的字典
        """
        cursor = self.connection.cursor()

        info = {
            'db_path': self.db_path,
            'db_size': Path(self.db_path).stat().st_size if Path(self.db_path).exists() else 0,
        }

        # 获取 PRAGMA 信息
        pragmas = [
            'journal_mode',
            'synchronous',
            'cache_size',
            'temp_store',
            'mmap_size',
        ]

        for pragma in pragmas:
            cursor.execute(f"PRAGMA {pragma}")
            info[pragma] = cursor.fetchone()[0]

        return info

    def close(self) -> None:
        """
        关闭数据库连接
        """
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("数据库连接已关闭")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()
        return False
