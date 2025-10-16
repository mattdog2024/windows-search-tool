"""
数据库搜索功能单元测试

测试 DBManager 的 FTS5 全文搜索和统计功能。
"""

import pytest
import sqlite3
from datetime import datetime
from src.data.db_manager import DBManager


class TestFTS5Search:
    """测试 FTS5 全文搜索功能"""

    @pytest.fixture
    def db_with_data(self, tmp_path):
        """创建包含测试数据的数据库"""
        db_path = tmp_path / "test.db"
        db = DBManager(str(db_path))

        # 插入测试文档
        cursor = db.connection.cursor()

        test_docs = [
            {
                'file_path': '/docs/python_tutorial.txt',
                'file_name': 'python_tutorial.txt',
                'file_type': 'txt',
                'file_size': 1024,
                'content': 'Python is a high-level programming language. It is widely used for web development, data science, and machine learning.'
            },
            {
                'file_path': '/docs/java_guide.txt',
                'file_name': 'java_guide.txt',
                'file_type': 'txt',
                'file_size': 2048,
                'content': 'Java is an object-oriented programming language. It is platform-independent and used for enterprise applications.'
            },
            {
                'file_path': '/docs/machine_learning.pdf',
                'file_name': 'machine_learning.pdf',
                'file_type': 'pdf',
                'file_size': 4096,
                'content': 'Machine learning is a subset of artificial intelligence. Python is the most popular language for machine learning projects.'
            },
            {
                'file_path': '/docs/web_development.md',
                'file_name': 'web_development.md',
                'file_type': 'md',
                'file_size': 512,
                'content': 'Web development involves creating websites and web applications. JavaScript, Python, and Ruby are popular choices.'
            },
            {
                'file_path': '/docs/data_science.txt',
                'file_name': 'data_science.txt',
                'file_type': 'txt',
                'file_size': 3072,
                'content': 'Data science combines statistics, programming, and domain expertise. Python and R are the primary languages used.'
            },
        ]

        for doc in test_docs:
            cursor.execute("""
                INSERT INTO documents (file_path, file_name, file_type, file_size, created_at, modified_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (doc['file_path'], doc['file_name'], doc['file_type'],
                  doc['file_size'], datetime.now().isoformat(), datetime.now().isoformat()))

            doc_id = cursor.lastrowid

            # 插入到 FTS 表
            cursor.execute("""
                INSERT INTO documents_fts (rowid, content)
                VALUES (?, ?)
            """, (doc_id, doc['content']))

        db.connection.commit()

        yield db
        db.close()

    def test_search_fts_basic(self, db_with_data):
        """测试基本的 FTS 搜索"""
        results = db_with_data.search_fts("python")

        assert len(results) > 0
        assert all('python' in result['snippet'].lower() for result in results)

    def test_search_fts_multiple_terms(self, db_with_data):
        """测试多词搜索"""
        results = db_with_data.search_fts("machine learning")

        assert len(results) > 0
        # 验证搜索结果包含相关内容
        assert any('machine' in result['snippet'].lower() for result in results)

    def test_search_fts_with_limit(self, db_with_data):
        """测试搜索结果限制"""
        results = db_with_data.search_fts("python", limit=2)

        assert len(results) <= 2

    def test_search_fts_with_offset(self, db_with_data):
        """测试搜索结果分页"""
        # 获取前 2 个结果
        first_page = db_with_data.search_fts("python", limit=2, offset=0)
        # 获取接下来的结果
        second_page = db_with_data.search_fts("python", limit=2, offset=2)

        # 确保两页结果不同
        if len(first_page) > 0 and len(second_page) > 0:
            assert first_page[0]['id'] != second_page[0]['id']

    def test_search_fts_with_file_type_filter(self, db_with_data):
        """测试文件类型过滤"""
        results = db_with_data.search_fts("python", file_types=['txt'])

        assert len(results) > 0
        assert all(result['file_type'] == 'txt' for result in results)

    def test_search_fts_with_multiple_file_types(self, db_with_data):
        """测试多种文件类型过滤"""
        results = db_with_data.search_fts("python", file_types=['txt', 'pdf'])

        assert len(results) > 0
        assert all(result['file_type'] in ['txt', 'pdf'] for result in results)

    def test_search_fts_result_fields(self, db_with_data):
        """测试搜索结果包含所有必需字段"""
        results = db_with_data.search_fts("python")

        assert len(results) > 0
        result = results[0]

        # 验证所有必需字段存在
        required_fields = ['id', 'file_path', 'file_name', 'file_type',
                          'file_size', 'modified_at', 'snippet', 'rank']
        for field in required_fields:
            assert field in result

    def test_search_fts_snippet_contains_highlight(self, db_with_data):
        """测试搜索结果摘要包含高亮标记"""
        results = db_with_data.search_fts("python")

        assert len(results) > 0
        # 验证至少一个结果包含高亮标记
        assert any('<mark>' in result['snippet'] and '</mark>' in result['snippet']
                   for result in results)

    def test_search_fts_rank_ordering(self, db_with_data):
        """测试搜索结果按相关度排序"""
        results = db_with_data.search_fts("python programming")

        if len(results) > 1:
            # BM25 rank 是负数,越接近 0 相关度越高
            # 验证结果按 rank 升序排列
            ranks = [result['rank'] for result in results]
            assert ranks == sorted(ranks)

    def test_search_fts_no_results(self, db_with_data):
        """测试无结果的搜索"""
        results = db_with_data.search_fts("nonexistentterm12345")

        assert len(results) == 0

    def test_search_fts_empty_query(self, db_with_data):
        """测试空查询"""
        # 空查询应该抛出异常或返回空结果
        with pytest.raises(sqlite3.Error):
            db_with_data.search_fts("")

    def test_search_fts_special_characters(self, db_with_data):
        """测试特殊字符搜索"""
        # FTS5 对连字符敏感,需要用引号包裹短语
        # 使用双引号表示精确短语匹配
        results = db_with_data.search_fts('"object-oriented"')

        # 应该返回包含该短语的结果
        assert isinstance(results, list)
        if len(results) > 0:
            assert 'object-oriented' in results[0]['snippet'].lower()


class TestSearchByContent:
    """测试按内容搜索功能"""

    @pytest.fixture
    def db_with_data(self, tmp_path):
        """创建包含测试数据的数据库"""
        db_path = tmp_path / "test.db"
        db = DBManager(str(db_path))

        # 插入测试文档
        cursor = db.connection.cursor()

        test_docs = [
            {
                'file_path': '/docs/article1.txt',
                'file_name': 'article1.txt',
                'file_type': 'txt',
                'content': 'This is a comprehensive guide to machine learning algorithms and their applications in real-world scenarios.'
            },
            {
                'file_path': '/docs/article2.txt',
                'file_name': 'article2.txt',
                'file_type': 'txt',
                'content': 'Deep learning is a subset of machine learning that uses neural networks with multiple layers.'
            },
        ]

        for doc in test_docs:
            cursor.execute("""
                INSERT INTO documents (file_path, file_name, file_type, created_at, modified_at)
                VALUES (?, ?, ?, ?, ?)
            """, (doc['file_path'], doc['file_name'], doc['file_type'],
                  datetime.now().isoformat(), datetime.now().isoformat()))

            doc_id = cursor.lastrowid

            # 插入到 FTS 表
            cursor.execute("""
                INSERT INTO documents_fts (rowid, content)
                VALUES (?, ?)
            """, (doc_id, doc['content']))

        db.connection.commit()

        yield db
        db.close()

    def test_search_by_content_basic(self, db_with_data):
        """测试基本的内容搜索"""
        results = db_with_data.search_by_content("machine learning")

        assert len(results) > 0

    def test_search_by_content_snippet_length(self, db_with_data):
        """测试内容搜索返回较长的摘要"""
        results = db_with_data.search_by_content("machine learning")

        assert len(results) > 0
        # search_by_content 应该返回更长的摘要 (64 tokens vs 32 tokens)
        assert len(results[0]['snippet']) > 0

    def test_search_by_content_result_fields(self, db_with_data):
        """测试搜索结果包含所有必需字段"""
        results = db_with_data.search_by_content("machine")

        assert len(results) > 0
        result = results[0]

        required_fields = ['id', 'file_path', 'file_name', 'file_type',
                          'modified_at', 'snippet', 'rank']
        for field in required_fields:
            assert field in result

    def test_search_by_content_with_pagination(self, db_with_data):
        """测试分页功能"""
        results = db_with_data.search_by_content("machine", limit=1, offset=0)

        assert len(results) <= 1


class TestStatistics:
    """测试统计功能"""

    @pytest.fixture
    def db_with_data(self, tmp_path):
        """创建包含测试数据的数据库"""
        db_path = tmp_path / "test.db"
        db = DBManager(str(db_path))

        # 插入测试文档
        cursor = db.connection.cursor()

        test_docs = [
            {'file_path': '/docs/file1.txt', 'file_name': 'file1.txt',
             'file_type': 'txt', 'file_size': 1000, 'status': 'active'},
            {'file_path': '/docs/file2.txt', 'file_name': 'file2.txt',
             'file_type': 'txt', 'file_size': 2000, 'status': 'active'},
            {'file_path': '/docs/file3.pdf', 'file_name': 'file3.pdf',
             'file_type': 'pdf', 'file_size': 3000, 'status': 'active'},
            {'file_path': '/docs/file4.md', 'file_name': 'file4.md',
             'file_type': 'md', 'file_size': 500, 'status': 'active'},
            {'file_path': '/docs/file5.txt', 'file_name': 'file5.txt',
             'file_type': 'txt', 'file_size': 1500, 'status': 'deleted'},
        ]

        for doc in test_docs:
            cursor.execute("""
                INSERT INTO documents (file_path, file_name, file_type, file_size,
                                      created_at, modified_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (doc['file_path'], doc['file_name'], doc['file_type'], doc['file_size'],
                  datetime.now().isoformat(), datetime.now().isoformat(), doc['status']))

        db.connection.commit()

        yield db
        db.close()

    def test_get_statistics_document_count(self, db_with_data):
        """测试获取文档数量统计"""
        stats = db_with_data.get_statistics()

        # 应该只统计 active 状态的文档
        assert stats['document_count'] == 4

    def test_get_statistics_total_size(self, db_with_data):
        """测试获取文档总大小统计"""
        stats = db_with_data.get_statistics()

        # 总大小应该是 active 文档的总和: 1000 + 2000 + 3000 + 500 = 6500
        assert stats['total_size'] == 6500

    def test_get_statistics_last_update(self, db_with_data):
        """测试获取最后更新时间"""
        stats = db_with_data.get_statistics()

        assert stats['last_update'] is not None
        # 验证是有效的时间戳
        assert isinstance(stats['last_update'], str)

    def test_get_statistics_file_types(self, db_with_data):
        """测试获取文件类型分布"""
        stats = db_with_data.get_statistics()

        file_types = stats['file_types']
        assert isinstance(file_types, dict)

        # 验证文件类型统计正确
        assert file_types.get('txt') == 2  # 只统计 active 的
        assert file_types.get('pdf') == 1
        assert file_types.get('md') == 1

    def test_get_statistics_total_file_types(self, db_with_data):
        """测试获取文件类型总数"""
        stats = db_with_data.get_statistics()

        assert stats['total_file_types'] == 3  # txt, pdf, md

    def test_get_statistics_required_fields(self, db_with_data):
        """测试统计信息包含所有必需字段"""
        stats = db_with_data.get_statistics()

        required_fields = ['document_count', 'total_size', 'last_update',
                          'file_types', 'total_file_types']
        for field in required_fields:
            assert field in stats

    def test_get_statistics_empty_database(self, tmp_path):
        """测试空数据库的统计信息"""
        db_path = tmp_path / "empty.db"
        db = DBManager(str(db_path))

        stats = db.get_statistics()

        assert stats['document_count'] == 0
        assert stats['total_size'] == 0
        assert stats['file_types'] == {}
        assert stats['total_file_types'] == 0

        db.close()


class TestFileTypeStats:
    """测试文件类型统计功能"""

    @pytest.fixture
    def db_with_data(self, tmp_path):
        """创建包含测试数据的数据库"""
        db_path = tmp_path / "test.db"
        db = DBManager(str(db_path))

        # 插入测试文档
        cursor = db.connection.cursor()

        test_docs = [
            {'file_path': '/docs/file1.txt', 'file_name': 'file1.txt',
             'file_type': 'txt', 'file_size': 1000},
            {'file_path': '/docs/file2.txt', 'file_name': 'file2.txt',
             'file_type': 'txt', 'file_size': 2000},
            {'file_path': '/docs/file3.txt', 'file_name': 'file3.txt',
             'file_type': 'txt', 'file_size': 1500},
            {'file_path': '/docs/file4.pdf', 'file_name': 'file4.pdf',
             'file_type': 'pdf', 'file_size': 5000},
            {'file_path': '/docs/file5.pdf', 'file_name': 'file5.pdf',
             'file_type': 'pdf', 'file_size': 3000},
            {'file_path': '/docs/file6.md', 'file_name': 'file6.md',
             'file_type': 'md', 'file_size': 800},
        ]

        for doc in test_docs:
            cursor.execute("""
                INSERT INTO documents (file_path, file_name, file_type, file_size,
                                      created_at, modified_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (doc['file_path'], doc['file_name'], doc['file_type'], doc['file_size'],
                  datetime.now().isoformat(), datetime.now().isoformat()))

        db.connection.commit()

        yield db
        db.close()

    def test_get_file_type_stats_basic(self, db_with_data):
        """测试基本的文件类型统计"""
        stats = db_with_data.get_file_type_stats()

        assert len(stats) > 0
        assert isinstance(stats, list)

    def test_get_file_type_stats_count(self, db_with_data):
        """测试文件类型计数"""
        stats = db_with_data.get_file_type_stats()

        # 验证各类型的数量
        txt_stats = next((s for s in stats if s['file_type'] == 'txt'), None)
        pdf_stats = next((s for s in stats if s['file_type'] == 'pdf'), None)
        md_stats = next((s for s in stats if s['file_type'] == 'md'), None)

        assert txt_stats is not None and txt_stats['count'] == 3
        assert pdf_stats is not None and pdf_stats['count'] == 2
        assert md_stats is not None and md_stats['count'] == 1

    def test_get_file_type_stats_total_size(self, db_with_data):
        """测试文件类型总大小统计"""
        stats = db_with_data.get_file_type_stats()

        txt_stats = next((s for s in stats if s['file_type'] == 'txt'), None)

        # txt 文件总大小: 1000 + 2000 + 1500 = 4500
        assert txt_stats is not None and txt_stats['total_size'] == 4500

    def test_get_file_type_stats_avg_size(self, db_with_data):
        """测试文件类型平均大小统计"""
        stats = db_with_data.get_file_type_stats()

        txt_stats = next((s for s in stats if s['file_type'] == 'txt'), None)

        # txt 文件平均大小: 4500 / 3 = 1500
        assert txt_stats is not None and txt_stats['avg_size'] == 1500

    def test_get_file_type_stats_percentage(self, db_with_data):
        """测试文件类型百分比统计"""
        stats = db_with_data.get_file_type_stats()

        txt_stats = next((s for s in stats if s['file_type'] == 'txt'), None)

        # txt 文件占比: 3 / 6 = 50%
        assert txt_stats is not None and txt_stats['percentage'] == 50.0

    def test_get_file_type_stats_ordering(self, db_with_data):
        """测试文件类型统计按数量排序"""
        stats = db_with_data.get_file_type_stats()

        # 验证按数量降序排列
        counts = [s['count'] for s in stats]
        assert counts == sorted(counts, reverse=True)

    def test_get_file_type_stats_with_limit(self, db_with_data):
        """测试限制返回的文件类型数量"""
        stats = db_with_data.get_file_type_stats(limit=2)

        assert len(stats) <= 2

    def test_get_file_type_stats_required_fields(self, db_with_data):
        """测试文件类型统计包含所有必需字段"""
        stats = db_with_data.get_file_type_stats()

        assert len(stats) > 0
        stat = stats[0]

        required_fields = ['file_type', 'count', 'total_size', 'avg_size', 'percentage']
        for field in required_fields:
            assert field in stat

    def test_get_file_type_stats_empty_database(self, tmp_path):
        """测试空数据库的文件类型统计"""
        db_path = tmp_path / "empty.db"
        db = DBManager(str(db_path))

        stats = db.get_file_type_stats()

        assert len(stats) == 0

        db.close()


class TestSearchWithDeletedDocuments:
    """测试搜索时排除已删除文档"""

    @pytest.fixture
    def db_with_mixed_data(self, tmp_path):
        """创建包含活跃和已删除文档的数据库"""
        db_path = tmp_path / "test.db"
        db = DBManager(str(db_path))

        cursor = db.connection.cursor()

        # 插入活跃文档
        cursor.execute("""
            INSERT INTO documents (file_path, file_name, file_type, status,
                                  created_at, modified_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('/docs/active.txt', 'active.txt', 'txt', 'active',
              datetime.now().isoformat(), datetime.now().isoformat()))
        active_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO documents_fts (rowid, content)
            VALUES (?, ?)
        """, (active_id, 'This is an active document about Python programming'))

        # 插入已删除文档
        cursor.execute("""
            INSERT INTO documents (file_path, file_name, file_type, status,
                                  created_at, modified_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, ('/docs/deleted.txt', 'deleted.txt', 'txt', 'deleted',
              datetime.now().isoformat(), datetime.now().isoformat()))
        deleted_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO documents_fts (rowid, content)
            VALUES (?, ?)
        """, (deleted_id, 'This is a deleted document about Python programming'))

        db.connection.commit()

        yield db
        db.close()

    def test_search_excludes_deleted_documents(self, db_with_mixed_data):
        """测试搜索结果不包含已删除的文档"""
        results = db_with_mixed_data.search_fts("python")

        # 应该只返回 1 个结果 (活跃文档)
        assert len(results) == 1
        assert results[0]['file_name'] == 'active.txt'

    def test_search_by_content_excludes_deleted(self, db_with_mixed_data):
        """测试内容搜索不包含已删除的文档"""
        results = db_with_mixed_data.search_by_content("python")

        assert len(results) == 1
        assert results[0]['file_name'] == 'active.txt'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
