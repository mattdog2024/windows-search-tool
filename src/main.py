"""
Windows Search Tool - 主程序入口

智能文件内容索引和搜索系统
"""

import sys
import multiprocessing
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.config import init_config
from src.utils.logger import init_logger_from_config


def init_application():
    """初始化应用程序"""
    # 初始化配置
    config = init_config()

    # 初始化日志
    logger = init_logger_from_config(config)
    logger.info('=' * 50)
    logger.info('Windows Search Tool 启动中...')
    logger.info(f'版本: {config.get("app.version", "0.1.0")}')
    logger.info('=' * 50)

    return config, logger


def main():
    """主函数"""
    try:
        config, logger = init_application()

        logger.info('应用程序初始化完成')
        logger.info('核心功能已就绪:')
        logger.info('  ✓ 文档解析框架')
        logger.info('  ✓ 数据库和索引管理')
        logger.info('  ✓ 搜索引擎')
        logger.info('  ✓ AI 语义搜索')
        logger.info('  ✓ 文档智能摘要')
        logger.info('  ✓ GUI 界面')

        # 启动 GUI 应用
        logger.info('\n启动图形界面...')

        from src.ui.app_controller import AppController

        # 获取数据库路径
        db_path = config.get('database.path', 'search_index.db')

        # 创建并运行应用控制器
        app = AppController(db_path=db_path)
        app.run()

        logger.info('\n应用程序正常退出')

    except KeyboardInterrupt:
        logger.info('\n\n应用程序被用户中断')
    except Exception as e:
        logger.exception(f'应用程序发生错误: {e}')
        return 1

    return 0


if __name__ == '__main__':
    # Windows 下 multiprocessing 需要 freeze_support
    # 防止打包后的可执行文件无限创建进程
    multiprocessing.freeze_support()

    sys.exit(main())
