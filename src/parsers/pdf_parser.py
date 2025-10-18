"""
PDF 文档解析器

使用 pdfplumber 提取 PDF 文档内容,支持 OCR 识别扫描版 PDF
"""

import logging
from typing import Dict, Any
import pdfplumber
from .base import BaseParser, ParseResult

logger = logging.getLogger(__name__)

# OCR 相关导入
try:
    import pytesseract
    from PIL import Image
    import os
    import io

    # 配置 Tesseract 路径 (支持便携版)
    if os.name == 'nt':  # Windows 系统
        # 便携版路径优先 (相对于程序根目录)
        import sys
        if getattr(sys, 'frozen', False):
            # 打包后的可执行文件
            app_dir = os.path.dirname(sys.executable)
        else:
            # 开发模式
            app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        tesseract_paths = [
            # 1. 便携版路径 (portable/tesseract/tesseract.exe)
            os.path.join(app_dir, 'portable', 'tesseract', 'tesseract.exe'),
            # 2. 系统安装路径
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        ]
        for path in tesseract_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                logger.info(f"使用 Tesseract: {path}")
                break

    OCR_AVAILABLE = True
except ImportError as e:
    OCR_AVAILABLE = False
    logger.warning(f"OCR 功能不可用: {e}. 安装 pytesseract 以启用 OCR 支持.")


class PdfParser(BaseParser):
    """
    PDF 文档解析器 (支持 OCR)

    使用 pdfplumber 提取文本型 PDF 的内容和元数据。
    对于扫描版 PDF,使用 Tesseract OCR 进行文字识别。

    Attributes:
        supported_extensions: 支持的文件扩展名列表
        enable_ocr: 是否启用 OCR 功能
    """

    def __init__(self, enable_ocr: bool = True):
        """
        初始化 PDF 解析器

        Args:
            enable_ocr: 是否启用 OCR 功能 (默认 True)
        """
        super().__init__(supported_extensions=['.pdf'])
        self.enable_ocr = enable_ocr and OCR_AVAILABLE

        if enable_ocr and not OCR_AVAILABLE:
            logger.warning("OCR 功能已禁用: 缺少必要的库 (pytesseract, pdf2image)")

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

                # 如果是扫描版且启用了 OCR,进行 OCR 识别
                if is_scanned and self.enable_ocr:
                    logger.info(
                        f"{file_path} 是扫描版 PDF "
                        f"(平均每页 {avg_chars_per_page:.1f} 个字符),开始 OCR 识别..."
                    )
                    ocr_content = self._perform_ocr(file_path)
                    if ocr_content:
                        content = ocr_content
                        metadata['ocr_processed'] = True
                        logger.info(f"OCR 识别完成,提取了 {len(content)} 个字符")
                    else:
                        logger.warning(f"OCR 识别失败或未提取到内容")
                        metadata['ocr_processed'] = False
                elif is_scanned and not self.enable_ocr:
                    logger.warning(
                        f"{file_path} 是扫描版 PDF,但 OCR 功能未启用"
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

    def _perform_ocr(self, file_path: str) -> str:
        """
        对 PDF 文件执行 OCR 识别

        Args:
            file_path: PDF 文件路径

        Returns:
            识别出的文本内容

        说明:
            使用 pdfplumber 提取 PDF 页面中的图像,
            然后使用 Tesseract OCR 识别图像中的文字。
            支持中英文混合识别。
        """
        if not OCR_AVAILABLE:
            logger.warning("OCR 功能不可用")
            return ""

        try:
            # 打开 PDF 文档
            logger.info(f"正在打开 PDF 进行 OCR... {file_path}")

            with pdfplumber.open(file_path) as pdf:
                total_pages = len(pdf.pages)
                text_parts = []

                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        logger.info(f"OCR 识别第 {page_num}/{total_pages} 页...")

                        # 将页面转换为图像
                        # resolution=300 提供较好的识别质量
                        img = page.to_image(resolution=300)

                        # 获取 PIL Image
                        pil_image = img.original

                        # 图像预处理 - 转换为灰度图并提高对比度
                        pil_image = pil_image.convert('L')  # 转为灰度图

                        # 使用 Tesseract 进行 OCR
                        # lang='chi_sim' 只使用中文模型(避免英文干扰)
                        # --psm 1: 自动页面分割与OSD
                        # --oem 1: 使用LSTM神经网络引擎
                        text = pytesseract.image_to_string(
                            pil_image,
                            lang='chi_sim',
                            config='--psm 1 --oem 1'
                        )

                        if text.strip():
                            text_parts.append(text)
                            logger.debug(f"第 {page_num} 页识别了 {len(text)} 个字符")

                    except Exception as e:
                        logger.warning(f"OCR 识别第 {page_num} 页失败: {e}")
                        continue

                # 合并所有页面的文本
                content = '\n\n'.join(text_parts)

                # 清理 OCR 结果中的多余空格
                # Tesseract 经常在中文字符之间插入空格,需要去除
                content = self._clean_ocr_text(content)

                logger.info(f"OCR 完成,总共识别了 {len(content)} 个字符")
                return content

        except Exception as e:
            logger.error(f"OCR 处理失败: {e}")
            return ""

    def _clean_ocr_text(self, text: str) -> str:
        """
        清理 OCR 识别结果中的多余空格

        Args:
            text: OCR 识别的原始文本

        Returns:
            清理后的文本

        说明:
            Tesseract OCR 在识别中文时,经常会在每个字符之间插入空格。
            例如: "侦 查 科 长" -> "侦查科长"
            此方法会:
            1. 移除中文字符之间的单个空格
            2. 保留英文单词之间的空格
            3. 保留换行符和标点符号
        """
        import re

        # 移除中文字符之间的单个空格
        # 匹配: 中文字符 + 一个或多个空格 + 中文字符
        # 替换为: 两个中文字符直接相连
        text = re.sub(r'([\u4e00-\u9fff])\s+([\u4e00-\u9fff])', r'\1\2', text)

        # 可能需要多次替换,因为 re.sub 不会重叠匹配
        # 例如: "A B C" 第一次只会替换 "A B", 需要再次替换 "B C"
        for _ in range(3):  # 最多重复 3 次以处理连续的空格
            text = re.sub(r'([\u4e00-\u9fff])\s+([\u4e00-\u9fff])', r'\1\2', text)

        # 移除行首行尾的空格
        lines = text.split('\n')
        lines = [line.strip() for line in lines]
        text = '\n'.join(lines)

        # 移除多余的空行(保留最多一个空行)
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text

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
