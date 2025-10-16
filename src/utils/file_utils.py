"""
文件工具类

提供文件系统操作的实用工具函数,包括:
- 路径处理和验证
- 文件检查和信息获取
- SHA256 哈希计算
- 时间格式化工具
"""

import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Union


def normalize_path(path: Union[str, Path]) -> Path:
    """
    规范化文件路径

    将路径转换为绝对路径并解析所有符号链接。

    Args:
        path: 输入路径(字符串或Path对象)

    Returns:
        Path: 规范化后的绝对路径

    Examples:
        >>> normalize_path("./data/file.txt")
        WindowsPath('C:/Users/xxx/project/data/file.txt')

        >>> normalize_path("~/documents")
        WindowsPath('C:/Users/xxx/documents')
    """
    path_obj = Path(path).expanduser()
    return path_obj.resolve()


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    确保目录存在,如果不存在则创建

    Args:
        path: 目录路径

    Returns:
        Path: 规范化的目录路径

    Raises:
        ValueError: 如果路径存在但不是目录

    Examples:
        >>> ensure_dir("./output/logs")
        WindowsPath('C:/Users/xxx/project/output/logs')
    """
    dir_path = normalize_path(path)

    if dir_path.exists() and not dir_path.is_dir():
        raise ValueError(f"路径已存在但不是目录: {dir_path}")

    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def is_file_accessible(path: Union[str, Path]) -> bool:
    """
    检查文件是否存在且可访问

    Args:
        path: 文件路径

    Returns:
        bool: 如果文件存在且可读返回 True,否则返回 False

    Examples:
        >>> is_file_accessible("data.txt")
        True

        >>> is_file_accessible("not_exist.txt")
        False
    """
    try:
        path_obj = Path(path)
        return path_obj.exists() and path_obj.is_file() and os.access(path_obj, os.R_OK)
    except (OSError, ValueError):
        return False


def get_file_size(path: Union[str, Path]) -> int:
    """
    获取文件大小(字节)

    Args:
        path: 文件路径

    Returns:
        int: 文件大小(字节)

    Raises:
        FileNotFoundError: 如果文件不存在
        OSError: 如果无法访问文件

    Examples:
        >>> get_file_size("data.txt")
        1024
    """
    path_obj = Path(path)

    if not path_obj.exists():
        raise FileNotFoundError(f"文件不存在: {path_obj}")

    if not path_obj.is_file():
        raise OSError(f"路径不是文件: {path_obj}")

    return path_obj.stat().st_size


def get_file_extension(path: Union[str, Path]) -> str:
    """
    获取文件扩展名(小写,包含点号)

    Args:
        path: 文件路径

    Returns:
        str: 文件扩展名(小写),如 ".txt", ".docx"

    Examples:
        >>> get_file_extension("document.DOCX")
        '.docx'

        >>> get_file_extension("README")
        ''
    """
    return Path(path).suffix.lower()


def calculate_file_hash(path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    计算文件的哈希值

    使用指定的哈希算法计算文件内容的哈希值。
    支持大文件(分块读取)。

    Args:
        path: 文件路径
        algorithm: 哈希算法名称,默认为 "sha256"
                  支持: md5, sha1, sha256, sha512 等

    Returns:
        str: 十六进制格式的哈希值

    Raises:
        FileNotFoundError: 如果文件不存在
        ValueError: 如果哈希算法不支持

    Examples:
        >>> calculate_file_hash("data.txt")
        'a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e'

        >>> calculate_file_hash("data.txt", "md5")
        '5d41402abc4b2a76b9719d911017c592'
    """
    path_obj = Path(path)

    if not path_obj.exists():
        raise FileNotFoundError(f"文件不存在: {path_obj}")

    if not path_obj.is_file():
        raise OSError(f"路径不是文件: {path_obj}")

    try:
        hasher = hashlib.new(algorithm)
    except ValueError as e:
        raise ValueError(f"不支持的哈希算法: {algorithm}") from e

    # 分块读取文件(8KB chunks)
    chunk_size = 8192
    with open(path_obj, 'rb') as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)

    return hasher.hexdigest()


def get_file_modified_time(path: Union[str, Path]) -> datetime:
    """
    获取文件的最后修改时间

    Args:
        path: 文件路径

    Returns:
        datetime: 文件的最后修改时间

    Raises:
        FileNotFoundError: 如果文件不存在

    Examples:
        >>> get_file_modified_time("data.txt")
        datetime.datetime(2025, 10, 16, 10, 30, 45)
    """
    path_obj = Path(path)

    if not path_obj.exists():
        raise FileNotFoundError(f"文件不存在: {path_obj}")

    timestamp = path_obj.stat().st_mtime
    return datetime.fromtimestamp(timestamp)


def get_file_created_time(path: Union[str, Path]) -> datetime:
    """
    获取文件的创建时间

    注意: 在 Unix 系统上,这可能返回最后状态变更时间。

    Args:
        path: 文件路径

    Returns:
        datetime: 文件的创建时间

    Raises:
        FileNotFoundError: 如果文件不存在

    Examples:
        >>> get_file_created_time("data.txt")
        datetime.datetime(2025, 10, 15, 9, 20, 30)
    """
    path_obj = Path(path)

    if not path_obj.exists():
        raise FileNotFoundError(f"文件不存在: {path_obj}")

    timestamp = path_obj.stat().st_ctime
    return datetime.fromtimestamp(timestamp)


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    格式化日期时间为字符串

    Args:
        dt: datetime 对象
        format_str: 格式化字符串,默认为 "%Y-%m-%d %H:%M:%S"

    Returns:
        str: 格式化后的日期时间字符串

    Examples:
        >>> dt = datetime(2025, 10, 16, 10, 30, 45)
        >>> format_datetime(dt)
        '2025-10-16 10:30:45'

        >>> format_datetime(dt, "%Y/%m/%d")
        '2025/10/16'
    """
    return dt.strftime(format_str)


def format_file_size(size_bytes: int) -> str:
    """
    将文件大小(字节)格式化为人类可读的字符串

    Args:
        size_bytes: 文件大小(字节)

    Returns:
        str: 格式化后的大小字符串,如 "1.5 KB", "2.3 MB"

    Examples:
        >>> format_file_size(1024)
        '1.00 KB'

        >>> format_file_size(1536)
        '1.50 KB'

        >>> format_file_size(1048576)
        '1.00 MB'

        >>> format_file_size(500)
        '500 B'
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0 or unit == 'TB':
            break
        size_bytes /= 1024.0

    if unit == 'B':
        return f"{int(size_bytes)} {unit}"
    return f"{size_bytes:.2f} {unit}"


def get_relative_path(path: Union[str, Path], base: Union[str, Path]) -> Path:
    """
    获取相对于基准路径的相对路径

    Args:
        path: 目标路径
        base: 基准路径

    Returns:
        Path: 相对路径

    Raises:
        ValueError: 如果无法计算相对路径

    Examples:
        >>> get_relative_path("/home/user/docs/file.txt", "/home/user")
        PosixPath('docs/file.txt')
    """
    try:
        path_obj = normalize_path(path)
        base_obj = normalize_path(base)
        return path_obj.relative_to(base_obj)
    except ValueError as e:
        raise ValueError(f"无法计算相对路径: {path} 相对于 {base}") from e


def is_path_under(path: Union[str, Path], parent: Union[str, Path]) -> bool:
    """
    检查路径是否在父路径之下

    Args:
        path: 要检查的路径
        parent: 父路径

    Returns:
        bool: 如果 path 在 parent 之下返回 True,否则返回 False

    Examples:
        >>> is_path_under("/home/user/docs/file.txt", "/home/user")
        True

        >>> is_path_under("/etc/config", "/home/user")
        False
    """
    try:
        path_obj = normalize_path(path)
        parent_obj = normalize_path(parent)
        path_obj.relative_to(parent_obj)
        return True
    except ValueError:
        return False


def safe_filename(filename: str, replacement: str = "_") -> str:
    """
    将文件名转换为安全的文件名

    移除或替换 Windows 和 Unix 系统中的非法字符。

    Args:
        filename: 原始文件名
        replacement: 用于替换非法字符的字符,默认为 "_"

    Returns:
        str: 安全的文件名

    Examples:
        >>> safe_filename("file:name?.txt")
        'file_name_.txt'

        >>> safe_filename("document/backup.txt")
        'document_backup.txt'
    """
    # Windows 和 Unix 非法字符
    illegal_chars = '<>:"/\\|?*'

    # 替换非法字符
    safe_name = filename
    for char in illegal_chars:
        safe_name = safe_name.replace(char, replacement)

    # 移除控制字符 (ASCII 0-31)
    safe_name = ''.join(char for char in safe_name if ord(char) >= 32)

    # 移除首尾空格
    safe_name = safe_name.strip()

    # 如果文件名为空或只有扩展名,使用默认名称
    if not safe_name or safe_name.startswith('.'):
        safe_name = f"unnamed{safe_name}"

    # Windows 保留名称
    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }

    name_without_ext = os.path.splitext(safe_name)[0].upper()
    if name_without_ext in reserved_names:
        safe_name = f"_{safe_name}"

    return safe_name
