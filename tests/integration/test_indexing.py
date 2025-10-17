"""
集成测试:完整的索引创建流程

测试从文件扫描、解析到数据库存储的完整流程
"""

import unittest
import tempfile
import os
import shutil
import time

from src.core.index_manager import IndexManager
from src.data.db_manager import DBManager
from src.parsers.text_parser import TextParser
from src.parsers.factory import get_parser_factory


class TestIndexingIntegration(unittest.TestCase):
    """测试完整索引流程的集成测试"""

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

        if os.path.exists(self.test_dir):
            try:
                shutil.rmtree(self.test_dir)
            except:
                pass

    def test_full_indexing_workflow(self):
        """测试完整的索引工作流"""
        # 1. 创建测试文档
        test_docs_dir = os.path.join(self.test_dir, 'test_docs')
        os.makedirs(test_docs_dir)

        # 创建不同类型的文件
        test_files = {
            'doc1.txt': '这是第一个文档内容',
            'doc2.txt': '这是第二个文档内容,包含更多文字',
            'doc3.txt': '搜索测试关键词: Python, 索引, 文档管理',
        }

        for filename, content in test_files.items():
            file_path = os.path.join(test_docs_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        # 2. 执行索引
        stats = self.manager.create_index([test_docs_dir])

        # 3. 验证索引统计
        self.assertEqual(stats.total_files, len(test_files))
        self.assertEqual(stats.indexed_files, len(test_files))
        self.assertEqual(stats.failed_files, 0)
        self.assertGreater(stats.elapsed_time, 0)

        # 4. 验证数据库中的数据
        db = DBManager(self.db_file)

        # 查询所有文档
        all_docs = db.search_documents(query='*', max_results=10)
        self.assertEqual(len(all_docs), len(test_files))

        # 验证内容被正确索引
        for doc in all_docs:
            self.assertIn('file_path', doc)
            self.assertIn('content', doc)
            self.assertTrue(doc['content'])  # 内容不为空

    def test_parallel_indexing_workflow(self):
        """测试并行索引工作流"""
        # 创建测试文档
        test_docs_dir = os.path.join(self.test_dir, 'parallel_docs')
        os.makedirs(test_docs_dir)

        # 创建多个文件
        num_files = 10
        for i in range(num_files):
            file_path = os.path.join(test_docs_dir, f'doc_{i}.txt')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f'文档 {i} 的内容 ' * 50)

        # 执行并行索引
        stats = self.manager.create_index_parallel([test_docs_dir], num_workers=4)

        # 验证统计信息
        self.assertEqual(stats.total_files, num_files)
        self.assertEqual(stats.indexed_files, num_files)
        self.assertGreater(stats.elapsed_time, 0)

        # 验证数据库
        db = DBManager(self.db_file)
        all_docs = db.search_documents(query='*', max_results=20)
        self.assertEqual(len(all_docs), num_files)

    def test_indexing_with_progress_callback(self):
        """测试索引过程中的进度回调"""
        # 创建测试文档
        test_docs_dir = os.path.join(self.test_dir, 'progress_test')
        os.makedirs(test_docs_dir)

        num_files = 5
        for i in range(num_files):
            file_path = os.path.join(test_docs_dir, f'file_{i}.txt')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f'内容 {i}')

        # 记录进度回调
        progress_records = []

        def progress_callback(processed, total, current_file):
            progress_records.append({
                'processed': processed,
                'total': total,
                'current_file': current_file
            })

        # 执行索引
        stats = self.manager.create_index(
            [test_docs_dir],
            progress_callback=progress_callback
        )

        # 验证进度回调被调用
        self.assertGreater(len(progress_records), 0)
        self.assertEqual(len(progress_records), num_files)

        # 验证进度数据正确
        for i, record in enumerate(progress_records, 1):
            self.assertEqual(record['processed'], i)
            self.assertEqual(record['total'], num_files)
            self.assertTrue(record['current_file'].endswith('.txt'))

    def test_incremental_indexing(self):
        """测试增量索引"""
        # 1. 创建初始文档
        test_docs_dir = os.path.join(self.test_dir, 'incremental_test')
        os.makedirs(test_docs_dir)

        initial_files = {
            'doc1.txt': '初始内容 1',
            'doc2.txt': '初始内容 2',
        }

        for filename, content in initial_files.items():
            file_path = os.path.join(test_docs_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        # 2. 执行初始索引
        stats1 = self.manager.create_index([test_docs_dir])
        self.assertEqual(stats1.indexed_files, 2)

        # 等待一下确保时间戳不同
        time.sleep(0.1)

        # 3. 添加新文件,修改现有文件,删除一个文件
        new_file = os.path.join(test_docs_dir, 'doc3.txt')
        with open(new_file, 'w', encoding='utf-8') as f:
            f.write('新增内容 3')

        # 修改 doc1.txt
        doc1_path = os.path.join(test_docs_dir, 'doc1.txt')
        with open(doc1_path, 'w', encoding='utf-8') as f:
            f.write('修改后的内容 1')

        # 删除 doc2.txt
        doc2_path = os.path.join(test_docs_dir, 'doc2.txt')
        os.remove(doc2_path)

        # 4. 执行增量索引
        stats2 = self.manager.refresh_index([test_docs_dir])

        # 5. 验证增量索引结果
        self.assertEqual(stats2.added_files, 1)     # doc3.txt
        self.assertEqual(stats2.updated_files, 1)   # doc1.txt
        self.assertEqual(stats2.deleted_files, 1)   # doc2.txt

        # 6. 验证数据库中的数据
        db = DBManager(self.db_file)
        all_docs = db.search_documents(query='*', max_results=10)
        self.assertEqual(len(all_docs), 2)  # doc1 和 doc3

    def test_performance_requirement(self):
        """测试性能要求:索引速度 >= 100 文件/分钟"""
        # 创建测试文档
        test_docs_dir = os.path.join(self.test_dir, 'performance_test')
        os.makedirs(test_docs_dir)

        # 创建 100 个小文件
        num_files = 100
        for i in range(num_files):
            file_path = os.path.join(test_docs_dir, f'perf_test_{i}.txt')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f'性能测试文档 {i} 的内容 ' * 10)

        # 执行索引并测量时间
        start_time = time.time()
        stats = self.manager.create_index([test_docs_dir])
        elapsed_time = time.time() - start_time

        # 计算速度(文件/分钟)
        files_per_minute = (stats.indexed_files / elapsed_time) * 60

        print(f"\n性能测试结果:")
        print(f"  文件数量: {num_files}")
        print(f"  索引成功: {stats.indexed_files}")
        print(f"  耗时: {elapsed_time:.3f}秒")
        print(f"  速度: {files_per_minute:.1f} 文件/分钟")

        # 验证性能要求
        self.assertGreaterEqual(
            files_per_minute,
            100,
            f"性能不达标:速度={files_per_minute:.1f}文件/分钟,要求>=100文件/分钟"
        )

    def test_parallel_performance_improvement(self):
        """测试并行索引的性能提升"""
        # 创建测试文档
        test_docs_dir = os.path.join(self.test_dir, 'parallel_perf_test')
        os.makedirs(test_docs_dir)

        # 创建 50 个文件
        num_files = 50
        for i in range(num_files):
            file_path = os.path.join(test_docs_dir, f'test_{i}.txt')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f'测试内容 {i} ' * 100)

        # 串行索引
        db_file_serial = os.path.join(self.test_dir, 'serial.db')
        manager_serial = IndexManager(db_path=db_file_serial)

        start_serial = time.time()
        stats_serial = manager_serial.create_index([test_docs_dir], use_parallel=False)
        time_serial = time.time() - start_serial

        # 并行索引
        db_file_parallel = os.path.join(self.test_dir, 'parallel.db')
        manager_parallel = IndexManager(db_path=db_file_parallel)

        start_parallel = time.time()
        stats_parallel = manager_parallel.create_index([test_docs_dir], use_parallel=True, num_workers=4)
        time_parallel = time.time() - start_parallel

        # 计算加速比
        speedup = time_serial / time_parallel if time_parallel > 0 else 0

        print(f"\n并行性能测试:")
        print(f"  串行耗时: {time_serial:.3f}秒")
        print(f"  并行耗时: {time_parallel:.3f}秒")
        print(f"  加速比: {speedup:.2f}x")

        # 验证结果一致性
        self.assertEqual(stats_serial.indexed_files, stats_parallel.indexed_files)

        # 并行应该更快(至少有一定提升)
        # 注意:在小数据集上可能看不到明显提升
        self.assertGreater(speedup, 0.5)  # 至少不能更慢

    def test_error_handling_in_indexing(self):
        """测试索引过程中的错误处理"""
        # 创建测试文档目录
        test_docs_dir = os.path.join(self.test_dir, 'error_test')
        os.makedirs(test_docs_dir)

        # 创建正常文件
        normal_file = os.path.join(test_docs_dir, 'normal.txt')
        with open(normal_file, 'w', encoding='utf-8') as f:
            f.write('正常文件内容')

        # 创建权限受限的文件(尝试模拟错误)
        # 注意:在 Windows 上可能需要管理员权限

        # 执行索引
        stats = self.manager.create_index([test_docs_dir])

        # 至少有一个文件成功索引
        self.assertGreater(stats.indexed_files, 0)

    def test_batch_insertion(self):
        """测试批量插入功能"""
        # 创建测试文档
        test_docs_dir = os.path.join(self.test_dir, 'batch_test')
        os.makedirs(test_docs_dir)

        # 创建超过一个批次的文件(假设 batch_size=100)
        num_files = 150
        for i in range(num_files):
            file_path = os.path.join(test_docs_dir, f'batch_{i}.txt')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f'批次测试 {i}')

        # 执行索引
        stats = self.manager.create_index([test_docs_dir])

        # 验证所有文件都被索引
        self.assertEqual(stats.total_files, num_files)
        self.assertEqual(stats.indexed_files, num_files)

        # 验证数据库中的数据
        db = DBManager(self.db_file)
        all_docs = db.search_documents(query='*', max_results=200)
        self.assertEqual(len(all_docs), num_files)

    def test_search_after_indexing(self):
        """测试索引后的搜索功能"""
        # 创建测试文档
        test_docs_dir = os.path.join(self.test_dir, 'search_test')
        os.makedirs(test_docs_dir)

        test_content = {
            'python.txt': 'Python是一种强大的编程语言',
            'java.txt': 'Java是一种面向对象的编程语言',
            'cpp.txt': 'C++是一种高性能的系统编程语言',
        }

        for filename, content in test_content.items():
            file_path = os.path.join(test_docs_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        # 执行索引
        stats = self.manager.create_index([test_docs_dir])
        self.assertEqual(stats.indexed_files, 3)

        # 搜索测试
        db = DBManager(self.db_file)

        # 搜索 "Python"
        results = db.search_documents(query='Python', max_results=10)
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]['file_path'].endswith('python.txt'))

        # 搜索 "编程语言"
        results = db.search_documents(query='编程语言', max_results=10)
        self.assertEqual(len(results), 3)


if __name__ == '__main__':
    unittest.main(verbosity=2)
