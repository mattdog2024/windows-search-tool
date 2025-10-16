"""
测试日志系统

测试日志记录器的基本功能、文件轮转、多级别日志等功能
"""

import logging
import os
import tempfile
import time
from pathlib import Path

import pytest

from src.utils.logger import Logger, get_logger, init_logger


@pytest.fixture
def temp_log_file():
    """创建临时日志文件"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        log_file = f.name
    yield log_file
    # 清理
    try:
        if os.path.exists(log_file):
            os.unlink(log_file)
        # 清理备份文件
        log_dir = os.path.dirname(log_file)
        log_name = os.path.basename(log_file)
        for i in range(1, 10):
            backup_file = os.path.join(log_dir, f"{log_name}.{i}")
            if os.path.exists(backup_file):
                os.unlink(backup_file)
    except:
        pass


@pytest.fixture
def cleanup_logger():
    """清理日志器"""
    loggers = []
    yield loggers
    # 清理所有创建的日志器
    for logger in loggers:
        try:
            logger.close()
        except:
            pass


class TestLogger:
    """测试 Logger 类"""

    def test_logger_initialization(self, temp_log_file, cleanup_logger):
        """测试日志器初始化"""
        logger = Logger(
            name='TestLogger',
            log_file=temp_log_file,
            level='INFO',
            max_size_mb=10,
            backup_count=5
        )
        cleanup_logger.append(logger)

        # 验证配置
        assert logger.name == 'TestLogger'
        assert logger.level == 'INFO'
        assert logger.max_size_mb == 10
        assert logger.backup_count == 5
        assert logger.log_file == temp_log_file

        # 验证日志器设置
        assert logger.logger.level == logging.INFO

        logger.close()

    def test_logger_levels(self, cleanup_logger):
        """测试多个日志级别"""
        levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']

        for level in levels:
            # 为每个级别使用唯一的日志器名称,避免冲突
            logger_name = f'TestLogger_{level}_{int(time.time() * 1000000)}'
            logger = Logger(
                name=logger_name,
                log_file=None,  # 不使用文件
                level=level
            )
            cleanup_logger.append(logger)

            assert logger.logger.level == getattr(logging, level)
            logger.close()

    def test_logger_writes_to_file(self, temp_log_file, cleanup_logger):
        """测试日志写入文件"""
        logger_name = f'TestLogger_{int(time.time() * 1000000)}'
        logger = Logger(
            name=logger_name,
            log_file=temp_log_file,
            level='DEBUG'
        )
        cleanup_logger.append(logger)

        # 写入不同级别的日志
        logger.debug('Debug message')
        logger.info('Info message')
        logger.warning('Warning message')
        logger.error('Error message')
        logger.critical('Critical message')

        # 强制刷新缓冲区
        for handler in logger.logger.handlers:
            handler.flush()

        # 验证日志内容
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'Debug message' in content
            assert 'Info message' in content
            assert 'Warning message' in content
            assert 'Error message' in content
            assert 'Critical message' in content
            assert logger_name in content
            assert 'DEBUG' in content
            assert 'INFO' in content
            assert 'WARNING' in content
            assert 'ERROR' in content
            assert 'CRITICAL' in content

        logger.close()

    def test_logger_format(self, temp_log_file, cleanup_logger):
        """测试日志格式"""
        logger_name = f'TestLogger_{int(time.time() * 1000000)}'
        logger = Logger(
            name=logger_name,
            log_file=temp_log_file,
            level='INFO'
        )
        cleanup_logger.append(logger)

        logger.info('Test message')

        # 强制刷新缓冲区
        for handler in logger.logger.handlers:
            handler.flush()

        # 验证日志格式: %(asctime)s - %(name)s - %(levelname)s - %(message)s
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # 格式应包含:时间戳 - 名称 - 级别 - 消息
            parts = content.split(' - ')
            assert len(parts) >= 4
            assert logger_name in content
            assert 'INFO' in content
            assert 'Test message' in content

        logger.close()

    def test_logger_file_rotation(self, cleanup_logger):
        """测试日志文件轮转"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, 'test_rotation.log')
            logger_name = f'TestLogger_{int(time.time() * 1000000)}'

            # 创建小容量日志器以便测试轮转
            logger = Logger(
                name=logger_name,
                log_file=log_file,
                level='INFO',
                max_size_mb=0.001,  # 1KB
                backup_count=3
            )
            cleanup_logger.append(logger)

            # 写入大量日志触发轮转
            for i in range(100):
                logger.info(f'Test message {i} ' + 'x' * 100)

            # 强制刷新缓冲区
            for handler in logger.logger.handlers:
                handler.flush()

            # 验证日志文件存在
            assert os.path.exists(log_file)

            # 检查是否有备份文件
            log_files = list(Path(tmpdir).glob('test_rotation.log*'))
            # 应该有主日志文件 + 至少一个备份文件
            assert len(log_files) >= 2

            logger.close()

    def test_logger_without_file(self, cleanup_logger):
        """测试不使用文件的日志器"""
        logger_name = f'TestLogger_{int(time.time() * 1000000)}'
        logger = Logger(name=logger_name, log_file=None, level='INFO')
        cleanup_logger.append(logger)

        # 验证只有控制台处理器
        assert len(logger.logger.handlers) == 1
        assert isinstance(logger.logger.handlers[0], logging.StreamHandler)

        logger.close()

    def test_logger_creates_log_directory(self, cleanup_logger):
        """测试日志器自动创建日志目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = os.path.join(tmpdir, 'nested', 'log', 'dir')
            log_file = os.path.join(log_dir, 'test.log')
            logger_name = f'TestLogger_{int(time.time() * 1000000)}'

            logger = Logger(
                name=logger_name,
                log_file=log_file,
                level='INFO'
            )
            cleanup_logger.append(logger)

            logger.info('Test message')

            # 强制刷新缓冲区
            for handler in logger.logger.handlers:
                handler.flush()

            # 验证目录和文件都被创建
            assert os.path.exists(log_dir)
            assert os.path.exists(log_file)

            logger.close()

    def test_logger_exception_logging(self, temp_log_file, cleanup_logger):
        """测试异常日志记录"""
        logger_name = f'TestLogger_{int(time.time() * 1000000)}'
        logger = Logger(
            name=logger_name,
            log_file=temp_log_file,
            level='DEBUG'
        )
        cleanup_logger.append(logger)

        # 记录异常信息
        try:
            raise ValueError('Test exception')
        except ValueError:
            logger.exception('An error occurred')

        # 强制刷新缓冲区
        for handler in logger.logger.handlers:
            handler.flush()

        # 验证异常信息和堆栈跟踪被记录
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'An error occurred' in content
            assert 'ValueError: Test exception' in content
            assert 'Traceback' in content

        logger.close()

    def test_logger_dual_output(self, temp_log_file, cleanup_logger):
        """测试控制台和文件双输出"""
        logger_name = f'TestLogger_{int(time.time() * 1000000)}'
        logger = Logger(
            name=logger_name,
            log_file=temp_log_file,
            level='INFO'
        )
        cleanup_logger.append(logger)

        # 验证有两个处理器:控制台 + 文件
        assert len(logger.logger.handlers) == 2

        handler_types = [type(h).__name__ for h in logger.logger.handlers]
        assert 'StreamHandler' in handler_types
        assert 'RotatingFileHandler' in handler_types

        logger.close()

    def test_logger_level_filtering(self, temp_log_file, cleanup_logger):
        """测试日志级别过滤"""
        logger_name = f'TestLogger_{int(time.time() * 1000000)}'

        # 创建 INFO 级别的日志器
        logger = Logger(
            name=logger_name,
            log_file=temp_log_file,
            level='INFO'
        )
        cleanup_logger.append(logger)

        # 写入不同级别的日志
        logger.debug('Debug message')  # 不应该记录
        logger.info('Info message')  # 应该记录
        logger.warning('Warning message')  # 应该记录

        # 强制刷新缓冲区
        for handler in logger.logger.handlers:
            handler.flush()

        # 验证日志内容
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # DEBUG 消息不应该出现(因为级别是 INFO)
            assert 'Debug message' not in content
            # INFO 和 WARNING 消息应该出现
            assert 'Info message' in content
            assert 'Warning message' in content

        logger.close()

    def test_logger_rotating_file_handler_config(self, temp_log_file, cleanup_logger):
        """测试 RotatingFileHandler 配置"""
        logger_name = f'TestLogger_{int(time.time() * 1000000)}'
        logger = Logger(
            name=logger_name,
            log_file=temp_log_file,
            level='INFO',
            max_size_mb=10,
            backup_count=5
        )
        cleanup_logger.append(logger)

        # 找到 RotatingFileHandler
        rotating_handler = None
        for handler in logger.logger.handlers:
            if handler.__class__.__name__ == 'RotatingFileHandler':
                rotating_handler = handler
                break

        assert rotating_handler is not None
        # 验证配置
        assert rotating_handler.maxBytes == 10 * 1024 * 1024  # 10MB
        assert rotating_handler.backupCount == 5

        logger.close()


class TestGlobalLogger:
    """测试全局日志器功能"""

    def test_get_logger_singleton(self):
        """测试获取全局日志实例是单例"""
        # 重置全局日志器
        import src.utils.logger as logger_module
        logger_module._global_logger = None

        # 获取全局日志器
        logger1 = get_logger()
        logger2 = get_logger()

        # 验证返回的是同一个实例
        assert logger1 is logger2

    def test_init_logger(self, temp_log_file):
        """测试初始化全局日志实例"""
        # 重置全局日志器
        import src.utils.logger as logger_module
        logger_module._global_logger = None

        # 初始化全局日志器
        logger = init_logger(
            name='CustomLogger',
            log_file=temp_log_file,
            level='DEBUG',
            max_size_mb=5,
            backup_count=3
        )

        # 验证配置
        assert logger.name == 'CustomLogger'
        assert logger.level == 'DEBUG'
        assert logger.max_size_mb == 5
        assert logger.backup_count == 3

        # 验证 get_logger 返回新初始化的实例
        logger2 = get_logger()
        assert logger is logger2

        # 清理
        logger.close()


class TestLoggerIntegration:
    """测试日志系统集成场景"""

    def test_concurrent_logging(self, temp_log_file, cleanup_logger):
        """测试并发日志记录"""
        logger_name = f'TestLogger_{int(time.time() * 1000000)}'
        logger = Logger(
            name=logger_name,
            log_file=temp_log_file,
            level='INFO'
        )
        cleanup_logger.append(logger)

        # 模拟多次日志记录
        for i in range(50):
            logger.info(f'Message {i}')
            logger.warning(f'Warning {i}')
            logger.error(f'Error {i}')

        # 强制刷新缓冲区
        for handler in logger.logger.handlers:
            handler.flush()

        # 验证所有消息都被记录
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # 检查部分消息存在
            assert 'Message 0' in content
            assert 'Message 49' in content
            assert 'Warning 25' in content
            assert 'Error 40' in content

        logger.close()

    def test_logger_with_special_characters(self, temp_log_file, cleanup_logger):
        """测试特殊字符处理"""
        logger_name = f'TestLogger_{int(time.time() * 1000000)}'
        logger = Logger(
            name=logger_name,
            log_file=temp_log_file,
            level='INFO'
        )
        cleanup_logger.append(logger)

        # 记录包含特殊字符的消息
        special_messages = [
            '中文消息',
            'Special chars: \\n\\t\\\\',
            'Unicode: 中文'
        ]

        for msg in special_messages:
            logger.info(msg)

        # 强制刷新缓冲区
        for handler in logger.logger.handlers:
            handler.flush()

        # 验证特殊字符被正确记录
        with open(temp_log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert '中文消息' in content
            assert 'Special chars' in content

        logger.close()

    def test_logger_multiple_instances(self, cleanup_logger):
        """测试多个日志器实例"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file1 = os.path.join(tmpdir, 'logger1.log')
            log_file2 = os.path.join(tmpdir, 'logger2.log')

            # 创建两个独立的日志器
            logger1 = Logger(
                name=f'Logger1_{int(time.time() * 1000000)}',
                log_file=log_file1,
                level='INFO'
            )
            logger2 = Logger(
                name=f'Logger2_{int(time.time() * 1000000)}',
                log_file=log_file2,
                level='DEBUG'
            )
            cleanup_logger.extend([logger1, logger2])

            # 分别写入日志
            logger1.info('Logger1 message')
            logger2.debug('Logger2 message')

            # 强制刷新缓冲区
            for handler in logger1.logger.handlers:
                handler.flush()
            for handler in logger2.logger.handlers:
                handler.flush()

            # 验证日志被写入各自的文件
            with open(log_file1, 'r', encoding='utf-8') as f:
                assert 'Logger1 message' in f.read()

            with open(log_file2, 'r', encoding='utf-8') as f:
                assert 'Logger2 message' in f.read()

            logger1.close()
            logger2.close()
