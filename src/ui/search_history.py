"""
搜索历史管理器

Story 2.6: 搜索历史和快捷功能
- 记录搜索历史
- 提供最近搜索
- 持久化存储
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import OrderedDict

logger = logging.getLogger(__name__)


class SearchHistory:
    """
    搜索历史管理器

    功能:
    1. 记录搜索查询
    2. 获取最近搜索
    3. 清除历史
    4. 持久化存储
    """

    def __init__(self, max_history: int = 100, history_file: Optional[str] = None):
        """
        初始化搜索历史管理器

        Args:
            max_history: 最大历史记录数
            history_file: 历史文件路径
        """
        self.max_history = max_history
        self.history_file = history_file or "search_history.json"

        # 使用 OrderedDict 保持顺序
        self.history: OrderedDict[str, Dict[str, Any]] = OrderedDict()

        # 加载历史记录
        self._load_history()

        logger.info(f"Search history initialized (max: {max_history})")

    def add_search(self, query: str, mode: str = "fts", result_count: int = 0):
        """
        添加搜索记录

        Args:
            query: 搜索查询
            mode: 搜索模式
            result_count: 结果数量
        """
        if not query or not query.strip():
            return

        query = query.strip()

        # 如果已存在,先删除旧记录
        if query in self.history:
            del self.history[query]

        # 添加新记录到最前面
        self.history[query] = {
            'query': query,
            'mode': mode,
            'result_count': result_count,
            'timestamp': datetime.now().isoformat(),
            'count': self.history.get(query, {}).get('count', 0) + 1
        }

        # 移动到最前面
        self.history.move_to_end(query, last=False)

        # 限制历史记录数量
        while len(self.history) > self.max_history:
            self.history.popitem(last=True)  # 删除最旧的

        # 保存到文件
        self._save_history()

        logger.debug(f"Added search to history: {query}")

    def get_recent_searches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取最近的搜索记录

        Args:
            limit: 返回的记录数量

        Returns:
            搜索记录列表
        """
        recent = list(self.history.values())[:limit]
        return recent

    def get_suggestions(self, prefix: str, limit: int = 5) -> List[str]:
        """
        根据前缀获取搜索建议

        Args:
            prefix: 查询前缀
            limit: 返回的建议数量

        Returns:
            建议查询列表
        """
        if not prefix:
            return []

        prefix = prefix.lower()
        suggestions = []

        for query in self.history.keys():
            if query.lower().startswith(prefix):
                suggestions.append(query)
                if len(suggestions) >= limit:
                    break

        return suggestions

    def get_popular_searches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取热门搜索(按搜索次数排序)

        Args:
            limit: 返回的记录数量

        Returns:
            搜索记录列表
        """
        sorted_history = sorted(
            self.history.values(),
            key=lambda x: x.get('count', 0),
            reverse=True
        )
        return sorted_history[:limit]

    def clear_history(self):
        """清除所有历史记录"""
        self.history.clear()
        self._save_history()
        logger.info("Search history cleared")

    def remove_search(self, query: str):
        """
        删除指定的搜索记录

        Args:
            query: 要删除的查询
        """
        if query in self.history:
            del self.history[query]
            self._save_history()
            logger.debug(f"Removed search from history: {query}")

    def _load_history(self):
        """从文件加载历史记录"""
        try:
            history_path = Path(self.history_file)

            if history_path.exists():
                with open(history_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # 转换为 OrderedDict
                self.history = OrderedDict()
                for item in data:
                    query = item['query']
                    self.history[query] = item

                logger.info(f"Loaded {len(self.history)} search history items")

        except Exception as e:
            logger.error(f"Failed to load search history: {e}")
            self.history = OrderedDict()

    def _save_history(self):
        """保存历史记录到文件"""
        try:
            history_path = Path(self.history_file)

            # 转换为列表
            data = list(self.history.values())

            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.debug(f"Saved {len(data)} search history items")

        except Exception as e:
            logger.error(f"Failed to save search history: {e}")


# 全局单例
_search_history_instance: Optional[SearchHistory] = None


def get_search_history() -> SearchHistory:
    """
    获取全局搜索历史实例

    Returns:
        搜索历史管理器
    """
    global _search_history_instance

    if _search_history_instance is None:
        _search_history_instance = SearchHistory()

    return _search_history_instance
