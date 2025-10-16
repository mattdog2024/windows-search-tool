"""
PDF 解析器单元测试
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from src.parsers.pdf_parser import PdfParser
from src.parsers.base import ParseResult


class TestPdfParser:
    """测试 PdfParser 类"""

    @pytest.fixture
    def parser(self):
        """创建解析器实例"""
        return PdfParser()

    def test_init(self, parser):
        """测试初始化"""
        assert parser is not None
        assert '.pdf' in parser.supported_extensions

    def test_supports_pdf(self, parser):
        """测试是否支持 PDF 文件"""
        assert parser.supports('document.pdf') is True
        assert parser.supports('document.PDF') is True
        assert parser.supports('path/to/file.pdf') is True

    def test_not_supports_other_formats(self, parser):
        """测试不支持其他格式"""
        assert parser.supports('document.txt') is False
        assert parser.supports('document.docx') is False
        assert parser.supports('document.xlsx') is False

    def test_parse_nonexistent_file(self, parser):
        """测试解析不存在的文件"""
        result = parser.parse('nonexistent.pdf')
        assert result.success is False
        assert result.error is not None
        assert '不存在' in result.error or '无法访问' in result.error

    def test_parse_with_mock_pdf(self, parser):
        """测试解析 PDF（使用 mock）"""
        # 创建 mock PDF 对象
        mock_page = Mock()
        mock_page.extract_text.return_value = "This is test content from page 1."

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.metadata = {
            'Author': 'Test Author',
            'Title': 'Test Title',
            'CreationDate': 'D:20230101120000',
        }

        with patch('pdfplumber.open', return_value=mock_pdf):
            # 创建临时文件
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                temp_path = f.name

            try:
                result = parser.parse(temp_path)

                assert result.success is True
                assert 'test content' in result.content.lower()
                assert result.metadata['pages'] == 1
                assert result.metadata['author'] == 'Test Author'
                assert result.metadata['title'] == 'Test Title'
                assert result.parse_time > 0
            finally:
                os.unlink(temp_path)

    def test_parse_multi_page_pdf(self, parser):
        """测试解析多页 PDF"""
        # 创建 mock 多页 PDF
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Content from page 1."

        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "Content from page 2."

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page1, mock_page2]
        mock_pdf.metadata = {}

        with patch('pdfplumber.open', return_value=mock_pdf):
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                temp_path = f.name

            try:
                result = parser.parse(temp_path)

                assert result.success is True
                assert 'page 1' in result.content.lower()
                assert 'page 2' in result.content.lower()
                assert result.metadata['pages'] == 2
            finally:
                os.unlink(temp_path)

    def test_parse_scanned_pdf(self, parser):
        """测试解析扫描版 PDF（几乎无文本）"""
        # 创建几乎无文本的 mock PDF
        mock_page = Mock()
        mock_page.extract_text.return_value = "abc"  # 很少的文本

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.metadata = {}

        with patch('pdfplumber.open', return_value=mock_pdf):
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                temp_path = f.name

            try:
                result = parser.parse(temp_path)

                assert result.success is True
                assert result.metadata['is_scanned'] is True
            finally:
                os.unlink(temp_path)

    def test_parse_text_pdf(self, parser):
        """测试解析文本型 PDF"""
        # 创建包含大量文本的 mock PDF
        mock_page = Mock()
        mock_page.extract_text.return_value = "This is a normal text PDF with lots of content. " * 10

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.metadata = {}

        with patch('pdfplumber.open', return_value=mock_pdf):
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                temp_path = f.name

            try:
                result = parser.parse(temp_path)

                assert result.success is True
                assert result.metadata['is_scanned'] is False
            finally:
                os.unlink(temp_path)

    def test_parse_pdf_with_chinese(self, parser):
        """测试解析包含中文的 PDF"""
        mock_page = Mock()
        mock_page.extract_text.return_value = "这是一个包含中文内容的PDF文档。\nChinese content test."

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.metadata = {}

        with patch('pdfplumber.open', return_value=mock_pdf):
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                temp_path = f.name

            try:
                result = parser.parse(temp_path)

                assert result.success is True
                assert '中文' in result.content
                assert 'Chinese' in result.content
            finally:
                os.unlink(temp_path)

    def test_parse_pdf_with_empty_pages(self, parser):
        """测试解析包含空白页的 PDF"""
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Content on page 1."

        mock_page2 = Mock()
        mock_page2.extract_text.return_value = None  # 空白页

        mock_page3 = Mock()
        mock_page3.extract_text.return_value = "Content on page 3."

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page1, mock_page2, mock_page3]
        mock_pdf.metadata = {}

        with patch('pdfplumber.open', return_value=mock_pdf):
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                temp_path = f.name

            try:
                result = parser.parse(temp_path)

                assert result.success is True
                assert 'page 1' in result.content.lower()
                assert 'page 3' in result.content.lower()
                assert result.metadata['pages'] == 3
            finally:
                os.unlink(temp_path)

    def test_parse_pdf_exception(self, parser):
        """测试解析 PDF 时发生异常"""
        with patch('pdfplumber.open', side_effect=Exception("Test error")):
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                temp_path = f.name

            try:
                result = parser.parse(temp_path)

                assert result.success is False
                assert result.error is not None
                assert 'Test error' in result.error
            finally:
                os.unlink(temp_path)

    def test_parse_pdf_page_exception(self, parser):
        """测试解析某页时发生异常"""
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Page 1 content."

        mock_page2 = Mock()
        mock_page2.extract_text.side_effect = Exception("Page error")

        mock_page3 = Mock()
        mock_page3.extract_text.return_value = "Page 3 content."

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page1, mock_page2, mock_page3]
        mock_pdf.metadata = {}

        with patch('pdfplumber.open', return_value=mock_pdf):
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                temp_path = f.name

            try:
                result = parser.parse(temp_path)

                # 应该成功，但跳过出错的页面
                assert result.success is True
                assert 'Page 1' in result.content
                assert 'Page 3' in result.content
            finally:
                os.unlink(temp_path)

    def test_get_metadata(self, parser):
        """测试获取元数据"""
        mock_page = Mock()
        mock_page.extract_text.return_value = "Test content with enough text to not be scanned."

        mock_pdf = Mock()
        mock_pdf.pages = [mock_page]
        mock_pdf.metadata = {
            'Author': 'Test Author',
            'Title': 'Test Title',
        }

        with patch('pdfplumber.open', return_value=mock_pdf):
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                temp_path = f.name

            try:
                metadata = parser.get_metadata(temp_path)

                assert metadata['pages'] == 1
                assert metadata['author'] == 'Test Author'
                assert metadata['title'] == 'Test Title'
            finally:
                os.unlink(temp_path)

    def test_get_metadata_exception(self, parser):
        """测试获取元数据时发生异常"""
        with patch('pdfplumber.open', side_effect=Exception("Metadata error")):
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                temp_path = f.name

            try:
                metadata = parser.get_metadata(temp_path)
                assert metadata == {}
            finally:
                os.unlink(temp_path)

    def test_extract_metadata_with_all_fields(self, parser):
        """测试提取完整的元数据"""
        mock_pdf = Mock()
        mock_pdf.pages = [Mock()]
        mock_pdf.metadata = {
            'Author': 'John Doe',
            'Title': 'Sample Document',
            'Subject': 'Testing',
            'Creator': 'Test App',
            'Producer': 'PDF Library',
            'CreationDate': 'D:20230101120000',
            'ModDate': 'D:20230102120000',
        }

        metadata = parser._extract_metadata(mock_pdf, False)

        assert metadata['author'] == 'John Doe'
        assert metadata['title'] == 'Sample Document'
        assert metadata['subject'] == 'Testing'
        assert metadata['creator'] == 'Test App'
        assert metadata['producer'] == 'PDF Library'
        assert 'creationdate' in metadata
        assert 'moddate' in metadata
        assert metadata['is_scanned'] is False

    def test_extract_metadata_minimal(self, parser):
        """测试提取最少元数据"""
        mock_pdf = Mock()
        mock_pdf.pages = [Mock(), Mock()]
        mock_pdf.metadata = None

        metadata = parser._extract_metadata(mock_pdf, True)

        assert metadata['pages'] == 2
        assert metadata['is_scanned'] is True
        # 不应该有其他字段
        assert 'author' not in metadata
        assert 'title' not in metadata
