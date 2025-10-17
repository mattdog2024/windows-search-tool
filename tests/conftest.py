"""
Pytest 配置文件

提供全局 fixtures 和配置
"""

import pytest
import tempfile
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def temp_db():
    """
    创建临时数据库用于测试

    Yields:
        tuple: (db_path, DBManager 实例)
    """
    from src.data.db_manager import DBManager

    # 创建临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
        db_path = f.name

    # 创建数据库管理器 (自动初始化)
    db = DBManager(db_path)

    yield db_path, db

    # 清理
    db.close()
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except PermissionError:
            pass  # Windows 可能会锁定文件


@pytest.fixture
def db_manager(temp_db):
    """
    返回 DBManager 实例

    Yields:
        DBManager: 数据库管理器实例
    """
    db_path, db = temp_db
    yield db


@pytest.fixture
def search_engine(db_manager):
    """
    创建 SearchEngine 实例

    Args:
        db_manager: DBManager fixture

    Returns:
        SearchEngine: 搜索引擎实例
    """
    from src.core.search_engine import SearchEngine
    return SearchEngine(db_manager=db_manager)
