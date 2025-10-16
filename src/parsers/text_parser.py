"""
文本文件解析器

支持纯文本文件的解析
"""

import os
from typing import Dict, Any
from .base import BaseParser, ParseResult


class TextParser(BaseParser):
    """
    纯文本文件解析器

    支持 .txt, .md, .csv 等文本格式
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
        """
        try:
            # 尝试多种编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']
            content = None
            used_encoding = None

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    used_encoding = encoding
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue

            if content is None:
                return ParseResult(
                    success=False,
                    content='',
                    error='无法使用任何已知编码解码文件'
                )

            # 获取文件信息
            file_stat = os.stat(file_path)
            metadata = {
                'encoding': used_encoding,
                'size': file_stat.st_size,
                'lines': len(content.splitlines()),
                'characters': len(content)
            }

            return ParseResult(
                success=True,
                content=content,
                metadata=metadata
            )

        except Exception as e:
            return ParseResult(
                success=False,
                content='',
                error=f'读取文件失败: {str(e)}'
            )

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
