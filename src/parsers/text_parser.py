"""
文本文件解析器

支持纯文本文件的解析，使用 chardet 自动检测文件编码
"""

import os
import logging
from typing import Dict, Any
import chardet
from .base import BaseParser, ParseResult

logger = logging.getLogger(__name__)


class TextParser(BaseParser):
    """
    文本文件解析器

    支持 .txt, .md, .csv 等文本格式，自动检测文件编码。

    特性：
    - 使用 chardet 自动检测文件编码（支持 UTF-8、GBK、GB2312 等）
    - 正确处理 BOM 标记
    - 支持 CSV、Markdown 等文本格式
    - 处理中文和特殊字符

    Attributes:
        supported_extensions: 支持的文件扩展名列表
    """

    def __init__(self):
        """初始化文本解析器"""
        super().__init__(supported_extensions=['.txt', '.md', '.csv', '.log', '.json', '.xml'])

    def _parse_impl(self, file_path: str) -> ParseResult:
        """
        解析文本文件

        Args:
            file_path: 文件路径

        Returns:
            解析结果

        解析过程：
        1. 读取文件原始字节
        2. 使用 chardet 检测编码
        3. 使用检测到的编码解码文件
        4. 提取文件元数据
        """
        try:
            # 读取文件原始字节用于编码检测
            with open(file_path, 'rb') as f:
                raw_data = f.read()

            # 检测编码
            detection_result = chardet.detect(raw_data)
            encoding = detection_result.get('encoding')
            confidence = detection_result.get('confidence', 0.0)

            # 如果检测失败或置信度太低，尝试常见编码
            if not encoding or confidence < 0.7:
                logger.warning(
                    f"{file_path}: chardet 检测编码置信度较低 "
                    f"({encoding}, {confidence:.2f})，尝试常见编码"
                )
                encoding = self._try_common_encodings(raw_data)

            if not encoding:
                return ParseResult(
                    success=False,
                    content='',
                    error='无法检测文件编码'
                )

            # 使用检测到的编码读取文件
            try:
                content = raw_data.decode(encoding)
            except (UnicodeDecodeError, UnicodeError) as e:
                logger.error(f"{file_path}: 使用编码 {encoding} 解码失败: {e}")
                # 尝试使用 errors='ignore' 读取
                content = raw_data.decode(encoding, errors='ignore')
                logger.warning(f"{file_path}: 使用 errors='ignore' 模式读取，可能丢失部分内容")

            # 移除 BOM 标记（如果存在）
            content = self._remove_bom(content)

            # 获取文件信息
            file_stat = os.stat(file_path)
            metadata = {
                'encoding': encoding,
                'encoding_confidence': confidence,
                'size': file_stat.st_size,
                'lines': len(content.splitlines()),
                'characters': len(content),
                'has_bom': raw_data.startswith((
                    b'\xef\xbb\xbf',  # UTF-8 BOM
                    b'\xff\xfe',       # UTF-16 LE BOM
                    b'\xfe\xff'        # UTF-16 BE BOM
                ))
            }

            return ParseResult(
                success=True,
                content=content,
                metadata=metadata
            )

        except Exception as e:
            error_msg = f'读取文件失败: {str(e)}'
            logger.error(f"{file_path}: {error_msg}")
            return ParseResult(
                success=False,
                content='',
                error=error_msg
            )

    def _try_common_encodings(self, raw_data: bytes) -> str:
        """
        尝试常见编码

        Args:
            raw_data: 文件原始字节

        Returns:
            成功的编码名称，如果都失败则返回 None
        """
        common_encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'utf-16', 'latin-1']

        for encoding in common_encodings:
            try:
                raw_data.decode(encoding)
                logger.info(f"成功使用编码: {encoding}")
                return encoding
            except (UnicodeDecodeError, UnicodeError):
                continue

        return None

    def _remove_bom(self, content: str) -> str:
        """
        移除 BOM 标记

        Args:
            content: 文本内容

        Returns:
            移除 BOM 后的内容
        """
        # UTF-8 BOM
        if content.startswith('\ufeff'):
            return content[1:]
        return content

    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        获取文本文件元数据

        Args:
            file_path: 文件路径

        Returns:
            元数据字典
        """
        try:
            file_stat = os.stat(file_path)
            return {
                'size': file_stat.st_size,
                'modified': file_stat.st_mtime,
                'created': file_stat.st_ctime
            }
        except Exception:
            return {}
