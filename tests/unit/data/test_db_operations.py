"""
数据库 CRUD 操作单元测试

测试 DBManager 的增删改查操作、批量插入、事务管理等功能。
"""

import pytest
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from src.data.db_manager import DBManager


class TestDocumentInsert:
    """测试文档插入操作"""

    @pytest.fixture
    def db(self, tmp_path):
        """创建测试数据库"""
        db_path = tmp_path / "test.db"
        db_manager = DBManager(str(db_path))
        yield db_manager
        db_manager.close()

    def test_insert_document_basic(self, db):
        """测试基本文档插入"""
        doc_id = db.insert_document(
            file_path="/test/file1.txt",
            file_name="file1.txt",
            content="This is test content",
            file_size=1024,
            file_type="txt"
        )

        assert doc_id > 0
        assert isinstance(doc_id, int)

    def test_insert_document_with_metadata(self, db):
        """测试插入带元数据的文档"""
        metadata = {
            "author": "John Doe",
            "category": "test",
            "version": "1.0"
        }

        doc_id = db.insert_document(
            file_path="/test/file2.txt",
            file_name="file2.txt",
            content="Test content with metadata",
            file_type="txt",
            metadata=metadata
        )

        # 验证插入成功
        assert doc_id > 0

        # 验证文档可以查询
        doc = db.get_document_by_id(doc_id)
        assert doc is not None
        assert doc['file_path'] == "/test/file2.txt"
        assert doc['metadata']['author'] == "John Doe"
        assert doc['metadata']['category'] == "test"

    def test_insert_document_with_timestamps(self, db):
        """测试插入带时间戳的文档"""
        now = datetime.now().isoformat()

        doc_id = db.insert_document(
            file_path="/test/file3.txt",
            file_name="file3.txt",
            content="Test content",
            created_at=now,
            modified_at=now
        )

        assert doc_id > 0

        # 验证时间戳
        doc = db.get_document_by_id(doc_id)
        assert doc['created_at'] == now
        assert doc['modified_at'] == now

    def test_insert_document_with_hash(self, db):
        """测试插入带哈希值的文档"""
        content_hash = "abc123def456"

        doc_id = db.insert_document(
            file_path="/test/file4.txt",
            file_name="file4.txt",
            content="Test content",
            content_hash=content_hash
        )

        doc = db.get_document_by_id(doc_id)
        assert doc['content_hash'] == content_hash

    def test_insert_duplicate_path(self, db):
        """测试插入重复路径的文档"""
        # 插入第一个文档
        db.insert_document(
            file_path="/test/duplicate.txt",
            file_name="duplicate.txt",
            content="First content"
        )

        # 尝试插入相同路径的文档,应该失败
        with pytest.raises(sqlite3.IntegrityError):
            db.insert_document(
                file_path="/test/duplicate.txt",
                file_name="duplicate2.txt",
                content="Second content"
            )

    def test_insert_document_fts_content(self, db):
        """测试插入文档后 FTS 表有内容"""
        content = "This is searchable content about Python programming"

        doc_id = db.insert_document(
            file_path="/test/searchable.txt",
            file_name="searchable.txt",
            content=content
        )

        # 验证 FTS 表有记录
        cursor = db.connection.cursor()
        cursor.execute("SELECT rowid, content FROM documents_fts WHERE rowid = ?", (doc_id,))
        fts_row = cursor.fetchone()

        assert fts_row is not None
        assert fts_row['content'] == content


class TestBatchInsert:
    """测试批量插入操作"""

    @pytest.fixture
    def db(self, tmp_path):
        """创建测试数据库"""
        db_path = tmp_path / "test.db"
        db_manager = DBManager(str(db_path))
        yield db_manager
        db_manager.close()

    def test_batch_insert_small_batch(self, db):
        """测试小批量插入 (< 100 条)"""
        documents = [
            {
                "file_path": f"/test/file{i}.txt",
                "file_name": f"file{i}.txt",
                "content": f"Content for file {i}",
                "file_size": 1024 * i,
                "file_type": "txt"
            }
            for i in range(10)
        ]

        doc_ids = db.batch_insert_documents(documents)

        assert len(doc_ids) == 10
        assert all(isinstance(doc_id, int) for doc_id in doc_ids)
        assert all(doc_id > 0 for doc_id in doc_ids)

    def test_batch_insert_large_batch(self, db):
        """测试大批量插入 (> 100 条)"""
        documents = [
            {
                "file_path": f"/test/large/file{i}.txt",
                "file_name": f"file{i}.txt",
                "content": f"Content for file {i}",
                "file_size": 1024,
                "file_type": "txt"
            }
            for i in range(250)
        ]

        doc_ids = db.batch_insert_documents(documents)

        assert len(doc_ids) == 250
        assert all(doc_id > 0 for doc_id in doc_ids)

    def test_batch_insert_with_metadata(self, db):
        """测试批量插入带元数据的文档"""
        documents = [
            {
                "file_path": f"/test/meta/file{i}.txt",
                "file_name": f"file{i}.txt",
                "content": f"Content {i}",
                "metadata": {
                    "index": str(i),
                    "category": "test"
                }
            }
            for i in range(5)
        ]

        doc_ids = db.batch_insert_documents(documents)

        # 验证元数据
        doc = db.get_document_by_id(doc_ids[0])
        assert doc['metadata']['index'] == "0"
        assert doc['metadata']['category'] == "test"

    def test_batch_insert_performance(self, db):
        """测试批量插入性能 (应 >= 100 条/秒)"""
        documents = [
            {
                "file_path": f"/test/perf/file{i}.txt",
                "file_name": f"file{i}.txt",
                "content": f"Performance test content {i}",
                "file_size": 1024,
                "file_type": "txt"
            }
            for i in range(500)
        ]

        start_time = time.time()
        doc_ids = db.batch_insert_documents(documents)
        elapsed_time = time.time() - start_time

        # 计算插入速率
        rate = len(doc_ids) / elapsed_time

        assert len(doc_ids) == 500
        # 性能要求: >= 100 条/秒
        assert rate >= 100, f"插入速率 {rate:.2f} 条/秒 < 100 条/秒"

    def test_batch_insert_custom_batch_size(self, db):
        """测试自定义批次大小"""
        documents = [
            {
                "file_path": f"/test/custom/file{i}.txt",
                "file_name": f"file{i}.txt",
                "content": f"Content {i}"
            }
            for i in range(150)
        ]

        # 使用批次大小 50
        doc_ids = db.batch_insert_documents(documents, batch_size=50)

        assert len(doc_ids) == 150


class TestDocumentUpdate:
    """测试文档更新操作"""

    @pytest.fixture
    def db(self, tmp_path):
        """创建测试数据库"""
        db_path = tmp_path / "test.db"
        db_manager = DBManager(str(db_path))
        yield db_manager
        db_manager.close()

    def test_update_document_content(self, db):
        """测试更新文档内容"""
        # 插入文档
        doc_id = db.insert_document(
            file_path="/test/update1.txt",
            file_name="update1.txt",
            content="Original content"
        )

        # 更新内容
        success = db.update_document(
            document_id=doc_id,
            content="Updated content"
        )

        assert success is True

        # 验证更新 - 通过 FTS 搜索
        cursor = db.connection.cursor()
        cursor.execute("SELECT content FROM documents_fts WHERE rowid = ?", (doc_id,))
        fts_content = cursor.fetchone()['content']
        assert fts_content == "Updated content"

    def test_update_document_fields(self, db):
        """测试更新文档字段"""
        doc_id = db.insert_document(
            file_path="/test/update2.txt",
            file_name="update2.txt",
            content="Content",
            file_size=1024,
            file_type="txt"
        )

        # 更新多个字段
        success = db.update_document(
            document_id=doc_id,
            file_size=2048,
            file_type="md",
            content_hash="newhash123"
        )

        assert success is True

        # 验证更新
        doc = db.get_document_by_id(doc_id)
        assert doc['file_size'] == 2048
        assert doc['file_type'] == "md"
        assert doc['content_hash'] == "newhash123"

    def test_update_document_status(self, db):
        """测试更新文档状态"""
        doc_id = db.insert_document(
            file_path="/test/update3.txt",
            file_name="update3.txt",
            content="Content"
        )

        # 更新状态为 deleted
        success = db.update_document(
            document_id=doc_id,
            status="deleted"
        )

        assert success is True

        doc = db.get_document_by_id(doc_id)
        assert doc['status'] == "deleted"

    def test_update_document_metadata(self, db):
        """测试更新文档元数据"""
        doc_id = db.insert_document(
            file_path="/test/update4.txt",
            file_name="update4.txt",
            content="Content",
            metadata={"author": "John", "version": "1.0"}
        )

        # 更新元数据
        new_metadata = {"author": "Jane", "version": "2.0", "status": "final"}
        success = db.update_document(
            document_id=doc_id,
            metadata=new_metadata
        )

        assert success is True

        # 验证元数据已更新
        doc = db.get_document_by_id(doc_id)
        assert doc['metadata']['author'] == "Jane"
        assert doc['metadata']['version'] == "2.0"
        assert doc['metadata']['status'] == "final"
        # 旧的元数据应该被替换
        assert len(doc['metadata']) == 3

    def test_update_nonexistent_document(self, db):
        """测试更新不存在的文档"""
        success = db.update_document(
            document_id=99999,
            content="New content"
        )

        assert success is False

    def test_update_indexed_at_timestamp(self, db):
        """测试更新操作自动更新 indexed_at"""
        doc_id = db.insert_document(
            file_path="/test/update5.txt",
            file_name="update5.txt",
            content="Content"
        )

        # 获取原始 indexed_at
        doc_before = db.get_document_by_id(doc_id)
        indexed_at_before = doc_before['indexed_at']

        # 稍作延迟
        time.sleep(0.1)

        # 更新文档
        db.update_document(document_id=doc_id, file_size=2048)

        # 获取更新后的 indexed_at
        doc_after = db.get_document_by_id(doc_id)
        indexed_at_after = doc_after['indexed_at']

        # indexed_at 应该已更新
        assert indexed_at_after >= indexed_at_before


class TestDocumentDelete:
    """测试文档删除操作"""

    @pytest.fixture
    def db(self, tmp_path):
        """创建测试数据库"""
        db_path = tmp_path / "test.db"
        db_manager = DBManager(str(db_path))
        yield db_manager
        db_manager.close()

    def test_soft_delete_document(self, db):
        """测试软删除文档"""
        doc_id = db.insert_document(
            file_path="/test/delete1.txt",
            file_name="delete1.txt",
            content="Content to delete"
        )

        # 软删除
        success = db.delete_document(doc_id, hard_delete=False)
        assert success is True

        # 文档应该还存在,但状态为 deleted
        doc = db.get_document_by_id(doc_id)
        assert doc is not None
        assert doc['status'] == "deleted"

    def test_hard_delete_document(self, db):
        """测试硬删除文档"""
        doc_id = db.insert_document(
            file_path="/test/delete2.txt",
            file_name="delete2.txt",
            content="Content to delete"
        )

        # 硬删除
        success = db.delete_document(doc_id, hard_delete=True)
        assert success is True

        # 文档应该完全不存在
        doc = db.get_document_by_id(doc_id)
        assert doc is None

    def test_hard_delete_removes_fts_entry(self, db):
        """测试硬删除同时删除 FTS 记录"""
        doc_id = db.insert_document(
            file_path="/test/delete3.txt",
            file_name="delete3.txt",
            content="Content to delete"
        )

        # 硬删除
        db.delete_document(doc_id, hard_delete=True)

        # FTS 记录应该被删除
        cursor = db.connection.cursor()
        cursor.execute("SELECT rowid FROM documents_fts WHERE rowid = ?", (doc_id,))
        fts_row = cursor.fetchone()
        assert fts_row is None

    def test_hard_delete_cascades_metadata(self, db):
        """测试硬删除级联删除元数据"""
        doc_id = db.insert_document(
            file_path="/test/delete4.txt",
            file_name="delete4.txt",
            content="Content",
            metadata={"author": "John", "version": "1.0"}
        )

        # 硬删除
        db.delete_document(doc_id, hard_delete=True)

        # 元数据应该被级联删除
        cursor = db.connection.cursor()
        cursor.execute("SELECT * FROM document_metadata WHERE document_id = ?", (doc_id,))
        metadata_rows = cursor.fetchall()
        assert len(metadata_rows) == 0

    def test_delete_nonexistent_document(self, db):
        """测试删除不存在的文档"""
        success = db.delete_document(99999, hard_delete=False)
        assert success is False

    def test_batch_delete_documents(self, db):
        """测试批量删除文档"""
        # 插入多个文档
        doc_ids = []
        for i in range(5):
            doc_id = db.insert_document(
                file_path=f"/test/batch_delete{i}.txt",
                file_name=f"batch_delete{i}.txt",
                content=f"Content {i}"
            )
            doc_ids.append(doc_id)

        # 批量软删除
        deleted_count = db.delete_documents(doc_ids, hard_delete=False)
        assert deleted_count == 5

        # 验证所有文档状态为 deleted
        for doc_id in doc_ids:
            doc = db.get_document_by_id(doc_id)
            assert doc['status'] == "deleted"

    def test_batch_hard_delete_documents(self, db):
        """测试批量硬删除文档"""
        # 插入多个文档
        doc_ids = []
        for i in range(5):
            doc_id = db.insert_document(
                file_path=f"/test/batch_hard_delete{i}.txt",
                file_name=f"batch_hard_delete{i}.txt",
                content=f"Content {i}"
            )
            doc_ids.append(doc_id)

        # 批量硬删除
        deleted_count = db.delete_documents(doc_ids, hard_delete=True)
        assert deleted_count == 5

        # 验证所有文档不存在
        for doc_id in doc_ids:
            doc = db.get_document_by_id(doc_id)
            assert doc is None

    def test_batch_delete_with_nonexistent_ids(self, db):
        """测试批量删除包含不存在的 ID"""
        # 插入 2 个文档
        doc_id1 = db.insert_document(
            file_path="/test/exists1.txt",
            file_name="exists1.txt",
            content="Content 1"
        )
        doc_id2 = db.insert_document(
            file_path="/test/exists2.txt",
            file_name="exists2.txt",
            content="Content 2"
        )

        # 尝试删除,包括不存在的 ID
        doc_ids = [doc_id1, 99999, doc_id2, 99998]
        deleted_count = db.delete_documents(doc_ids, hard_delete=True)

        # 只有 2 个文档被删除
        assert deleted_count == 2


class TestDocumentQuery:
    """测试文档查询操作"""

    @pytest.fixture
    def db(self, tmp_path):
        """创建测试数据库"""
        db_path = tmp_path / "test.db"
        db_manager = DBManager(str(db_path))
        yield db_manager
        db_manager.close()

    def test_get_document_by_id(self, db):
        """测试根据 ID 查询文档"""
        doc_id = db.insert_document(
            file_path="/test/query1.txt",
            file_name="query1.txt",
            content="Query test content",
            file_size=1024,
            file_type="txt"
        )

        doc = db.get_document_by_id(doc_id)

        assert doc is not None
        assert doc['id'] == doc_id
        assert doc['file_path'] == "/test/query1.txt"
        assert doc['file_name'] == "query1.txt"
        assert doc['file_size'] == 1024
        assert doc['file_type'] == "txt"
        assert doc['status'] == "active"

    def test_get_document_by_id_nonexistent(self, db):
        """测试查询不存在的文档 ID"""
        doc = db.get_document_by_id(99999)
        assert doc is None

    def test_get_document_by_path(self, db):
        """测试根据路径查询文档"""
        db.insert_document(
            file_path="/test/query2.txt",
            file_name="query2.txt",
            content="Content"
        )

        doc = db.get_document_by_path("/test/query2.txt")

        assert doc is not None
        assert doc['file_path'] == "/test/query2.txt"
        assert doc['file_name'] == "query2.txt"

    def test_get_document_by_path_nonexistent(self, db):
        """测试查询不存在的文件路径"""
        doc = db.get_document_by_path("/nonexistent/path.txt")
        assert doc is None

    def test_get_document_includes_metadata(self, db):
        """测试查询文档包含元数据"""
        metadata = {"author": "John", "version": "1.0"}

        doc_id = db.insert_document(
            file_path="/test/query3.txt",
            file_name="query3.txt",
            content="Content",
            metadata=metadata
        )

        doc = db.get_document_by_id(doc_id)

        assert 'metadata' in doc
        assert doc['metadata']['author'] == "John"
        assert doc['metadata']['version'] == "1.0"

    def test_list_documents_all(self, db):
        """测试列出所有文档"""
        # 插入多个文档
        for i in range(10):
            db.insert_document(
                file_path=f"/test/list{i}.txt",
                file_name=f"list{i}.txt",
                content=f"Content {i}"
            )

        docs = db.list_documents(limit=20)

        assert len(docs) == 10
        assert all('file_path' in doc for doc in docs)

    def test_list_documents_with_status_filter(self, db):
        """测试按状态过滤文档列表"""
        # 插入活跃文档
        for i in range(3):
            db.insert_document(
                file_path=f"/test/active{i}.txt",
                file_name=f"active{i}.txt",
                content=f"Content {i}"
            )

        # 插入并删除文档
        for i in range(2):
            doc_id = db.insert_document(
                file_path=f"/test/deleted{i}.txt",
                file_name=f"deleted{i}.txt",
                content=f"Content {i}"
            )
            db.delete_document(doc_id, hard_delete=False)

        # 查询活跃文档
        active_docs = db.list_documents(status='active')
        assert len(active_docs) == 3

        # 查询已删除文档
        deleted_docs = db.list_documents(status='deleted')
        assert len(deleted_docs) == 2

    def test_list_documents_with_file_type_filter(self, db):
        """测试按文件类型过滤"""
        # 插入不同类型的文档
        for i in range(3):
            db.insert_document(
                file_path=f"/test/file{i}.txt",
                file_name=f"file{i}.txt",
                content=f"Content {i}",
                file_type="txt"
            )

        for i in range(2):
            db.insert_document(
                file_path=f"/test/file{i}.pdf",
                file_name=f"file{i}.pdf",
                content=f"Content {i}",
                file_type="pdf"
            )

        # 查询 txt 文件
        txt_docs = db.list_documents(file_type='txt')
        assert len(txt_docs) == 3

        # 查询 pdf 文件
        pdf_docs = db.list_documents(file_type='pdf')
        assert len(pdf_docs) == 2

    def test_list_documents_pagination(self, db):
        """测试分页查询"""
        # 插入 25 个文档
        for i in range(25):
            db.insert_document(
                file_path=f"/test/page{i}.txt",
                file_name=f"page{i}.txt",
                content=f"Content {i}"
            )

        # 第一页 (10 条)
        page1 = db.list_documents(limit=10, offset=0)
        assert len(page1) == 10

        # 第二页 (10 条)
        page2 = db.list_documents(limit=10, offset=10)
        assert len(page2) == 10

        # 第三页 (5 条)
        page3 = db.list_documents(limit=10, offset=20)
        assert len(page3) == 5

        # 验证文档不重复
        page1_ids = {doc['id'] for doc in page1}
        page2_ids = {doc['id'] for doc in page2}
        assert len(page1_ids & page2_ids) == 0

    def test_list_documents_ordering(self, db):
        """测试排序"""
        # 插入文档,不同的时间戳和大小
        for i in range(5):
            db.insert_document(
                file_path=f"/test/order{i}.txt",
                file_name=f"order{i}.txt",
                content=f"Content {i}",
                file_size=1024 * (i + 1)
            )
            time.sleep(0.1)  # 确保时间戳明显不同

        # 按 file_size 降序 (更可靠的测试)
        docs_size_desc = db.list_documents(order_by='file_size', order_desc=True)
        assert docs_size_desc[0]['file_size'] == 1024 * 5  # 最大的
        assert docs_size_desc[0]['file_name'] == "order4.txt"

        # 按 file_size 升序
        docs_size_asc = db.list_documents(order_by='file_size', order_desc=False)
        assert docs_size_asc[0]['file_size'] == 1024  # 最小的
        assert docs_size_asc[0]['file_name'] == "order0.txt"

        # 按 file_name 升序
        docs_name_asc = db.list_documents(order_by='file_name', order_desc=False)
        assert docs_name_asc[0]['file_name'] == "order0.txt"

        # 按 file_name 降序
        docs_name_desc = db.list_documents(order_by='file_name', order_desc=True)
        assert docs_name_desc[0]['file_name'] == "order4.txt"

    def test_list_documents_combined_filters(self, db):
        """测试组合过滤条件"""
        # 插入不同状态和类型的文档
        for i in range(3):
            db.insert_document(
                file_path=f"/test/combo{i}.txt",
                file_name=f"combo{i}.txt",
                content=f"Content {i}",
                file_type="txt"
            )

        for i in range(2):
            doc_id = db.insert_document(
                file_path=f"/test/combo{i}.pdf",
                file_name=f"combo{i}.pdf",
                content=f"Content {i}",
                file_type="pdf"
            )
            if i == 0:
                db.delete_document(doc_id, hard_delete=False)

        # 查询: status='active' AND file_type='pdf'
        docs = db.list_documents(status='active', file_type='pdf')
        assert len(docs) == 1


class TestTransactionIntegrity:
    """测试事务完整性"""

    @pytest.fixture
    def db(self, tmp_path):
        """创建测试数据库"""
        db_path = tmp_path / "test.db"
        db_manager = DBManager(str(db_path))
        yield db_manager
        db_manager.close()

    def test_insert_transaction_rollback(self, db):
        """测试插入失败时事务回滚"""
        try:
            with db.transaction() as cursor:
                # 插入有效文档
                cursor.execute("""
                    INSERT INTO documents (file_path, file_name)
                    VALUES (?, ?)
                """, ("/test/rollback1.txt", "rollback1.txt"))

                # 故意插入重复路径触发错误
                cursor.execute("""
                    INSERT INTO documents (file_path, file_name)
                    VALUES (?, ?)
                """, ("/test/rollback1.txt", "rollback2.txt"))
        except sqlite3.IntegrityError:
            pass

        # 验证事务已回滚,没有文档被插入
        cursor = db.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents")
        count = cursor.fetchone()[0]
        assert count == 0

    def test_batch_insert_transaction_integrity(self, db):
        """测试批量插入的事务完整性"""
        # 创建包含重复路径的文档列表
        documents = [
            {"file_path": "/test/batch1.txt", "file_name": "batch1.txt", "content": "Content 1"},
            {"file_path": "/test/batch2.txt", "file_name": "batch2.txt", "content": "Content 2"},
            {"file_path": "/test/batch1.txt", "file_name": "batch3.txt", "content": "Content 3"},  # 重复
        ]

        # 批量插入应该失败
        with pytest.raises(sqlite3.IntegrityError):
            db.batch_insert_documents(documents)

        # 验证整个批次都被回滚
        cursor = db.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM documents")
        count = cursor.fetchone()[0]
        assert count == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
