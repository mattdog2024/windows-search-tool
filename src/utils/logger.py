"""
日志模块

提供统一的日志记录功能
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from typing import Optional
from pathlib import Path


class Logger:
    """
    日志管理器

    封装 Python logging 模块，提供便捷的日志记录接口
    """

    def __init__(
        self,
        name: str = 'WindowsSearchTool',
        log_file: Optional[str] = None,
        level: str = 'INFO',
        max_size_mb: int = 10,
        backup_count: int = 5
    ):
        """
        初始化日志管理器

        Args:
            name: 日志器名称
            log_file: 日志文件路径
            level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            max_size_mb: 单个日志文件最大大小（MB）
            backup_count: 保留的备份文件数量
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

        # 存储配置用于测试验证
        self.name = name
        self.level = level.upper()
        self.max_size_mb = max_size_mb
        self.backup_count = backup_count
        self.log_file = log_file

        # 避免重复添加处理器
        if not self.logger.handlers:
            # 设置日志格式(按照任务要求的格式)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

            # 控制台处理器(支持所有配置的日志级别)
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, level.upper()))
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

            # 文件处理器
            if log_file:
                # 确保日志目录存在
                log_dir = os.path.dirname(log_file)
                if log_dir:
                    os.makedirs(log_dir, exist_ok=True)

                file_handler = RotatingFileHandler(
                    log_file,
                    maxBytes=max_size_mb * 1024 * 1024,
                    backupCount=backup_count,
                    encoding='utf-8'
                )
                file_handler.setLevel(getattr(logging, level.upper()))
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)

    def debug(self, message: str, *args, **kwargs):
        """记录调试信息"""
        self.logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        """记录一般信息"""
        self.logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        """记录警告信息"""
        self.logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        """记录错误信息"""
        self.logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs):
        """记录严重错误信息"""
        self.logger.critical(message, *args, **kwargs)

    def exception(self, message: str, *args, **kwargs):
        """记录异常信息（包含堆栈跟踪）"""
        self.logger.exception(message, *args, **kwargs)

    def close(self):
        """关闭所有日志处理器"""
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)


# 全局日志实例
_global_logger: Optional[Logger] = None


def get_logger() -> Logger:
    """
    获取全局日志实例

    Returns:
        日志管理器
    """
    global _global_logger
    if _global_logger is None:
        # 使用默认配置 - 按照任务要求使用 APPDATA 路径
        appdata = os.getenv('APPDATA')
        if appdata:
            log_dir = Path(appdata) / 'WindowsSearchTool' / 'logs'
            log_file = str(log_dir / 'app.log')
        else:
            # 后备方案:使用项目相对路径
            project_root = Path(__file__).parent.parent.parent
            log_file = str(project_root / 'logs' / 'app.log')
        _global_logger = Logger(log_file=log_file)
    return _global_logger


def init_logger(
    name: str = 'WindowsSearchTool',
    log_file: Optional[str] = None,
    level: str = 'INFO',
    max_size_mb: int = 10,
    backup_count: int = 5
) -> Logger:
    """
    初始化全局日志实例

    Args:
        name: 日志器名称
        log_file: 日志文件路径
        level: 日志级别
        max_size_mb: 单个日志文件最大大小（MB）
        backup_count: 保留的备份文件数量

    Returns:
        日志管理器
    """
    global _global_logger
    _global_logger = Logger(
        name=name,
        log_file=log_file,
        level=level,
        max_size_mb=max_size_mb,
        backup_count=backup_count
    )
    return _global_logger


def init_logger_from_config(config: 'Config') -> Logger:
    """
    从配置初始化日志

    Args:
        config: 配置管理器

    Returns:
        日志管理器
    """
    project_root = Path(__file__).parent.parent.parent
    log_file = str(project_root / config.get('logging.file', 'logs/app.log'))

    return init_logger(
        name=config.get('app.name', 'WindowsSearchTool'),
        log_file=log_file,
        level=config.get('logging.level', 'INFO'),
        max_size_mb=config.get('logging.max_size_mb', 10),
        backup_count=config.get('logging.backup_count', 5)
    )
