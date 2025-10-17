"""
搜索功能集成测试

端到端测试完整的搜索流程,包括:
- 文档索引
- 全文搜索
- 高级搜索
- 搜索建议
- 结果排序和分页
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from pathlib import Path

from src.core.search_engine import SearchEngine
from src.data.db_manager import DBManager


class TestSearchIntegration:
    """搜索功能集成测试"""

    @pytest.fixture(scope='class')
    def test_db_path(self):
        """创建临时数据库"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name

        yield db_path

        if os.path.exists(db_path):
            os.remove(db_path)

    @pytest.fixture(scope='class')
    def db_manager(self, test_db_path):
        """创建数据库管理器"""
        db = DBManager(test_db_path)
        db.connect()
        db.initialize_schema()

        yield db

        db.close()

    @pytest.fixture(scope='class')
    def search_engine(self, db_manager):
        """创建搜索引擎实例"""
        return SearchEngine(db_manager)

    @pytest.fixture(scope='class', autouse=True)
    def setup_test_data(self, db_manager):
        """设置测试数据"""
        now = datetime.now()

        # 创建测试文档
        test_documents = [
            {
                'file_path': '/documents/python_guide.pdf',
                'file_name': 'python_guide.pdf',
                'file_type': 'pdf',
                'file_size': 2 * 1024 * 1024,  # 2MB
                'modified_at': (now - timedelta(days=5)).isoformat(),
                'content': 'Python programming language guide. Learn Python basics and advanced concepts.'
            },
            {
                'file_path': '/documents/javascript_tutorial.pdf',
                'file_name': 'javascript_tutorial.pdf',
                'file_type': 'pdf',
                'file_size': 1.5 * 1024 * 1024,  # 1.5MB
                'modified_at': (now - timedelta(days=10)).isoformat(),
                'content': 'JavaScript tutorial for beginners. Master JavaScript programming.'
            },
            {
                'file_path': '/documents/project_notes.txt',
                'file_name': 'project_notes.txt',
                'file_type': 'txt',
                'file_size': 50 * 1024,  # 50KB
                'modified_at': (now - timedelta(days=2)).isoformat(),
                'content': 'Project notes and documentation. Important information about the Python project.'
            },
            {
                'file_path': '/documents/meeting_notes.txt',
                'file_name': 'meeting_notes.txt',
                'file_type': 'txt',
                'file_size': 30 * 1024,  # 30KB
                'modified_at': now.isoformat(),
                'content': 'Meeting notes from team discussion about project timeline.'
            },
            {
                'file_path': '/documents/annual_report_2024.pdf',
                'file_name': 'annual_report_2024.pdf',
                'file_type': 'pdf',
                'file_size': 5 * 1024 * 1024,  # 5MB
                'modified_at': (now - timedelta(days=30)).isoformat(),
                'content': 'Annual report for 2024. Financial summary and project achievements.'
            },
            {
                'file_path': '/documents/readme.md',
                'file_name': 'readme.md',
                'file_type': 'md',
                'file_size': 10 * 1024,  # 10KB
                'modified_at': (now - timedelta(days=1)).isoformat(),
                'content': 'README documentation for the project. Installation and usage guide.'
            }
        ]

        # 插入文档到数据库
        for doc in test_documents:
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

    def test_basic_fuzzy_search(self, search_engine):
        """测试基本模糊搜索"""
        response = search_engine.search("python", mode="fuzzy", limit=10)

        # 应该找到包含 "python" 的文档
        assert response.total >= 2
        assert len(response.results) >= 2

        # 验证结果包含关键词
        for result in response.results:
            assert 'python' in result.snippet.lower() or 'python' in result.file_name.lower()

    def test_exact_search(self, search_engine):
        """测试精确搜索"""
        response = search_engine.search(
            "Python programming",
            mode="exact",
            limit=10
        )

        # 应该找到包含完整短语的文档
        assert response.total >= 1

    def test_search_with_file_type_filter(self, search_engine):
        """测试文件类型过滤"""
        response = search_engine.search(
            "project",
            mode="fuzzy",
            file_types=['txt'],
            limit=10
        )

        # 所有结果应该是 txt 文件
        assert response.total >= 1
        for result in response.results:
            assert result.metadata['file_type'] == 'txt'

    def test_advanced_search_date_filter(self, search_engine):
        """测试高级搜索 - 日期过滤"""
        now = datetime.now()
        date_from = (now - timedelta(days=7)).isoformat()
        date_to = now.isoformat()

        response = search_engine.advanced_search(
            query="project",
            date_from=date_from,
            date_to=date_to,
            limit=10
        )

        # 应该只返回最近7天内的文档
        assert response.total >= 1
        for result in response.results:
            modified_at = result.metadata['modified_at']
            assert modified_at >= date_from
            assert modified_at <= date_to

    def test_advanced_search_size_filter(self, search_engine):
        """测试高级搜索 - 文件大小过滤"""
        size_min = 100 * 1024  # 100KB
        size_max = 2 * 1024 * 1024  # 2MB

        response = search_engine.advanced_search(
            query="guide",
            size_min=size_min,
            size_max=size_max,
            limit=10
        )

        # 所有结果应该在大小范围内
        for result in response.results:
            file_size = result.metadata['file_size']
            assert file_size >= size_min
            assert file_size <= size_max

    def test_advanced_search_combined_filters(self, search_engine):
        """测试高级搜索 - 组合过滤"""
        now = datetime.now()
        date_from = (now - timedelta(days=15)).isoformat()

        response = search_engine.advanced_search(
            query="python",
            file_types=['pdf', 'txt'],
            date_from=date_from,
            size_min=40 * 1024,  # 40KB
            limit=10
        )

        # 验证所有过滤条件
        for result in response.results:
            assert result.metadata['file_type'] in ['pdf', 'txt']
            assert result.metadata['file_size'] >= 40 * 1024
            assert result.metadata['modified_at'] >= date_from

    def test_search_pagination(self, search_engine):
        """测试搜索分页"""
        # 第一页
        page1 = search_engine.search("project", limit=2, offset=0)

        assert page1.page == 1
        assert page1.page_size == 2
        assert len(page1.results) <= 2

        if page1.total > 2:
            # 第二页
            page2 = search_engine.search("project", limit=2, offset=2)

            assert page2.page == 2
            assert page2.page_size == 2

            # 两页的结果不应该重复
            page1_ids = {r.id for r in page1.results}
            page2_ids = {r.id for r in page2.results}
            assert len(page1_ids & page2_ids) == 0

    def test_search_with_sort(self, search_engine):
        """测试搜索结果排序"""
        # 按文件名排序
        response = search_engine.search_with_sort(
            query="document",
            sort_by='name',
            sort_order='asc',
            limit=10
        )

        # 验证排序
        if len(response.results) > 1:
            file_names = [r.file_name for r in response.results]
            assert file_names == sorted(file_names)

    def test_search_suggestions(self, search_engine):
        """测试搜索建议"""
        # 先执行一些搜索建立历史
        search_engine.search("python", mode="fuzzy")
        search_engine.search("project", mode="fuzzy")

        # 获取建议
        suggestions = search_engine.get_suggestions("p", limit=5)

        # 应该有建议
        assert len(suggestions) >= 1

        # 所有建议应该以 "p" 开头
        for suggestion in suggestions:
            assert suggestion.startswith("p")

    def test_search_caching(self, search_engine):
        """测试搜索缓存"""
        # 清除缓存
        search_engine.clear_cache()

        # 第一次搜索
        response1 = search_engine.search("python", mode="fuzzy", limit=10)
        assert response1.cache_hit is False

        # 相同的搜索应该命中缓存
        response2 = search_engine.search("python", mode="fuzzy", limit=10)
        assert response2.cache_hit is True

        # 验证结果相同
        assert response1.total == response2.total

    def test_search_stats(self, search_engine):
        """测试搜索统计"""
        # 执行几次搜索
        search_engine.search("python", mode="fuzzy")
        search_engine.search("javascript", mode="fuzzy")
        search_engine.search("python", mode="fuzzy")

        # 获取统计
        stats = search_engine.get_search_stats()

        # 验证统计信息
        assert stats['total_searches'] >= 3
        assert stats['unique_queries'] >= 2
        assert 'avg_response_time' in stats
        assert 'popular_queries' in stats
        assert 'recent_searches' in stats

        # 验证热门查询
        popular = stats['popular_queries']
        assert len(popular) > 0

    def test_search_history(self, search_engine):
        """测试搜索历史"""
        # 执行搜索
        search_engine.search("test query 1", mode="fuzzy")
        search_engine.search("test query 2", mode="exact")

        # 获取历史
        history = search_engine.get_search_history(limit=10)

        # 验证历史记录
        assert len(history) >= 2

        # 最近的应该在前面
        assert history[0]['query'] == 'test query 2'
        assert history[0]['mode'] == 'exact'

    def test_popular_queries(self, search_engine):
        """测试热门查询统计"""
        # 执行多次相同查询
        for _ in range(3):
            search_engine.search("popular query", mode="fuzzy")

        search_engine.search("less popular", mode="fuzzy")

        # 获取热门查询
        popular = search_engine.get_popular_queries(top_n=5)

        # 验证
        assert len(popular) > 0
        # "popular query" 应该是最热门的
        top_query, top_count = popular[0]
        assert top_count >= 3

    def test_end_to_end_workflow(self, search_engine, db_manager):
        """测试完整的端到端工作流"""
        # 1. 添加新文档
        now = datetime.now()
        db_manager.add_document(
            file_path='/new/workflow_test.txt',
            file_name='workflow_test.txt',
            file_type='txt',
            file_size=20 * 1024,
            modified_at=now.isoformat()
        )

        # 添加到 FTS 索引
        doc_id = db_manager.connection.execute(
            "SELECT id FROM documents WHERE file_path = ?",
            ('/new/workflow_test.txt',)
        ).fetchone()['id']

        db_manager.connection.execute(
            "INSERT INTO documents_fts(rowid, content) VALUES (?, ?)",
            (doc_id, 'This is a workflow test document for integration testing')
        )
        db_manager.connection.commit()

        # 2. 清除缓存(确保搜索新数据)
        search_engine.clear_cache()

        # 3. 搜索新文档
        response = search_engine.search("workflow", mode="fuzzy", limit=10)

        # 4. 验证能找到新文档
        assert response.total >= 1
        found = any('workflow_test.txt' in r.file_name for r in response.results)
        assert found

        # 5. 获取搜索建议
        suggestions = search_engine.get_suggestions("work", limit=5)
        assert len(suggestions) >= 0

        # 6. 查看统计
        stats = search_engine.get_search_stats()
        assert stats['total_searches'] > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
