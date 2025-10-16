"""
解析器工厂单元测试

测试 ParserFactory 和 get_parser_factory 功能
"""

import pytest
import tempfile
import os
from src.parsers.factory import ParserFactory, get_parser_factory
from src.parsers.base import IDocumentParser, BaseParser, ParseResult


class MockTextParser(BaseParser):
    """模拟文本解析器"""

    def __init__(self):
        super().__init__(supported_extensions=['.txt', '.md'])

    def _parse_impl(self, file_path: str) -> ParseResult:
        return ParseResult(
            success=True,
            content="文本内容",
            metadata={"type": "text"}
        )


class MockPdfParser(BaseParser):
    """模拟PDF解析器"""

    def __init__(self):
        super().__init__(supported_extensions=['.pdf'])

    def _parse_impl(self, file_path: str) -> ParseResult:
        return ParseResult(
            success=True,
            content="PDF内容",
            metadata={"type": "pdf"}
        )


class MockDocxParser(BaseParser):
    """模拟Word解析器"""

    def __init__(self):
        super().__init__(supported_extensions=['.docx', '.doc'])

    def _parse_impl(self, file_path: str) -> ParseResult:
        return ParseResult(
            success=True,
            content="Word内容",
            metadata={"type": "docx"}
        )


class TestParserFactory:
    """测试解析器工厂"""

    def test_factory_initialization(self):
        """测试工厂初始化"""
        factory = ParserFactory()

        assert factory is not None
        assert factory.get_parser_names() == []
        assert factory.get_supported_extensions() == []

    def test_register_single_parser(self):
        """测试注册单个解析器"""
        factory = ParserFactory()
        text_parser = MockTextParser()

        factory.register_parser('text', ['.txt', '.md'], text_parser)

        assert 'text' in factory.get_parser_names()
        assert '.txt' in factory.get_supported_extensions()
        assert '.md' in factory.get_supported_extensions()

    def test_register_parser_without_dot(self):
        """测试注册解析器时扩展名不带点"""
        factory = ParserFactory()
        text_parser = MockTextParser()

        factory.register_parser('text', ['txt', 'md'], text_parser)

        assert '.txt' in factory.get_supported_extensions()
        assert '.md' in factory.get_supported_extensions()

    def test_register_multiple_parsers(self):
        """测试注册多个解析器"""
        factory = ParserFactory()

        factory.register_parser('text', ['.txt', '.md'], MockTextParser())
        factory.register_parser('pdf', ['.pdf'], MockPdfParser())
        factory.register_parser('docx', ['.docx', '.doc'], MockDocxParser())

        parser_names = factory.get_parser_names()
        assert 'text' in parser_names
        assert 'pdf' in parser_names
        assert 'docx' in parser_names
        assert len(parser_names) == 3

    def test_get_parser_by_extension(self):
        """测试根据扩展名获取解析器"""
        factory = ParserFactory()
        text_parser = MockTextParser()

        factory.register_parser('text', ['.txt', '.md'], text_parser)

        parser = factory.get_parser('document.txt')
        assert parser is not None
        assert isinstance(parser, MockTextParser)

    def test_get_parser_case_insensitive(self):
        """测试获取解析器时扩展名不区分大小写"""
        factory = ParserFactory()
        text_parser = MockTextParser()

        factory.register_parser('text', ['.txt'], text_parser)

        assert factory.get_parser('file.txt') is not None
        assert factory.get_parser('file.TXT') is not None
        assert factory.get_parser('file.Txt') is not None
        assert factory.get_parser('file.TxT') is not None

    def test_get_parser_not_found(self):
        """测试获取不存在的解析器"""
        factory = ParserFactory()

        parser = factory.get_parser('file.unknown')
        assert parser is None

    def test_get_parser_returns_correct_parser(self):
        """测试获取正确的解析器实例"""
        factory = ParserFactory()

        factory.register_parser('text', ['.txt'], MockTextParser())
        factory.register_parser('pdf', ['.pdf'], MockPdfParser())
        factory.register_parser('docx', ['.docx'], MockDocxParser())

        txt_parser = factory.get_parser('file.txt')
        pdf_parser = factory.get_parser('file.pdf')
        docx_parser = factory.get_parser('file.docx')

        assert isinstance(txt_parser, MockTextParser)
        assert isinstance(pdf_parser, MockPdfParser)
        assert isinstance(docx_parser, MockDocxParser)

    def test_supports_file_type(self):
        """测试检查文件类型是否支持"""
        factory = ParserFactory()

        factory.register_parser('text', ['.txt', '.md'], MockTextParser())

        assert factory.supports('file.txt') is True
        assert factory.supports('file.md') is True
        assert factory.supports('file.pdf') is False

    def test_supports_case_insensitive(self):
        """测试支持检查不区分大小写"""
        factory = ParserFactory()

        factory.register_parser('text', ['.txt'], MockTextParser())

        assert factory.supports('file.txt') is True
        assert factory.supports('file.TXT') is True
        assert factory.supports('file.Txt') is True

    def test_get_supported_extensions_sorted(self):
        """测试获取支持的扩展名列表已排序"""
        factory = ParserFactory()

        factory.register_parser('text', ['.txt', '.md', '.csv'], MockTextParser())
        factory.register_parser('pdf', ['.pdf'], MockPdfParser())

        extensions = factory.get_supported_extensions()
        assert extensions == sorted(extensions)

    def test_get_parser_names_sorted(self):
        """测试获取解析器名称列表已排序"""
        factory = ParserFactory()

        factory.register_parser('text', ['.txt'], MockTextParser())
        factory.register_parser('pdf', ['.pdf'], MockPdfParser())
        factory.register_parser('docx', ['.docx'], MockDocxParser())

        names = factory.get_parser_names()
        assert names == sorted(names)

    def test_unregister_parser(self):
        """测试注销解析器"""
        factory = ParserFactory()

        factory.register_parser('text', ['.txt', '.md'], MockTextParser())

        assert factory.get_parser('file.txt') is not None
        assert 'text' in factory.get_parser_names()

        success = factory.unregister_parser('text')

        assert success is True
        assert factory.get_parser('file.txt') is None
        assert 'text' not in factory.get_parser_names()
        assert '.txt' not in factory.get_supported_extensions()
        assert '.md' not in factory.get_supported_extensions()

    def test_unregister_nonexistent_parser(self):
        """测试注销不存在的解析器"""
        factory = ParserFactory()

        success = factory.unregister_parser('nonexistent')
        assert success is False

    def test_unregister_parser_removes_all_extensions(self):
        """测试注销解析器时移除所有关联的扩展名"""
        factory = ParserFactory()

        factory.register_parser('text', ['.txt', '.md', '.csv'], MockTextParser())

        factory.unregister_parser('text')

        assert '.txt' not in factory.get_supported_extensions()
        assert '.md' not in factory.get_supported_extensions()
        assert '.csv' not in factory.get_supported_extensions()

    def test_clear_factory(self):
        """测试清空工厂"""
        factory = ParserFactory()

        factory.register_parser('text', ['.txt'], MockTextParser())
        factory.register_parser('pdf', ['.pdf'], MockPdfParser())

        factory.clear()

        assert factory.get_parser_names() == []
        assert factory.get_supported_extensions() == []
        assert factory.get_parser('file.txt') is None

    def test_get_parser_info_exists(self):
        """测试获取存在的解析器信息"""
        factory = ParserFactory()
        text_parser = MockTextParser()

        factory.register_parser('text', ['.txt', '.md'], text_parser)

        info = factory.get_parser_info('text')

        assert info is not None
        assert info['name'] == 'text'
        assert '.txt' in info['extensions']
        assert '.md' in info['extensions']
        assert info['parser'] is text_parser

    def test_get_parser_info_not_exists(self):
        """测试获取不存在的解析器信息"""
        factory = ParserFactory()

        info = factory.get_parser_info('nonexistent')
        assert info is None

    def test_get_parser_info_extensions_sorted(self):
        """测试解析器信息中的扩展名已排序"""
        factory = ParserFactory()

        factory.register_parser('text', ['.md', '.txt', '.csv'], MockTextParser())

        info = factory.get_parser_info('text')
        assert info['extensions'] == sorted(info['extensions'])

    def test_register_same_extension_to_different_parsers(self):
        """测试同一扩展名注册到不同解析器（后者覆盖前者）"""
        factory = ParserFactory()

        factory.register_parser('parser1', ['.txt'], MockTextParser())
        factory.register_parser('parser2', ['.txt'], MockPdfParser())

        # 后注册的解析器应该覆盖前面的
        parser = factory.get_parser('file.txt')
        assert isinstance(parser, MockPdfParser)

    def test_factory_with_file_paths(self):
        """测试工厂处理完整文件路径"""
        factory = ParserFactory()

        factory.register_parser('text', ['.txt'], MockTextParser())

        # 测试各种路径格式
        assert factory.get_parser('file.txt') is not None
        assert factory.get_parser('./dir/file.txt') is not None
        assert factory.get_parser('/absolute/path/file.txt') is not None
        assert factory.get_parser('C:\\Windows\\file.txt') is not None

    def test_factory_with_multiple_dots_in_filename(self):
        """测试包含多个点的文件名"""
        factory = ParserFactory()

        factory.register_parser('text', ['.txt'], MockTextParser())

        parser = factory.get_parser('file.backup.old.txt')
        assert parser is not None
        assert isinstance(parser, MockTextParser)

    def test_factory_integration_with_real_parsing(self):
        """测试工厂与实际解析的集成"""
        factory = ParserFactory()

        factory.register_parser('text', ['.txt'], MockTextParser())

        # 创建临时文件
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.txt',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write('测试内容')
            temp_file = f.name

        try:
            # 获取解析器并解析
            parser = factory.get_parser(temp_file)
            assert parser is not None

            result = parser.parse(temp_file)
            assert result.success is True
            assert result.content == "文本内容"
            assert result.metadata['type'] == 'text'
        finally:
            os.unlink(temp_file)


class TestGetParserFactory:
    """测试全局工厂实例获取函数"""

    def test_get_parser_factory_returns_instance(self):
        """测试获取全局工厂实例"""
        factory = get_parser_factory()

        assert factory is not None
        assert isinstance(factory, ParserFactory)

    def test_get_parser_factory_returns_singleton(self):
        """测试多次调用返回同一实例"""
        factory1 = get_parser_factory()
        factory2 = get_parser_factory()

        assert factory1 is factory2

    def test_global_factory_registration(self):
        """测试全局工厂的注册功能"""
        factory = get_parser_factory()

        # 清空工厂以避免测试干扰
        factory.clear()

        # 注册解析器
        factory.register_parser('test', ['.test'], MockTextParser())

        # 再次获取工厂,应该保留注册的解析器
        factory2 = get_parser_factory()
        assert 'test' in factory2.get_parser_names()

        # 清理
        factory.clear()

    def test_global_factory_isolation_between_tests(self):
        """测试测试之间的工厂状态隔离"""
        factory = get_parser_factory()

        # 清空确保干净状态
        factory.clear()

        # 注册一个测试解析器
        factory.register_parser('isolated', ['.iso'], MockTextParser())

        assert 'isolated' in factory.get_parser_names()

        # 清理
        factory.unregister_parser('isolated')

        assert 'isolated' not in factory.get_parser_names()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
