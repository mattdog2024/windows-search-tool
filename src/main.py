"""
Windows Search Tool - 主程序入口

智能文件内容索引和搜索系统
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import init_config, get_config
from src.utils.logger import init_logger_from_config, get_logger
from src.parsers.base import get_parser_factory
from src.parsers.text_parser import TextParser


def init_application():
    """初始化应用程序"""
    # 初始化配置
    config = init_config()

    # 初始化日志
    logger = init_logger_from_config(config)
    logger.info('=' * 50)
    logger.info('Windows Search Tool 启动中...')
    logger.info(f'版本: {config.get("app.version")}')
    logger.info('=' * 50)

    # 注册解析器
    factory = get_parser_factory()
    text_parser = TextParser()
    factory.register_parser('text', ['.txt', '.md', '.csv', '.log'], text_parser)
    logger.info(f'已注册解析器: {factory.get_parser_names()}')
    logger.info(f'支持的文件类型: {factory.get_supported_extensions()}')

    return config, logger


def main():
    """主函数"""
    try:
        config, logger = init_application()

        logger.info('应用程序初始化完成')
        logger.info('目前处于开发阶段，GUI 界面尚未实现')
        logger.info('核心框架已就绪:')
        logger.info('  ✓ 配置管理模块')
        logger.info('  ✓ 日志模块')
        logger.info('  ✓ 文档解析框架')
        logger.info('  ✓ 文本文件解析器')

        # 演示解析器工厂
        factory = get_parser_factory()
        logger.info(f'\n支持的文件格式:')
        for ext in factory.get_supported_extensions():
            logger.info(f'  - {ext}')

        logger.info('\n下一步开发计划:')
        logger.info('  1. 实现 Office 文档解析器 (Word, Excel, PowerPoint)')
        logger.info('  2. 实现 PDF 解析器和 OCR 功能')
        logger.info('  3. 构建 SQLite FTS5 数据库')
        logger.info('  4. 开发 GUI 界面')

        logger.info('\n按 Ctrl+C 退出...')

        # 保持程序运行
        import time
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info('\n\n应用程序正常退出')
    except Exception as e:
        logger.exception(f'应用程序发生错误: {e}')
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
