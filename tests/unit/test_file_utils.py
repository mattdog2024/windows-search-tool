"""
文件工具类单元测试

测试 src/utils/file_utils.py 中的所有工具函数。
"""

import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from src.utils.file_utils import (
    calculate_file_hash,
    ensure_dir,
    format_datetime,
    format_file_size,
    get_file_created_time,
    get_file_extension,
    get_file_modified_time,
    get_file_size,
    get_relative_path,
    is_file_accessible,
    is_path_under,
    normalize_path,
    safe_filename,
)


class TestNormalizePath:
    """测试 normalize_path 函数"""

    def test_normalize_relative_path(self):
        """测试相对路径规范化"""
        result = normalize_path(".")
        assert result.is_absolute()

    def test_normalize_absolute_path(self):
        """测试绝对路径规范化"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = normalize_path(tmpdir)
            assert result.is_absolute()
            assert str(result) == str(Path(tmpdir).resolve())

    def test_normalize_path_object(self):
        """测试 Path 对象作为输入"""
        path = Path(".")
        result = normalize_path(path)
        assert result.is_absolute()

    def test_normalize_expanduser(self):
        """测试用户目录展开"""
        # 跳过在没有家目录的环境中
        try:
            result = normalize_path("~")
            assert result.is_absolute()
            assert "~" not in str(result)
        except (RuntimeError, OSError):
            pytest.skip("无法展开用户目录")


class TestEnsureDir:
    """测试 ensure_dir 函数"""

    def test_create_new_directory(self):
        """测试创建新目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "test_dir"
            result = ensure_dir(new_dir)

            assert result.exists()
            assert result.is_dir()

    def test_create_nested_directories(self):
        """测试创建嵌套目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = Path(tmpdir) / "level1" / "level2" / "level3"
            result = ensure_dir(new_dir)

            assert result.exists()
            assert result.is_dir()

    def test_existing_directory(self):
        """测试已存在的目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = ensure_dir(tmpdir)
            assert result.exists()
            assert result.is_dir()

    def test_path_is_file_raises_error(self):
        """测试路径是文件时抛出异常"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name

        try:
            with pytest.raises(ValueError, match="路径已存在但不是目录"):
                ensure_dir(tmp_path)
        finally:
            os.unlink(tmp_path)


class TestIsFileAccessible:
    """测试 is_file_accessible 函数"""

    def test_accessible_file(self):
        """测试可访问的文件"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name

        try:
            assert is_file_accessible(tmp_path) is True
        finally:
            os.unlink(tmp_path)

    def test_nonexistent_file(self):
        """测试不存在的文件"""
        assert is_file_accessible("/nonexistent/file.txt") is False

    def test_directory_not_accessible(self):
        """测试目录返回 False"""
        with tempfile.TemporaryDirectory() as tmpdir:
            assert is_file_accessible(tmpdir) is False


class TestGetFileSize:
    """测试 get_file_size 函数"""

    def test_empty_file(self):
        """测试空文件"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name

        try:
            assert get_file_size(tmp_path) == 0
        finally:
            os.unlink(tmp_path)

    def test_file_with_content(self):
        """测试有内容的文件"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp.write("Hello, World!")
            tmp_path = tmp.name

        try:
            size = get_file_size(tmp_path)
            assert size == 13  # "Hello, World!" 的字节数
        finally:
            os.unlink(tmp_path)

    def test_nonexistent_file_raises_error(self):
        """测试不存在的文件抛出异常"""
        with pytest.raises(FileNotFoundError, match="文件不存在"):
            get_file_size("/nonexistent/file.txt")

    def test_directory_raises_error(self):
        """测试目录抛出异常"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(OSError, match="路径不是文件"):
                get_file_size(tmpdir)


class TestGetFileExtension:
    """测试 get_file_extension 函数"""

    def test_common_extensions(self):
        """测试常见扩展名"""
        assert get_file_extension("file.txt") == ".txt"
        assert get_file_extension("document.docx") == ".docx"
        assert get_file_extension("image.PNG") == ".png"

    def test_uppercase_extension(self):
        """测试大写扩展名转小写"""
        assert get_file_extension("FILE.TXT") == ".txt"
        assert get_file_extension("Document.DOCX") == ".docx"

    def test_no_extension(self):
        """测试没有扩展名的文件"""
        assert get_file_extension("README") == ""
        assert get_file_extension("Makefile") == ""

    def test_multiple_dots(self):
        """测试多个点号的文件名"""
        assert get_file_extension("archive.tar.gz") == ".gz"
        assert get_file_extension("config.json.bak") == ".bak"

    def test_hidden_file(self):
        """测试隐藏文件"""
        assert get_file_extension(".gitignore") == ""
        assert get_file_extension(".env.local") == ".local"


class TestCalculateFileHash:
    """测试 calculate_file_hash 函数"""

    def test_sha256_hash(self):
        """测试 SHA256 哈希计算"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp.write("Hello, World!")
            tmp_path = tmp.name

        try:
            hash_value = calculate_file_hash(tmp_path)
            # "Hello, World!" 的 SHA256 哈希值
            expected = "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
            assert hash_value == expected
        finally:
            os.unlink(tmp_path)

    def test_md5_hash(self):
        """测试 MD5 哈希计算"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp.write("Hello, World!")
            tmp_path = tmp.name

        try:
            hash_value = calculate_file_hash(tmp_path, "md5")
            # "Hello, World!" 的 MD5 哈希值
            expected = "65a8e27d8879283831b664bd8b7f0ad4"
            assert hash_value == expected
        finally:
            os.unlink(tmp_path)

    def test_empty_file_hash(self):
        """测试空文件的哈希"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name

        try:
            hash_value = calculate_file_hash(tmp_path)
            # 空文件的 SHA256 哈希值
            expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
            assert hash_value == expected
        finally:
            os.unlink(tmp_path)

    def test_nonexistent_file_raises_error(self):
        """测试不存在的文件抛出异常"""
        with pytest.raises(FileNotFoundError, match="文件不存在"):
            calculate_file_hash("/nonexistent/file.txt")

    def test_invalid_algorithm_raises_error(self):
        """测试无效的哈希算法抛出异常"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name

        try:
            with pytest.raises(ValueError, match="不支持的哈希算法"):
                calculate_file_hash(tmp_path, "invalid_algorithm")
        finally:
            os.unlink(tmp_path)


class TestGetFileModifiedTime:
    """测试 get_file_modified_time 函数"""

    def test_get_modified_time(self):
        """测试获取修改时间"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name

        try:
            mod_time = get_file_modified_time(tmp_path)
            assert isinstance(mod_time, datetime)
            # 修改时间应该在最近
            assert (datetime.now() - mod_time).total_seconds() < 10
        finally:
            os.unlink(tmp_path)

    def test_nonexistent_file_raises_error(self):
        """测试不存在的文件抛出异常"""
        with pytest.raises(FileNotFoundError, match="文件不存在"):
            get_file_modified_time("/nonexistent/file.txt")


class TestGetFileCreatedTime:
    """测试 get_file_created_time 函数"""

    def test_get_created_time(self):
        """测试获取创建时间"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name

        try:
            created_time = get_file_created_time(tmp_path)
            assert isinstance(created_time, datetime)
            # 创建时间应该在最近
            assert (datetime.now() - created_time).total_seconds() < 10
        finally:
            os.unlink(tmp_path)

    def test_nonexistent_file_raises_error(self):
        """测试不存在的文件抛出异常"""
        with pytest.raises(FileNotFoundError, match="文件不存在"):
            get_file_created_time("/nonexistent/file.txt")


class TestFormatDatetime:
    """测试 format_datetime 函数"""

    def test_default_format(self):
        """测试默认格式"""
        dt = datetime(2025, 10, 16, 10, 30, 45)
        result = format_datetime(dt)
        assert result == "2025-10-16 10:30:45"

    def test_custom_format(self):
        """测试自定义格式"""
        dt = datetime(2025, 10, 16, 10, 30, 45)
        result = format_datetime(dt, "%Y/%m/%d")
        assert result == "2025/10/16"

    def test_time_only_format(self):
        """测试仅时间格式"""
        dt = datetime(2025, 10, 16, 10, 30, 45)
        result = format_datetime(dt, "%H:%M:%S")
        assert result == "10:30:45"


class TestFormatFileSize:
    """测试 format_file_size 函数"""

    def test_bytes(self):
        """测试字节格式化"""
        assert format_file_size(0) == "0 B"
        assert format_file_size(100) == "100 B"
        assert format_file_size(1023) == "1023 B"

    def test_kilobytes(self):
        """测试 KB 格式化"""
        assert format_file_size(1024) == "1.00 KB"
        assert format_file_size(1536) == "1.50 KB"
        assert format_file_size(2048) == "2.00 KB"

    def test_megabytes(self):
        """测试 MB 格式化"""
        assert format_file_size(1048576) == "1.00 MB"
        assert format_file_size(1572864) == "1.50 MB"

    def test_gigabytes(self):
        """测试 GB 格式化"""
        assert format_file_size(1073741824) == "1.00 GB"
        assert format_file_size(2147483648) == "2.00 GB"

    def test_terabytes(self):
        """测试 TB 格式化"""
        assert format_file_size(1099511627776) == "1.00 TB"
        assert format_file_size(5497558138880) == "5.00 TB"


class TestGetRelativePath:
    """测试 get_relative_path 函数"""

    def test_relative_path_calculation(self):
        """测试相对路径计算"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            subdir = base / "subdir"
            subdir.mkdir()
            file_path = subdir / "file.txt"
            file_path.touch()

            result = get_relative_path(file_path, base)
            assert result == Path("subdir/file.txt") or result == Path("subdir\\file.txt")

    def test_same_path(self):
        """测试相同路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = get_relative_path(tmpdir, tmpdir)
            assert result == Path(".")

    def test_unrelated_paths_raises_error(self):
        """测试不相关的路径抛出异常"""
        with tempfile.TemporaryDirectory() as tmpdir1:
            with tempfile.TemporaryDirectory() as tmpdir2:
                with pytest.raises(ValueError, match="无法计算相对路径"):
                    get_relative_path(tmpdir2, tmpdir1)


class TestIsPathUnder:
    """测试 is_path_under 函数"""

    def test_path_under_parent(self):
        """测试路径在父路径之下"""
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            subdir = base / "subdir"
            subdir.mkdir()

            assert is_path_under(subdir, base) is True

    def test_same_path(self):
        """测试相同路径"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 相同路径应该返回 True (. 相对于 .)
            assert is_path_under(tmpdir, tmpdir) is True

    def test_path_not_under_parent(self):
        """测试路径不在父路径之下"""
        with tempfile.TemporaryDirectory() as tmpdir1:
            with tempfile.TemporaryDirectory() as tmpdir2:
                assert is_path_under(tmpdir1, tmpdir2) is False


class TestSafeFilename:
    """测试 safe_filename 函数"""

    def test_remove_illegal_characters(self):
        """测试移除非法字符"""
        assert safe_filename("file:name?.txt") == "file_name_.txt"
        assert safe_filename("document/backup.txt") == "document_backup.txt"
        assert safe_filename("file<test>.txt") == "file_test_.txt"

    def test_preserve_legal_characters(self):
        """测试保留合法字符"""
        assert safe_filename("normal_file-123.txt") == "normal_file-123.txt"
        assert safe_filename("file (copy).txt") == "file (copy).txt"

    def test_custom_replacement(self):
        """测试自定义替换字符"""
        assert safe_filename("file:name.txt", "-") == "file-name.txt"

    def test_empty_filename(self):
        """测试空文件名"""
        assert safe_filename("") == "unnamed"
        assert safe_filename("   ") == "unnamed"

    def test_hidden_file(self):
        """测试隐藏文件"""
        assert safe_filename(".gitignore") == "unnamed.gitignore"

    def test_windows_reserved_names(self):
        """测试 Windows 保留名称"""
        assert safe_filename("CON.txt") == "_CON.txt"
        assert safe_filename("aux.log") == "_aux.log"
        assert safe_filename("NUL") == "_NUL"
        assert safe_filename("COM1.dat") == "_COM1.dat"

    def test_strip_whitespace(self):
        """测试移除首尾空格"""
        assert safe_filename("  file.txt  ") == "file.txt"

    def test_control_characters_removed(self):
        """测试移除控制字符"""
        # ASCII 控制字符应该被移除
        filename_with_control = "file\x00\x01\x02name.txt"
        result = safe_filename(filename_with_control)
        assert "\x00" not in result
        assert "\x01" not in result
        assert "\x02" not in result
