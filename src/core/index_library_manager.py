"""
索引库管理器模块

管理多个索引库，支持创建、删除、启用/禁用索引库。
"""

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class IndexLibrary:
    """索引库信息"""
    name: str
    db_path: str
    created: str
    last_used: str
    doc_count: int = 0
    size_bytes: int = 0
    enabled: bool = True
    color: str = "#4CAF50"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'db_path': self.db_path,
            'created': self.created,
            'last_used': self.last_used,
            'doc_count': self.doc_count,
            'size_bytes': self.size_bytes,
            'enabled': self.enabled,
            'color': self.color
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'IndexLibrary':
        """从字典创建"""
        return IndexLibrary(
            name=data['name'],
            db_path=data['db_path'],
            created=data.get('created', datetime.now().isoformat()),
            last_used=data.get('last_used', datetime.now().isoformat()),
            doc_count=data.get('doc_count', 0),
            size_bytes=data.get('size_bytes', 0),
            enabled=data.get('enabled', True),
            color=data.get('color', '#4CAF50')
        )


class IndexLibraryManager:
    """
    索引库管理器

    管理多个索引库，支持：
    - 添加/删除索引库
    - 启用/禁用索引库
    - 获取启用的索引库列表
    - 更新索引库统计信息
    """

    def __init__(self, config_file: str = 'indexes.json'):
        """
        初始化索引库管理器

        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.libraries: List[IndexLibrary] = []
        self.default_library: Optional[str] = None
        self._load_libraries()

        logger.info(f"IndexLibraryManager initialized with {len(self.libraries)} libraries")

    def _load_libraries(self):
        """从配置文件加载索引库列表"""
        if not os.path.exists(self.config_file):
            logger.info(f"配置文件不存在，创建默认配置: {self.config_file}")
            # 创建默认索引库（当前的 search_index.db）
            default_lib = IndexLibrary(
                name="默认索引库",
                db_path="search_index.db",
                created=datetime.now().isoformat(),
                last_used=datetime.now().isoformat(),
                enabled=True
            )
            self.libraries = [default_lib]
            self.default_library = "默认索引库"
            self._save_libraries()
            return

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.default_library = data.get('default_library')
            self.libraries = [
                IndexLibrary.from_dict(lib_data)
                for lib_data in data.get('libraries', [])
            ]

            logger.info(f"加载了 {len(self.libraries)} 个索引库")

        except Exception as e:
            logger.error(f"加载索引库配置失败: {e}")
            self.libraries = []

    def _save_libraries(self):
        """保存索引库列表到配置文件"""
        try:
            data = {
                'version': '1.0',
                'default_library': self.default_library,
                'libraries': [lib.to_dict() for lib in self.libraries]
            }

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"保存了 {len(self.libraries)} 个索引库配置")

        except Exception as e:
            logger.error(f"保存索引库配置失败: {e}")

    def add_library(
        self,
        name: str,
        db_path: str,
        set_as_default: bool = False
    ) -> IndexLibrary:
        """
        添加索引库

        Args:
            name: 索引库名称
            db_path: 数据库文件路径
            set_as_default: 是否设为默认索引库

        Returns:
            创建的索引库对象
        """
        # 检查名称是否已存在
        if self.get_library(name):
            raise ValueError(f"索引库名称已存在: {name}")

        # 检查路径是否已存在
        for lib in self.libraries:
            if lib.db_path == db_path:
                raise ValueError(f"数据库路径已被使用: {db_path}")

        library = IndexLibrary(
            name=name,
            db_path=db_path,
            created=datetime.now().isoformat(),
            last_used=datetime.now().isoformat(),
            enabled=True
        )

        self.libraries.append(library)

        if set_as_default or not self.default_library:
            self.default_library = name

        self._save_libraries()
        logger.info(f"添加索引库: {name} -> {db_path}")

        return library

    def remove_library(self, name: str) -> bool:
        """
        删除索引库

        Args:
            name: 索引库名称

        Returns:
            是否删除成功
        """
        library = self.get_library(name)
        if not library:
            logger.warning(f"索引库不存在: {name}")
            return False

        self.libraries.remove(library)

        # 如果删除的是默认库，选择第一个作为默认
        if self.default_library == name:
            self.default_library = self.libraries[0].name if self.libraries else None

        self._save_libraries()
        logger.info(f"删除索引库: {name}")

        return True

    def get_library(self, name: str) -> Optional[IndexLibrary]:
        """
        获取索引库信息

        Args:
            name: 索引库名称

        Returns:
            索引库对象，如果不存在返回 None
        """
        for library in self.libraries:
            if library.name == name:
                return library
        return None

    def get_enabled_libraries(self) -> List[IndexLibrary]:
        """
        获取已启用的索引库列表

        Returns:
            已启用的索引库列表
        """
        return [lib for lib in self.libraries if lib.enabled]

    def set_library_enabled(self, name: str, enabled: bool):
        """
        设置索引库启用状态

        Args:
            name: 索引库名称
            enabled: 是否启用
        """
        library = self.get_library(name)
        if library:
            library.enabled = enabled
            self._save_libraries()
            logger.info(f"设置索引库 {name} 启用状态: {enabled}")

    def update_library_stats(self, name: str, doc_count: int = None, size_bytes: int = None):
        """
        更新索引库统计信息

        Args:
            name: 索引库名称
            doc_count: 文档数量
            size_bytes: 数据库大小（字节）
        """
        library = self.get_library(name)
        if library:
            if doc_count is not None:
                library.doc_count = doc_count
            if size_bytes is not None:
                library.size_bytes = size_bytes
            library.last_used = datetime.now().isoformat()
            self._save_libraries()
            logger.debug(f"更新索引库统计: {name}, docs={doc_count}, size={size_bytes}")

    def get_all_libraries(self) -> List[IndexLibrary]:
        """获取所有索引库"""
        return self.libraries

    def set_default_library(self, name: str):
        """设置默认索引库"""
        if self.get_library(name):
            self.default_library = name
            self._save_libraries()
            logger.info(f"设置默认索引库: {name}")

    def get_default_library(self) -> Optional[IndexLibrary]:
        """获取默认索引库"""
        if self.default_library:
            return self.get_library(self.default_library)
        return self.libraries[0] if self.libraries else None

    def enable_all(self):
        """启用所有索引库"""
        for library in self.libraries:
            library.enabled = True
        self._save_libraries()
        logger.info("启用所有索引库")

    def disable_all(self):
        """禁用所有索引库"""
        for library in self.libraries:
            library.enabled = False
        self._save_libraries()
        logger.info("禁用所有索引库")

    def get_selection_summary(self) -> str:
        """
        获取当前选择的摘要文本

        Returns:
            摘要文本，例如: "全部索引库 (3个)" 或 "默认索引库" 或 "2个索引库"
        """
        enabled = self.get_enabled_libraries()
        total = len(self.libraries)

        if len(enabled) == 0:
            return "未选择索引库"
        elif len(enabled) == total:
            return f"全部索引库 ({total}个)"
        elif len(enabled) == 1:
            return enabled[0].name
        else:
            return f"{len(enabled)} 个索引库"
