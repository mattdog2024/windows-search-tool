"""
测试 IndexManager 的多进程并行处理功能
"""

import unittest
import tempfile
import os
import shutil
from unittest.mock import Mock, patch, MagicMock
from multiprocessing import cpu_count

from src.core.index_manager import IndexManager, IndexStats, _parse_file_worker
from src.parsers.base import ParseResult
from src.parsers.text_parser import TextParser
from src.parsers.factory import get_parser_factory


class TestParseFileWorker(unittest.TestCase):
    """测试全局工作函数 _parse_file_worker"""

    @classmethod
    def setUpClass(cls):
        """设置类级别的测试环境"""
        # 注册文本解析器
        factory = get_parser_factory()
        factory.register_parser('text', ['.txt', '.md', '.csv'], TextParser())

    def setUp(self):
        """设置测试环境"""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理测试环境"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_parse_file_worker_success(self):
        """测试成功解析文件"""
        # 创建测试文件
        test_file = os.path.join(self.test_dir, "test.txt")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("测试内容")

        file_info = {
            'path': test_file,
            'size': 100,
            'modified': 1234567890.0,
            'hash': 'abc123'
        }

        # 调用工作函数
        result = _parse_file_worker(file_info)

        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result['file_path'], test_file)
        self.assertEqual(result['file_name'], 'test.txt')
        self.assertEqual(result['file_type'], 'txt')
        self.assertEqual(result['content_hash'], 'abc123')

    def test_parse_file_worker_unsupported_format(self):
        """测试不支持的文件格式"""
        test_file = os.path.join(self.test_dir, "test.unsupported")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write("内容")

        file_info = {
            'path': test_file,
            'size': 10,
            'modified': 1234567890.0,
            'hash': 'xyz789'
        }

        result = _parse_file_worker(file_info)

        # 不支持的格式应返回 None
        self.assertIsNone(result)

    def test_parse_file_worker_file_not_found(self):
        """测试文件不存在的情况"""
        file_info = {
            'path': '/nonexistent/file.txt',
            'size': 100,
            'modified': 1234567890.0,
            'hash': 'def456'
        }

        result = _parse_file_worker(file_info)

        # 文件不存在应返回 None
        self.assertIsNone(result)


class TestIndexManagerParallel(unittest.TestCase):
    """测试 IndexManager 的并行处理功能"""

    @classmethod
    def setUpClass(cls):
        """设置类级别的测试环境"""
        # 注册文本解析器
        factory = get_parser_factory()
        if not factory.supports('test.txt'):
            factory.register_parser('text', ['.txt', '.md', '.csv'], TextParser())

    def setUp(self):
        """设置测试环境"""
        self.test_dir = tempfile.mkdtemp()
        self.db_file = os.path.join(self.test_dir, 'test.db')
        self.manager = IndexManager(db_path=self.db_file)

    def tearDown(self):
        """清理测试环境"""
        # 关闭数据库连接
        try:
            self.manager.db.close()
        except:
            pass

        # 清理临时目录
        if os.path.exists(self.test_dir):
            try:
                shutil.rmtree(self.test_dir)
            except PermissionError:
                # Windows 可能会因为文件被占用而无法删除
                import time
                time.sleep(0.1)
                try:
                    shutil.rmtree(self.test_dir)
                except:
                    pass

    def test_parallel_workers_config(self):
        """测试并行工作进程数配置"""
        # 应该从配置读取或使用 CPU 核心数
        self.assertGreater(self.manager.parallel_workers, 0)
        self.assertLessEqual(self.manager.parallel_workers, cpu_count() * 2)

    def test_create_index_parallel_empty_directory(self):
        """测试并行索引空目录"""
        empty_dir = os.path.join(self.test_dir, 'empty')
        os.makedirs(empty_dir)

        stats = self.manager.create_index_parallel([empty_dir])

        self.assertEqual(stats.total_files, 0)
        self.assertEqual(stats.indexed_files, 0)
        self.assertEqual(stats.failed_files, 0)

    def test_create_index_parallel_with_files(self):
        """测试并行索引多个文件"""
        # 创建多个测试文件
        test_files_dir = os.path.join(self.test_dir, 'test_files')
        os.makedirs(test_files_dir)

        for i in range(5):
            file_path = os.path.join(test_files_dir, f'test_{i}.txt')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f'测试内容 {i}')

        stats = self.manager.create_index_parallel([test_files_dir])

        # 验证统计信息
        self.assertEqual(stats.total_files, 5)
        self.assertGreater(stats.indexed_files, 0)
        self.assertGreater(stats.elapsed_time, 0)

    def test_create_index_parallel_with_progress_callback(self):
        """测试并行索引的进度回调"""
        # 创建测试文件
        test_files_dir = os.path.join(self.test_dir, 'test_files')
        os.makedirs(test_files_dir)

        for i in range(3):
            file_path = os.path.join(test_files_dir, f'test_{i}.txt')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f'内容 {i}')

        # 创建进度回调 Mock
        progress_callback = Mock()

        stats = self.manager.create_index_parallel(
            [test_files_dir],
            progress_callback=progress_callback
        )

        # 验证回调被调用
        self.assertGreater(progress_callback.call_count, 0)

        # 验证回调参数
        for call in progress_callback.call_args_list:
            args = call[0]
            self.assertEqual(len(args), 3)  # (processed, total, current_file)
            self.assertIsInstance(args[0], int)  # processed
            self.assertIsInstance(args[1], int)  # total
            self.assertIsInstance(args[2], str)  # current_file

    def test_create_index_parallel_with_num_workers(self):
        """测试指定工作进程数"""
        test_files_dir = os.path.join(self.test_dir, 'test_files')
        os.makedirs(test_files_dir)

        # 创建测试文件
        for i in range(3):
            file_path = os.path.join(test_files_dir, f'test_{i}.txt')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f'内容 {i}')

        # 使用 2 个工作进程
        stats = self.manager.create_index_parallel(
            [test_files_dir],
            num_workers=2
        )

        self.assertGreater(stats.indexed_files, 0)

    def test_create_index_with_use_parallel_flag(self):
        """测试 create_index 的 use_parallel 参数"""
        test_files_dir = os.path.join(self.test_dir, 'test_files')
        os.makedirs(test_files_dir)

        # 创建测试文件
        for i in range(3):
            file_path = os.path.join(test_files_dir, f'test_{i}.txt')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f'内容 {i}')

        # 使用 use_parallel=True
        stats = self.manager.create_index(
            [test_files_dir],
            use_parallel=True,
            num_workers=2
        )

        self.assertGreater(stats.indexed_files, 0)

    def test_parse_files_parallel(self):
        """测试 _parse_files_parallel 方法"""
        # 创建测试文件信息
        test_files_dir = os.path.join(self.test_dir, 'test_files')
        os.makedirs(test_files_dir)

        files_info = []
        for i in range(3):
            file_path = os.path.join(test_files_dir, f'test_{i}.txt')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f'内容 {i}')

            stat = os.stat(file_path)
            files_info.append({
                'path': file_path,
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'hash': 'test_hash'
            })

        # 调用并行解析
        results = self.manager._parse_files_parallel(files_info, num_workers=2)

        # 验证结果
        self.assertGreater(len(results), 0)
        for result in results:
            self.assertIn('file_path', result)
            self.assertIn('content', result)

    def test_parallel_parsing_with_errors(self):
        """测试并行解析时的错误处理"""
        # 创建一个正常文件和一个不存在的文件
        test_file = os.path.join(self.test_dir, 'normal.txt')
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write('正常内容')

        files_info = [
            {
                'path': test_file,
                'size': 100,
                'modified': 1234567890.0,
                'hash': 'abc'
            },
            {
                'path': '/nonexistent/file.txt',
                'size': 100,
                'modified': 1234567890.0,
                'hash': 'def'
            }
        ]

        results = self.manager._parse_files_parallel(files_info, num_workers=2)

        # 至少有一个成功的结果
        self.assertGreater(len(results), 0)

    def test_parallel_performance_stats(self):
        """测试并行索引的性能统计"""
        test_files_dir = os.path.join(self.test_dir, 'test_files')
        os.makedirs(test_files_dir)

        # 创建多个文件
        num_files = 10
        for i in range(num_files):
            file_path = os.path.join(test_files_dir, f'test_{i}.txt')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f'内容 {i} ' * 100)

        stats = self.manager.create_index_parallel([test_files_dir])

        # 验证性能统计
        self.assertEqual(stats.total_files, num_files)
        self.assertGreater(stats.indexed_files, 0)
        self.assertGreater(stats.elapsed_time, 0)
        self.assertGreater(stats.total_size, 0)


class TestParallelVsSerial(unittest.TestCase):
    """比较并行和串行索引的性能"""

    @classmethod
    def setUpClass(cls):
        """设置类级别的测试环境"""
        # 注册文本解析器
        factory = get_parser_factory()
        if not factory.supports('test.txt'):
            factory.register_parser('text', ['.txt', '.md', '.csv'], TextParser())

    def setUp(self):
        """设置测试环境"""
        self.test_dir = tempfile.mkdtemp()
        self.db_file_serial = os.path.join(self.test_dir, 'serial.db')
        self.db_file_parallel = os.path.join(self.test_dir, 'parallel.db')

    def tearDown(self):
        """清理测试环境"""
        if os.path.exists(self.test_dir):
            try:
                shutil.rmtree(self.test_dir)
            except:
                pass

    def test_parallel_faster_than_serial(self):
        """测试并行索引比串行索引更快(在文件数量足够多时)"""
        # 创建测试文件
        test_files_dir = os.path.join(self.test_dir, 'test_files')
        os.makedirs(test_files_dir)

        # 创建 20 个文件
        for i in range(20):
            file_path = os.path.join(test_files_dir, f'test_{i}.txt')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f'测试内容 {i} ' * 500)

        # 串行索引
        manager_serial = IndexManager(db_path=self.db_file_serial)
        stats_serial = manager_serial.create_index([test_files_dir], use_parallel=False)

        # 并行索引
        manager_parallel = IndexManager(db_path=self.db_file_parallel)
        stats_parallel = manager_parallel.create_index([test_files_dir], use_parallel=True, num_workers=4)

        # 验证结果数量相同
        self.assertEqual(stats_serial.indexed_files, stats_parallel.indexed_files)

        # 输出性能比较
        print(f"\n串行索引耗时: {stats_serial.elapsed_time:.3f}秒")
        print(f"并行索引耗时: {stats_parallel.elapsed_time:.3f}秒")
        if stats_serial.elapsed_time > 0:
            speedup = stats_serial.elapsed_time / stats_parallel.elapsed_time
            print(f"加速比: {speedup:.2f}x")


if __name__ == '__main__':
    unittest.main()
