"""
Office 文档解析器单元测试

测试 DocxParser, XlsxParser, PptxParser 的功能
"""

import os
import pytest
from pathlib import Path
from src.parsers.office_parsers import DocxParser, XlsxParser, PptxParser
from src.parsers.base import ParseResult


# 测试文件路径
FIXTURES_DIR = Path(__file__).parent.parent.parent / 'fixtures' / 'sample_files'
SAMPLE_DOCX = FIXTURES_DIR / 'sample.docx'
SAMPLE_XLSX = FIXTURES_DIR / 'sample.xlsx'
SAMPLE_PPTX = FIXTURES_DIR / 'sample.pptx'


class TestDocxParser:
    """测试 Word 文档解析器"""

    @pytest.fixture
    def parser(self):
        """创建解析器实例"""
        return DocxParser()

    def test_supports(self, parser):
        """测试文件类型支持"""
        assert parser.supports('test.docx') is True
        assert parser.supports('test.DOCX') is True
        assert parser.supports('test.doc') is False
        assert parser.supports('test.pdf') is False
        assert parser.supports('test.txt') is False

    def test_parse_sample_docx(self, parser):
        """测试解析真实 Word 文档"""
        if not SAMPLE_DOCX.exists():
            pytest.skip(f"测试文件不存在: {SAMPLE_DOCX}")

        result = parser.parse(str(SAMPLE_DOCX))

        # 验证解析成功
        assert isinstance(result, ParseResult)
        assert result.success is True
        assert result.error is None
        assert result.parse_time > 0

        # 验证内容提取
        assert len(result.content) > 0
        assert '测试 Word 文档' in result.content
        assert '第一段内容' in result.content
        assert '张三' in result.content  # 表格内容
        assert '工程师' in result.content  # 表格内容

        # 验证元数据
        assert 'file_type' in result.metadata
        assert result.metadata['file_type'] == 'docx'
        assert 'author' in result.metadata
        assert result.metadata['author'] == '测试作者'
        assert 'title' in result.metadata
        assert result.metadata['title'] == 'Word 测试文档'
        assert 'paragraphs' in result.metadata
        assert result.metadata['paragraphs'] > 0
        assert 'tables' in result.metadata
        assert result.metadata['tables'] > 0

    def test_parse_chinese_content(self, parser):
        """测试中文内容解析"""
        if not SAMPLE_DOCX.exists():
            pytest.skip(f"测试文件不存在: {SAMPLE_DOCX}")

        result = parser.parse(str(SAMPLE_DOCX))

        assert result.success is True
        # 验证中文内容正确提取
        assert '中文' in result.content
        assert '测试' in result.content

    def test_parse_nonexistent_file(self, parser):
        """测试不存在的文件"""
        result = parser.parse('nonexistent.docx')

        assert result.success is False
        assert result.error is not None
        assert '不存在' in result.error or '无法访问' in result.error

    def test_parse_invalid_file(self, parser, tmp_path):
        """测试无效文件"""
        # 创建一个无效的 docx 文件
        invalid_file = tmp_path / 'invalid.docx'
        invalid_file.write_text('This is not a valid docx file')

        result = parser.parse(str(invalid_file))

        assert result.success is False
        assert result.error is not None

    def test_extract_metadata(self, parser):
        """测试元数据提取"""
        if not SAMPLE_DOCX.exists():
            pytest.skip(f"测试文件不存在: {SAMPLE_DOCX}")

        result = parser.parse(str(SAMPLE_DOCX))

        # 验证必要的元数据字段
        required_fields = [
            'file_type', 'author', 'title', 'subject',
            'keywords', 'created', 'modified', 'paragraphs',
            'tables', 'sections', 'file_size'
        ]

        for field in required_fields:
            assert field in result.metadata, f"缺少元数据字段: {field}"

    def test_extract_table(self, parser):
        """测试表格提取"""
        if not SAMPLE_DOCX.exists():
            pytest.skip(f"测试文件不存在: {SAMPLE_DOCX}")

        result = parser.parse(str(SAMPLE_DOCX))

        # 验证表格内容被提取
        assert '姓名' in result.content
        assert '年龄' in result.content
        assert '职位' in result.content
        assert '张三' in result.content
        assert '李四' in result.content
        assert '王五' in result.content

    def test_extract_headers_footers(self, parser):
        """测试页眉页脚提取"""
        if not SAMPLE_DOCX.exists():
            pytest.skip(f"测试文件不存在: {SAMPLE_DOCX}")

        result = parser.parse(str(SAMPLE_DOCX))

        # 验证页眉页脚被提取
        assert '页眉' in result.content or '测试文档页眉' in result.content
        assert '页脚' in result.content or '第 1 页' in result.content


class TestXlsxParser:
    """测试 Excel 文档解析器"""

    @pytest.fixture
    def parser(self):
        """创建解析器实例"""
        return XlsxParser()

    def test_supports(self, parser):
        """测试文件类型支持"""
        assert parser.supports('test.xlsx') is True
        assert parser.supports('test.XLSX') is True
        assert parser.supports('test.xls') is True
        assert parser.supports('test.XLS') is True
        assert parser.supports('test.pdf') is False
        assert parser.supports('test.txt') is False

    def test_parse_sample_xlsx(self, parser):
        """测试解析真实 Excel 文档"""
        if not SAMPLE_XLSX.exists():
            pytest.skip(f"测试文件不存在: {SAMPLE_XLSX}")

        result = parser.parse(str(SAMPLE_XLSX))

        # 验证解析成功
        assert isinstance(result, ParseResult)
        assert result.success is True
        assert result.error is None
        assert result.parse_time > 0

        # 验证内容提取
        assert len(result.content) > 0
        assert '员工信息' in result.content
        assert '销售数据' in result.content
        assert '张三' in result.content
        assert 'Python工程师' in result.content

        # 验证元数据
        assert 'file_type' in result.metadata
        assert result.metadata['file_type'] == 'xlsx'
        assert 'sheets' in result.metadata
        assert result.metadata['sheets'] >= 3
        assert 'sheet_names' in result.metadata
        assert '员工信息' in result.metadata['sheet_names']
        assert '销售数据' in result.metadata['sheet_names']

    def test_parse_multiple_sheets(self, parser):
        """测试多工作表解析"""
        if not SAMPLE_XLSX.exists():
            pytest.skip(f"测试文件不存在: {SAMPLE_XLSX}")

        result = parser.parse(str(SAMPLE_XLSX))

        assert result.success is True
        # 验证多个工作表都被提取
        assert '工作表: 员工信息' in result.content
        assert '工作表: 销售数据' in result.content
        assert '工作表: 特殊字符测试' in result.content

    def test_parse_chinese_content(self, parser):
        """测试中文内容解析"""
        if not SAMPLE_XLSX.exists():
            pytest.skip(f"测试文件不存在: {SAMPLE_XLSX}")

        result = parser.parse(str(SAMPLE_XLSX))

        assert result.success is True
        # 验证中文内容正确提取
        assert '技术部' in result.content
        assert '设计部' in result.content
        assert '产品部' in result.content

    def test_parse_numeric_data(self, parser):
        """测试数值数据解析"""
        if not SAMPLE_XLSX.exists():
            pytest.skip(f"测试文件不存在: {SAMPLE_XLSX}")

        result = parser.parse(str(SAMPLE_XLSX))

        assert result.success is True
        # 验证数值被转换为字符串
        assert '15000' in result.content or '12000' in result.content

    def test_parse_nonexistent_file(self, parser):
        """测试不存在的文件"""
        result = parser.parse('nonexistent.xlsx')

        assert result.success is False
        assert result.error is not None
        assert '不存在' in result.error or '无法访问' in result.error

    def test_parse_invalid_file(self, parser, tmp_path):
        """测试无效文件"""
        invalid_file = tmp_path / 'invalid.xlsx'
        invalid_file.write_text('This is not a valid xlsx file')

        result = parser.parse(str(invalid_file))

        assert result.success is False
        assert result.error is not None

    def test_extract_metadata(self, parser):
        """测试元数据提取"""
        if not SAMPLE_XLSX.exists():
            pytest.skip(f"测试文件不存在: {SAMPLE_XLSX}")

        result = parser.parse(str(SAMPLE_XLSX))

        # 验证必要的元数据字段
        required_fields = [
            'file_type', 'sheets', 'sheet_names', 'total_cells',
            'title', 'author', 'created', 'modified', 'file_size'
        ]

        for field in required_fields:
            assert field in result.metadata, f"缺少元数据字段: {field}"

    def test_extract_special_characters(self, parser):
        """测试特殊字符提取"""
        if not SAMPLE_XLSX.exists():
            pytest.skip(f"测试文件不存在: {SAMPLE_XLSX}")

        result = parser.parse(str(SAMPLE_XLSX))

        assert result.success is True
        # 验证特殊字符工作表被提取
        assert '特殊字符测试' in result.content


class TestPptxParser:
    """测试 PowerPoint 文档解析器"""

    @pytest.fixture
    def parser(self):
        """创建解析器实例"""
        return PptxParser()

    def test_supports(self, parser):
        """测试文件类型支持"""
        assert parser.supports('test.pptx') is True
        assert parser.supports('test.PPTX') is True
        assert parser.supports('test.ppt') is True
        assert parser.supports('test.PPT') is True
        assert parser.supports('test.pdf') is False
        assert parser.supports('test.txt') is False

    def test_parse_sample_pptx(self, parser):
        """测试解析真实 PowerPoint 文档"""
        if not SAMPLE_PPTX.exists():
            pytest.skip(f"测试文件不存在: {SAMPLE_PPTX}")

        result = parser.parse(str(SAMPLE_PPTX))

        # 验证解析成功
        assert isinstance(result, ParseResult)
        assert result.success is True
        assert result.error is None
        assert result.parse_time > 0

        # 验证内容提取
        assert len(result.content) > 0
        assert 'Windows 搜索工具' in result.content
        assert '功能特性' in result.content
        assert '技术架构' in result.content

        # 验证元数据
        assert 'file_type' in result.metadata
        assert result.metadata['file_type'] == 'pptx'
        assert 'slides' in result.metadata
        assert result.metadata['slides'] >= 5

    def test_parse_slide_order(self, parser):
        """测试幻灯片顺序"""
        if not SAMPLE_PPTX.exists():
            pytest.skip(f"测试文件不存在: {SAMPLE_PPTX}")

        result = parser.parse(str(SAMPLE_PPTX))

        assert result.success is True
        # 验证幻灯片按顺序提取
        assert '幻灯片 1' in result.content
        assert '幻灯片 2' in result.content
        assert '幻灯片 3' in result.content

    def test_parse_slide_titles(self, parser):
        """测试幻灯片标题提取"""
        if not SAMPLE_PPTX.exists():
            pytest.skip(f"测试文件不存在: {SAMPLE_PPTX}")

        result = parser.parse(str(SAMPLE_PPTX))

        assert result.success is True
        # 验证标题被提取
        assert 'Windows 搜索工具' in result.content
        assert '功能特性' in result.content
        assert '技术架构' in result.content
        assert '总结' in result.content

    def test_parse_slide_content(self, parser):
        """测试幻灯片内容提取"""
        if not SAMPLE_PPTX.exists():
            pytest.skip(f"测试文件不存在: {SAMPLE_PPTX}")

        result = parser.parse(str(SAMPLE_PPTX))

        assert result.success is True
        # 验证正文内容被提取
        assert '主要功能' in result.content or '支持多种文档格式' in result.content
        assert '核心组件' in result.content or 'python-docx' in result.content

    def test_parse_slide_notes(self, parser):
        """测试幻灯片备注提取"""
        if not SAMPLE_PPTX.exists():
            pytest.skip(f"测试文件不存在: {SAMPLE_PPTX}")

        result = parser.parse(str(SAMPLE_PPTX))

        assert result.success is True
        # 验证备注被提取
        assert '备注:' in result.content

    def test_parse_chinese_content(self, parser):
        """测试中文内容解析"""
        if not SAMPLE_PPTX.exists():
            pytest.skip(f"测试文件不存在: {SAMPLE_PPTX}")

        result = parser.parse(str(SAMPLE_PPTX))

        assert result.success is True
        # 验证中文内容正确提取
        assert '文档解析引擎' in result.content
        assert '智能内容提取' in result.content
        assert '中文分词与索引' in result.content

    def test_parse_nonexistent_file(self, parser):
        """测试不存在的文件"""
        result = parser.parse('nonexistent.pptx')

        assert result.success is False
        assert result.error is not None
        assert '不存在' in result.error or '无法访问' in result.error

    def test_parse_invalid_file(self, parser, tmp_path):
        """测试无效文件"""
        invalid_file = tmp_path / 'invalid.pptx'
        invalid_file.write_text('This is not a valid pptx file')

        result = parser.parse(str(invalid_file))

        assert result.success is False
        assert result.error is not None

    def test_extract_metadata(self, parser):
        """测试元数据提取"""
        if not SAMPLE_PPTX.exists():
            pytest.skip(f"测试文件不存在: {SAMPLE_PPTX}")

        result = parser.parse(str(SAMPLE_PPTX))

        # 验证必要的元数据字段
        required_fields = [
            'file_type', 'slides', 'title', 'author',
            'created', 'modified', 'file_size'
        ]

        for field in required_fields:
            assert field in result.metadata, f"缺少元数据字段: {field}"

    def test_extract_special_characters(self, parser):
        """测试特殊字符提取"""
        if not SAMPLE_PPTX.exists():
            pytest.skip(f"测试文件不存在: {SAMPLE_PPTX}")

        result = parser.parse(str(SAMPLE_PPTX))

        assert result.success is True
        # 验证特殊字符幻灯片被提取
        assert '特殊字符测试' in result.content


# 集成测试
class TestOfficeParserIntegration:
    """Office 解析器集成测试"""

    def test_all_parsers_with_valid_files(self):
        """测试所有解析器处理有效文件"""
        parsers = {
            'docx': (DocxParser(), SAMPLE_DOCX),
            'xlsx': (XlsxParser(), SAMPLE_XLSX),
            'pptx': (PptxParser(), SAMPLE_PPTX),
        }

        for file_type, (parser, file_path) in parsers.items():
            if not file_path.exists():
                pytest.skip(f"测试文件不存在: {file_path}")

            result = parser.parse(str(file_path))

            assert result.success is True, f"{file_type} 解析失败: {result.error}"
            assert len(result.content) > 0, f"{file_type} 内容为空"
            assert result.parse_time > 0, f"{file_type} 解析时间异常"
            assert result.metadata['file_type'] == file_type, f"{file_type} 文件类型错误"

    def test_all_parsers_with_chinese(self):
        """测试所有解析器的中文支持"""
        test_cases = [
            (DocxParser(), SAMPLE_DOCX, ['测试', '中文']),
            (XlsxParser(), SAMPLE_XLSX, ['员工', '部门']),
            (PptxParser(), SAMPLE_PPTX, ['搜索', '文档']),
        ]

        for parser, file_path, keywords in test_cases:
            if not file_path.exists():
                continue

            result = parser.parse(str(file_path))
            assert result.success is True

            for keyword in keywords:
                assert keyword in result.content, f"关键词 '{keyword}' 未找到"

    def test_parse_time_reasonable(self):
        """测试解析时间合理性"""
        parsers = [
            (DocxParser(), SAMPLE_DOCX),
            (XlsxParser(), SAMPLE_XLSX),
            (PptxParser(), SAMPLE_PPTX),
        ]

        for parser, file_path in parsers:
            if not file_path.exists():
                continue

            result = parser.parse(str(file_path))
            assert result.success is True
            # 解析时间应该小于 5 秒
            assert result.parse_time < 5.0, f"解析时间过长: {result.parse_time}s"

    def test_metadata_completeness(self):
        """测试元数据完整性"""
        common_fields = ['file_type', 'author', 'title', 'created', 'modified', 'file_size']

        parsers = [
            (DocxParser(), SAMPLE_DOCX),
            (XlsxParser(), SAMPLE_XLSX),
            (PptxParser(), SAMPLE_PPTX),
        ]

        for parser, file_path in parsers:
            if not file_path.exists():
                continue

            result = parser.parse(str(file_path))
            assert result.success is True

            for field in common_fields:
                assert field in result.metadata, f"缺少元数据字段: {field}"
