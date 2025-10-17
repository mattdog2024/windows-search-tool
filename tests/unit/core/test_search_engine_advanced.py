"""
高级搜索功能单元测试

测试 SearchEngine 的高级搜索功能,包括:
- 日期范围过滤
- 文件大小范围过滤
- 搜索建议
- 搜索统计
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path

from src.core.search_engine import SearchEngine, SearchResult, SearchResponse
from src.data.db_manager import DBManager


class TestAdvancedSearch:
    """高级搜索功能测试"""

    @pytest.fixture
    def db_manager(self):
        """创建临时数据库用于测试"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name

        db = DBManager(db_path)
        db.connect()
        db.initialize_schema()

        yield db

        db.close()
        if os.path.exists(db_path):
            os.remove(db_path)

    @pytest.fixture
    def search_engine(self, db_manager):
        """创建搜索引擎实例"""
        return SearchEngine(db_manager)

    @pytest.fixture
    def sample_documents(self, db_manager):
        """创建测试文档"""
        # 创建不同日期和大小的文档
        now = datetime.now()
        documents = [
            {
                'file_path': '/path/to/report_2024.pdf',
                'file_name': 'report_2024.pdf',
                'file_type': 'pdf',
                'file_size': 1024 * 1024,  # 1MB
                'modified_at': (now - timedelta(days=1)).isoformat(),
                'content': 'Annual report for 2024'
            },
            {
                'file_path': '/path/to/report_2023.pdf',
                'file_name': 'report_2023.pdf',
                'file_type': 'pdf',
                'file_size': 2 * 1024 * 1024,  # 2MB
                'modified_at': (now - timedelta(days=365)).isoformat(),
                'content': 'Annual report for 2023'
            },
            {
                'file_path': '/path/to/document.txt',
                'file_name': 'document.txt',
                'file_type': 'txt',
                'file_size': 512 * 1024,  # 512KB
                'modified_at': (now - timedelta(days=7)).isoformat(),
                'content': 'Important documentation file'
            },
            {
                'file_path': '/path/to/notes.txt',
                'file_name': 'notes.txt',
                'file_type': 'txt',
                'file_size': 10 * 1024,  # 10KB
                'modified_at': now.isoformat(),
                'content': 'Personal notes and documentation'
            }
        ]

        # 插入文档
        for doc in documents:
            db_manager.add_document(
                file_path=doc['file_path'],
                file_name=doc['file_name'],
                file_type=doc['file_type'],
                file_size=doc['file_size'],
                modified_at=doc['modified_at']
            )
            # 添加到 FTS 索引
            doc_id = db_manager.connection.execute(
                "SELECT id FROM documents WHERE file_path = ?",
                (doc['file_path'],)
            ).fetchone()['id']

            db_manager.connection.execute(
                "INSERT INTO documents_fts(rowid, content) VALUES (?, ?)",
                (doc_id, doc['content'])
            )

        db_manager.connection.commit()
        return documents

    def test_advanced_search_date_range(self, search_engine, sample_documents):
        """测试日期范围过滤"""
        now = datetime.now()
        date_from = (now - timedelta(days=10)).isoformat()
        date_to = now.isoformat()

        response = search_engine.advanced_search(
            query="report",
            date_from=date_from,
            date_to=date_to
        )

        # 应该只返回最近10天内的文档
        assert response.total >= 1
        # report_2024.pdf 应该在结果中
        file_names = [r.file_name for r in response.results]
        assert 'report_2024.pdf' in file_names
        # report_2023.pdf 不应该在结果中
        assert 'report_2023.pdf' not in file_names

    def test_advanced_search_size_range(self, search_engine, sample_documents):
        """测试文件大小范围过滤"""
        # 搜索大于 500KB 的文件
        size_min = 500 * 1024  # 500KB

        response = search_engine.advanced_search(
            query="report",
            size_min=size_min
        )

        # 应该返回 >= 500KB 的文档
        assert response.total >= 2
        for result in response.results:
            assert result.metadata['file_size'] >= size_min

    def test_advanced_search_size_max(self, search_engine, sample_documents):
        """测试最大文件大小过滤"""
        # 搜索小于 1MB 的文件
        size_max = 1024 * 1024  # 1MB

        response = search_engine.advanced_search(
            query="documentation",
            size_max=size_max
        )

        # 所有结果应该 <= 1MB
        for result in response.results:
            assert result.metadata['file_size'] <= size_max

    def test_advanced_search_combined_filters(self, search_engine, sample_documents):
        """测试组合过滤条件"""
        now = datetime.now()
        date_from = (now - timedelta(days=30)).isoformat()
        size_min = 100 * 1024  # 100KB
        size_max = 1024 * 1024  # 1MB

        response = search_engine.advanced_search(
            query="documentation",
            file_types=['txt'],
            date_from=date_from,
            size_min=size_min,
            size_max=size_max
        )

        # 验证所有过滤条件
        for result in response.results:
            assert result.metadata['file_type'] == 'txt'
            assert result.metadata['file_size'] >= size_min
            assert result.metadata['file_size'] <= size_max
            # 日期应该在范围内
            modified_at = result.metadata['modified_at']
            assert modified_at >= date_from

    def test_advanced_search_invalid_date_range(self, search_engine):
        """测试无效的日期范围"""
        with pytest.raises(ValueError, match="起始日期不能晚于结束日期"):
            search_engine.advanced_search(
                query="test",
                date_from="2024-12-31",
                date_to="2024-01-01"
            )

    def test_advanced_search_invalid_size_range(self, search_engine):
        """测试无效的文件大小范围"""
        with pytest.raises(ValueError, match="最小文件大小不能大于最大文件大小"):
            search_engine.advanced_search(
                query="test",
                size_min=1000,
                size_max=500
            )

    def test_advanced_search_negative_size(self, search_engine):
        """测试负数文件大小"""
        with pytest.raises(ValueError, match="最小文件大小不能为负数"):
            search_engine.advanced_search(
                query="test",
                size_min=-100
            )


class TestSearchSuggestions:
    """搜索建议功能测试"""

    @pytest.fixture
    def db_manager(self):
        """创建临时数据库用于测试"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name

        db = DBManager(db_path)
        db.connect()
        db.initialize_schema()

        yield db

        db.close()
        if os.path.exists(db_path):
            os.remove(db_path)

    @pytest.fixture
    def search_engine(self, db_manager):
        """创建搜索引擎实例"""
        return SearchEngine(db_manager)

    @pytest.fixture
    def sample_documents(self, db_manager):
        """创建测试文档"""
        documents = [
            ('document.txt', 'txt', 'This is a document'),
            ('documentation.pdf', 'pdf', 'Documentation file'),
            ('docker_setup.md', 'md', 'Docker setup guide'),
            ('project_doc.txt', 'txt', 'Project documentation'),
        ]

        for file_name, file_type, content in documents:
            db_manager.add_document(
                file_path=f'/path/{file_name}',
                file_name=file_name,
                file_type=file_type,
                file_size=1024,
                modified_at=datetime.now().isoformat()
            )
            # 添加到 FTS 索引
            doc_id = db_manager.connection.execute(
                "SELECT id FROM documents WHERE file_name = ?",
                (file_name,)
            ).fetchone()['id']

            db_manager.connection.execute(
                "INSERT INTO documents_fts(rowid, content) VALUES (?, ?)",
                (doc_id, content)
            )

        db_manager.connection.commit()
        return documents

    def test_get_suggestions_basic(self, search_engine, sample_documents):
        """测试基本搜索建议"""
        suggestions = search_engine.get_suggestions("doc", limit=5)

        # 应该包含以 "doc" 开头的建议
        assert len(suggestions) >= 1
        for suggestion in suggestions:
            assert suggestion.startswith("doc")

    def test_get_suggestions_with_history(self, search_engine, sample_documents):
        """测试基于搜索历史的建议"""
        # 先执行几次搜索以建立历史
        search_engine.search("documentation", mode="fuzzy")
        search_engine.search("docker", mode="fuzzy")

        suggestions = search_engine.get_suggestions("doc", limit=10)

        # 建议应该包含历史查询
        assert len(suggestions) >= 1
        assert any("doc" in s for s in suggestions)

    def test_get_suggestions_empty_prefix(self, search_engine):
        """测试空前缀"""
        with pytest.raises(ValueError, match="搜索前缀不能为空"):
            search_engine.get_suggestions("")

    def test_get_suggestions_limit(self, search_engine, sample_documents):
        """测试限制建议数量"""
        suggestions = search_engine.get_suggestions("doc", limit=2)

        # 不应超过限制数量
        assert len(suggestions) <= 2


class TestSearchStats:
    """搜索统计功能测试"""

    @pytest.fixture
    def db_manager(self):
        """创建临时数据库用于测试"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name

        db = DBManager(db_path)
        db.connect()
        db.initialize_schema()

        yield db

        db.close()
        if os.path.exists(db_path):
            os.remove(db_path)

    @pytest.fixture
    def search_engine(self, db_manager):
        """创建搜索引擎实例"""
        return SearchEngine(db_manager)

    @pytest.fixture
    def sample_documents(self, db_manager):
        """创建测试文档"""
        db_manager.add_document(
            file_path='/path/test.txt',
            file_name='test.txt',
            file_type='txt',
            file_size=1024,
            modified_at=datetime.now().isoformat()
        )

        doc_id = db_manager.connection.execute(
            "SELECT id FROM documents WHERE file_path = ?",
            ('/path/test.txt',)
        ).fetchone()['id']

        db_manager.connection.execute(
            "INSERT INTO documents_fts(rowid, content) VALUES (?, ?)",
            (doc_id, 'test content python programming')
        )
        db_manager.connection.commit()

    def test_get_search_stats_initial(self, search_engine):
        """测试初始统计信息"""
        stats = search_engine.get_search_stats()

        assert stats['total_searches'] == 0
        assert stats['unique_queries'] == 0
        assert stats['avg_response_time'] == '0.000s'

    def test_get_search_stats_after_searches(self, search_engine, sample_documents):
        """测试执行搜索后的统计信息"""
        # 执行几次搜索
        search_engine.search("test", mode="fuzzy")
        search_engine.search("python", mode="fuzzy")
        search_engine.search("test", mode="fuzzy")  # 重复查询

        stats = search_engine.get_search_stats()

        assert stats['total_searches'] == 3
        assert stats['unique_queries'] == 2  # test 和 python
        assert 'avg_response_time' in stats
        assert 'min_response_time' in stats
        assert 'max_response_time' in stats

    def test_get_search_stats_popular_queries(self, search_engine, sample_documents):
        """测试热门查询统计"""
        # 执行搜索
        search_engine.search("test", mode="fuzzy")
        search_engine.search("test", mode="fuzzy")
        search_engine.search("python", mode="fuzzy")

        stats = search_engine.get_search_stats()

        # 应该有热门查询列表
        assert 'popular_queries' in stats
        popular = stats['popular_queries']
        assert len(popular) > 0

        # test 应该是最热门的
        assert popular[0]['query'] == 'test'
        assert popular[0]['count'] == 2

    def test_get_search_stats_recent_searches(self, search_engine, sample_documents):
        """测试最近搜索统计"""
        # 执行搜索
        search_engine.search("test", mode="fuzzy")
        search_engine.search("python", mode="exact")

        stats = search_engine.get_search_stats()

        # 应该有最近搜索列表
        assert 'recent_searches' in stats
        recent = stats['recent_searches']
        assert len(recent) == 2

        # 最近的应该在前面
        assert recent[0]['query'] == 'python'
        assert recent[0]['mode'] == 'exact'
        assert recent[1]['query'] == 'test'
        assert recent[1]['mode'] == 'fuzzy'

    def test_get_search_stats_cache_info(self, search_engine, sample_documents):
        """测试缓存统计"""
        # 执行搜索
        search_engine.search("test", mode="fuzzy")
        # 重复搜索应该命中缓存
        search_engine.search("test", mode="fuzzy")

        stats = search_engine.get_search_stats()

        # 应该有缓存统计
        assert 'cache_hit_rate' in stats
        assert 'cache_size' in stats
        assert stats['cache_size'] >= 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
