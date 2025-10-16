"""
SearchEngine 基础功能单元测试

测试 SearchEngine 类的基础搜索功能,包括:
- 初始化
- 精确搜索
- 模糊搜索
- 参数验证
- 结果转换
"""

import pytest
import tempfile
import os
from pathlib import Path

from src.core.search_engine import SearchEngine, SearchResult, SearchResponse
from src.data.db_manager import DBManager


class TestSearchEngineInit:
    """测试 SearchEngine 初始化"""

    def test_init_with_valid_db_manager(self):
        """测试使用有效的 DBManager 初始化"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name

        try:
            db = DBManager(db_path)
            engine = SearchEngine(db)

            assert engine.db_manager is db
            assert isinstance(engine.db_manager, DBManager)

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_init_with_invalid_db_manager(self):
        """测试使用无效的 db_manager 初始化应抛出异常"""
        with pytest.raises(TypeError, match="db_manager 必须是 DBManager 实例"):
            SearchEngine("not a db manager")

        with pytest.raises(TypeError, match="db_manager 必须是 DBManager 实例"):
            SearchEngine(None)


class TestSearchEngineSearch:
    """测试搜索功能"""

    @pytest.fixture
    def db_with_data(self):
        """创建包含测试数据的数据库"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name

        db = DBManager(db_path)

        # 插入测试文档
        test_docs = [
            {
                'file_path': '/path/to/python_tutorial.txt',
                'file_name': 'python_tutorial.txt',
                'content': 'Python is a high-level programming language. '
                          'Python is easy to learn and powerful.',
                'file_type': 'txt',
                'file_size': 1024,
            },
            {
                'file_path': '/path/to/java_guide.txt',
                'file_name': 'java_guide.txt',
                'content': 'Java is an object-oriented programming language. '
                          'Java is widely used in enterprise applications.',
                'file_type': 'txt',
                'file_size': 2048,
            },
            {
                'file_path': '/path/to/web_development.pdf',
                'file_name': 'web_development.pdf',
                'content': 'Web development includes HTML, CSS, and JavaScript. '
                          'Python and Java are also used in web development.',
                'file_type': 'pdf',
                'file_size': 4096,
            },
        ]

        db.batch_insert_documents(test_docs)

        yield db, db_path

        db.close()
        if os.path.exists(db_path):
            os.unlink(db_path)

    def test_search_fuzzy_mode(self, db_with_data):
        """测试模糊搜索"""
        db, _ = db_with_data
        engine = SearchEngine(db)

        # 搜索 "python"
        response = engine.search("python", mode="fuzzy")

        assert isinstance(response, SearchResponse)
        assert response.query == "python"
        assert response.mode == "fuzzy"
        assert response.total >= 2  # 至少匹配两个文档
        assert len(response.results) >= 2
        assert response.page == 1
        assert response.page_size == 20

        # 验证结果包含 SearchResult 对象
        for result in response.results:
            assert isinstance(result, SearchResult)
            assert result.id > 0
            assert result.file_path
            assert result.file_name
            assert result.snippet
            assert isinstance(result.rank, float)
            assert isinstance(result.metadata, dict)

    def test_search_exact_mode(self, db_with_data):
        """测试精确搜索"""
        db, _ = db_with_data
        engine = SearchEngine(db)

        # 精确搜索短语 "programming language"
        response = engine.search("programming language", mode="exact")

        assert isinstance(response, SearchResponse)
        assert response.query == "programming language"
        assert response.mode == "exact"
        assert response.total >= 2  # Python 和 Java 文档都包含这个短语

    def test_search_with_limit_and_offset(self, db_with_data):
        """测试分页参数"""
        db, _ = db_with_data
        engine = SearchEngine(db)

        # 第一页,每页 1 条
        response1 = engine.search("development", limit=1, offset=0)
        assert len(response1.results) == 1
        assert response1.page == 1
        assert response1.page_size == 1

        # 第二页
        response2 = engine.search("development", limit=1, offset=1)
        assert response2.page == 2

        # 验证两页的结果不同(如果有多个结果)
        if response1.total > 1:
            assert response1.results[0].id != response2.results[0].id

    def test_search_with_file_type_filter(self, db_with_data):
        """测试文件类型过滤"""
        db, _ = db_with_data
        engine = SearchEngine(db)

        # 只搜索 txt 文件
        response = engine.search("programming", file_types=["txt"])

        assert response.total >= 2  # Python 和 Java 都是 txt 文件
        for result in response.results:
            assert result.metadata['file_type'] == 'txt'

        # 只搜索 pdf 文件
        response_pdf = engine.search("development", file_types=["pdf"])
        for result in response_pdf.results:
            assert result.metadata['file_type'] == 'pdf'

    def test_search_empty_query(self, db_with_data):
        """测试空查询应抛出异常"""
        db, _ = db_with_data
        engine = SearchEngine(db)

        with pytest.raises(ValueError, match="查询字符串不能为空"):
            engine.search("")

        with pytest.raises(ValueError, match="查询字符串不能为空"):
            engine.search("   ")

    def test_search_invalid_mode(self, db_with_data):
        """测试无效的搜索模式应抛出异常"""
        db, _ = db_with_data
        engine = SearchEngine(db)

        with pytest.raises(ValueError, match="无效的搜索模式"):
            engine.search("test", mode="invalid")

    def test_search_invalid_limit(self, db_with_data):
        """测试无效的 limit 参数应抛出异常"""
        db, _ = db_with_data
        engine = SearchEngine(db)

        with pytest.raises(ValueError, match="limit 必须大于 0"):
            engine.search("test", limit=0)

        with pytest.raises(ValueError, match="limit 必须大于 0"):
            engine.search("test", limit=-1)

    def test_search_invalid_offset(self, db_with_data):
        """测试无效的 offset 参数应抛出异常"""
        db, _ = db_with_data
        engine = SearchEngine(db)

        with pytest.raises(ValueError, match="offset 必须大于或等于 0"):
            engine.search("test", offset=-1)

    def test_search_no_results(self, db_with_data):
        """测试没有匹配结果的搜索"""
        db, _ = db_with_data
        engine = SearchEngine(db)

        response = engine.search("nonexistent_keyword_xyz123", mode="fuzzy")

        assert response.total == 0
        assert len(response.results) == 0
        assert response.total_pages == 0

    def test_search_performance(self, db_with_data):
        """测试搜索性能"""
        db, _ = db_with_data
        engine = SearchEngine(db)

        response = engine.search("python", mode="fuzzy")

        # 验证记录了查询耗时
        assert response.elapsed_time >= 0
        # 小型数据库搜索应该很快 (< 1 秒)
        assert response.elapsed_time < 1.0


class TestSearchEngineFTSQuery:
    """测试 FTS 查询构建"""

    def test_build_fts_query_exact(self):
        """测试精确搜索查询构建"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name

        try:
            db = DBManager(db_path)
            engine = SearchEngine(db)

            # 测试精确搜索查询
            query = engine._build_fts_query("hello world", "exact")
            assert query == '"hello world"'

            # 测试包含引号的查询(应该被转义)
            query_with_quotes = engine._build_fts_query('test "quote"', "exact")
            assert '""' in query_with_quotes  # 引号被转义为双引号

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_build_fts_query_fuzzy(self):
        """测试模糊搜索查询构建"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name

        try:
            db = DBManager(db_path)
            engine = SearchEngine(db)

            # 单个词
            query = engine._build_fts_query("python", "fuzzy")
            assert query == "python*"

            # 多个词
            query = engine._build_fts_query("python programming", "fuzzy")
            assert "python*" in query
            assert "programming*" in query
            assert " OR " in query

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_escape_fts_word(self):
        """测试特殊字符转义"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
            db_path = tmp.name

        try:
            db = DBManager(db_path)
            engine = SearchEngine(db)

            # 测试移除特殊字符
            assert engine._escape_fts_word('test*') == 'test'
            assert engine._escape_fts_word('test"word') == 'testword'
            assert engine._escape_fts_word('(test)') == 'test'

            db.close()
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


class TestSearchResult:
    """测试 SearchResult 数据类"""

    def test_search_result_creation(self):
        """测试创建 SearchResult 对象"""
        result = SearchResult(
            id=1,
            file_path="/path/to/file.txt",
            file_name="file.txt",
            snippet="This is a <mark>test</mark> snippet",
            rank=-0.5,
            metadata={'file_type': 'txt', 'file_size': 1024}
        )

        assert result.id == 1
        assert result.file_path == "/path/to/file.txt"
        assert result.file_name == "file.txt"
        assert result.snippet == "This is a <mark>test</mark> snippet"
        assert result.rank == -0.5
        assert result.metadata['file_type'] == 'txt'


class TestSearchResponse:
    """测试 SearchResponse 数据类"""

    def test_search_response_creation(self):
        """测试创建 SearchResponse 对象"""
        results = [
            SearchResult(
                id=1,
                file_path="/path/to/file.txt",
                file_name="file.txt",
                snippet="snippet",
                rank=-0.5,
                metadata={}
            )
        ]

        response = SearchResponse(
            results=results,
            total=10,
            query="test",
            mode="fuzzy",
            elapsed_time=0.123,
            page=1,
            page_size=20,
            total_pages=1
        )

        assert len(response.results) == 1
        assert response.total == 10
        assert response.query == "test"
        assert response.mode == "fuzzy"
        assert response.elapsed_time == 0.123
        assert response.page == 1
        assert response.page_size == 20
        assert response.total_pages == 1
