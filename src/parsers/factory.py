"""
解析器工厂模块

提供文档解析器的注册和获取功能
"""

from typing import Dict, List, Optional
import os
from .base import IDocumentParser


class ParserFactory:
    """
    解析器工厂

    负责管理和分发文档解析器,支持动态注册和获取解析器
    """

    def __init__(self):
        """初始化工厂"""
        self._parsers: Dict[str, IDocumentParser] = {}
        self._extension_map: Dict[str, str] = {}  # 扩展名到解析器类型的映射

    def register_parser(
        self,
        name: str,
        extensions: List[str],
        parser: IDocumentParser
    ) -> None:
        """
        注册解析器

        Args:
            name: 解析器名称
            extensions: 支持的文件扩展名列表（如 ['.txt', '.md']）
            parser: 解析器实例

        Example:
            >>> factory = ParserFactory()
            >>> factory.register_parser('text', ['.txt', '.md'], TextParser())
        """
        # 存储解析器
        self._parsers[name] = parser

        # 建立扩展名映射
        for ext in extensions:
            ext_lower = ext.lower()
            if not ext_lower.startswith('.'):
                ext_lower = '.' + ext_lower
            self._extension_map[ext_lower] = name

    def get_parser(self, file_path: str) -> Optional[IDocumentParser]:
        """
        根据文件路径获取合适的解析器

        Args:
            file_path: 文件路径

        Returns:
            解析器实例,如果没有找到则返回 None

        Example:
            >>> factory = ParserFactory()
            >>> parser = factory.get_parser('document.txt')
            >>> if parser:
            ...     result = parser.parse('document.txt')
        """
        # 获取文件扩展名
        _, ext = os.path.splitext(file_path)
        ext_lower = ext.lower()

        # 查找对应的解析器
        parser_name = self._extension_map.get(ext_lower)
        if parser_name:
            return self._parsers.get(parser_name)

        return None

    def supports(self, file_path: str) -> bool:
        """
        检查文件是否支持解析

        Args:
            file_path: 文件路径

        Returns:
            是否支持该文件类型
        """
        return self.get_parser(file_path) is not None

    def get_supported_extensions(self) -> List[str]:
        """
        获取所有支持的文件扩展名

        Returns:
            扩展名列表(按字母顺序排序)

        Example:
            >>> factory = ParserFactory()
            >>> extensions = factory.get_supported_extensions()
            >>> print(extensions)
            ['.csv', '.md', '.txt']
        """
        return sorted(list(self._extension_map.keys()))

    def get_parser_names(self) -> List[str]:
        """
        获取所有已注册的解析器名称

        Returns:
            解析器名称列表(按字母顺序排序)
        """
        return sorted(list(self._parsers.keys()))

    def unregister_parser(self, name: str) -> bool:
        """
        注销解析器

        Args:
            name: 解析器名称

        Returns:
            是否成功注销

        Example:
            >>> factory = ParserFactory()
            >>> factory.register_parser('text', ['.txt'], TextParser())
            >>> factory.unregister_parser('text')
            True
        """
        if name not in self._parsers:
            return False

        # 删除解析器
        del self._parsers[name]

        # 删除相关的扩展名映射
        extensions_to_remove = [
            ext for ext, parser_name in self._extension_map.items()
            if parser_name == name
        ]
        for ext in extensions_to_remove:
            del self._extension_map[ext]

        return True

    def clear(self) -> None:
        """
        清空所有已注册的解析器

        用于测试或重置工厂状态
        """
        self._parsers.clear()
        self._extension_map.clear()

    def get_parser_info(self, name: str) -> Optional[Dict[str, any]]:
        """
        获取解析器信息

        Args:
            name: 解析器名称

        Returns:
            解析器信息字典,包含名称、支持的扩展名等,如果不存在则返回 None
        """
        if name not in self._parsers:
            return None

        # 查找该解析器支持的所有扩展名
        extensions = [
            ext for ext, parser_name in self._extension_map.items()
            if parser_name == name
        ]

        return {
            'name': name,
            'extensions': sorted(extensions),
            'parser': self._parsers[name]
        }


# 全局解析器工厂实例
_parser_factory = ParserFactory()


def get_parser_factory() -> ParserFactory:
    """
    获取全局解析器工厂实例

    Returns:
        解析器工厂单例

    Example:
        >>> factory = get_parser_factory()
        >>> factory.register_parser('text', ['.txt'], TextParser())
    """
    return _parser_factory
