"""
索引管理器解析和数据库写入功能单元测试

测试 IndexManager 的以下功能:
- _parse_file(): 解析单个文件
- _batch_insert(): 批量插入文档到数据库
- create_index(): 创建完整索引
"""

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.core.index_manager import IndexManager, IndexStats
from src.parsers.base import ParseResult
from src.parsers.factory import ParserFactory


class TestIndexManagerParse(unittest.TestCase):
    """测试 IndexManager 的文件解析功能"""

    def setUp(self):
        """测试前准备"""
        # 创建临时目录
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, 'test_index.db')

        # 创建测试文件
        self.test_file1 = os.path.join(self.test_dir, 'test1.txt')
        self.test_file2 = os.path.join(self.test_dir, 'test2.txt')
        self.test_file3 = os.path.join(self.test_dir, 'test3.txt')

        with open(self.test_file1, 'w', encoding='utf-8') as f:
            f.write('这是测试文件1的内容')

        with open(self.test_file2, 'w', encoding='utf-8') as f:
            f.write('这是测试文件2的内容')

        with open(self.test_file3, 'w', encoding='utf-8') as f:
            f.write('这是测试文件3的内容')

    def tearDown(self):
        """测试后清理"""
        # 关闭数据库连接
        if hasattr(self, 'manager') and self.manager:
            if hasattr(self.manager, 'db') and self.manager.db:
                self.manager.db.close()

        # 重置单例
        IndexManager._instance = None

        # 删除临时目录
        if os.path.exists(self.test_dir):
            try:
                shutil.rmtree(self.test_dir)
            except PermissionError:
                # Windows 下可能需要等待文件句柄释放
                import time
                time.sleep(0.1)
                shutil.rmtree(self.test_dir)

    def test_parse_file_success(self):
        """测试成功解析文件"""
        # 创建 IndexManager 实例
        self.manager = IndexManager(db_path=self.db_path)
        manager = self.manager

        # 注册测试解析器
        mock_parser = Mock()
        mock_parser.parse.return_value = ParseResult(
            success=True,
            content='解析后的内容',
            metadata={'author': 'test'}
        )
        manager.parser_factory.register_parser('txt', ['.txt'], mock_parser)

        # 准备文件信息
        file_info = {
            'path': self.test_file1,
            'size': 1024,
            'modified': 1234567890.0,
            'hash': 'abc123'
        }

        # 解析文件
        result = manager._parse_file(file_info)

        # 验证结果
        self.assertIsNotNone(result)
        self.assertEqual(result['file_path'], self.test_file1)
        self.assertEqual(result['file_name'], 'test1.txt')
        self.assertEqual(result['file_size'], 1024)
        self.assertEqual(result['file_type'], 'txt')
        self.assertEqual(result['content_hash'], 'abc123')
        self.assertEqual(result['content'], '解析后的内容')
        self.assertEqual(result['metadata'], {'author': 'test'})

        # 验证 parser.parse 被调用
        mock_parser.parse.assert_called_once_with(self.test_file1)

    def test_parse_file_parser_not_found(self):
        """测试解析器未找到的情况"""
        self.manager = IndexManager(db_path=self.db_path)
        manager = self.manager

        file_info = {
            'path': self.test_file1,
            'size': 1024,
            'modified': 1234567890.0,
            'hash': 'abc123'
        }

        # 解析文件 (没有注册解析器)
        result = manager._parse_file(file_info)

        # 验证返回 None
        self.assertIsNone(result)

    def test_parse_file_parse_failed(self):
        """测试解析失败的情况"""
        self.manager = IndexManager(db_path=self.db_path)
        manager = self.manager

        # 注册测试解析器 (返回失败结果)
        mock_parser = Mock()
        mock_parser.parse.return_value = ParseResult(
            success=False,
            content='',
            error='解析失败'
        )
        manager.parser_factory.register_parser('txt', ['.txt'], mock_parser)

        file_info = {
            'path': self.test_file1,
            'size': 1024,
            'modified': 1234567890.0,
            'hash': 'abc123'
        }

        # 解析文件
        result = manager._parse_file(file_info)

        # 验证返回 None
        self.assertIsNone(result)

    def test_parse_file_exception(self):
        """测试解析过程中抛出异常"""
        self.manager = IndexManager(db_path=self.db_path)
        manager = self.manager

        # 注册测试解析器 (抛出异常)
        mock_parser = Mock()
        mock_parser.parse.side_effect = Exception('解析异常')
        manager.parser_factory.register_parser('txt', ['.txt'], mock_parser)

        file_info = {
            'path': self.test_file1,
            'size': 1024,
            'modified': 1234567890.0,
            'hash': 'abc123'
        }

        # 解析文件
        result = manager._parse_file(file_info)

        # 验证返回 None
        self.assertIsNone(result)

    def test_batch_insert_success(self):
        """测试批量插入成功"""
        self.manager = IndexManager(db_path=self.db_path)
        manager = self.manager

        # 准备文档数据
        documents = [
            {
                'file_path': self.test_file1,
                'file_name': 'test1.txt',
                'content': '内容1',
                'file_size': 100,
                'file_type': 'txt',
                'content_hash': 'hash1',
                'modified_at': '2024-01-01 00:00:00',
                'metadata': {}
            },
            {
                'file_path': self.test_file2,
                'file_name': 'test2.txt',
                'content': '内容2',
                'file_size': 200,
                'file_type': 'txt',
                'content_hash': 'hash2',
                'modified_at': '2024-01-02 00:00:00',
                'metadata': {}
            }
        ]

        # 批量插入
        count = manager._batch_insert(documents)

        # 验证结果
        self.assertEqual(count, 2)

        # 验证数据库中的记录
        doc1 = manager.db.get_document_by_path(self.test_file1)
        self.assertIsNotNone(doc1)
        self.assertEqual(doc1['file_name'], 'test1.txt')

        doc2 = manager.db.get_document_by_path(self.test_file2)
        self.assertIsNotNone(doc2)
        self.assertEqual(doc2['file_name'], 'test2.txt')

    def test_batch_insert_empty_list(self):
        """测试批量插入空列表"""
        self.manager = IndexManager(db_path=self.db_path)
        manager = self.manager

        # 批量插入空列表
        count = manager._batch_insert([])

        # 验证返回 0
        self.assertEqual(count, 0)

    def test_batch_insert_fallback_to_single(self):
        """测试批量插入失败后回退到单个插入"""
        self.manager = IndexManager(db_path=self.db_path)
        manager = self.manager

        # Mock batch_insert_documents 抛出异常
        with patch.object(manager.db, 'batch_insert_documents', side_effect=Exception('批量插入失败')):
            documents = [
                {
                    'file_path': self.test_file1,
                    'file_name': 'test1.txt',
                    'content': '内容1',
                    'file_size': 100,
                    'file_type': 'txt',
                    'content_hash': 'hash1',
                    'modified_at': '2024-01-01 00:00:00',
                    'metadata': {}
                }
            ]

            # 批量插入
            count = manager._batch_insert(documents)

            # 验证成功插入 (回退到单个插入)
            self.assertEqual(count, 1)

            # 验证数据库中的记录
            doc = manager.db.get_document_by_path(self.test_file1)
            self.assertIsNotNone(doc)

    def test_create_index_success(self):
        """测试成功创建索引"""
        self.manager = IndexManager(db_path=self.db_path)
        manager = self.manager

        # 注册测试解析器
        mock_parser = Mock()
        mock_parser.parse.return_value = ParseResult(
            success=True,
            content='解析后的内容',
            metadata={}
        )
        manager.parser_factory.register_parser('txt', ['.txt'], mock_parser)

        # 创建索引
        stats = manager.create_index([self.test_dir])

        # 验证统计信息
        self.assertEqual(stats.total_files, 3)
        self.assertEqual(stats.indexed_files, 3)
        self.assertEqual(stats.failed_files, 0)
        self.assertGreater(stats.total_size, 0)
        self.assertGreater(stats.elapsed_time, 0)

        # 验证数据库中的记录
        paths = manager.db.get_all_file_paths()
        self.assertEqual(len(paths), 3)

    def test_create_index_with_progress_callback(self):
        """测试带进度回调的索引创建"""
        self.manager = IndexManager(db_path=self.db_path)
        manager = self.manager

        # 注册测试解析器
        mock_parser = Mock()
        mock_parser.parse.return_value = ParseResult(
            success=True,
            content='解析后的内容',
            metadata={}
        )
        manager.parser_factory.register_parser('txt', ['.txt'], mock_parser)

        # 创建进度回调 Mock
        progress_callback = Mock()

        # 创建索引
        stats = manager.create_index([self.test_dir], progress_callback=progress_callback)

        # 验证进度回调被调用
        self.assertEqual(progress_callback.call_count, 3)

        # 验证回调参数
        calls = progress_callback.call_args_list
        self.assertEqual(calls[0][0][0], 1)  # 第一次: processed=1
        self.assertEqual(calls[0][0][1], 3)  # 第一次: total=3
        self.assertEqual(calls[1][0][0], 2)  # 第二次: processed=2
        self.assertEqual(calls[2][0][0], 3)  # 第三次: processed=3

    def test_create_index_no_files(self):
        """测试空目录创建索引"""
        empty_dir = os.path.join(self.test_dir, 'empty')
        os.makedirs(empty_dir)

        self.manager = IndexManager(db_path=self.db_path)
        manager = self.manager

        # 创建索引
        stats = manager.create_index([empty_dir])

        # 验证统计信息
        self.assertEqual(stats.total_files, 0)
        self.assertEqual(stats.indexed_files, 0)

    def test_create_index_with_failures(self):
        """测试包含解析失败的索引创建"""
        self.manager = IndexManager(db_path=self.db_path)
        manager = self.manager

        # 注册测试解析器 (部分失败)
        call_count = [0]

        def mock_parse(file_path):
            call_count[0] += 1
            if call_count[0] == 2:
                # 第二次调用返回失败
                return ParseResult(success=False, content='', error='解析失败')
            return ParseResult(success=True, content='解析后的内容', metadata={})

        mock_parser = Mock()
        mock_parser.parse.side_effect = mock_parse
        manager.parser_factory.register_parser('txt', ['.txt'], mock_parser)

        # 创建索引
        stats = manager.create_index([self.test_dir])

        # 验证统计信息
        self.assertEqual(stats.total_files, 3)
        self.assertEqual(stats.indexed_files, 2)
        self.assertEqual(stats.failed_files, 1)

    def test_create_index_batch_processing(self):
        """测试批量处理功能"""
        self.manager = IndexManager(db_path=self.db_path)
        manager = self.manager
        manager.batch_size = 2  # 设置批量大小为 2

        # 注册测试解析器
        mock_parser = Mock()
        mock_parser.parse.return_value = ParseResult(
            success=True,
            content='解析后的内容',
            metadata={}
        )
        manager.parser_factory.register_parser('txt', ['.txt'], mock_parser)

        # Mock _batch_insert 方法以验证批次
        original_batch_insert = manager._batch_insert
        batch_sizes = []

        def mock_batch_insert(documents):
            batch_sizes.append(len(documents))
            return original_batch_insert(documents)

        with patch.object(manager, '_batch_insert', side_effect=mock_batch_insert):
            # 创建索引
            stats = manager.create_index([self.test_dir])

            # 验证批次
            # 3 个文件,批量大小为 2,应该有 2 次批量插入: [2, 1]
            self.assertEqual(len(batch_sizes), 2)
            self.assertEqual(batch_sizes[0], 2)
            self.assertEqual(batch_sizes[1], 1)

    def test_create_index_exception_handling(self):
        """测试索引创建过程中的异常处理"""
        self.manager = IndexManager(db_path=self.db_path)
        manager = self.manager

        # Mock list_files 抛出异常
        with patch.object(manager, 'list_files', side_effect=Exception('扫描失败')):
            # 验证抛出异常
            with self.assertRaises(Exception) as context:
                manager.create_index([self.test_dir])

            self.assertIn('扫描失败', str(context.exception))


class TestIndexManagerIntegration(unittest.TestCase):
    """索引管理器集成测试"""

    def setUp(self):
        """测试前准备"""
        # 创建临时目录
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, 'test_index.db')

        # 创建测试文件结构
        self.docs_dir = os.path.join(self.test_dir, 'docs')
        os.makedirs(self.docs_dir)

        # 创建多个测试文件
        for i in range(10):
            file_path = os.path.join(self.docs_dir, f'doc{i}.txt')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f'这是文档 {i} 的内容\n' * 10)

    def tearDown(self):
        """测试后清理"""
        # 关闭数据库连接
        if hasattr(self, 'manager') and self.manager:
            if hasattr(self.manager, 'db') and self.manager.db:
                self.manager.db.close()

        # 重置单例
        IndexManager._instance = None

        # 删除临时目录
        if os.path.exists(self.test_dir):
            try:
                shutil.rmtree(self.test_dir)
            except PermissionError:
                import time
                time.sleep(0.1)
                shutil.rmtree(self.test_dir)

    def test_full_indexing_workflow(self):
        """测试完整的索引工作流"""
        self.manager = IndexManager(db_path=self.db_path)
        manager = self.manager

        # 注册文本解析器
        from src.parsers.text_parser import TextParser
        manager.parser_factory.register_parser('text', ['.txt', '.md'], TextParser())

        # 创建索引
        stats = manager.create_index([self.docs_dir])

        # 验证统计信息
        self.assertEqual(stats.total_files, 10)
        self.assertEqual(stats.indexed_files, 10)
        self.assertEqual(stats.failed_files, 0)
        self.assertGreater(stats.total_size, 0)

        # 验证数据库中的记录
        db_stats = manager.db.get_statistics()
        self.assertEqual(db_stats['document_count'], 10)

        # 验证所有文件都被索引
        all_paths = manager.db.get_all_file_paths()
        self.assertEqual(len(all_paths), 10)


if __name__ == '__main__':
    unittest.main()
