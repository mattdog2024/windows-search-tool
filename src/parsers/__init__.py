"""
文档解析器模块

提供文档解析的核心功能:
- ParseResult: 解析结果数据类
- IDocumentParser: 解析器接口
- BaseParser: 基础解析器实现
- ParserFactory: 解析器工厂
- get_parser_factory: 获取全局工厂实例
"""

from .base import ParseResult, IDocumentParser, BaseParser
from .factory import ParserFactory, get_parser_factory

__all__ = [
    'ParseResult',
    'IDocumentParser',
    'BaseParser',
    'ParserFactory',
    'get_parser_factory',
]
