"""
PDF 文档解析器

使用 pdfplumber 提取 PDF 文档内容
"""

import logging
from typing import Dict, Any
import pdfplumber
from .base import BaseParser, ParseResult

logger = logging.getLogger(__name__)


class PdfParser(BaseParser):
    """
    PDF 文档解析器（基础版，不包含 OCR）

    使用 pdfplumber 提取文本型 PDF 的内容和元数据。
    对于扫描版 PDF，会检测并标记，但不进行 OCR 处理（OCR 功能在 Task 8 实现）。

    Attributes:
        supported_extensions: 支持的文件扩展名列表
    """

    def __init__(self):
        """初始化 PDF 解析器"""
        super().__init__(supported_extensions=['.pdf'])

    def _parse_impl(self, file_path: str) -> ParseResult:
        """
        解析 PDF 文档

        Args:
            file_path: PDF 文件路径

        Returns:
            ParseResult: 解析结果，包含文本内容和元数据

        解析过程：
        1. 使用 pdfplumber 打开 PDF
        2. 逐页提取文本内容
        3. 提取文档元数据（页数、作者、标题等）
        4. 检测是否为扫描版 PDF
        """
        try:
            with pdfplumber.open(file_path) as pdf:
                # 提取所有页面的文本
                text_parts = []
                total_chars = 0

                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        text = page.extract_text()
                        if text:
                            text_parts.append(text)
                            total_chars += len(text.strip())
                    except Exception as e:
                        logger.warning(f"无法提取第 {page_num} 页内容: {e}")
                        continue

                # 合并所有文本
                content = '\n'.join(text_parts)

                # 检测是否为扫描版 PDF
                # 如果平均每页字符数少于 50，可能是扫描版
                avg_chars_per_page = total_chars / len(pdf.pages) if pdf.pages else 0
                is_scanned = avg_chars_per_page < 50

                # 提取元数据
                metadata = self._extract_metadata(pdf, is_scanned)

                if is_scanned:
                    logger.warning(
                        f"{file_path} 可能是扫描版 PDF "
                        f"(平均每页 {avg_chars_per_page:.1f} 个字符)，需要 OCR 处理"
                    )

                return ParseResult(
                    success=True,
                    content=content,
                    metadata=metadata
                )

        except Exception as e:
            error_msg = f'解析 PDF 失败: {str(e)}'
            logger.error(f"{file_path}: {error_msg}")
            return ParseResult(
                success=False,
                content='',
                error=error_msg
            )

    def _extract_metadata(
        self,
        pdf: pdfplumber.PDF,
        is_scanned: bool
    ) -> Dict[str, Any]:
        """
        提取 PDF 元数据

        Args:
            pdf: pdfplumber PDF 对象
            is_scanned: 是否为扫描版

        Returns:
            元数据字典
        """
        metadata = {
            'pages': len(pdf.pages),
            'is_scanned': is_scanned,
        }

        # 尝试提取 PDF 内置元数据
        if pdf.metadata:
            # 清理和提取常用元数据字段
            for key in ['Author', 'Title', 'Subject', 'Creator', 'Producer']:
                value = pdf.metadata.get(key, '')
                if value:
                    metadata[key.lower()] = str(value)

            # 提取创建和修改日期
            for date_key in ['CreationDate', 'ModDate']:
                date_value = pdf.metadata.get(date_key, '')
                if date_value:
                    # PDF 日期格式通常为 D:YYYYMMDDHHmmSS
                    metadata[date_key.lower()] = str(date_value)

        return metadata

    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        仅获取 PDF 文档元数据（不解析全文）

        Args:
            file_path: PDF 文件路径

        Returns:
            元数据字典
        """
        try:
            with pdfplumber.open(file_path) as pdf:
                # 快速检查是否为扫描版
                is_scanned = False
                if pdf.pages:
                    first_page_text = pdf.pages[0].extract_text() or ''
                    is_scanned = len(first_page_text.strip()) < 50

                return self._extract_metadata(pdf, is_scanned)
        except Exception as e:
            logger.error(f"获取 PDF 元数据失败 {file_path}: {e}")
            return {}
