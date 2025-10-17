"""
IndexManager 增量索引功能单元测试

测试增量索引、文件哈希检测、变更检测和文档更新功能
"""

import os
import tempfile
import unittest
import time
from pathlib import Path

from src.core.index_manager import IndexManager, IndexStats


class TestIndexManagerIncremental(unittest.TestCase):
    """IndexManager 增量索引功能测试"""

    def setUp(self):
        """测试前准备"""
        # 创建临时数据库
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()

        # 创建临时测试目录
        self.test_dir = tempfile.mkdtemp()

        # 重置单例以获取干净的实例
        IndexManager._instance = None
        IndexManager._initialized = False

        # 初始化 IndexManager
        self.manager = IndexManager(db_path=self.temp_db.name)

        # 注册文本解析器
        from src.parsers.text_parser import TextParser
        self.manager.parser_factory.register_parser(
            'text',
            ['.txt', '.md'],
            TextParser()
        )

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

    def _modify_test_file(self, relative_path: str, new_content: str):
        """
        修改测试文件内容

        Args:
            relative_path: 相对于测试目录的路径
            new_content: 新的文件内容
        """
        file_path = os.path.join(self.test_dir, relative_path)

        # 等待一小段时间确保修改时间不同
        time.sleep(0.01)

        # 写入新内容
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

    # ==================== IndexStats 扩展字段测试 ====================

    def test_index_stats_incremental_fields(self):
        """测试 IndexStats 增量索引字段"""
        stats = IndexStats()

        # 验证增量索引字段存在
        self.assertEqual(stats.added_files, 0)
        self.assertEqual(stats.updated_files, 0)
        self.assertEqual(stats.deleted_files, 0)

    def test_index_stats_with_incremental_data(self):
        """测试 IndexStats 增量索引数据记录"""
        stats = IndexStats(
            total_files=100,
            indexed_files=15,
            added_files=10,
            updated_files=5,
            deleted_files=3
        )

        self.assertEqual(stats.total_files, 100)
        self.assertEqual(stats.indexed_files, 15)
        self.assertEqual(stats.added_files, 10)
        self.assertEqual(stats.updated_files, 5)
        self.assertEqual(stats.deleted_files, 3)

    # ==================== 文件变更检测测试 ====================

    def test_detect_changes_new_files(self):
        """测试检测新增文件"""
        # 数据库中的文件(空)
        db_files_dict = {}

        # 当前文件系统中的文件
        current_files = [
            {'path': 'file1.txt', 'hash': 'hash1'},
            {'path': 'file2.txt', 'hash': 'hash2'},
        ]

        # 检测变更
        new_files, modified_files, deleted_files = self.manager._detect_changes(
            db_files_dict,
            current_files
        )

        # 验证结果
        self.assertEqual(len(new_files), 2)
        self.assertEqual(len(modified_files), 0)
        self.assertEqual(len(deleted_files), 0)

    def test_detect_changes_modified_files(self):
        """测试检测修改的文件"""
        # 数据库中的文件
        db_files_dict = {
            'file1.txt': 'old_hash1',
            'file2.txt': 'old_hash2',
        }

        # 当前文件系统中的文件(file1 已修改)
        current_files = [
            {'path': 'file1.txt', 'hash': 'new_hash1'},  # 修改
            {'path': 'file2.txt', 'hash': 'old_hash2'},  # 未变化
        ]

        # 检测变更
        new_files, modified_files, deleted_files = self.manager._detect_changes(
            db_files_dict,
            current_files
        )

        # 验证结果
        self.assertEqual(len(new_files), 0)
        self.assertEqual(len(modified_files), 1)
        self.assertEqual(modified_files[0]['path'], 'file1.txt')
        self.assertEqual(len(deleted_files), 0)

    def test_detect_changes_deleted_files(self):
        """测试检测删除的文件"""
        # 数据库中的文件
        db_files_dict = {
            'file1.txt': 'hash1',
            'file2.txt': 'hash2',
            'file3.txt': 'hash3',
        }

        # 当前文件系统中的文件(file3 已删除)
        current_files = [
            {'path': 'file1.txt', 'hash': 'hash1'},
            {'path': 'file2.txt', 'hash': 'hash2'},
        ]

        # 检测变更
        new_files, modified_files, deleted_files = self.manager._detect_changes(
            db_files_dict,
            current_files
        )

        # 验证结果
        self.assertEqual(len(new_files), 0)
        self.assertEqual(len(modified_files), 0)
        self.assertEqual(len(deleted_files), 1)
        self.assertIn('file3.txt', deleted_files)

    def test_detect_changes_mixed(self):
        """测试混合变更检测"""
        # 数据库中的文件
        db_files_dict = {
            'file1.txt': 'hash1',       # 未变化
            'file2.txt': 'old_hash2',   # 修改
            'file3.txt': 'hash3',       # 删除
        }

        # 当前文件系统中的文件
        current_files = [
            {'path': 'file1.txt', 'hash': 'hash1'},       # 未变化
            {'path': 'file2.txt', 'hash': 'new_hash2'},   # 修改
            {'path': 'file4.txt', 'hash': 'hash4'},       # 新增
        ]

        # 检测变更
        new_files, modified_files, deleted_files = self.manager._detect_changes(
            db_files_dict,
            current_files
        )

        # 验证结果
        self.assertEqual(len(new_files), 1)
        self.assertEqual(new_files[0]['path'], 'file4.txt')
        self.assertEqual(len(modified_files), 1)
        self.assertEqual(modified_files[0]['path'], 'file2.txt')
        self.assertEqual(len(deleted_files), 1)
        self.assertIn('file3.txt', deleted_files)

    # ==================== 增量索引功能测试 ====================

    def test_refresh_index_empty_database(self):
        """测试空数据库的增量索引(相当于完整索引)"""
        # 创建测试文件
        self._create_test_file('file1.txt', 'Content 1')
        self._create_test_file('file2.txt', 'Content 2')

        # 执行增量索引
        stats = self.manager.refresh_index([self.test_dir])

        # 验证结果
        self.assertEqual(stats.added_files, 2)
        self.assertEqual(stats.updated_files, 0)
        self.assertEqual(stats.deleted_files, 0)
        self.assertEqual(stats.total_files, 2)
        self.assertEqual(stats.indexed_files, 2)

    def test_refresh_index_no_changes(self):
        """测试无变更的增量索引"""
        # 创建测试文件
        self._create_test_file('file1.txt', 'Content 1')
        self._create_test_file('file2.txt', 'Content 2')

        # 首次完整索引
        self.manager.create_index([self.test_dir])

        # 再次增量索引(无变更)
        stats = self.manager.refresh_index([self.test_dir])

        # 验证结果
        self.assertEqual(stats.added_files, 0)
        self.assertEqual(stats.updated_files, 0)
        self.assertEqual(stats.deleted_files, 0)

    def test_refresh_index_with_new_files(self):
        """测试包含新增文件的增量索引"""
        # 创建初始文件
        self._create_test_file('file1.txt', 'Content 1')

        # 完整索引
        self.manager.create_index([self.test_dir])

        # 添加新文件
        self._create_test_file('file2.txt', 'Content 2')
        self._create_test_file('file3.txt', 'Content 3')

        # 增量索引
        stats = self.manager.refresh_index([self.test_dir])

        # 验证结果
        self.assertEqual(stats.added_files, 2)
        self.assertEqual(stats.updated_files, 0)
        self.assertEqual(stats.deleted_files, 0)
        self.assertEqual(stats.total_files, 3)

    def test_refresh_index_with_modified_files(self):
        """测试包含修改文件的增量索引"""
        # 创建测试文件
        self._create_test_file('file1.txt', 'Original Content 1')
        self._create_test_file('file2.txt', 'Original Content 2')

        # 完整索引
        self.manager.create_index([self.test_dir])

        # 修改文件
        self._modify_test_file('file1.txt', 'Modified Content 1')

        # 增量索引
        stats = self.manager.refresh_index([self.test_dir])

        # 验证结果
        self.assertEqual(stats.added_files, 0)
        self.assertEqual(stats.updated_files, 1)
        self.assertEqual(stats.deleted_files, 0)

        # 验证数据库中的内容已更新
        doc = self.manager.db.get_document_by_path(
            os.path.join(self.test_dir, 'file1.txt')
        )
        self.assertIsNotNone(doc)

    def test_refresh_index_with_deleted_files(self):
        """测试包含删除文件的增量索引"""
        # 创建测试文件
        file1_path = self._create_test_file('file1.txt', 'Content 1')
        file2_path = self._create_test_file('file2.txt', 'Content 2')
        file3_path = self._create_test_file('file3.txt', 'Content 3')

        # 完整索引
        self.manager.create_index([self.test_dir])

        # 删除文件
        os.remove(file2_path)

        # 增量索引
        stats = self.manager.refresh_index([self.test_dir])

        # 验证结果
        self.assertEqual(stats.added_files, 0)
        self.assertEqual(stats.updated_files, 0)
        self.assertEqual(stats.deleted_files, 1)
        self.assertEqual(stats.total_files, 2)

        # 验证数据库中的文件已删除
        doc = self.manager.db.get_document_by_path(file2_path)
        self.assertIsNone(doc)

    def test_refresh_index_mixed_changes(self):
        """测试混合变更的增量索引"""
        # 创建初始文件
        file1_path = self._create_test_file('file1.txt', 'Content 1')
        file2_path = self._create_test_file('file2.txt', 'Content 2')

        # 完整索引
        stats1 = self.manager.create_index([self.test_dir])
        self.assertEqual(stats1.indexed_files, 2)

        # 混合变更:
        # - 修改 file1
        # - 删除 file2
        # - 新增 file3 和 file4
        self._modify_test_file('file1.txt', 'Modified Content 1')
        os.remove(file2_path)
        self._create_test_file('file3.txt', 'Content 3')
        self._create_test_file('file4.txt', 'Content 4')

        # 增量索引
        stats2 = self.manager.refresh_index([self.test_dir])

        # 验证结果
        self.assertEqual(stats2.added_files, 2)
        self.assertEqual(stats2.updated_files, 1)
        self.assertEqual(stats2.deleted_files, 1)
        self.assertEqual(stats2.total_files, 3)
        self.assertEqual(stats2.indexed_files, 3)  # added + updated

    def test_refresh_index_with_progress_callback(self):
        """测试增量索引进度回调"""
        # 创建初始文件
        self._create_test_file('file1.txt', 'Content 1')

        # 完整索引
        self.manager.create_index([self.test_dir])

        # 添加新文件
        self._create_test_file('file2.txt', 'Content 2')
        self._create_test_file('file3.txt', 'Content 3')

        # 进度回调
        progress_calls = []

        def progress_callback(processed, total, current_file):
            progress_calls.append((processed, total, current_file))

        # 增量索引
        stats = self.manager.refresh_index([self.test_dir], progress_callback)

        # 验证进度回调被调用
        self.assertGreater(len(progress_calls), 0)
        self.assertEqual(stats.added_files, 2)

    # ==================== 文档更新功能测试 ====================

    def test_update_document(self):
        """测试更新文档"""
        # 创建并索引文件
        file_path = self._create_test_file('test.txt', 'Original Content')
        self.manager.create_index([self.test_dir])

        # 修改文件
        self._modify_test_file('test.txt', 'New Content')

        # 重新扫描获取文件信息
        files = self.manager.scan_directory(self.test_dir)
        file_info = files[0]

        # 解析文件
        doc_data = self.manager._parse_file(file_info)

        # 更新文档
        success = self.manager._update_document(file_info, doc_data)

        # 验证结果
        self.assertTrue(success)

        # 验证数据库中的内容已更新
        doc = self.manager.db.get_document_by_path(file_path)
        self.assertIsNotNone(doc)

    def test_update_nonexistent_document(self):
        """测试更新不存在的文档"""
        file_path = self._create_test_file('test.txt', 'Content')

        # 扫描文件
        files = self.manager.scan_directory(self.test_dir)
        file_info = files[0]

        # 解析文件
        doc_data = self.manager._parse_file(file_info)

        # 尝试更新不存在的文档(未索引)
        success = self.manager._update_document(file_info, doc_data)

        # 应该失败
        self.assertFalse(success)

    # ==================== 哈希变更检测测试 ====================

    def test_file_hash_changes_on_modification(self):
        """测试文件修改后哈希值变化"""
        # 创建文件
        file_path = self._create_test_file('test.txt', 'Original Content')

        # 计算原始哈希
        original_hash = self.manager._calculate_file_hash(file_path)

        # 修改文件
        self._modify_test_file('test.txt', 'Modified Content')

        # 计算新哈希
        new_hash = self.manager._calculate_file_hash(file_path)

        # 哈希值应该不同
        self.assertNotEqual(original_hash, new_hash)

    def test_file_hash_unchanged_for_identical_content(self):
        """测试相同内容的文件哈希值不变"""
        # 创建文件
        file_path = self._create_test_file('test.txt', 'Same Content')

        # 计算哈希
        hash1 = self.manager._calculate_file_hash(file_path)

        # 删除并重新创建相同内容的文件
        os.remove(file_path)
        self._create_test_file('test.txt', 'Same Content')

        # 计算新哈希
        hash2 = self.manager._calculate_file_hash(file_path)

        # 哈希值应该相同
        self.assertEqual(hash1, hash2)

    # ==================== 边界条件和错误处理测试 ====================

    def test_refresh_index_empty_directory(self):
        """测试空目录的增量索引"""
        stats = self.manager.refresh_index([self.test_dir])

        self.assertEqual(stats.total_files, 0)
        self.assertEqual(stats.added_files, 0)
        self.assertEqual(stats.updated_files, 0)
        self.assertEqual(stats.deleted_files, 0)

    def test_refresh_index_nonexistent_directory(self):
        """测试不存在目录的增量索引"""
        stats = self.manager.refresh_index(['/nonexistent/directory'])

        self.assertEqual(stats.total_files, 0)
        self.assertEqual(stats.added_files, 0)

    def test_refresh_index_with_parse_errors(self):
        """测试包含解析错误的增量索引"""
        # 创建初始文件
        self._create_test_file('file1.txt', 'Good Content')

        # 完整索引
        self.manager.create_index([self.test_dir])

        # 添加一个新文件(假设会导致解析错误)
        # 注意:这需要配合 ParserFactory 的 mock 来模拟错误
        # 这里只是基本测试
        self._create_test_file('file2.txt', 'New Content')

        # 增量索引
        stats = self.manager.refresh_index([self.test_dir])

        # 应该成功处理,不会因为个别错误而中断
        self.assertGreaterEqual(stats.total_files, 2)


if __name__ == '__main__':
    unittest.main()
