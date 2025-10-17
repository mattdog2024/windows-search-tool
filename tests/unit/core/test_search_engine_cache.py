"""
测试搜索引擎缓存和分页功能

测试 SearchEngine 的缓存、分页、排序和历史记录功能。
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime

from src.core.search_engine import SearchEngine, SearchResult, SearchResponse
from src.data.db_manager import DBManager


@pytest.fixture
def mock_db_manager():
    """创建模拟的 DBManager"""
    db_manager = Mock(spec=DBManager)
    db_manager.connection = Mock()
    return db_manager


@pytest.fixture
def search_engine(mock_db_manager):
    """创建 SearchEngine 实例"""
    return SearchEngine(mock_db_manager)


@pytest.fixture
def sample_search_results():
    """创建示例搜索结果"""
    return [
        {
            'id': 1,
            'file_path': '/path/to/file1.txt',
            'file_name': 'file1.txt',
            'snippet': 'This is a test file',
            'rank': -1.5,
            'file_type': 'txt',
            'file_size': 1024,
            'modified_at': '2024-01-01T10:00:00'
        },
        {
            'id': 2,
            'file_path': '/path/to/file2.txt',
            'file_name': 'file2.txt',
            'snippet': 'Another test file',
            'rank': -2.0,
            'file_type': 'txt',
            'file_size': 2048,
            'modified_at': '2024-01-02T10:00:00'
        },
        {
            'id': 3,
            'file_path': '/path/to/file3.txt',
            'file_name': 'file3.txt',
            'snippet': 'Third test file',
            'rank': -1.0,
            'file_type': 'txt',
            'file_size': 512,
            'modified_at': '2024-01-03T10:00:00'
        }
    ]


class TestSearchEngineCache:
    """测试缓存功能"""

    def test_cache_initialization(self, search_engine):
        """测试缓存初始化"""
        assert hasattr(search_engine, '_cache')
        assert hasattr(search_engine, '_cache_size')
        assert hasattr(search_engine, '_cache_hits')
        assert hasattr(search_engine, '_cache_misses')
        assert search_engine._cache_size == 100  # 默认值

    def test_make_cache_key(self, search_engine):
        """测试缓存键生成"""
        key1 = search_engine._make_cache_key(
            'test query', 'fuzzy', 20, 0, None
        )
        key2 = search_engine._make_cache_key(
            'test query', 'fuzzy', 20, 0, None
        )
        key3 = search_engine._make_cache_key(
            'test query', 'exact', 20, 0, None
        )

        # 相同参数应该生成相同的键
        assert key1 == key2
        # 不同参数应该生成不同的键
        assert key1 != key3

    def test_make_cache_key_with_file_types(self, search_engine):
        """测试带文件类型的缓存键生成"""
        key1 = search_engine._make_cache_key(
            'test', 'fuzzy', 20, 0, ['txt', 'pdf']
        )
        key2 = search_engine._make_cache_key(
            'test', 'fuzzy', 20, 0, ['pdf', 'txt']  # 顺序不同
        )

        # 文件类型会被排序,所以应该生成相同的键
        assert key1 == key2

    def test_cache_put_and_get(self, search_engine):
        """测试缓存存取"""
        cache_key = 'test_key'
        mock_response = Mock(spec=SearchResponse)

        # 放入缓存
        search_engine._put_to_cache(cache_key, mock_response)

        # 从缓存获取
        cached = search_engine._get_from_cache(cache_key)

        assert cached is mock_response

    def test_cache_miss(self, search_engine):
        """测试缓存未命中"""
        cached = search_engine._get_from_cache('non_existent_key')
        assert cached is None

    def test_cache_lru_eviction(self, search_engine):
        """测试 LRU 缓存淘汰"""
        # 设置小的缓存大小
        search_engine._cache_size = 3

        # 添加 3 个项
        for i in range(3):
            key = f'key_{i}'
            response = Mock(spec=SearchResponse)
            search_engine._put_to_cache(key, response)

        # 所有项都应该在缓存中
        assert len(search_engine._cache) == 3

        # 添加第 4 个项,应该淘汰最久未使用的 key_0 (第一个添加的)
        search_engine._put_to_cache('key_3', Mock(spec=SearchResponse))

        assert len(search_engine._cache) == 3
        # key_0 被淘汰
        assert search_engine._get_from_cache('key_0') is None
        # key_1, key_2, key_3 应该还在
        assert search_engine._get_from_cache('key_1') is not None
        assert search_engine._get_from_cache('key_2') is not None
        assert search_engine._get_from_cache('key_3') is not None

    def test_cache_lru_move_to_end(self, search_engine):
        """测试 LRU 访问更新"""
        search_engine._cache_size = 3

        # 添加 3 个项
        for i in range(3):
            search_engine._put_to_cache(f'key_{i}', Mock(spec=SearchResponse))

        # 访问 key_0,将其移到末尾
        search_engine._get_from_cache('key_0')

        # 添加新项,应该淘汰 key_1 (最久未使用)
        search_engine._put_to_cache('key_3', Mock(spec=SearchResponse))

        assert search_engine._get_from_cache('key_0') is not None
        assert search_engine._get_from_cache('key_1') is None

    def test_clear_cache(self, search_engine):
        """测试清空缓存"""
        # 添加一些项
        for i in range(5):
            search_engine._put_to_cache(f'key_{i}', Mock(spec=SearchResponse))

        assert len(search_engine._cache) == 5

        # 清空缓存
        search_engine.clear_cache()

        assert len(search_engine._cache) == 0

    def test_cache_stats(self, search_engine):
        """测试缓存统计"""
        # 模拟一些缓存命中和未命中
        search_engine._cache_hits = 7
        search_engine._cache_misses = 3

        stats = search_engine.get_cache_stats()

        assert stats['cache_hits'] == 7
        assert stats['cache_misses'] == 3
        assert stats['hit_rate'] == '70.00%'

    def test_search_with_cache_hit(self, search_engine, mock_db_manager, sample_search_results):
        """测试搜索缓存命中"""
        # 设置数据库模拟
        mock_db_manager.search_fts.return_value = sample_search_results
        cursor_mock = Mock()
        cursor_mock.fetchone.return_value = {'count': 3}
        mock_db_manager.connection.cursor.return_value = cursor_mock

        # 第一次搜索 (缓存未命中)
        response1 = search_engine.search('test query', mode='fuzzy')
        assert response1.cache_hit is False
        assert search_engine._cache_hits == 0
        assert search_engine._cache_misses == 1

        # 第二次搜索相同查询 (缓存命中)
        response2 = search_engine.search('test query', mode='fuzzy')
        assert response2.cache_hit is True
        assert search_engine._cache_hits == 1
        assert search_engine._cache_misses == 1

        # 数据库查询应该只被调用一次
        assert mock_db_manager.search_fts.call_count == 1

    def test_search_without_cache(self, search_engine, mock_db_manager, sample_search_results):
        """测试禁用缓存的搜索"""
        # 设置数据库模拟
        mock_db_manager.search_fts.return_value = sample_search_results
        cursor_mock = Mock()
        cursor_mock.fetchone.return_value = {'count': 3}
        mock_db_manager.connection.cursor.return_value = cursor_mock

        # 两次搜索都不使用缓存
        response1 = search_engine.search('test', use_cache=False)
        response2 = search_engine.search('test', use_cache=False)

        # 两次都应该是缓存未命中
        assert search_engine._cache_hits == 0
        assert search_engine._cache_misses == 2

        # 数据库查询应该被调用两次
        assert mock_db_manager.search_fts.call_count == 2


class TestSearchEnginePagination:
    """测试分页功能"""

    def test_pagination_info(self, search_engine, mock_db_manager, sample_search_results):
        """测试分页信息"""
        # 设置总共有 50 个结果
        mock_db_manager.search_fts.return_value = sample_search_results[:2]
        cursor_mock = Mock()
        cursor_mock.fetchone.return_value = {'count': 50}
        mock_db_manager.connection.cursor.return_value = cursor_mock

        # 第一页
        response = search_engine.search('test', limit=20, offset=0)
        assert response.page == 1
        assert response.total_pages == 3
        assert response.has_prev_page is False
        assert response.has_next_page is True

        # 第二页
        response = search_engine.search('test', limit=20, offset=20, use_cache=False)
        assert response.page == 2
        assert response.has_prev_page is True
        assert response.has_next_page is True

        # 最后一页
        response = search_engine.search('test', limit=20, offset=40, use_cache=False)
        assert response.page == 3
        assert response.has_prev_page is True
        assert response.has_next_page is False

    def test_pagination_edge_cases(self, search_engine, mock_db_manager):
        """测试分页边界情况"""
        mock_db_manager.search_fts.return_value = []
        cursor_mock = Mock()

        # 没有结果
        cursor_mock.fetchone.return_value = {'count': 0}
        mock_db_manager.connection.cursor.return_value = cursor_mock

        response = search_engine.search('nonexistent')
        assert response.total == 0
        assert response.total_pages == 0
        assert response.has_prev_page is False
        assert response.has_next_page is False

        # 只有 1 个结果
        cursor_mock.fetchone.return_value = {'count': 1}
        response = search_engine.search('single', use_cache=False)
        assert response.total_pages == 1


class TestSearchEngineSorting:
    """测试排序功能"""

    def test_sort_by_rank(self, search_engine):
        """测试按相关度排序"""
        results = [
            SearchResult(1, '/a', 'a.txt', 'snippet', -2.0, {'file_size': 100, 'modified_at': '2024-01-01'}),
            SearchResult(2, '/b', 'b.txt', 'snippet', -1.0, {'file_size': 200, 'modified_at': '2024-01-02'}),
            SearchResult(3, '/c', 'c.txt', 'snippet', -3.0, {'file_size': 300, 'modified_at': '2024-01-03'})
        ]

        sorted_results = search_engine._sort_results(results, 'rank', 'asc')

        # rank 越小越相关 (因为是负值)
        assert sorted_results[0].rank == -3.0
        assert sorted_results[1].rank == -2.0
        assert sorted_results[2].rank == -1.0

    def test_sort_by_name(self, search_engine):
        """测试按文件名排序"""
        results = [
            SearchResult(1, '/c', 'c.txt', 'snippet', -1.0, {}),
            SearchResult(2, '/a', 'a.txt', 'snippet', -1.0, {}),
            SearchResult(3, '/b', 'b.txt', 'snippet', -1.0, {})
        ]

        # 升序
        sorted_results = search_engine._sort_results(results, 'name', 'asc')
        assert sorted_results[0].file_name == 'a.txt'
        assert sorted_results[1].file_name == 'b.txt'
        assert sorted_results[2].file_name == 'c.txt'

        # 降序
        sorted_results = search_engine._sort_results(results, 'name', 'desc')
        assert sorted_results[0].file_name == 'c.txt'
        assert sorted_results[2].file_name == 'a.txt'

    def test_sort_by_size(self, search_engine):
        """测试按文件大小排序"""
        results = [
            SearchResult(1, '/a', 'a.txt', 'snippet', -1.0, {'file_size': 2048}),
            SearchResult(2, '/b', 'b.txt', 'snippet', -1.0, {'file_size': 512}),
            SearchResult(3, '/c', 'c.txt', 'snippet', -1.0, {'file_size': 1024})
        ]

        # 升序
        sorted_results = search_engine._sort_results(results, 'size', 'asc')
        assert sorted_results[0].metadata['file_size'] == 512
        assert sorted_results[2].metadata['file_size'] == 2048

        # 降序
        sorted_results = search_engine._sort_results(results, 'size', 'desc')
        assert sorted_results[0].metadata['file_size'] == 2048
        assert sorted_results[2].metadata['file_size'] == 512

    def test_sort_by_modified(self, search_engine):
        """测试按修改时间排序"""
        results = [
            SearchResult(1, '/a', 'a.txt', 'snippet', -1.0, {'modified_at': '2024-01-02'}),
            SearchResult(2, '/b', 'b.txt', 'snippet', -1.0, {'modified_at': '2024-01-01'}),
            SearchResult(3, '/c', 'c.txt', 'snippet', -1.0, {'modified_at': '2024-01-03'})
        ]

        # 降序 (最新的在前)
        sorted_results = search_engine._sort_results(results, 'modified', 'desc')
        assert sorted_results[0].metadata['modified_at'] == '2024-01-03'
        assert sorted_results[2].metadata['modified_at'] == '2024-01-01'

    def test_search_with_sort_validation(self, search_engine):
        """测试排序参数验证"""
        # 无效的排序字段
        with pytest.raises(ValueError, match="无效的排序字段"):
            search_engine.search_with_sort('test', sort_by='invalid')

        # 无效的排序顺序
        with pytest.raises(ValueError, match="无效的排序顺序"):
            search_engine.search_with_sort('test', sort_order='invalid')


class TestSearchEngineHistory:
    """测试搜索历史功能"""

    def test_add_to_history(self, search_engine):
        """测试添加搜索历史"""
        search_engine._add_to_history('test query', 'fuzzy', 10, False)

        assert len(search_engine._search_history) == 1
        entry = search_engine._search_history[0]
        assert entry['query'] == 'test query'
        assert entry['mode'] == 'fuzzy'
        assert entry['result_count'] == 10
        assert entry['cache_hit'] is False
        assert 'timestamp' in entry

    def test_history_size_limit(self, search_engine):
        """测试历史记录大小限制"""
        # 添加超过最大数量的历史
        for i in range(60):
            search_engine._add_to_history(f'query_{i}', 'fuzzy', 10, False)

        # 应该只保留最近的 50 条
        assert len(search_engine._search_history) == 50
        # 最早的应该是 query_10
        assert search_engine._search_history[0]['query'] == 'query_10'
        # 最新的应该是 query_59
        assert search_engine._search_history[-1]['query'] == 'query_59'

    def test_get_search_history(self, search_engine):
        """测试获取搜索历史"""
        # 添加一些历史
        for i in range(15):
            search_engine._add_to_history(f'query_{i}', 'fuzzy', 10, False)

        # 获取最近 5 条
        history = search_engine.get_search_history(limit=5)

        assert len(history) == 5
        # 应该是倒序排列,最新的在前
        assert history[0]['query'] == 'query_14'
        assert history[4]['query'] == 'query_10'

    def test_get_popular_queries(self, search_engine):
        """测试获取热门查询"""
        # 添加一些重复查询
        queries = ['python', 'python', 'python', 'java', 'java', 'javascript']
        for query in queries:
            search_engine._search_queries.append(query)

        popular = search_engine.get_popular_queries(top_n=3)

        assert len(popular) == 3
        # 应该按频次降序排列
        assert popular[0] == ('python', 3)
        assert popular[1] == ('java', 2)
        assert popular[2] == ('javascript', 1)

    def test_get_stats(self, search_engine):
        """测试获取统计信息"""
        # 添加一些测试数据
        search_engine._total_searches = 10
        search_engine._query_times = [0.1, 0.2, 0.15, 0.3, 0.25]
        search_engine._search_queries = ['a', 'b', 'c', 'a', 'b']
        search_engine._search_history = [{'query': 'test'}] * 3
        search_engine._cache_hits = 3
        search_engine._cache_misses = 7

        stats = search_engine.get_stats()

        assert stats['total_searches'] == 10
        assert 'avg_query_time' in stats
        assert stats['unique_queries'] == 3  # a, b, c
        assert stats['history_size'] == 3
        assert 'cache_hit_rate' in stats

    def test_clear_history(self, search_engine):
        """测试清空搜索历史"""
        # 添加一些历史
        for i in range(5):
            search_engine._add_to_history(f'query_{i}', 'fuzzy', 10, False)
            search_engine._search_queries.append(f'query_{i}')
            search_engine._query_times.append(0.1)

        # 验证历史存在
        assert len(search_engine._search_history) == 5
        assert len(search_engine._search_queries) == 5
        assert len(search_engine._query_times) == 5

        # 清空历史
        search_engine.clear_history()

        # 验证所有历史数据都被清空
        assert len(search_engine._search_history) == 0
        assert len(search_engine._search_queries) == 0
        assert len(search_engine._query_times) == 0

        # 验证获取历史返回空列表
        history = search_engine.get_search_history()
        assert len(history) == 0

    def test_get_cache_info_alias(self, search_engine):
        """测试 get_cache_info 方法(get_cache_stats 的别名)"""
        # 设置一些缓存数据
        search_engine._cache_hits = 10
        search_engine._cache_misses = 5

        # 验证两个方法返回相同的结果
        stats = search_engine.get_cache_stats()
        info = search_engine.get_cache_info()

        assert stats == info
        assert stats['cache_hits'] == 10
        assert stats['cache_misses'] == 5
        assert 'hit_rate' in info
        assert 'cache_size' in info


class TestSearchEngineIntegration:
    """集成测试"""

    def test_search_with_all_features(self, search_engine, mock_db_manager, sample_search_results):
        """测试搜索的所有功能集成"""
        # 设置数据库模拟
        mock_db_manager.search_fts.return_value = sample_search_results
        cursor_mock = Mock()
        cursor_mock.fetchone.return_value = {'count': 3}
        mock_db_manager.connection.cursor.return_value = cursor_mock

        # 第一次搜索
        response = search_engine.search('test', mode='fuzzy', limit=10)

        # 验证基本功能
        assert response.total == 3
        assert len(response.results) == 3
        assert response.cache_hit is False

        # 验证分页信息
        assert response.page == 1
        assert response.has_prev_page is False

        # 验证历史记录
        history = search_engine.get_search_history()
        assert len(history) == 1
        assert history[0]['query'] == 'test'

        # 第二次搜索 (应该命中缓存)
        response2 = search_engine.search('test', mode='fuzzy', limit=10)
        assert response2.cache_hit is True

        # 验证统计信息
        stats = search_engine.get_stats()
        assert stats['total_searches'] == 2
        assert stats['unique_queries'] == 1
