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

            # 启用外键约束
            self.connection.execute("PRAGMA foreign_keys=ON")

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

    # ==================== CRUD 操作 ====================

    def insert_document(
        self,
        file_path: str,
        file_name: str,
        content: str,
        file_size: Optional[int] = None,
        file_type: Optional[str] = None,
        content_hash: Optional[str] = None,
        created_at: Optional[str] = None,
        modified_at: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None
    ) -> int:
        """
        插入单个文档

        Args:
            file_path: 文件路径 (必须唯一)
            file_name: 文件名
            content: 文档内容 (用于全文搜索)
            file_size: 文件大小 (字节)
            file_type: 文件类型/扩展名
            content_hash: 内容哈希值
            created_at: 创建时间
            modified_at: 修改时间
            metadata: 元数据键值对

        Returns:
            int: 插入文档的 ID

        Raises:
            sqlite3.IntegrityError: 文件路径重复
            sqlite3.Error: 插入失败

        Example:
            >>> doc_id = db.insert_document(
            ...     file_path="/path/to/file.txt",
            ...     file_name="file.txt",
            ...     content="document content",
            ...     file_type="txt",
            ...     metadata={"author": "John"}
            ... )
        """
        with self.transaction() as cursor:
            # 插入文档主记录
            cursor.execute("""
                INSERT INTO documents (
                    file_path, file_name, file_size, file_type,
                    content_hash, created_at, modified_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                file_path,
                file_name,
                file_size,
                file_type,
                content_hash,
                created_at,
                modified_at
            ))

            doc_id = cursor.lastrowid

            # 插入全文搜索内容
            cursor.execute("""
                INSERT INTO documents_fts (rowid, content)
                VALUES (?, ?)
            """, (doc_id, content))

            # 插入元数据
            if metadata:
                for key, value in metadata.items():
                    cursor.execute("""
                        INSERT INTO document_metadata (document_id, key, value)
                        VALUES (?, ?, ?)
                    """, (doc_id, key, str(value)))

            logger.info(f"文档插入成功: {file_path} (ID: {doc_id})")
            return doc_id

    def batch_insert_documents(
        self,
        documents: list[dict[str, Any]],
        batch_size: int = 100
    ) -> list[int]:
        """
        批量插入文档

        使用事务批量提交优化性能,支持分批处理大量数据。

        Args:
            documents: 文档列表,每个文档包含以下字段:
                - file_path (必需): 文件路径
                - file_name (必需): 文件名
                - content (必需): 文档内容
                - file_size: 文件大小
                - file_type: 文件类型
                - content_hash: 内容哈希
                - created_at: 创建时间
                - modified_at: 修改时间
                - metadata: 元数据字典
            batch_size: 批次大小 (默认 100)

        Returns:
            list[int]: 插入文档的 ID 列表

        Raises:
            sqlite3.Error: 批量插入失败

        Example:
            >>> docs = [
            ...     {"file_path": "/path1.txt", "file_name": "1.txt", "content": "..."},
            ...     {"file_path": "/path2.txt", "file_name": "2.txt", "content": "..."}
            ... ]
            >>> doc_ids = db.batch_insert_documents(docs)
        """
        doc_ids = []
        total = len(documents)

        # 分批处理
        for i in range(0, total, batch_size):
            batch = documents[i:i + batch_size]

            with self.transaction() as cursor:
                for doc in batch:
                    # 插入主记录
                    cursor.execute("""
                        INSERT INTO documents (
                            file_path, file_name, file_size, file_type,
                            content_hash, created_at, modified_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        doc['file_path'],
                        doc['file_name'],
                        doc.get('file_size'),
                        doc.get('file_type'),
                        doc.get('content_hash'),
                        doc.get('created_at'),
                        doc.get('modified_at')
                    ))

                    doc_id = cursor.lastrowid
                    doc_ids.append(doc_id)

                    # 插入全文搜索内容
                    cursor.execute("""
                        INSERT INTO documents_fts (rowid, content)
                        VALUES (?, ?)
                    """, (doc_id, doc['content']))

                    # 插入元数据
                    if 'metadata' in doc and doc['metadata']:
                        for key, value in doc['metadata'].items():
                            cursor.execute("""
                                INSERT INTO document_metadata (document_id, key, value)
                                VALUES (?, ?, ?)
                            """, (doc_id, key, str(value)))

            logger.info(f"批量插入进度: {min(i + batch_size, total)}/{total}")

        logger.info(f"批量插入完成: {len(doc_ids)} 条记录")
        return doc_ids

    def update_document(
        self,
        document_id: int,
        content: Optional[str] = None,
        file_size: Optional[int] = None,
        file_type: Optional[str] = None,
        content_hash: Optional[str] = None,
        modified_at: Optional[str] = None,
        status: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None
    ) -> bool:
        """
        更新文档信息

        Args:
            document_id: 文档 ID
            content: 更新的内容 (会同步更新 FTS 表)
            file_size: 文件大小
            file_type: 文件类型
            content_hash: 内容哈希
            modified_at: 修改时间
            status: 文档状态 (active/deleted/error)
            metadata: 元数据键值对 (会覆盖现有元数据)

        Returns:
            bool: 更新成功返回 True,文档不存在返回 False

        Raises:
            sqlite3.Error: 更新失败

        Example:
            >>> success = db.update_document(
            ...     document_id=123,
            ...     content="new content",
            ...     status="active"
            ... )
        """
        with self.transaction() as cursor:
            # 检查文档是否存在
            cursor.execute("SELECT id FROM documents WHERE id = ?", (document_id,))
            if not cursor.fetchone():
                logger.warning(f"文档不存在: ID {document_id}")
                return False

            # 构建更新语句
            update_fields = []
            update_values = []

            if file_size is not None:
                update_fields.append("file_size = ?")
                update_values.append(file_size)

            if file_type is not None:
                update_fields.append("file_type = ?")
                update_values.append(file_type)

            if content_hash is not None:
                update_fields.append("content_hash = ?")
                update_values.append(content_hash)

            if modified_at is not None:
                update_fields.append("modified_at = ?")
                update_values.append(modified_at)

            if status is not None:
                update_fields.append("status = ?")
                update_values.append(status)

            # 更新 indexed_at 时间戳
            update_fields.append("indexed_at = CURRENT_TIMESTAMP")

            # 更新主表
            if update_fields:
                update_values.append(document_id)
                sql = f"UPDATE documents SET {', '.join(update_fields)} WHERE id = ?"
                cursor.execute(sql, update_values)

            # 更新全文搜索内容
            if content is not None:
                cursor.execute("""
                    UPDATE documents_fts SET content = ? WHERE rowid = ?
                """, (content, document_id))

            # 更新元数据
            if metadata is not None:
                # 删除旧元数据
                cursor.execute("""
                    DELETE FROM document_metadata WHERE document_id = ?
                """, (document_id,))

                # 插入新元数据
                for key, value in metadata.items():
                    cursor.execute("""
                        INSERT INTO document_metadata (document_id, key, value)
                        VALUES (?, ?, ?)
                    """, (document_id, key, str(value)))

            logger.info(f"文档更新成功: ID {document_id}")
            return True

    def delete_document(
        self,
        document_id: int,
        hard_delete: bool = False
    ) -> bool:
        """
        删除文档

        Args:
            document_id: 文档 ID
            hard_delete: True 为硬删除(物理删除),False 为软删除(标记为 deleted)

        Returns:
            bool: 删除成功返回 True,文档不存在返回 False

        Raises:
            sqlite3.Error: 删除失败

        Example:
            >>> # 软删除
            >>> db.delete_document(123)
            >>> # 硬删除
            >>> db.delete_document(123, hard_delete=True)
        """
        with self.transaction() as cursor:
            # 检查文档是否存在
            cursor.execute("SELECT id FROM documents WHERE id = ?", (document_id,))
            if not cursor.fetchone():
                logger.warning(f"文档不存在: ID {document_id}")
                return False

            if hard_delete:
                # 硬删除 - 物理删除记录
                # 删除主记录 (外键级联会自动删除 metadata 和 summaries)
                cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))

                # 删除 FTS 记录
                cursor.execute("DELETE FROM documents_fts WHERE rowid = ?", (document_id,))

                logger.info(f"文档硬删除成功: ID {document_id}")
            else:
                # 软删除 - 标记为 deleted
                cursor.execute("""
                    UPDATE documents SET status = 'deleted', indexed_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (document_id,))

                logger.info(f"文档软删除成功: ID {document_id}")

            return True

    def delete_documents(
        self,
        document_ids: list[int],
        hard_delete: bool = False
    ) -> int:
        """
        批量删除文档

        Args:
            document_ids: 文档 ID 列表
            hard_delete: True 为硬删除,False 为软删除

        Returns:
            int: 实际删除的文档数量

        Raises:
            sqlite3.Error: 删除失败

        Example:
            >>> deleted_count = db.delete_documents([1, 2, 3], hard_delete=False)
        """
        deleted_count = 0

        with self.transaction() as cursor:
            for doc_id in document_ids:
                # 检查文档是否存在
                cursor.execute("SELECT id FROM documents WHERE id = ?", (doc_id,))
                if not cursor.fetchone():
                    continue

                if hard_delete:
                    # 硬删除
                    cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
                    cursor.execute("DELETE FROM documents_fts WHERE rowid = ?", (doc_id,))
                else:
                    # 软删除
                    cursor.execute("""
                        UPDATE documents SET status = 'deleted', indexed_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (doc_id,))

                deleted_count += 1

        logger.info(f"批量删除完成: {deleted_count}/{len(document_ids)} 条记录")
        return deleted_count

    def get_document_by_id(self, document_id: int) -> Optional[dict[str, Any]]:
        """
        根据 ID 查询文档

        Args:
            document_id: 文档 ID

        Returns:
            Optional[dict]: 文档信息字典,不存在返回 None

        Example:
            >>> doc = db.get_document_by_id(123)
            >>> print(doc['file_path'], doc['file_name'])
        """
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT
                id, file_path, file_name, file_size, file_type,
                content_hash, created_at, modified_at, indexed_at, status
            FROM documents
            WHERE id = ?
        """, (document_id,))

        row = cursor.fetchone()
        if not row:
            return None

        # 转换为字典
        doc = dict(row)

        # 查询元数据
        cursor.execute("""
            SELECT key, value FROM document_metadata
            WHERE document_id = ?
        """, (document_id,))
        doc['metadata'] = {row['key']: row['value'] for row in cursor.fetchall()}

        return doc

    def get_document_by_path(self, file_path: str) -> Optional[dict[str, Any]]:
        """
        根据文件路径查询文档

        Args:
            file_path: 文件路径

        Returns:
            Optional[dict]: 文档信息字典,不存在返回 None

        Example:
            >>> doc = db.get_document_by_path("/path/to/file.txt")
        """
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT
                id, file_path, file_name, file_size, file_type,
                content_hash, created_at, modified_at, indexed_at, status
            FROM documents
            WHERE file_path = ?
        """, (file_path,))

        row = cursor.fetchone()
        if not row:
            return None

        # 转换为字典
        doc = dict(row)

        # 查询元数据
        cursor.execute("""
            SELECT key, value FROM document_metadata
            WHERE document_id = ?
        """, (doc['id'],))
        doc['metadata'] = {row['key']: row['value'] for row in cursor.fetchall()}

        return doc

    def list_documents(
        self,
        status: Optional[str] = None,
        file_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        order_by: str = 'indexed_at',
        order_desc: bool = True
    ) -> list[dict[str, Any]]:
        """
        查询文档列表

        Args:
            status: 过滤状态 (active/deleted/error)
            file_type: 过滤文件类型
            limit: 返回记录数量限制
            offset: 偏移量 (分页)
            order_by: 排序字段 (indexed_at/modified_at/file_size)
            order_desc: True 为降序,False 为升序

        Returns:
            list[dict]: 文档列表

        Example:
            >>> # 查询所有活跃文档
            >>> docs = db.list_documents(status='active', limit=50)
            >>> # 查询 PDF 文件
            >>> pdfs = db.list_documents(file_type='pdf')
        """
        # 构建查询条件
        conditions = []
        params = []

        if status:
            conditions.append("status = ?")
            params.append(status)

        if file_type:
            conditions.append("file_type = ?")
            params.append(file_type)

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        # 排序方向
        order_direction = "DESC" if order_desc else "ASC"

        # 验证排序字段
        valid_order_fields = ['indexed_at', 'modified_at', 'file_size', 'file_name']
        if order_by not in valid_order_fields:
            order_by = 'indexed_at'

        # 执行查询
        cursor = self.connection.cursor()
        sql = f"""
            SELECT
                id, file_path, file_name, file_size, file_type,
                content_hash, created_at, modified_at, indexed_at, status
            FROM documents
            {where_clause}
            ORDER BY {order_by} {order_direction}
            LIMIT ? OFFSET ?
        """

        params.extend([limit, offset])
        cursor.execute(sql, params)

        # 转换为字典列表
        documents = [dict(row) for row in cursor.fetchall()]

        return documents

    # ==================== 搜索和统计 ====================

    def search_fts(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        file_types: Optional[list[str]] = None
    ) -> list[dict[str, Any]]:
        """
        FTS5 全文搜索

        使用 FTS5 引擎进行全文搜索,支持 BM25 相关度排序和分页。

        Args:
            query: FTS5 查询字符串,支持 FTS5 查询语法
            limit: 返回结果数量限制,默认 20
            offset: 结果偏移量,用于分页,默认 0
            file_types: 可选的文件类型过滤列表,如 ['txt', 'pdf']

        Returns:
            list[dict]: 搜索结果列表,每个结果包含:
                - id: 文档 ID
                - file_path: 文件路径
                - file_name: 文件名
                - file_type: 文件类型
                - file_size: 文件大小
                - modified_at: 修改时间
                - snippet: 搜索结果摘要,包含高亮标记
                - rank: BM25 相关度分数 (负数,越接近 0 相关度越高)

        Example:
            >>> results = db.search_fts("python programming", limit=10)
            >>> for result in results:
            ...     print(f"{result['file_name']}: {result['snippet']}")
        """
        cursor = self.connection.cursor()

        try:
            # 构建查询语句
            base_query = """
                SELECT
                    d.id,
                    d.file_path,
                    d.file_name,
                    d.file_type,
                    d.file_size,
                    d.modified_at,
                    snippet(documents_fts, 0, '<mark>', '</mark>', '...', 32) as snippet,
                    rank as rank
                FROM documents_fts
                JOIN documents d ON documents_fts.rowid = d.id
                WHERE documents_fts MATCH ?
                  AND d.status = 'active'
            """

            # 添加文件类型过滤
            params = [query]
            if file_types:
                placeholders = ','.join(['?' for _ in file_types])
                base_query += f" AND d.file_type IN ({placeholders})"
                params.extend(file_types)

            # 添加排序和分页
            base_query += " ORDER BY rank LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(base_query, params)

            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row['id'],
                    'file_path': row['file_path'],
                    'file_name': row['file_name'],
                    'file_type': row['file_type'],
                    'file_size': row['file_size'],
                    'modified_at': row['modified_at'],
                    'snippet': row['snippet'],
                    'rank': row['rank']
                })

            logger.info(f"FTS 搜索完成: 查询='{query}', 结果数={len(results)}")
            return results

        except sqlite3.Error as e:
            logger.error(f"FTS 搜索失败: {e}")
            raise

    def search_by_content(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0
    ) -> list[dict[str, Any]]:
        """
        按内容搜索文档

        这是 search_fts() 的简化版本,返回更详细的搜索结果,
        包含更长的内容摘要。

        Args:
            query: 搜索查询字符串
            limit: 返回结果数量限制,默认 20
            offset: 结果偏移量,用于分页,默认 0

        Returns:
            list[dict]: 搜索结果列表,每个结果包含:
                - id: 文档 ID
                - file_path: 文件路径
                - file_name: 文件名
                - file_type: 文件类型
                - modified_at: 修改时间
                - snippet: 搜索结果摘要 (更长的片段)
                - rank: BM25 相关度分数

        Example:
            >>> results = db.search_by_content("machine learning")
            >>> for result in results:
            ...     print(result['snippet'])
        """
        cursor = self.connection.cursor()

        try:
            cursor.execute("""
                SELECT
                    d.id,
                    d.file_path,
                    d.file_name,
                    d.file_type,
                    d.modified_at,
                    snippet(documents_fts, 0, '<mark>', '</mark>', '...', 64) as snippet,
                    rank
                FROM documents_fts
                JOIN documents d ON documents_fts.rowid = d.id
                WHERE documents_fts MATCH ?
                  AND d.status = 'active'
                ORDER BY rank
                LIMIT ? OFFSET ?
            """, (query, limit, offset))

            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row['id'],
                    'file_path': row['file_path'],
                    'file_name': row['file_name'],
                    'file_type': row['file_type'],
                    'modified_at': row['modified_at'],
                    'snippet': row['snippet'],
                    'rank': row['rank']
                })

            logger.info(f"内容搜索完成: 查询='{query}', 结果数={len(results)}")
            return results

        except sqlite3.Error as e:
            logger.error(f"内容搜索失败: {e}")
            raise

    def get_statistics(self) -> dict[str, Any]:
        """
        获取数据库统计信息

        返回数据库的整体统计信息,包括文档数量、总大小、
        最后更新时间和文件类型分布。

        Returns:
            dict: 统计信息字典,包含:
                - document_count: 活跃文档总数
                - total_size: 所有文档总大小(字节)
                - last_update: 最后索引时间
                - file_types: 文件类型分布字典 {类型: 数量}
                - total_file_types: 文件类型总数

        Example:
            >>> stats = db.get_statistics()
            >>> print(f"共有 {stats['document_count']} 个文档")
            >>> print(f"总大小: {stats['total_size']} 字节")
        """
        cursor = self.connection.cursor()

        try:
            # 获取活跃文档数量
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM documents
                WHERE status='active'
            """)
            doc_count = cursor.fetchone()['count']

            # 获取文档总大小
            cursor.execute("""
                SELECT COALESCE(SUM(file_size), 0) as total_size
                FROM documents
                WHERE status='active'
            """)
            total_size = cursor.fetchone()['total_size']

            # 获取最后更新时间
            cursor.execute("""
                SELECT MAX(indexed_at) as last_update
                FROM documents
            """)
            last_update = cursor.fetchone()['last_update']

            # 获取文件类型分布
            cursor.execute("""
                SELECT file_type, COUNT(*) as count
                FROM documents
                WHERE status='active'
                GROUP BY file_type
                ORDER BY count DESC
            """)
            file_types = {row['file_type']: row['count'] for row in cursor.fetchall()}

            stats = {
                'document_count': doc_count,
                'total_size': total_size,
                'last_update': last_update,
                'file_types': file_types,
                'total_file_types': len(file_types)
            }

            logger.info(f"统计信息: {doc_count} 个文档, {len(file_types)} 种文件类型")
            return stats

        except sqlite3.Error as e:
            logger.error(f"获取统计信息失败: {e}")
            raise

    def get_file_type_stats(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        获取文件类型统计信息

        返回文件类型的详细统计,包括数量、总大小等信息。

        Args:
            limit: 返回的文件类型数量限制,默认 10

        Returns:
            list[dict]: 文件类型统计列表,每个条目包含:
                - file_type: 文件类型
                - count: 该类型的文档数量
                - total_size: 该类型文档的总大小(字节)
                - avg_size: 该类型文档的平均大小(字节)
                - percentage: 该类型占总文档数的百分比

        Example:
            >>> stats = db.get_file_type_stats(limit=5)
            >>> for stat in stats:
            ...     print(f"{stat['file_type']}: {stat['count']} 个文件")
        """
        cursor = self.connection.cursor()

        try:
            # 获取总文档数
            cursor.execute("""
                SELECT COUNT(*) as total_count
                FROM documents
                WHERE status='active'
            """)
            total_count = cursor.fetchone()['total_count']

            # 获取每种文件类型的统计信息
            cursor.execute("""
                SELECT
                    file_type,
                    COUNT(*) as count,
                    COALESCE(SUM(file_size), 0) as total_size,
                    COALESCE(AVG(file_size), 0) as avg_size
                FROM documents
                WHERE status='active'
                GROUP BY file_type
                ORDER BY count DESC
                LIMIT ?
            """, (limit,))

            results = []
            for row in cursor.fetchall():
                percentage = (row['count'] / total_count * 100) if total_count > 0 else 0
                results.append({
                    'file_type': row['file_type'],
                    'count': row['count'],
                    'total_size': row['total_size'],
                    'avg_size': int(row['avg_size']),
                    'percentage': round(percentage, 2)
                })

            logger.info(f"文件类型统计: 返回 {len(results)} 种类型")
            return results

        except sqlite3.Error as e:
            logger.error(f"获取文件类型统计失败: {e}")
            raise

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
