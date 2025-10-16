"""
文档解析器基础模块

定义文档解析器的抽象接口和数据结构
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import time
import os


@dataclass
class ParseResult:
    """
    文档解析结果

    Attributes:
        success: 解析是否成功
        content: 提取的文本内容
        metadata: 文档元数据
        error: 错误信息（如果失败）
        parse_time: 解析耗时（秒）
    """
    success: bool
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    parse_time: float = 0.0

    def __post_init__(self):
        """验证数据"""
        if not self.success and not self.error:
            raise ValueError("解析失败时必须提供错误信息")


class IDocumentParser(ABC):
    """
    文档解析器接口

    所有文档解析器都应该继承此类并实现相应方法
    """

    @abstractmethod
    def supports(self, file_path: str) -> bool:
        """
        判断是否支持该文件类型

        Args:
            file_path: 文件路径

        Returns:
            是否支持该文件
        """
        pass

    @abstractmethod
    def parse(self, file_path: str) -> ParseResult:
        """
        解析文档

        Args:
            file_path: 文件路径

        Returns:
            解析结果
        """
        pass

    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        获取文档元数据（可选实现）

        Args:
            file_path: 文件路径

        Returns:
            元数据字典
        """
        return {}

    def validate_file(self, file_path: str) -> bool:
        """
        验证文件是否存在且可读

        Args:
            file_path: 文件路径

        Returns:
            文件是否有效
        """
        if not os.path.exists(file_path):
            return False
        if not os.path.isfile(file_path):
            return False
        if not os.access(file_path, os.R_OK):
            return False
        return True


class ParserFactory:
    """
    解析器工厂

    负责管理和分发文档解析器
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
            解析器实例，如果没有找到则返回 None
        """
        # 获取文件扩展名
        _, ext = os.path.splitext(file_path)
        ext_lower = ext.lower()

        # 查找对应的解析器
        parser_name = self._extension_map.get(ext_lower)
        if parser_name:
            return self._parsers.get(parser_name)

        return None

    def get_supported_extensions(self) -> List[str]:
        """
        获取所有支持的文件扩展名

        Returns:
            扩展名列表
        """
        return list(self._extension_map.keys())

    def get_parser_names(self) -> List[str]:
        """
        获取所有已注册的解析器名称

        Returns:
            解析器名称列表
        """
        return list(self._parsers.keys())

    def unregister_parser(self, name: str) -> bool:
        """
        注销解析器

        Args:
            name: 解析器名称

        Returns:
            是否成功注销
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


class BaseParser(IDocumentParser):
    """
    基础解析器实现

    提供通用的功能实现，具体解析器可以继承此类
    """

    def __init__(self, supported_extensions: List[str]):
        """
        初始化

        Args:
            supported_extensions: 支持的文件扩展名列表
        """
        self.supported_extensions = [
            ext.lower() if ext.startswith('.') else '.' + ext.lower()
            for ext in supported_extensions
        ]

    def supports(self, file_path: str) -> bool:
        """检查是否支持该文件"""
        _, ext = os.path.splitext(file_path)
        return ext.lower() in self.supported_extensions

    def parse(self, file_path: str) -> ParseResult:
        """
        解析文档（带计时和错误处理）

        子类应该重写 _parse_impl 方法而不是这个方法
        """
        start_time = time.time()

        # 验证文件
        if not self.validate_file(file_path):
            return ParseResult(
                success=False,
                content='',
                error=f'文件不存在或无法访问: {file_path}',
                parse_time=time.time() - start_time
            )

        # 检查是否支持
        if not self.supports(file_path):
            return ParseResult(
                success=False,
                content='',
                error=f'不支持的文件类型: {os.path.splitext(file_path)[1]}',
                parse_time=time.time() - start_time
            )

        try:
            # 调用具体实现
            result = self._parse_impl(file_path)
            result.parse_time = time.time() - start_time
            return result
        except Exception as e:
            return ParseResult(
                success=False,
                content='',
                error=f'解析失败: {str(e)}',
                parse_time=time.time() - start_time
            )

    @abstractmethod
    def _parse_impl(self, file_path: str) -> ParseResult:
        """
        具体的解析实现

        子类应该重写此方法

        Args:
            file_path: 文件路径

        Returns:
            解析结果
        """
        pass


# 全局解析器工厂实例
parser_factory = ParserFactory()


def get_parser_factory() -> ParserFactory:
    """
    获取全局解析器工厂实例

    Returns:
        解析器工厂
    """
    return parser_factory
