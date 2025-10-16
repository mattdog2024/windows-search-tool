"""
数据库模式和初始化单元测试

测试 DBManager 的数据库创建、模式初始化、性能配置等功能。
"""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
from src.data.db_manager import DBManager


class TestDBManagerInitialization:
    """测试 DBManager 初始化功能"""

    def test_db_creation(self, tmp_path):
        """测试数据库文件创建"""
        db_path = tmp_path / "test.db"

        db = DBManager(str(db_path))

        assert db_path.exists()
        assert db.connection is not None
        assert db.db_path == str(db_path)

        db.close()

    def test_db_directory_creation(self, tmp_path):
        """测试数据库目录自动创建"""
        db_path = tmp_path / "subdir" / "nested" / "test.db"

        db = DBManager(str(db_path))

        assert db_path.exists()
        assert db_path.parent.exists()

        db.close()

    def test_connection_settings(self, tmp_path):
        """测试数据库连接设置"""
        db_path = tmp_path / "test.db"
        db = DBManager(str(db_path))

        # 验证 row_factory 设置
        assert db.connection.row_factory == sqlite3.Row

        db.close()


class TestDBSchema:
    """测试数据库模式创建"""

    @pytest.fixture
    def db(self, tmp_path):
        """创建测试数据库"""
        db_path = tmp_path / "test.db"
        db_manager = DBManager(str(db_path))
        yield db_manager
        db_manager.close()

    def test_documents_table_exists(self, db):
        """测试 documents 表是否创建"""
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='documents'
        """)
        result = cursor.fetchone()

        assert result is not None
        assert result[0] == 'documents'

    def test_documents_table_schema(self, db):
        """测试 documents 表结构"""
        cursor = db.connection.cursor()
        cursor.execute("PRAGMA table_info(documents)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        # 验证所有必需字段存在
        expected_columns = {
            'id': 'INTEGER',
            'file_path': 'TEXT',
            'file_name': 'TEXT',
            'file_size': 'INTEGER',
            'file_type': 'TEXT',
            'content_hash': 'TEXT',
            'created_at': 'DATETIME',
            'modified_at': 'DATETIME',
            'indexed_at': 'DATETIME',
            'status': 'TEXT',
        }

        for col_name, col_type in expected_columns.items():
            assert col_name in columns
            assert columns[col_name] == col_type

    def test_documents_fts_table_exists(self, db):
        """测试 documents_fts FTS5 表是否创建"""
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='documents_fts'
        """)
        result = cursor.fetchone()

        assert result is not None
        assert result[0] == 'documents_fts'

    def test_fts_tokenizer_configuration(self, db):
        """测试 FTS5 分词器配置"""
        cursor = db.connection.cursor()

        # 验证 FTS5 表能正常使用
        # 插入测试数据
        cursor.execute("INSERT INTO documents (file_path, file_name) VALUES (?, ?)",
                      ("/test/path", "test.txt"))
        doc_id = cursor.lastrowid

        cursor.execute("INSERT INTO documents_fts (rowid, content) VALUES (?, ?)",
                      (doc_id, "This is a test document with porter stemming"))

        # 测试搜索功能 (porter 词干提取应该能匹配 test/testing)
        cursor.execute("""
            SELECT rowid FROM documents_fts WHERE documents_fts MATCH 'test'
        """)
        result = cursor.fetchone()

        assert result is not None
        assert result[0] == doc_id

    def test_document_metadata_table_exists(self, db):
        """测试 document_metadata 表是否创建"""
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='document_metadata'
        """)
        result = cursor.fetchone()

        assert result is not None
        assert result[0] == 'document_metadata'

    def test_document_metadata_table_schema(self, db):
        """测试 document_metadata 表结构"""
        cursor = db.connection.cursor()
        cursor.execute("PRAGMA table_info(document_metadata)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        expected_columns = {
            'id': 'INTEGER',
            'document_id': 'INTEGER',
            'key': 'TEXT',
            'value': 'TEXT',
        }

        for col_name, col_type in expected_columns.items():
            assert col_name in columns
            assert columns[col_name] == col_type

    def test_document_summaries_table_exists(self, db):
        """测试 document_summaries 表是否创建"""
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='document_summaries'
        """)
        result = cursor.fetchone()

        assert result is not None
        assert result[0] == 'document_summaries'

    def test_document_summaries_table_schema(self, db):
        """测试 document_summaries 表结构"""
        cursor = db.connection.cursor()
        cursor.execute("PRAGMA table_info(document_summaries)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        expected_columns = {
            'id': 'INTEGER',
            'document_id': 'INTEGER',
            'summary': 'TEXT',
            'key_points': 'TEXT',
            'entities': 'TEXT',
            'generated_at': 'DATETIME',
        }

        for col_name, col_type in expected_columns.items():
            assert col_name in columns
            assert columns[col_name] == col_type

    def test_index_config_table_exists(self, db):
        """测试 index_config 表是否创建"""
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='index_config'
        """)
        result = cursor.fetchone()

        assert result is not None
        assert result[0] == 'index_config'

    def test_index_config_table_schema(self, db):
        """测试 index_config 表结构"""
        cursor = db.connection.cursor()
        cursor.execute("PRAGMA table_info(index_config)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        expected_columns = {
            'key': 'TEXT',
            'value': 'TEXT',
        }

        for col_name, col_type in expected_columns.items():
            assert col_name in columns
            assert columns[col_name] == col_type

    def test_foreign_key_constraints(self, db):
        """测试外键约束"""
        cursor = db.connection.cursor()

        # 测试 document_metadata 外键约束
        cursor.execute("PRAGMA foreign_key_list(document_metadata)")
        fk_info = cursor.fetchall()

        assert len(fk_info) > 0
        assert fk_info[0][2] == 'documents'  # 引用的表

        # 测试 document_summaries 外键约束
        cursor.execute("PRAGMA foreign_key_list(document_summaries)")
        fk_info = cursor.fetchall()

        assert len(fk_info) > 0
        assert fk_info[0][2] == 'documents'  # 引用的表


class TestDBIndexes:
    """测试数据库索引创建"""

    @pytest.fixture
    def db(self, tmp_path):
        """创建测试数据库"""
        db_path = tmp_path / "test.db"
        db_manager = DBManager(str(db_path))
        yield db_manager
        db_manager.close()

    def test_all_indexes_created(self, db):
        """测试所有索引是否创建"""
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='index' AND name LIKE 'idx_%'
        """)
        indexes = [row[0] for row in cursor.fetchall()]

        expected_indexes = [
            'idx_documents_file_path',
            'idx_documents_file_type',
            'idx_documents_modified_at',
            'idx_documents_status',
            'idx_metadata_document_id',
            'idx_metadata_key',
        ]

        for index_name in expected_indexes:
            assert index_name in indexes, f"索引 {index_name} 未创建"

    def test_index_on_file_path(self, db):
        """测试 file_path 索引"""
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT sql FROM sqlite_master
            WHERE type='index' AND name='idx_documents_file_path'
        """)
        result = cursor.fetchone()

        assert result is not None
        assert 'file_path' in result[0]

    def test_index_on_file_type(self, db):
        """测试 file_type 索引"""
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT sql FROM sqlite_master
            WHERE type='index' AND name='idx_documents_file_type'
        """)
        result = cursor.fetchone()

        assert result is not None
        assert 'file_type' in result[0]

    def test_index_on_modified_at(self, db):
        """测试 modified_at 索引"""
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT sql FROM sqlite_master
            WHERE type='index' AND name='idx_documents_modified_at'
        """)
        result = cursor.fetchone()

        assert result is not None
        assert 'modified_at' in result[0]

    def test_index_on_status(self, db):
        """测试 status 索引"""
        cursor = db.connection.cursor()
        cursor.execute("""
            SELECT sql FROM sqlite_master
            WHERE type='index' AND name='idx_documents_status'
        """)
        result = cursor.fetchone()

        assert result is not None
        assert 'status' in result[0]


class TestPerformanceConfiguration:
    """测试性能配置"""

    @pytest.fixture
    def db(self, tmp_path):
        """创建测试数据库"""
        db_path = tmp_path / "test.db"
        db_manager = DBManager(str(db_path))
        yield db_manager
        db_manager.close()

    def test_wal_mode_enabled(self, db):
        """测试 WAL 模式是否启用"""
        cursor = db.connection.cursor()
        cursor.execute("PRAGMA journal_mode")
        result = cursor.fetchone()

        assert result[0].lower() == 'wal'

    def test_synchronous_mode(self, db):
        """测试同步模式配置"""
        cursor = db.connection.cursor()
        cursor.execute("PRAGMA synchronous")
        result = cursor.fetchone()

        # NORMAL = 1
        assert result[0] == 1

    def test_cache_size(self, db):
        """测试缓存大小配置"""
        cursor = db.connection.cursor()
        cursor.execute("PRAGMA cache_size")
        result = cursor.fetchone()

        # 应该是 -64000 (64MB)
        assert result[0] == -64000

    def test_temp_store_memory(self, db):
        """测试临时存储配置"""
        cursor = db.connection.cursor()
        cursor.execute("PRAGMA temp_store")
        result = cursor.fetchone()

        # MEMORY = 2
        assert result[0] == 2

    def test_mmap_size(self, db):
        """测试内存映射大小配置"""
        cursor = db.connection.cursor()
        cursor.execute("PRAGMA mmap_size")
        result = cursor.fetchone()

        # 应该是 268435456 (256MB)
        assert result[0] == 268435456


class TestDBManagerUtilities:
    """测试 DBManager 工具函数"""

    @pytest.fixture
    def db(self, tmp_path):
        """创建测试数据库"""
        db_path = tmp_path / "test.db"
        db_manager = DBManager(str(db_path))
        yield db_manager
        db_manager.close()

    def test_check_integrity(self, db):
        """测试数据库完整性检查"""
        result = db.check_integrity()
        assert result is True

    def test_vacuum(self, db):
        """测试数据库压缩"""
        # 插入一些数据
        cursor = db.connection.cursor()
        cursor.execute("INSERT INTO documents (file_path, file_name) VALUES (?, ?)",
                      ("/test/path1", "test1.txt"))
        cursor.execute("INSERT INTO documents (file_path, file_name) VALUES (?, ?)",
                      ("/test/path2", "test2.txt"))
        db.connection.commit()

        # 删除数据
        cursor.execute("DELETE FROM documents")
        db.connection.commit()

        # 压缩数据库
        db.vacuum()

        # 验证压缩成功 (不抛出异常即可)
        assert True

    def test_backup(self, db, tmp_path):
        """测试数据库备份"""
        backup_path = tmp_path / "backup" / "test_backup.db"

        # 插入一些测试数据
        cursor = db.connection.cursor()
        cursor.execute("INSERT INTO documents (file_path, file_name) VALUES (?, ?)",
                      ("/test/path", "test.txt"))
        db.connection.commit()

        # 执行备份
        db.backup(str(backup_path))

        # 验证备份文件存在
        assert backup_path.exists()

        # 验证备份数据完整性
        backup_conn = sqlite3.connect(str(backup_path))
        backup_cursor = backup_conn.cursor()
        backup_cursor.execute("SELECT COUNT(*) FROM documents")
        count = backup_cursor.fetchone()[0]
        backup_conn.close()

        assert count == 1

    def test_get_db_info(self, db):
        """测试获取数据库信息"""
        info = db.get_db_info()

        assert 'db_path' in info
        assert 'db_size' in info
        assert 'journal_mode' in info
        assert 'synchronous' in info
        assert 'cache_size' in info
        assert 'temp_store' in info
        assert 'mmap_size' in info

        assert info['journal_mode'].lower() == 'wal'
        assert info['cache_size'] == -64000

    def test_transaction_success(self, db):
        """测试事务成功提交"""
        with db.transaction() as cursor:
            cursor.execute("INSERT INTO documents (file_path, file_name) VALUES (?, ?)",
                          ("/test/path", "test.txt"))

        # 验证数据已插入
        cursor = db.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents")
        count = cursor.fetchone()[0]

        assert count == 1

    def test_transaction_rollback(self, db):
        """测试事务回滚"""
        try:
            with db.transaction() as cursor:
                cursor.execute("INSERT INTO documents (file_path, file_name) VALUES (?, ?)",
                              ("/test/path", "test.txt"))
                # 触发错误
                raise Exception("测试异常")
        except Exception:
            pass

        # 验证数据未插入 (已回滚)
        cursor = db.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents")
        count = cursor.fetchone()[0]

        assert count == 0

    def test_context_manager(self, tmp_path):
        """测试上下文管理器"""
        db_path = tmp_path / "test.db"

        with DBManager(str(db_path)) as db:
            assert db.connection is not None

        # 退出上下文后连接应关闭
        assert db.connection is None

    def test_close(self, tmp_path):
        """测试关闭数据库连接"""
        db_path = tmp_path / "test.db"
        db = DBManager(str(db_path))

        assert db.connection is not None

        db.close()

        assert db.connection is None


class TestDBConstraints:
    """测试数据库约束"""

    @pytest.fixture
    def db(self, tmp_path):
        """创建测试数据库"""
        db_path = tmp_path / "test.db"
        db_manager = DBManager(str(db_path))
        yield db_manager
        db_manager.close()

    def test_file_path_unique_constraint(self, db):
        """测试 file_path 唯一约束"""
        cursor = db.connection.cursor()

        # 插入第一条记录
        cursor.execute("INSERT INTO documents (file_path, file_name) VALUES (?, ?)",
                      ("/test/path", "test.txt"))
        db.connection.commit()

        # 尝试插入重复的 file_path
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("INSERT INTO documents (file_path, file_name) VALUES (?, ?)",
                          ("/test/path", "test2.txt"))
            db.connection.commit()

    def test_metadata_unique_constraint(self, db):
        """测试元数据唯一约束 (document_id, key)"""
        cursor = db.connection.cursor()

        # 插入文档
        cursor.execute("INSERT INTO documents (file_path, file_name) VALUES (?, ?)",
                      ("/test/path", "test.txt"))
        doc_id = cursor.lastrowid

        # 插入元数据
        cursor.execute("INSERT INTO document_metadata (document_id, key, value) VALUES (?, ?, ?)",
                      (doc_id, "author", "John Doe"))
        db.connection.commit()

        # 尝试插入重复的 (document_id, key)
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("INSERT INTO document_metadata (document_id, key, value) VALUES (?, ?, ?)",
                          (doc_id, "author", "Jane Doe"))
            db.connection.commit()

    def test_summary_unique_constraint(self, db):
        """测试摘要唯一约束 (document_id)"""
        cursor = db.connection.cursor()

        # 插入文档
        cursor.execute("INSERT INTO documents (file_path, file_name) VALUES (?, ?)",
                      ("/test/path", "test.txt"))
        doc_id = cursor.lastrowid

        # 插入摘要
        cursor.execute("INSERT INTO document_summaries (document_id, summary) VALUES (?, ?)",
                      (doc_id, "Test summary"))
        db.connection.commit()

        # 尝试插入重复的 document_id
        with pytest.raises(sqlite3.IntegrityError):
            cursor.execute("INSERT INTO document_summaries (document_id, summary) VALUES (?, ?)",
                          (doc_id, "Another summary"))
            db.connection.commit()

    def test_default_values(self, db):
        """测试默认值"""
        cursor = db.connection.cursor()

        # 插入最小数据
        cursor.execute("INSERT INTO documents (file_path, file_name) VALUES (?, ?)",
                      ("/test/path", "test.txt"))
        doc_id = cursor.lastrowid
        db.connection.commit()

        # 查询并验证默认值
        cursor.execute("SELECT status, indexed_at FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()

        assert row['status'] == 'active'
        assert row['indexed_at'] is not None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
