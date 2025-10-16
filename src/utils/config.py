"""
配置管理模块

管理应用程序配置
"""

import json
import os
from typing import Any, Dict, Optional
from pathlib import Path


class Config:
    """
    配置管理器

    支持从 JSON 文件加载配置，并提供访问接口
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径，如果为 None 则使用默认路径
        """
        self._config: Dict[str, Any] = {}
        self._config_path = config_path or self._get_default_config_path()
        self._load_default_config()

        # 如果配置文件存在，加载它
        if os.path.exists(self._config_path):
            self.load(self._config_path)

    def _get_default_config_path(self) -> str:
        """获取默认配置文件路径"""
        # 使用项目根目录下的 config.json
        project_root = Path(__file__).parent.parent.parent
        return str(project_root / 'resources' / 'config' / 'config.json')

    def _load_default_config(self):
        """加载默认配置"""
        self._config = {
            'app': {
                'name': 'Windows Search Tool',
                'version': '0.1.0',
                'theme': 'light'
            },
            'database': {
                'cache_size_mb': 64,
                'page_size': 4096,
                'wal_mode': True
            },
            'indexing': {
                'parallel_workers': 4,
                'batch_size': 100,
                'excluded_extensions': ['.exe', '.dll', '.sys', '.tmp'],
                'excluded_paths': ['C:\\Windows', 'C:\\Program Files']
            },
            'search': {
                'results_per_page': 20,
                'snippet_length': 100,
                'cache_size': 100
            },
            'ai': {
                'provider': 'deepseek',
                'api_endpoint': 'https://api.deepseek.com/v1',
                'model': 'deepseek-chat',
                'timeout_seconds': 10,
                'max_retries': 3,
                'enabled': False
            },
            'ocr': {
                'tesseract_path': 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe',
                'languages': ['chi_sim', 'eng'],
                'confidence_threshold': 60
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/app.log',
                'max_size_mb': 10,
                'backup_count': 5
            }
        }

    def load(self, config_path: str) -> bool:
        """
        从文件加载配置

        Args:
            config_path: 配置文件路径

        Returns:
            是否加载成功
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)

            # 合并配置（保留默认值）
            self._merge_config(loaded_config)
            self._config_path = config_path
            return True
        except Exception as e:
            print(f'加载配置文件失败: {e}')
            return False

    def save(self, config_path: Optional[str] = None) -> bool:
        """
        保存配置到文件

        Args:
            config_path: 配置文件路径，如果为 None 则使用初始化时的路径

        Returns:
            是否保存成功
        """
        save_path = config_path or self._config_path

        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f'保存配置文件失败: {e}')
            return False

    def _merge_config(self, new_config: Dict[str, Any]):
        """
        合并配置（递归）

        Args:
            new_config: 新配置
        """
        def merge_dict(base: Dict, updates: Dict):
            for key, value in updates.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    merge_dict(base[key], value)
                else:
                    base[key] = value

        merge_dict(self._config, new_config)

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值（支持点号分隔的路径）

        Args:
            key: 配置键，支持 'app.name' 这样的路径
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """
        设置配置值（支持点号分隔的路径）

        Args:
            key: 配置键
            value: 配置值
        """
        keys = key.split('.')
        config = self._config

        # 导航到最后一个键的父级
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # 设置值
        config[keys[-1]] = value

    def get_all(self) -> Dict[str, Any]:
        """
        获取所有配置

        Returns:
            配置字典
        """
        return self._config.copy()


# 全局配置实例
_global_config: Optional[Config] = None


def get_config() -> Config:
    """
    获取全局配置实例

    Returns:
        配置管理器
    """
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config


def init_config(config_path: Optional[str] = None) -> Config:
    """
    初始化全局配置

    Args:
        config_path: 配置文件路径

    Returns:
        配置管理器
    """
    global _global_config
    _global_config = Config(config_path)
    return _global_config
