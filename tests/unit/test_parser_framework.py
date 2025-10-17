"""
解析器框架单元测试
"""

import pytest
import os
import tempfile
from src.parsers.base import (
    ParseResult,
    IDocumentParser,
    BaseParser
)
from src.parsers.factory import ParserFactory
from src.parsers.text_parser import TextParser


class TestParseResult:
    """测试 ParseResult 数据类"""

    def test_create_success_result(self):
        """测试创建成功的解析结果"""
        result = ParseResult(
            success=True,
            content="Test content",
            metadata={"author": "Test"}
        )

        assert result.success is True
        assert result.content == "Test content"
        assert result.metadata["author"] == "Test"
        assert result.error is None

    def test_create_failure_result(self):
        """测试创建失败的解析结果"""
        result = ParseResult(
            success=False,
            content='',
            error="Parse error"
        )

        assert result.success is False
        assert result.content == ''
        assert result.error == "Parse error"

    def test_failure_without_error_raises(self):
        """测试失败时必须提供错误信息"""
        with pytest.raises(ValueError):
            ParseResult(success=False, content='')


class MockParser(BaseParser):
    """模拟解析器用于测试"""

    def __init__(self):
        super().__init__(supported_extensions=['.mock'])

    def _parse_impl(self, file_path: str) -> ParseResult:
        return ParseResult(
            success=True,
            content="Mock content",
            metadata={}
        )


class TestParserFactory:
    """测试解析器工厂"""

    def test_register_and_get_parser(self):
        """测试注册和获取解析器"""
        factory = ParserFactory()
        mock_parser = MockParser()

        factory.register_parser('mock', ['.mock'], mock_parser)

        parser = factory.get_parser('test.mock')
        assert parser is not None
        assert isinstance(parser, MockParser)

    def test_get_parser_case_insensitive(self):
        """测试扩展名不区分大小写"""
        factory = ParserFactory()
        mock_parser = MockParser()

        factory.register_parser('mock', ['.mock'], mock_parser)

        parser1 = factory.get_parser('test.MOCK')
        parser2 = factory.get_parser('test.Mock')
        parser3 = factory.get_parser('test.mock')

        assert parser1 is not None
        assert parser2 is not None
        assert parser3 is not None

    def test_get_parser_not_found(self):
        """测试获取不存在的解析器"""
        factory = ParserFactory()

        parser = factory.get_parser('test.unknown')
        assert parser is None

    def test_get_supported_extensions(self):
        """测试获取支持的扩展名列表"""
        factory = ParserFactory()
        mock_parser = MockParser()

        factory.register_parser('mock', ['.mock', '.test'], mock_parser)

        extensions = factory.get_supported_extensions()
        assert '.mock' in extensions
        assert '.test' in extensions

    def test_unregister_parser(self):
        """测试注销解析器"""
        factory = ParserFactory()
        mock_parser = MockParser()

        factory.register_parser('mock', ['.mock'], mock_parser)
        assert factory.get_parser('test.mock') is not None

        success = factory.unregister_parser('mock')
        assert success is True
        assert factory.get_parser('test.mock') is None


class TestTextParser:
    """测试文本解析器"""

    def setup_method(self):
        """每个测试前的设置"""
        self.parser = TextParser()

    def test_supports_txt(self):
        """测试是否支持 .txt 文件"""
        assert self.parser.supports('test.txt') is True
        assert self.parser.supports('test.TXT') is True

    def test_supports_md(self):
        """测试是否支持 .md 文件"""
        assert self.parser.supports('README.md') is True

    def test_not_supports_docx(self):
        """测试不支持 .docx 文件"""
        assert self.parser.supports('test.docx') is False

    def test_parse_utf8_file(self):
        """测试解析 UTF-8 文本文件"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.txt',
            encoding='utf-8',
            delete=False
        ) as f:
            f.write('测试内容\nTest content')
            temp_file = f.name

        try:
            result = self.parser.parse(temp_file)

            assert result.success is True
            assert '测试内容' in result.content
            assert 'Test content' in result.content
            assert result.metadata['encoding'] == 'utf-8'
            assert result.metadata['lines'] == 2
        finally:
            os.unlink(temp_file)

    def test_parse_nonexistent_file(self):
        """测试解析不存在的文件"""
        result = self.parser.parse('nonexistent.txt')

        assert result.success is False
        assert '不存在' in result.error or '无法访问' in result.error

    def test_parse_unsupported_file(self):
        """测试解析不支持的文件类型"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.xyz',
            delete=False
        ) as f:
            f.write('content')
            temp_file = f.name

        try:
            result = self.parser.parse(temp_file)

            assert result.success is False
            assert '不支持' in result.error
        finally:
            os.unlink(temp_file)


class TestBaseParser:
    """测试基础解析器"""

    def test_validate_file_exists(self):
        """测试文件验证 - 存在的文件"""
        parser = MockParser()

        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = f.name

        try:
            assert parser.validate_file(temp_file) is True
        finally:
            os.unlink(temp_file)

    def test_validate_file_not_exists(self):
        """测试文件验证 - 不存在的文件"""
        parser = MockParser()
        assert parser.validate_file('nonexistent.file') is False

    def test_parse_with_timing(self):
        """测试解析时间记录"""
        parser = MockParser()

        # 创建临时文件
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.mock',
            delete=False
        ) as f:
            f.write('content')
            temp_file = f.name

        try:
            result = parser.parse(temp_file)

            assert result.success is True
            assert result.parse_time > 0
        finally:
            os.unlink(temp_file)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
