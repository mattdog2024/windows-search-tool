"""
文本解析器单元测试
"""

import pytest
import os
import tempfile
from unittest.mock import patch, Mock
from src.parsers.text_parser import TextParser
from src.parsers.base import ParseResult


class TestTextParser:
    """测试 TextParser 类"""

    @pytest.fixture
    def parser(self):
        """创建解析器实例"""
        return TextParser()

    def test_init(self, parser):
        """测试初始化"""
        assert parser is not None
        assert '.txt' in parser.supported_extensions
        assert '.md' in parser.supported_extensions
        assert '.csv' in parser.supported_extensions

    def test_supports_text_files(self, parser):
        """测试是否支持文本文件"""
        assert parser.supports('document.txt') is True
        assert parser.supports('document.TXT') is True
        assert parser.supports('readme.md') is True
        assert parser.supports('data.csv') is True
        assert parser.supports('app.log') is True
        assert parser.supports('config.json') is True
        assert parser.supports('data.xml') is True

    def test_not_supports_other_formats(self, parser):
        """测试不支持其他格式"""
        assert parser.supports('document.pdf') is False
        assert parser.supports('document.docx') is False
        assert parser.supports('image.png') is False

    def test_parse_nonexistent_file(self, parser):
        """测试解析不存在的文件"""
        result = parser.parse('nonexistent.txt')
        assert result.success is False
        assert result.error is not None

    def test_parse_utf8_file(self, parser):
        """测试解析 UTF-8 编码文件"""
        content = "这是UTF-8编码的文本\n包含中文内容"

        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            result = parser.parse(temp_path)

            assert result.success is True
            assert '中文' in result.content
            assert result.metadata['encoding'].lower() in ['utf-8', 'utf8', 'ascii']
            assert result.metadata['lines'] == 2
            assert result.parse_time > 0
        finally:
            os.unlink(temp_path)

    def test_parse_gbk_file(self, parser):
        """测试解析 GBK 编码文件"""
        content = "这是GBK编码的文本\n包含中文内容"

        with tempfile.NamedTemporaryFile(mode='w', encoding='gbk', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            result = parser.parse(temp_path)

            assert result.success is True
            assert '中文' in result.content
            # chardet 可能检测为 gbk 或 gb2312
            assert result.metadata['encoding'].lower() in ['gbk', 'gb2312', 'gb18030']
        finally:
            os.unlink(temp_path)

    def test_parse_utf8_with_bom(self, parser):
        """测试解析带 BOM 的 UTF-8 文件"""
        content = "UTF-8 BOM test\n测试内容"

        with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
            # 写入 UTF-8 BOM
            f.write(b'\xef\xbb\xbf')
            f.write(content.encode('utf-8'))
            temp_path = f.name

        try:
            result = parser.parse(temp_path)

            assert result.success is True
            assert result.metadata['has_bom'] is True
            # 内容不应包含 BOM 字符
            assert not result.content.startswith('\ufeff')
        finally:
            os.unlink(temp_path)

    def test_parse_csv_file(self, parser):
        """测试解析 CSV 文件"""
        content = "姓名,年龄,城市\n张三,28,北京\n李四,32,上海"

        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.csv', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            result = parser.parse(temp_path)

            assert result.success is True
            assert '姓名' in result.content
            assert '张三' in result.content
            assert '北京' in result.content
        finally:
            os.unlink(temp_path)

    def test_parse_markdown_file(self, parser):
        """测试解析 Markdown 文件"""
        content = "# 标题\n\n这是**粗体**文本。\n\n- 列表项1\n- 列表项2"

        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.md', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            result = parser.parse(temp_path)

            assert result.success is True
            assert '标题' in result.content
            assert '粗体' in result.content
            assert '列表项' in result.content
        finally:
            os.unlink(temp_path)

    def test_parse_empty_file(self, parser):
        """测试解析空文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            temp_path = f.name

        try:
            result = parser.parse(temp_path)

            assert result.success is True
            assert result.content == ''
            assert result.metadata['lines'] == 1  # 空文件有一行
            assert result.metadata['characters'] == 0
        finally:
            os.unlink(temp_path)

    def test_parse_large_file(self, parser):
        """测试解析大文件"""
        content = "Line {}\n" * 10000

        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f:
            for i in range(10000):
                f.write(f"Line {i}\n")
            temp_path = f.name

        try:
            result = parser.parse(temp_path)

            assert result.success is True
            assert result.metadata['lines'] == 10000
        finally:
            os.unlink(temp_path)

    def test_parse_special_characters(self, parser):
        """测试解析包含特殊字符的文件"""
        content = "特殊字符: !@#$%^&*()\n中文标点：，。！？；：\n表情符号: 😀🎉"

        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            result = parser.parse(temp_path)

            assert result.success is True
            assert '特殊字符' in result.content
            assert '!@#$%' in result.content
            assert '中文标点' in result.content
        finally:
            os.unlink(temp_path)

    def test_parse_multiline_text(self, parser):
        """测试解析多行文本"""
        content = """第一行
第二行
第三行

第五行（中间有空行）
"""

        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            result = parser.parse(temp_path)

            assert result.success is True
            assert '第一行' in result.content
            assert '第五行' in result.content
            assert result.metadata['lines'] == 6
        finally:
            os.unlink(temp_path)

    def test_chardet_low_confidence(self, parser):
        """测试 chardet 检测置信度低的情况"""
        content = "Test content"

        # Mock chardet.detect 返回低置信度
        with patch('chardet.detect') as mock_detect:
            mock_detect.return_value = {'encoding': 'ascii', 'confidence': 0.5}

            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f:
                f.write(content)
                temp_path = f.name

            try:
                result = parser.parse(temp_path)

                # 应该成功，使用备用编码
                assert result.success is True
            finally:
                os.unlink(temp_path)

    def test_chardet_fails(self, parser):
        """测试 chardet 完全失败的情况"""
        content = "Test content"

        # Mock chardet.detect 返回 None
        with patch('chardet.detect') as mock_detect:
            mock_detect.return_value = {'encoding': None, 'confidence': 0.0}

            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f:
                f.write(content)
                temp_path = f.name

            try:
                result = parser.parse(temp_path)

                # 应该成功，使用备用编码
                assert result.success is True
            finally:
                os.unlink(temp_path)

    def test_decode_error_with_fallback(self, parser):
        """测试解码错误时的降级处理"""
        # 创建包含无法解码字节的文件
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as f:
            f.write(b'Valid text\n')
            f.write(b'\xff\xfe\xfd')  # 无效字节
            f.write(b'\nMore text')
            temp_path = f.name

        try:
            # Mock chardet 返回错误的编码
            with patch('chardet.detect') as mock_detect:
                mock_detect.return_value = {'encoding': 'utf-8', 'confidence': 0.9}

                result = parser.parse(temp_path)

                # 应该成功，但使用 errors='ignore' 模式
                assert result.success is True
        finally:
            os.unlink(temp_path)

    def test_try_common_encodings(self, parser):
        """测试尝试常见编码"""
        # UTF-8 内容
        utf8_data = "测试内容".encode('utf-8')
        encoding = parser._try_common_encodings(utf8_data)
        assert encoding == 'utf-8'

        # GBK 内容
        gbk_data = "测试内容".encode('gbk')
        encoding = parser._try_common_encodings(gbk_data)
        assert encoding in ['utf-8', 'gbk', 'gb2312', 'gb18030']

        # 无效数据
        invalid_data = b'\xff\xfe\xfd\xfc'
        encoding = parser._try_common_encodings(invalid_data)
        # latin-1 总是能解码任何字节序列
        assert encoding == 'latin-1'

    def test_remove_bom(self, parser):
        """测试移除 BOM"""
        # 带 BOM 的内容
        content_with_bom = '\ufeffTest content'
        result = parser._remove_bom(content_with_bom)
        assert result == 'Test content'

        # 不带 BOM 的内容
        content_without_bom = 'Test content'
        result = parser._remove_bom(content_without_bom)
        assert result == 'Test content'

    def test_get_metadata(self, parser):
        """测试获取元数据"""
        content = "Test content"

        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            metadata = parser.get_metadata(temp_path)

            assert 'size' in metadata
            assert 'modified' in metadata
            assert 'created' in metadata
        finally:
            os.unlink(temp_path)

    def test_get_metadata_exception(self, parser):
        """测试获取元数据时发生异常"""
        metadata = parser.get_metadata('nonexistent.txt')
        assert metadata == {}

    def test_parse_exception(self, parser):
        """测试解析过程中发生异常"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            temp_path = f.name

        try:
            # Mock open 抛出异常
            with patch('builtins.open', side_effect=IOError("Test error")):
                result = parser.parse(temp_path)

                assert result.success is False
                assert result.error is not None
                assert 'Test error' in result.error
        finally:
            os.unlink(temp_path)

    def test_metadata_fields(self, parser):
        """测试元数据字段完整性"""
        content = "测试内容\n第二行"

        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            result = parser.parse(temp_path)

            assert result.success is True
            # 检查所有必要的元数据字段
            assert 'encoding' in result.metadata
            assert 'encoding_confidence' in result.metadata
            assert 'size' in result.metadata
            assert 'lines' in result.metadata
            assert 'characters' in result.metadata
            assert 'has_bom' in result.metadata

            assert result.metadata['size'] > 0
            assert result.metadata['lines'] == 2
            assert result.metadata['characters'] == len(content)
            assert result.metadata['has_bom'] is False
        finally:
            os.unlink(temp_path)
