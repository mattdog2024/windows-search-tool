"""
IndexManager 文件扫描功能单元测试
"""

import os
import tempfile
import unittest
from pathlib import Path

from src.core.index_manager import IndexManager, IndexStats


class TestIndexManagerScan(unittest.TestCase):
    """IndexManager 扫描功能测试"""

    def setUp(self):
        """测试前准备"""
        # 创建临时数据库
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()

        # 创建临时测试目录
        self.test_dir = tempfile.mkdtemp()

        # 初始化 IndexManager
        self.manager = IndexManager(db_path=self.temp_db.name)

    def tearDown(self):
        """测试后清理"""
        # 关闭数据库连接
        if hasattr(self.manager, 'db') and self.manager.db:
            self.manager.db.close()

        # 删除临时数据库
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

        # 清理测试目录
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _create_test_file(self, relative_path: str, content: str = "test content") -> str:
        """
        创建测试文件

        Args:
            relative_path: 相对于测试目录的路径
            content: 文件内容

        Returns:
            文件的完整路径
        """
        file_path = os.path.join(self.test_dir, relative_path)

        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return file_path

    # ==================== 单例模式测试 ====================

    def test_singleton_pattern(self):
        """测试单例模式"""
        manager1 = IndexManager(db_path=self.temp_db.name)
        manager2 = IndexManager(db_path=self.temp_db.name)

        # 应该是同一个实例
        self.assertIs(manager1, manager2)

    # ==================== 初始化测试 ====================

    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.manager.config)
        self.assertIsNotNone(self.manager.db)
        self.assertIsNotNone(self.manager.parser_factory)
        self.assertGreater(self.manager.max_file_size, 0)
        self.assertIsInstance(self.manager.excluded_extensions, list)
        self.assertIsInstance(self.manager.excluded_paths, list)

    # ==================== 扫描功能测试 ====================

    def test_scan_empty_directory(self):
        """测试扫描空目录"""
        files = self.manager.scan_directory(self.test_dir)
        self.assertEqual(len(files), 0)

    def test_scan_nonexistent_directory(self):
        """测试扫描不存在的目录"""
        files = self.manager.scan_directory('/nonexistent/directory')
        self.assertEqual(len(files), 0)

    def test_scan_single_text_file(self):
        """测试扫描单个文本文件"""
        # 注册文本解析器
        from src.parsers.text_parser import TextParser
        self.manager.parser_factory.register_parser(
            'text',
            ['.txt', '.md'],
            TextParser()
        )

        # 创建测试文件
        file_path = self._create_test_file('test.txt', 'Hello World')

        # 扫描目录
        files = self.manager.scan_directory(self.test_dir)

        # 验证结果
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]['path'], file_path)
        self.assertIn('size', files[0])
        self.assertIn('modified', files[0])
        self.assertIn('hash', files[0])
        self.assertGreater(len(files[0]['hash']), 0)

    def test_scan_multiple_files(self):
        """测试扫描多个文件"""
        # 注册解析器
        from src.parsers.text_parser import TextParser
        self.manager.parser_factory.register_parser(
            'text',
            ['.txt', '.md'],
            TextParser()
        )

        # 创建多个测试文件
        self._create_test_file('file1.txt', 'Content 1')
        self._create_test_file('file2.txt', 'Content 2')
        self._create_test_file('file3.md', 'Content 3')

        # 扫描目录
        files = self.manager.scan_directory(self.test_dir)

        # 验证结果
        self.assertEqual(len(files), 3)

    def test_scan_recursive(self):
        """测试递归扫描子目录"""
        # 注册解析器
        from src.parsers.text_parser import TextParser
        self.manager.parser_factory.register_parser(
            'text',
            ['.txt'],
            TextParser()
        )

        # 创建嵌套目录结构
        self._create_test_file('file1.txt', 'Root')
        self._create_test_file('subdir1/file2.txt', 'Sub 1')
        self._create_test_file('subdir1/subdir2/file3.txt', 'Sub 2')

        # 递归扫描
        files = self.manager.scan_directory(self.test_dir, recursive=True)
        self.assertEqual(len(files), 3)

        # 非递归扫描
        files = self.manager.scan_directory(self.test_dir, recursive=False)
        self.assertEqual(len(files), 1)

    def test_scan_ignores_unsupported_files(self):
        """测试忽略不支持的文件格式"""
        # 注册解析器 (只支持 .txt)
        from src.parsers.text_parser import TextParser
        self.manager.parser_factory.register_parser(
            'text',
            ['.txt'],
            TextParser()
        )

        # 创建不同格式的文件
        self._create_test_file('file1.txt', 'Supported')
        self._create_test_file('file2.xyz', 'Unsupported')
        self._create_test_file('file3.tmp', 'Unsupported')

        # 扫描目录
        files = self.manager.scan_directory(self.test_dir)

        # 只应该找到 .txt 文件
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0]['path'].endswith('.txt'))

    def test_scan_ignores_excluded_extensions(self):
        """测试忽略排除的扩展名"""
        # 注册解析器
        from src.parsers.text_parser import TextParser
        self.manager.parser_factory.register_parser(
            'text',
            ['.txt', '.log'],
            TextParser()
        )

        # 保存原始排除扩展名并设置新的
        original_excluded = self.manager.excluded_extensions.copy()
        self.manager.excluded_extensions = ['.log']

        try:
            # 创建文件
            self._create_test_file('file1.txt', 'Include')
            self._create_test_file('file2.log', 'Exclude')

            # 扫描目录
            files = self.manager.scan_directory(self.test_dir)

            # 只应该找到 .txt 文件
            self.assertEqual(len(files), 1)
            self.assertTrue(files[0]['path'].endswith('.txt'))
        finally:
            # 恢复原始配置
            self.manager.excluded_extensions = original_excluded

    def test_scan_ignores_excluded_paths(self):
        """测试忽略排除的路径"""
        # 注册解析器
        from src.parsers.text_parser import TextParser
        self.manager.parser_factory.register_parser(
            'text',
            ['.txt'],
            TextParser()
        )

        # 设置排除路径
        excluded_dir = os.path.join(self.test_dir, 'excluded')
        self.manager.excluded_paths = [excluded_dir]

        # 创建文件
        self._create_test_file('include.txt', 'Include')
        self._create_test_file('excluded/exclude.txt', 'Exclude')

        # 扫描目录
        files = self.manager.scan_directory(self.test_dir, recursive=True)

        # 只应该找到 include.txt
        self.assertEqual(len(files), 1)
        self.assertIn('include.txt', files[0]['path'])

    def test_scan_ignores_empty_files(self):
        """测试忽略空文件"""
        # 注册解析器
        from src.parsers.text_parser import TextParser
        self.manager.parser_factory.register_parser(
            'text',
            ['.txt'],
            TextParser()
        )

        # 创建文件
        self._create_test_file('normal.txt', 'Content')
        self._create_test_file('empty.txt', '')

        # 扫描目录
        files = self.manager.scan_directory(self.test_dir)

        # 只应该找到非空文件
        self.assertEqual(len(files), 1)
        self.assertIn('normal.txt', files[0]['path'])

    def test_scan_ignores_large_files(self):
        """测试忽略超大文件"""
        # 注册解析器
        from src.parsers.text_parser import TextParser
        self.manager.parser_factory.register_parser(
            'text',
            ['.txt'],
            TextParser()
        )

        # 设置较小的文件大小限制
        self.manager.max_file_size = 100  # 100 字节

        # 创建文件
        self._create_test_file('small.txt', 'Small')  # < 100 字节
        self._create_test_file('large.txt', 'X' * 200)  # > 100 字节

        # 扫描目录
        files = self.manager.scan_directory(self.test_dir)

        # 只应该找到小文件
        self.assertEqual(len(files), 1)
        self.assertIn('small.txt', files[0]['path'])

    # ==================== 多目录扫描测试 ====================

    def test_list_files_multiple_directories(self):
        """测试扫描多个目录"""
        # 注册解析器
        from src.parsers.text_parser import TextParser
        self.manager.parser_factory.register_parser(
            'text',
            ['.txt'],
            TextParser()
        )

        # 创建第二个测试目录
        test_dir2 = tempfile.mkdtemp()

        try:
            # 在两个目录中创建文件
            self._create_test_file('file1.txt', 'Dir1')
            file2_path = os.path.join(test_dir2, 'file2.txt')
            with open(file2_path, 'w') as f:
                f.write('Dir2')

            # 扫描两个目录
            files = self.manager.list_files([self.test_dir, test_dir2])

            # 应该找到两个文件
            self.assertEqual(len(files), 2)

        finally:
            # 清理第二个测试目录
            import shutil
            if os.path.exists(test_dir2):
                shutil.rmtree(test_dir2)

    # ==================== 哈希计算测试 ====================

    def test_file_hash_calculation(self):
        """测试文件哈希计算"""
        # 创建测试文件
        file_path = self._create_test_file('test.txt', 'Test Content')

        # 计算哈希
        hash1 = self.manager._calculate_file_hash(file_path)
        hash2 = self.manager._calculate_file_hash(file_path)

        # 相同文件应该有相同的哈希
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)  # SHA256 哈希长度

    def test_different_files_different_hashes(self):
        """测试不同文件产生不同哈希"""
        file1 = self._create_test_file('file1.txt', 'Content 1')
        file2 = self._create_test_file('file2.txt', 'Content 2')

        hash1 = self.manager._calculate_file_hash(file1)
        hash2 = self.manager._calculate_file_hash(file2)

        self.assertNotEqual(hash1, hash2)

    def test_hash_calculation_error_handling(self):
        """测试哈希计算错误处理"""
        # 不存在的文件
        hash_value = self.manager._calculate_file_hash('/nonexistent/file.txt')
        self.assertEqual(hash_value, "")

    # ==================== 过滤功能测试 ====================

    def test_is_excluded_path(self):
        """测试路径排除检查"""
        self.manager.excluded_paths = [
            'C:\\Windows',
            'C:\\Program Files',
            'temp'
        ]

        # 应该被排除
        self.assertTrue(self.manager._is_excluded_path('C:\\Windows\\System32'))
        self.assertTrue(self.manager._is_excluded_path('c:\\windows\\test'))  # 大小写不敏感
        self.assertTrue(self.manager._is_excluded_path('C:\\temp\\file.txt'))

        # 不应该被排除
        self.assertFalse(self.manager._is_excluded_path('C:\\Users\\test'))
        self.assertFalse(self.manager._is_excluded_path('D:\\Documents'))

    def test_should_index_file_checks(self):
        """测试文件索引检查"""
        # 注册解析器
        from src.parsers.text_parser import TextParser
        self.manager.parser_factory.register_parser(
            'text',
            ['.txt'],
            TextParser()
        )

        # 创建测试文件
        valid_file = self._create_test_file('valid.txt', 'Content')

        # 有效文件
        self.assertTrue(self.manager._should_index_file(valid_file))

        # 不存在的文件
        self.assertFalse(self.manager._should_index_file('/nonexistent.txt'))

        # 不支持的格式
        unsupported = self._create_test_file('unsupported.xyz', 'Content')
        self.assertFalse(self.manager._should_index_file(unsupported))

    # ==================== IndexStats 测试 ====================

    def test_index_stats_initialization(self):
        """测试 IndexStats 初始化"""
        stats = IndexStats()

        self.assertEqual(stats.total_files, 0)
        self.assertEqual(stats.indexed_files, 0)
        self.assertEqual(stats.failed_files, 0)
        self.assertEqual(stats.skipped_files, 0)
        self.assertEqual(stats.total_size, 0)
        self.assertEqual(stats.elapsed_time, 0.0)
        self.assertIsInstance(stats.errors, list)
        self.assertEqual(len(stats.errors), 0)

    def test_index_stats_with_data(self):
        """测试 IndexStats 数据记录"""
        stats = IndexStats(
            total_files=100,
            indexed_files=90,
            failed_files=5,
            skipped_files=5,
            total_size=1024000,
            elapsed_time=10.5,
            errors=[('/path/file1.txt', 'Parse error'), ('/path/file2.txt', 'Access denied')]
        )

        self.assertEqual(stats.total_files, 100)
        self.assertEqual(stats.indexed_files, 90)
        self.assertEqual(stats.failed_files, 5)
        self.assertEqual(stats.skipped_files, 5)
        self.assertEqual(stats.total_size, 1024000)
        self.assertEqual(stats.elapsed_time, 10.5)
        self.assertEqual(len(stats.errors), 2)


if __name__ == '__main__':
    unittest.main()
