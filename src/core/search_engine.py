"""
搜索引擎模块

提供基于 SQLite FTS5 的全文搜索功能,支持精确匹配和模糊搜索。
"""

import logging
import time
from dataclasses import dataclass
from typing import List, Dict, Optional, Any

from ..data.db_manager import DBManager

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """
    搜索结果数据类

    封装单个搜索结果的信息,包括文件信息、摘要片段和相关度分数。

    Attributes:
        id: 文档 ID
        file_path: 文件完整路径
        file_name: 文件名
        snippet: 包含搜索关键词的摘要片段
        rank: BM25 相关度分数 (FTS5 返回的负值,越接近 0 相关度越高)
        metadata: 文档元数据字典
    """
    id: int
    file_path: str
    file_name: str
    snippet: str
    rank: float
    metadata: Dict[str, Any]


@dataclass
class SearchResponse:
    """
    搜索响应数据类

    封装完整的搜索响应,包括结果列表、分页信息和性能指标。

    Attributes:
        results: 搜索结果列表
        total: 总结果数量
        query: 搜索查询字符串
        mode: 搜索模式 (exact/fuzzy)
        elapsed_time: 查询耗时(秒)
        page: 当前页码(从 1 开始)
        page_size: 每页结果数
        total_pages: 总页数
    """
    results: List[SearchResult]
    total: int
    query: str
    mode: str
    elapsed_time: float
    page: int
    page_size: int
    total_pages: int


class SearchEngine:
    """
    搜索引擎类

    提供全文搜索功能,基于 SQLite FTS5 实现高性能的文档检索。
    支持精确匹配和模糊搜索两种模式,使用 BM25 算法进行相关度排序。

    Features:
        - 精确搜索: 使用引号包裹查询,完整匹配短语
        - 模糊搜索: 使用前缀匹配,支持分词
        - BM25 排序: 基于词频和逆文档频率的相关度算法
        - 分页支持: 支持 limit 和 offset 参数
        - 结果摘要: 提取包含关键词的文本片段

    Example:
        >>> db = DBManager("search.db")
        >>> engine = SearchEngine(db)
        >>> response = engine.search("python", mode="fuzzy", limit=10)
        >>> print(f"找到 {response.total} 个结果")
    """

    def __init__(self, db_manager: DBManager):
        """
        初始化搜索引擎

        Args:
            db_manager: DBManager 实例,用于数据库操作

        Raises:
            TypeError: 如果 db_manager 不是 DBManager 实例
        """
        if not isinstance(db_manager, DBManager):
            raise TypeError("db_manager 必须是 DBManager 实例")

        self.db_manager = db_manager
        logger.info("SearchEngine 初始化完成")

    def search(
        self,
        query: str,
        mode: str = 'fuzzy',
        limit: int = 20,
        offset: int = 0,
        file_types: Optional[List[str]] = None
    ) -> SearchResponse:
        """
        执行搜索

        根据指定的查询字符串和搜索模式执行全文搜索。

        Args:
            query: 搜索查询字符串
            mode: 搜索模式,可选值:
                - 'exact': 精确匹配,使用引号包裹查询
                - 'fuzzy': 模糊搜索,使用前缀匹配(默认)
            limit: 返回结果数量限制,默认 20
            offset: 结果偏移量,用于分页,默认 0
            file_types: 可选的文件类型过滤列表,如 ['txt', 'pdf']

        Returns:
            SearchResponse: 搜索响应对象,包含结果列表和元信息

        Raises:
            ValueError: 如果 query 为空或 mode 无效

        Example:
            >>> # 精确搜索
            >>> response = engine.search("Windows Search Tool", mode="exact")
            >>> # 模糊搜索
            >>> response = engine.search("search", mode="fuzzy", limit=10)
            >>> # 按文件类型过滤
            >>> response = engine.search("report", file_types=["pdf", "docx"])
        """
        start_time = time.time()

        # 验证参数
        if not query or not query.strip():
            raise ValueError("查询字符串不能为空")

        if mode not in ['exact', 'fuzzy']:
            raise ValueError(f"无效的搜索模式: {mode},必须是 'exact' 或 'fuzzy'")

        if limit <= 0:
            raise ValueError("limit 必须大于 0")

        if offset < 0:
            raise ValueError("offset 必须大于或等于 0")

        # 构建 FTS5 查询
        fts_query = self._build_fts_query(query, mode)

        logger.info(f"执行搜索: query='{query}', mode={mode}, limit={limit}, offset={offset}")

        try:
            # 使用 DBManager 的 search_fts 方法执行搜索
            raw_results = self.db_manager.search_fts(
                query=fts_query,
                limit=limit,
                offset=offset,
                file_types=file_types
            )

            # 转换为 SearchResult 对象
            results = self._convert_to_search_results(raw_results)

            # 获取总结果数(无分页限制)
            total = self._count_total_results(fts_query, file_types)

            # 计算总页数
            page = (offset // limit) + 1
            total_pages = (total + limit - 1) // limit if limit > 0 else 0

            elapsed_time = time.time() - start_time

            logger.info(
                f"搜索完成: 找到 {total} 个结果, "
                f"返回 {len(results)} 个, 耗时 {elapsed_time:.3f}s"
            )

            return SearchResponse(
                results=results,
                total=total,
                query=query,
                mode=mode,
                elapsed_time=elapsed_time,
                page=page,
                page_size=limit,
                total_pages=total_pages
            )

        except Exception as e:
            logger.error(f"搜索失败: {e}", exc_info=True)
            raise

    def _build_fts_query(self, query: str, mode: str) -> str:
        """
        构建 FTS5 查询字符串

        根据搜索模式构建适当的 FTS5 查询语法。

        Args:
            query: 原始查询字符串
            mode: 搜索模式 ('exact' 或 'fuzzy')

        Returns:
            str: FTS5 格式的查询字符串

        FTS5 查询语法:
            - "phrase": 精确短语匹配
            - word*: 前缀匹配
            - word1 OR word2: 布尔 OR 操作
        """
        # 清理查询字符串
        query = query.strip()

        if mode == 'exact':
            # 精确匹配: 使用引号包裹
            # 转义查询中的引号
            escaped_query = query.replace('"', '""')
            fts_query = f'"{escaped_query}"'
            logger.debug(f"精确搜索查询: {fts_query}")

        elif mode == 'fuzzy':
            # 模糊搜索: 分词后每个词使用前缀匹配,用 OR 连接
            words = query.split()
            # 为每个词添加前缀匹配符号 *
            # 转义特殊字符
            escaped_words = [self._escape_fts_word(word) for word in words]
            fts_query = ' OR '.join(f'{word}*' for word in escaped_words if word)
            logger.debug(f"模糊搜索查询: {fts_query}")

        return fts_query

    def _escape_fts_word(self, word: str) -> str:
        """
        转义 FTS5 查询中的特殊字符

        Args:
            word: 要转义的词

        Returns:
            str: 转义后的词
        """
        # FTS5 特殊字符: " * ( ) 等
        # 移除这些字符以避免查询错误
        special_chars = ['"', '*', '(', ')']
        for char in special_chars:
            word = word.replace(char, '')
        return word

    def _convert_to_search_results(
        self,
        raw_results: List[Dict[str, Any]]
    ) -> List[SearchResult]:
        """
        将数据库原始结果转换为 SearchResult 对象

        Args:
            raw_results: DBManager.search_fts() 返回的原始结果列表

        Returns:
            List[SearchResult]: SearchResult 对象列表
        """
        search_results = []

        for result in raw_results:
            search_result = SearchResult(
                id=result['id'],
                file_path=result['file_path'],
                file_name=result['file_name'],
                snippet=result['snippet'],
                rank=result['rank'],
                metadata={
                    'file_type': result.get('file_type', ''),
                    'file_size': result.get('file_size', 0),
                    'modified_at': result.get('modified_at', '')
                }
            )
            search_results.append(search_result)

        return search_results

    def _count_total_results(
        self,
        fts_query: str,
        file_types: Optional[List[str]] = None
    ) -> int:
        """
        统计搜索结果总数

        Args:
            fts_query: FTS5 查询字符串
            file_types: 可选的文件类型过滤列表

        Returns:
            int: 搜索结果总数
        """
        cursor = self.db_manager.connection.cursor()

        try:
            # 构建 COUNT 查询
            query = """
                SELECT COUNT(*) as count
                FROM documents_fts
                JOIN documents d ON documents_fts.rowid = d.id
                WHERE documents_fts MATCH ?
                  AND d.status = 'active'
            """

            params = [fts_query]

            # 添加文件类型过滤
            if file_types:
                placeholders = ','.join(['?' for _ in file_types])
                query += f" AND d.file_type IN ({placeholders})"
                params.extend(file_types)

            cursor.execute(query, params)
            result = cursor.fetchone()

            return result['count'] if result else 0

        except Exception as e:
            logger.error(f"统计结果总数失败: {e}")
            return 0
