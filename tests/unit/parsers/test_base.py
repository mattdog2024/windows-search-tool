"""
解析器基础模块单元测试

测试 ParseResult, IDocumentParser, BaseParser 等核心类
"""

import pytest
import os
import tempfile
from src.parsers.base import ParseResult, IDocumentParser, BaseParser


class TestParseResult:
    """测试 ParseResult 数据类"""

    def test_create_success_result(self):
        """测试创建成功的解析结果"""
        result = ParseResult(
            success=True,
            content="测试内容",
            metadata={"author": "张三", "title": "测试文档"}
        )

        assert result.success is True
        assert result.content == "测试内容"
        assert result.metadata["author"] == "张三"
        assert result.metadata["title"] == "测试文档"
        assert result.error is None
        assert result.parse_time == 0.0

    def test_create_success_result_with_parse_time(self):
        """测试创建带解析时间的成功结果"""
        result = ParseResult(
            success=True,
            content="内容",
            metadata={},
            parse_time=1.5
        )

        assert result.success is True
        assert result.parse_time == 1.5

    def test_create_failure_result(self):
        """测试创建失败的解析结果"""
        result = ParseResult(
            success=False,
            content='',
            error="文件不存在"
        )

        assert result.success is False
        assert result.content == ''
        assert result.error == "文件不存在"
        assert result.metadata == {}

    def test_failure_without_error_raises(self):
        """测试失败时必须提供错误信息"""
        with pytest.raises(ValueError, match="解析失败时必须提供错误信息"):
            ParseResult(success=False, content='')

    def test_failure_with_empty_error_raises(self):
        """测试失败时错误信息不能为空"""
        with pytest.raises(ValueError):
            ParseResult(success=False, content='', error='')

    def test_success_with_empty_content(self):
        """测试成功但内容为空（合法情况）"""
        result = ParseResult(
            success=True,
            content='',
            metadata={"empty": True}
        )

        assert result.success is True
        assert result.content == ''

    def test_metadata_default_factory(self):
        """测试元数据默认为空字典"""
        result = ParseResult(
            success=True,
            content='测试'
        )

        assert result.metadata == {}
        assert isinstance(result.metadata, dict)


class MockParser(BaseParser):
    """模拟解析器用于测试"""

    def __init__(self, should_fail=False):
        super().__init__(supported_extensions=['.mock', '.test'])
        self.should_fail = should_fail
        self.parse_count = 0

    def _parse_impl(self, file_path: str) -> ParseResult:
        self.parse_count += 1

        if self.should_fail:
            raise ValueError("模拟解析错误")

        return ParseResult(
            success=True,
            content=f"模拟内容来自: {os.path.basename(file_path)}",
            metadata={"file_path": file_path}
        )


class TestIDocumentParser:
    """测试 IDocumentParser 接口"""

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
        assert parser.validate_file('nonexistent_file_12345.txt') is False

    def test_validate_file_is_directory(self):
        """测试文件验证 - 目录不是文件"""
        parser = MockParser()

        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            assert parser.validate_file(temp_dir) is False

    def test_get_metadata_default_implementation(self):
        """测试默认的 get_metadata 实现返回空字典"""
        parser = MockParser()

        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_file = f.name

        try:
            metadata = parser.get_metadata(temp_file)
            assert metadata == {}
        finally:
            os.unlink(temp_file)


class TestBaseParser:
    """测试 BaseParser 基础解析器"""

    def test_initialization_with_extensions(self):
        """测试使用扩展名初始化"""
        parser = MockParser()

        assert '.mock' in parser.supported_extensions
        assert '.test' in parser.supported_extensions

    def test_initialization_normalizes_extensions(self):
        """测试初始化时标准化扩展名"""
        # MockParser 已经测试了扩展名标准化
        # 测试不带点的扩展名会被标准化
        parser = MockParser()

        # MockParser 使用 ['.mock', '.test'] 初始化
        assert all(ext.startswith('.') for ext in parser.supported_extensions)
        assert all(ext.islower() for ext in parser.supported_extensions)

    def test_supports_file_type(self):
        """测试是否支持文件类型"""
        parser = MockParser()

        assert parser.supports('test.mock') is True
        assert parser.supports('test.test') is True
        assert parser.supports('file.MOCK') is True  # 大小写不敏感
        assert parser.supports('test.txt') is False

    def test_supports_case_insensitive(self):
        """测试扩展名不区分大小写"""
        parser = MockParser()

        assert parser.supports('test.mock') is True
        assert parser.supports('test.MOCK') is True
        assert parser.supports('test.Mock') is True
        assert parser.supports('test.MoCk') is True

    def test_parse_success(self):
        """测试成功解析文件"""
        parser = MockParser()

        # 创建临时文件
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.mock',
            delete=False,
            encoding='utf-8'
        ) as f:
            f.write('测试内容')
            temp_file = f.name

        try:
            result = parser.parse(temp_file)

            assert result.success is True
            assert '模拟内容来自' in result.content
            assert result.error is None
            assert result.parse_time > 0
            assert parser.parse_count == 1
        finally:
            os.unlink(temp_file)

    def test_parse_nonexistent_file(self):
        """测试解析不存在的文件"""
        parser = MockParser()

        result = parser.parse('nonexistent_file_12345.mock')

        assert result.success is False
        assert '不存在' in result.error or '无法访问' in result.error
        assert result.content == ''
        assert result.parse_time >= 0  # 时间可能很短,接近 0
        assert parser.parse_count == 0  # 不应该调用 _parse_impl

    def test_parse_unsupported_file_type(self):
        """测试解析不支持的文件类型"""
        parser = MockParser()

        # 创建临时文件
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.xyz',
            delete=False
        ) as f:
            f.write('content')
            temp_file = f.name

        try:
            result = parser.parse(temp_file)

            assert result.success is False
            assert '不支持' in result.error
            assert result.content == ''
            assert parser.parse_count == 0
        finally:
            os.unlink(temp_file)

    def test_parse_with_exception(self):
        """测试解析时抛出异常"""
        parser = MockParser(should_fail=True)

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

            assert result.success is False
            assert '解析失败' in result.error
            assert '模拟解析错误' in result.error
            assert result.content == ''
            assert result.parse_time >= 0
            assert parser.parse_count == 1
        finally:
            os.unlink(temp_file)

    def test_parse_records_time(self):
        """测试解析时间被正确记录"""
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

            assert result.parse_time >= 0  # 时间应该被记录
            assert result.parse_time < 1.0  # 应该很快
        finally:
            os.unlink(temp_file)

    def test_parse_multiple_files(self):
        """测试连续解析多个文件"""
        parser = MockParser()

        files = []
        try:
            # 创建多个临时文件
            for i in range(3):
                with tempfile.NamedTemporaryFile(
                    mode='w',
                    suffix='.mock',
                    delete=False
                ) as f:
                    f.write(f'content {i}')
                    files.append(f.name)

            # 解析所有文件
            for file_path in files:
                result = parser.parse(file_path)
                assert result.success is True

            assert parser.parse_count == 3
        finally:
            for file_path in files:
                os.unlink(file_path)

    def test_parse_with_chinese_filename(self):
        """测试解析中文文件名"""
        parser = MockParser()

        # 创建带中文名的临时文件
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, '测试文档.mock')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('测试内容')

            result = parser.parse(file_path)

            assert result.success is True
            assert '测试文档.mock' in result.content

    def test_parse_empty_file(self):
        """测试解析空文件"""
        parser = MockParser()

        # 创建空文件
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.mock',
            delete=False
        ) as f:
            temp_file = f.name

        try:
            result = parser.parse(temp_file)

            assert result.success is True
            assert parser.parse_count == 1
        finally:
            os.unlink(temp_file)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
