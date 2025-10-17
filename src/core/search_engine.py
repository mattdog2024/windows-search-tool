"""
搜索引擎模块

提供基于 SQLite FTS5 的全文搜索功能,支持精确匹配和模糊搜索。
"""

import logging
import time
from collections import Counter, OrderedDict
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from typing import List, Dict, Optional, Any, Tuple

from ..data.db_manager import DBManager
from ..utils.config import ConfigManager

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
        has_next_page: 是否有下一页
        has_prev_page: 是否有上一页
        cache_hit: 是否命中缓存
    """
    results: List[SearchResult]
    total: int
    query: str
    mode: str
    elapsed_time: float
    page: int
    page_size: int
    total_pages: int
    has_next_page: bool = False
    has_prev_page: bool = False
    cache_hit: bool = False


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
        self.config = ConfigManager()

        # 从配置获取缓存大小
        self._cache_size = self.config.get('search.cache_size', 100)

        # LRU 缓存存储 (使用 OrderedDict 实现)
        self._cache: OrderedDict[str, SearchResponse] = OrderedDict()
        self._cache_hits = 0
        self._cache_misses = 0

        # 搜索历史记录 (记录最近的搜索,带时间戳)
        self._search_history: List[Dict[str, Any]] = []
        self._max_history_size = 50  # 保存最近50条搜索历史

        # 搜索统计信息
        self._total_searches = 0
        self._search_queries: List[str] = []  # 保存所有查询历史
        self._query_times: List[float] = []  # 保存所有查询耗时

        logger.info(f"SearchEngine 初始化完成, 缓存大小: {self._cache_size}")

    def search(
        self,
        query: str,
        mode: str = 'fuzzy',
        limit: int = 20,
        offset: int = 0,
        file_types: Optional[List[str]] = None,
        use_cache: bool = True
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
            use_cache: 是否使用缓存,默认 True

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

        # 生成缓存键
        cache_key = self._make_cache_key(query, mode, limit, offset, file_types)

        # 尝试从缓存获取
        if use_cache:
            cached_response = self._get_from_cache(cache_key)
            if cached_response:
                # 更新耗时(缓存命中很快)
                cached_response.elapsed_time = time.time() - start_time
                cached_response.cache_hit = True
                self._cache_hits += 1

                # 更新统计信息 (缓存命中也计入总搜索次数)
                self._total_searches += 1
                self._search_queries.append(query)
                self._query_times.append(cached_response.elapsed_time)

                # 记录到历史
                self._add_to_history(query, mode, cached_response.total, True)

                logger.info(f"缓存命中: query='{query}', mode={mode}")
                return cached_response

        self._cache_misses += 1

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

            # 计算总页数和分页信息
            page = (offset // limit) + 1
            total_pages = (total + limit - 1) // limit if limit > 0 else 0
            has_next_page = page < total_pages
            has_prev_page = page > 1

            elapsed_time = time.time() - start_time

            # 更新统计信息
            self._total_searches += 1
            self._search_queries.append(query)
            self._query_times.append(elapsed_time)

            logger.info(
                f"搜索完成: 找到 {total} 个结果, "
                f"返回 {len(results)} 个, 耗时 {elapsed_time:.3f}s"
            )

            response = SearchResponse(
                results=results,
                total=total,
                query=query,
                mode=mode,
                elapsed_time=elapsed_time,
                page=page,
                page_size=limit,
                total_pages=total_pages,
                has_next_page=has_next_page,
                has_prev_page=has_prev_page,
                cache_hit=False
            )

            # 添加到缓存
            if use_cache:
                self._put_to_cache(cache_key, response)

            # 记录到历史
            self._add_to_history(query, mode, total, False)

            return response

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

    # ==================== 缓存管理方法 ====================

    def _make_cache_key(
        self,
        query: str,
        mode: str,
        limit: int,
        offset: int,
        file_types: Optional[List[str]]
    ) -> str:
        """
        生成缓存键

        Args:
            query: 查询字符串
            mode: 搜索模式
            limit: 结果限制
            offset: 偏移量
            file_types: 文件类型过滤

        Returns:
            str: 缓存键
        """
        # 将文件类型列表转换为元组以便哈希
        ft_tuple = tuple(sorted(file_types)) if file_types else None
        return f"{query}|{mode}|{limit}|{offset}|{ft_tuple}"

    def _get_from_cache(self, cache_key: str) -> Optional[SearchResponse]:
        """
        从缓存获取搜索结果

        Args:
            cache_key: 缓存键

        Returns:
            Optional[SearchResponse]: 缓存的搜索响应,如果不存在返回 None
        """
        if cache_key in self._cache:
            # LRU: 将访问的项移到末尾
            self._cache.move_to_end(cache_key)
            logger.debug(f"缓存命中: {cache_key}")
            return self._cache[cache_key]
        return None

    def _put_to_cache(self, cache_key: str, response: SearchResponse):
        """
        将搜索结果放入缓存

        Args:
            cache_key: 缓存键
            response: 搜索响应
        """
        # 如果缓存已满,移除最久未使用的项
        if len(self._cache) >= self._cache_size:
            # FIFO: 移除第一个项(最久未使用)
            self._cache.popitem(last=False)
            logger.debug(f"缓存已满,移除最久未使用的项")

        self._cache[cache_key] = response
        logger.debug(f"添加到缓存: {cache_key}")

    def clear_cache(self):
        """
        清空搜索缓存

        在索引更新后或手动调用时清除所有缓存的搜索结果。
        """
        self._cache.clear()
        logger.info("搜索缓存已清空")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            Dict: 包含缓存大小、命中率等信息的字典
        """
        total_requests = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_requests * 100) if total_requests > 0 else 0

        return {
            'cache_size': len(self._cache),
            'max_cache_size': self._cache_size,
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'hit_rate': f"{hit_rate:.2f}%"
        }

    # ==================== 排序方法 ====================

    def search_with_sort(
        self,
        query: str,
        mode: str = 'fuzzy',
        limit: int = 20,
        offset: int = 0,
        file_types: Optional[List[str]] = None,
        sort_by: str = 'rank',
        sort_order: str = 'asc',
        use_cache: bool = True
    ) -> SearchResponse:
        """
        执行搜索并支持自定义排序

        Args:
            query: 搜索查询字符串
            mode: 搜索模式 (exact/fuzzy)
            limit: 返回结果数量限制
            offset: 结果偏移量
            file_types: 文件类型过滤列表
            sort_by: 排序字段,可选值:
                - 'rank': 按相关度排序 (默认)
                - 'modified': 按修改时间排序
                - 'name': 按文件名排序
                - 'size': 按文件大小排序
            sort_order: 排序顺序 ('asc' 或 'desc')
            use_cache: 是否使用缓存

        Returns:
            SearchResponse: 搜索响应对象

        Raises:
            ValueError: 如果 sort_by 或 sort_order 无效

        Example:
            >>> # 按修改时间降序排列
            >>> response = engine.search_with_sort(
            ...     "python",
            ...     sort_by='modified',
            ...     sort_order='desc'
            ... )
        """
        # 验证排序参数
        valid_sort_fields = ['rank', 'modified', 'name', 'size']
        if sort_by not in valid_sort_fields:
            raise ValueError(f"无效的排序字段: {sort_by},必须是 {valid_sort_fields} 之一")

        if sort_order not in ['asc', 'desc']:
            raise ValueError(f"无效的排序顺序: {sort_order},必须是 'asc' 或 'desc'")

        # 先执行基本搜索
        response = self.search(
            query=query,
            mode=mode,
            limit=limit,
            offset=offset,
            file_types=file_types,
            use_cache=use_cache
        )

        # 如果不是按相关度排序,需要对结果重新排序
        if sort_by != 'rank':
            response.results = self._sort_results(
                response.results,
                sort_by,
                sort_order
            )

        return response

    def _sort_results(
        self,
        results: List[SearchResult],
        sort_by: str,
        sort_order: str
    ) -> List[SearchResult]:
        """
        对搜索结果进行排序

        Args:
            results: 搜索结果列表
            sort_by: 排序字段
            sort_order: 排序顺序

        Returns:
            List[SearchResult]: 排序后的结果列表
        """
        reverse = (sort_order == 'desc')

        if sort_by == 'rank':
            # 按相关度排序 (rank 越小越相关,因为是负值)
            results.sort(key=lambda x: x.rank, reverse=False)
        elif sort_by == 'modified':
            # 按修改时间排序
            results.sort(
                key=lambda x: x.metadata.get('modified_at', ''),
                reverse=reverse
            )
        elif sort_by == 'name':
            # 按文件名排序
            results.sort(
                key=lambda x: x.file_name.lower(),
                reverse=reverse
            )
        elif sort_by == 'size':
            # 按文件大小排序
            results.sort(
                key=lambda x: x.metadata.get('file_size', 0),
                reverse=reverse
            )

        return results

    # ==================== 搜索历史方法 ====================

    def _add_to_history(
        self,
        query: str,
        mode: str,
        result_count: int,
        cache_hit: bool
    ):
        """
        添加搜索记录到历史

        Args:
            query: 查询字符串
            mode: 搜索模式
            result_count: 结果数量
            cache_hit: 是否命中缓存
        """
        history_entry = {
            'query': query,
            'mode': mode,
            'result_count': result_count,
            'cache_hit': cache_hit,
            'timestamp': datetime.now().isoformat()
        }

        self._search_history.append(history_entry)

        # 保持历史记录在限制范围内
        if len(self._search_history) > self._max_history_size:
            self._search_history.pop(0)

        logger.debug(f"添加搜索历史: {query}")

    def get_search_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取搜索历史记录

        Args:
            limit: 返回的历史记录数量,默认 10

        Returns:
            List[Dict]: 搜索历史记录列表,按时间倒序排列

        Example:
            >>> history = engine.get_search_history(limit=5)
            >>> for entry in history:
            ...     print(f"{entry['timestamp']}: {entry['query']} ({entry['result_count']} 结果)")
        """
        # 返回最近的 limit 条记录,倒序排列
        return list(reversed(self._search_history[-limit:]))

    def get_popular_queries(self, top_n: int = 10) -> List[Tuple[str, int]]:
        """
        获取最热门的搜索查询

        Args:
            top_n: 返回前 N 个热门查询,默认 10

        Returns:
            List[Tuple[str, int]]: 查询和频次的元组列表,按频次降序排列

        Example:
            >>> popular = engine.get_popular_queries(top_n=5)
            >>> for query, count in popular:
            ...     print(f"{query}: {count} 次")
        """
        # 使用 Counter 统计查询频次
        query_counter = Counter(self._search_queries)
        return query_counter.most_common(top_n)

    def clear_history(self):
        """
        清空搜索历史记录

        清空所有搜索历史、查询记录和统计信息。

        Example:
            >>> engine.clear_history()
            >>> history = engine.get_search_history()
            >>> print(len(history))  # 输出: 0
        """
        self._search_history.clear()
        self._search_queries.clear()
        self._query_times.clear()
        logger.info("搜索历史已清空")

    def get_cache_info(self) -> Dict[str, Any]:
        """
        获取缓存信息 (get_cache_stats 的别名)

        Returns:
            Dict: 包含缓存大小、命中率等信息的字典

        Example:
            >>> info = engine.get_cache_info()
            >>> print(f"缓存大小: {info['cache_size']}/{info['max_cache_size']}")
        """
        return self.get_cache_stats()

    def get_stats(self) -> Dict[str, Any]:
        """
        获取搜索引擎统计信息

        Returns:
            Dict: 包含各种统计指标的字典

        Example:
            >>> stats = engine.get_stats()
            >>> print(f"总搜索次数: {stats['total_searches']}")
            >>> print(f"平均查询时间: {stats['avg_query_time']}")
            >>> print(f"缓存命中率: {stats['cache_hit_rate']}")
        """
        total_searches = self._total_searches
        avg_query_time = (
            sum(self._query_times) / len(self._query_times)
            if self._query_times else 0
        )

        cache_stats = self.get_cache_stats()

        return {
            'total_searches': total_searches,
            'avg_query_time': f"{avg_query_time:.3f}s",
            'cache_hit_rate': cache_stats['hit_rate'],
            'cache_size': cache_stats['cache_size'],
            'history_size': len(self._search_history),
            'unique_queries': len(set(self._search_queries))
        }

    # === Stream 3: 高级搜索和统计 ===

    def advanced_search(
        self,
        query: str,
        mode: str = 'fuzzy',
        limit: int = 20,
        offset: int = 0,
        file_types: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        size_min: Optional[int] = None,
        size_max: Optional[int] = None,
        use_cache: bool = True
    ) -> SearchResponse:
        """
        执行高级搜索,支持日期范围和大小范围过滤

        在基础搜索的基础上添加日期和大小过滤条件,允许更精确地定位文件。

        Args:
            query: 搜索查询字符串
            mode: 搜索模式 ('exact' 或 'fuzzy')
            limit: 返回结果数量限制
            offset: 结果偏移量
            file_types: 文件类型过滤列表
            date_from: 起始日期(ISO格式,如 '2024-01-01' 或 '2024-01-01T00:00:00')
            date_to: 结束日期(ISO格式)
            size_min: 最小文件大小(字节)
            size_max: 最大文件大小(字节)
            use_cache: 是否使用缓存

        Returns:
            SearchResponse: 搜索响应对象

        Raises:
            ValueError: 如果日期格式无效或大小范围无效

        Example:
            >>> # 搜索最近7天内的文档
            >>> response = engine.advanced_search(
            ...     "report",
            ...     date_from="2024-01-01",
            ...     date_to="2024-01-07"
            ... )
            >>> # 搜索大于1MB的PDF文件
            >>> response = engine.advanced_search(
            ...     "annual",
            ...     file_types=["pdf"],
            ...     size_min=1024*1024
            ... )
        """
        start_time = time.time()

        # 验证参数
        if not query or not query.strip():
            raise ValueError("查询字符串不能为空")

        if mode not in ['exact', 'fuzzy']:
            raise ValueError(f"无效的搜索模式: {mode}")

        # 验证日期范围
        if date_from and date_to:
            try:
                # 解析日期
                from_dt = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                to_dt = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                if from_dt > to_dt:
                    raise ValueError("起始日期不能晚于结束日期")
            except ValueError as e:
                raise ValueError(f"日期格式无效: {e}")

        # 验证大小范围
        if size_min is not None and size_min < 0:
            raise ValueError("最小文件大小不能为负数")
        if size_max is not None and size_max < 0:
            raise ValueError("最大文件大小不能为负数")
        if size_min is not None and size_max is not None and size_min > size_max:
            raise ValueError("最小文件大小不能大于最大文件大小")

        # 生成缓存键(包含高级参数)
        cache_key = self._make_advanced_cache_key(
            query, mode, limit, offset, file_types,
            date_from, date_to, size_min, size_max
        )

        # 尝试从缓存获取
        if use_cache:
            cached_response = self._get_from_cache(cache_key)
            if cached_response:
                cached_response.elapsed_time = time.time() - start_time
                cached_response.cache_hit = True
                self._cache_hits += 1
                self._total_searches += 1
                self._search_queries.append(query)
                self._query_times.append(cached_response.elapsed_time)
                self._add_to_history(query, mode, cached_response.total, True)
                logger.info(f"高级搜索缓存命中: query='{query}'")
                return cached_response

        self._cache_misses += 1

        # 构建 FTS5 查询
        fts_query = self._build_fts_query(query, mode)

        logger.info(
            f"执行高级搜索: query='{query}', mode={mode}, "
            f"date_from={date_from}, date_to={date_to}, "
            f"size_min={size_min}, size_max={size_max}"
        )

        try:
            # 执行数据库查询,添加高级过滤条件
            raw_results = self._execute_advanced_search(
                fts_query=fts_query,
                limit=limit,
                offset=offset,
                file_types=file_types,
                date_from=date_from,
                date_to=date_to,
                size_min=size_min,
                size_max=size_max
            )

            # 转换为 SearchResult 对象
            results = self._convert_to_search_results(raw_results)

            # 获取总结果数(包含高级过滤)
            total = self._count_advanced_results(
                fts_query, file_types, date_from, date_to, size_min, size_max
            )

            # 计算分页信息
            page = (offset // limit) + 1
            total_pages = (total + limit - 1) // limit if limit > 0 else 0
            has_next_page = page < total_pages
            has_prev_page = page > 1

            elapsed_time = time.time() - start_time

            # 更新统计信息
            self._total_searches += 1
            self._search_queries.append(query)
            self._query_times.append(elapsed_time)

            logger.info(
                f"高级搜索完成: 找到 {total} 个结果, "
                f"返回 {len(results)} 个, 耗时 {elapsed_time:.3f}s"
            )

            response = SearchResponse(
                results=results,
                total=total,
                query=query,
                mode=mode,
                elapsed_time=elapsed_time,
                page=page,
                page_size=limit,
                total_pages=total_pages,
                has_next_page=has_next_page,
                has_prev_page=has_prev_page,
                cache_hit=False
            )

            # 添加到缓存
            if use_cache:
                self._put_to_cache(cache_key, response)

            # 记录到历史
            self._add_to_history(query, mode, total, False)

            return response

        except Exception as e:
            logger.error(f"高级搜索失败: {e}", exc_info=True)
            raise

    def _execute_advanced_search(
        self,
        fts_query: str,
        limit: int,
        offset: int,
        file_types: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        size_min: Optional[int] = None,
        size_max: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        执行高级搜索数据库查询

        Args:
            fts_query: FTS5 查询字符串
            limit: 结果限制
            offset: 偏移量
            file_types: 文件类型过滤
            date_from: 起始日期
            date_to: 结束日期
            size_min: 最小文件大小
            size_max: 最大文件大小

        Returns:
            List[Dict]: 原始搜索结果列表
        """
        cursor = self.db_manager.connection.cursor()

        # 构建查询
        query = """
            SELECT
                d.id,
                d.file_path,
                d.file_name,
                d.file_type,
                d.file_size,
                d.modified_at,
                snippet(documents_fts, 0, '<mark>', '</mark>', '...', 64) as snippet,
                bm25(documents_fts) as rank
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

        # 添加日期范围过滤
        if date_from:
            query += " AND d.modified_at >= ?"
            params.append(date_from)
        if date_to:
            query += " AND d.modified_at <= ?"
            params.append(date_to)

        # 添加文件大小过滤
        if size_min is not None:
            query += " AND d.file_size >= ?"
            params.append(size_min)
        if size_max is not None:
            query += " AND d.file_size <= ?"
            params.append(size_max)

        # 排序和分页
        query += " ORDER BY rank ASC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        # 执行查询
        cursor.execute(query, params)
        columns = [desc[0] for desc in cursor.description]
        results = []

        for row in cursor.fetchall():
            result = dict(zip(columns, row))
            results.append(result)

        return results

    def _count_advanced_results(
        self,
        fts_query: str,
        file_types: Optional[List[str]] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        size_min: Optional[int] = None,
        size_max: Optional[int] = None
    ) -> int:
        """
        统计高级搜索结果总数

        Args:
            fts_query: FTS5 查询字符串
            file_types: 文件类型过滤
            date_from: 起始日期
            date_to: 结束日期
            size_min: 最小文件大小
            size_max: 最大文件大小

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

            # 添加日期范围过滤
            if date_from:
                query += " AND d.modified_at >= ?"
                params.append(date_from)
            if date_to:
                query += " AND d.modified_at <= ?"
                params.append(date_to)

            # 添加文件大小过滤
            if size_min is not None:
                query += " AND d.file_size >= ?"
                params.append(size_min)
            if size_max is not None:
                query += " AND d.file_size <= ?"
                params.append(size_max)

            cursor.execute(query, params)
            result = cursor.fetchone()

            return result['count'] if result else 0

        except Exception as e:
            logger.error(f"统计高级搜索结果总数失败: {e}")
            return 0

    def _make_advanced_cache_key(
        self,
        query: str,
        mode: str,
        limit: int,
        offset: int,
        file_types: Optional[List[str]],
        date_from: Optional[str],
        date_to: Optional[str],
        size_min: Optional[int],
        size_max: Optional[int]
    ) -> str:
        """
        生成高级搜索缓存键

        Args:
            query: 查询字符串
            mode: 搜索模式
            limit: 结果限制
            offset: 偏移量
            file_types: 文件类型过滤
            date_from: 起始日期
            date_to: 结束日期
            size_min: 最小文件大小
            size_max: 最大文件大小

        Returns:
            str: 缓存键
        """
        ft_tuple = tuple(sorted(file_types)) if file_types else None
        return (
            f"{query}|{mode}|{limit}|{offset}|{ft_tuple}|"
            f"{date_from}|{date_to}|{size_min}|{size_max}"
        )

    def get_suggestions(
        self,
        prefix: str,
        limit: int = 10
    ) -> List[str]:
        """
        获取搜索建议和自动补全

        基于用户输入的前缀,从已索引的文档中提取相关的搜索建议。
        建议来源包括文件名、常见词汇等。

        Args:
            prefix: 搜索前缀字符串
            limit: 返回的建议数量,默认 10

        Returns:
            List[str]: 建议词列表,按相关度排序

        Raises:
            ValueError: 如果 prefix 为空或 limit 无效

        Example:
            >>> # 获取以 "doc" 开头的建议
            >>> suggestions = engine.get_suggestions("doc", limit=5)
            >>> print(suggestions)
            ['document', 'documentation', 'docs', 'docker', 'docstring']
        """
        if not prefix or not prefix.strip():
            raise ValueError("搜索前缀不能为空")

        if limit <= 0:
            raise ValueError("limit 必须大于 0")

        prefix = prefix.strip().lower()

        logger.info(f"获取搜索建议: prefix='{prefix}', limit={limit}")

        cursor = self.db_manager.connection.cursor()
        suggestions = set()

        try:
            # 策略1: 从文件名中提取建议
            query = """
                SELECT DISTINCT file_name
                FROM documents
                WHERE LOWER(file_name) LIKE ?
                  AND status = 'active'
                LIMIT ?
            """
            cursor.execute(query, (f"{prefix}%", limit * 2))

            for row in cursor.fetchall():
                file_name = row['file_name']
                # 提取文件名中的单词
                words = file_name.replace('_', ' ').replace('-', ' ').split()
                for word in words:
                    word_lower = word.lower()
                    if word_lower.startswith(prefix) and len(word_lower) > len(prefix):
                        suggestions.add(word_lower)

            # 策略2: 从搜索历史中提取建议
            for entry in self._search_history:
                query_lower = entry['query'].lower()
                if query_lower.startswith(prefix):
                    suggestions.add(query_lower)

                # 也检查查询中的单词
                words = query_lower.split()
                for word in words:
                    if word.startswith(prefix) and len(word) > len(prefix):
                        suggestions.add(word)

            # 策略3: 从热门查询中提取建议
            for query in self._search_queries:
                query_lower = query.lower()
                if query_lower.startswith(prefix):
                    suggestions.add(query_lower)

                words = query_lower.split()
                for word in words:
                    if word.startswith(prefix) and len(word) > len(prefix):
                        suggestions.add(word)

            # 转换为列表并排序(按长度和字母顺序)
            suggestion_list = sorted(
                suggestions,
                key=lambda x: (len(x), x)
            )[:limit]

            logger.info(f"找到 {len(suggestion_list)} 个建议")
            return suggestion_list

        except Exception as e:
            logger.error(f"获取搜索建议失败: {e}", exc_info=True)
            return []

    def get_search_stats(self) -> Dict[str, Any]:
        """
        获取详细的搜索统计信息

        返回搜索引擎的详细统计数据,包括查询次数、平均响应时间、
        热门查询、缓存性能等。

        Returns:
            Dict[str, Any]: 包含详细统计信息的字典,包括:
                - total_searches: 总搜索次数
                - unique_queries: 唯一查询数
                - avg_response_time: 平均响应时间(秒)
                - min_response_time: 最小响应时间
                - max_response_time: 最大响应时间
                - cache_hit_rate: 缓存命中率
                - cache_size: 当前缓存大小
                - popular_queries: 热门查询列表(前10个)
                - recent_searches: 最近搜索列表(前10个)

        Example:
            >>> stats = engine.get_search_stats()
            >>> print(f"总搜索次数: {stats['total_searches']}")
            >>> print(f"平均响应时间: {stats['avg_response_time']}")
            >>> print(f"热门查询: {stats['popular_queries']}")
        """
        # 计算响应时间统计
        if self._query_times:
            avg_time = sum(self._query_times) / len(self._query_times)
            min_time = min(self._query_times)
            max_time = max(self._query_times)
        else:
            avg_time = min_time = max_time = 0.0

        # 获取缓存统计
        cache_stats = self.get_cache_stats()

        # 获取热门查询
        popular_queries = self.get_popular_queries(top_n=10)

        # 获取最近搜索
        recent_searches = self.get_search_history(limit=10)

        return {
            'total_searches': self._total_searches,
            'unique_queries': len(set(self._search_queries)),
            'avg_response_time': f"{avg_time:.3f}s",
            'min_response_time': f"{min_time:.3f}s",
            'max_response_time': f"{max_time:.3f}s",
            'cache_hit_rate': cache_stats['hit_rate'],
            'cache_size': cache_stats['cache_size'],
            'max_cache_size': cache_stats['max_cache_size'],
            'popular_queries': [
                {'query': q, 'count': c} for q, c in popular_queries
            ],
            'recent_searches': [
                {
                    'query': entry['query'],
                    'mode': entry['mode'],
                    'result_count': entry['result_count'],
                    'timestamp': entry['timestamp'],
                    'cache_hit': entry['cache_hit']
                }
                for entry in recent_searches
            ]
        }
