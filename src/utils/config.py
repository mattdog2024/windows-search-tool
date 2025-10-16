"""
配置管理模块

管理应用程序配置,支持默认配置和用户配置合并
"""

import json
import os
import copy
from typing import Any, Dict
from pathlib import Path


class ConfigManager:
    """
    配置管理器

    支持从 JSON 文件加载配置,提供配置的读写和合并功能。
    配置文件存储在 %APPDATA%/WindowsSearchTool/config.json
    """

    DEFAULT_CONFIG = {
        'app': {
            'name': 'Windows Search Tool',
            'version': '1.0.0',
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
            'excluded_extensions': ['.exe', '.dll', '.sys'],
            'excluded_paths': ['C:\\Windows', 'C:\\Program Files']
        },
        'search': {
            'results_per_page': 20,
            'snippet_length': 100,
            'cache_size': 100
        },
        'ocr': {
            'tesseract_path': 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe',
            'languages': ['chi_sim', 'eng'],
            'confidence_threshold': 60
        }
    }

    def __init__(self):
        """
        初始化配置管理器

        配置文件路径: %APPDATA%/WindowsSearchTool/config.json
        """
        self.config_dir = Path(os.getenv('APPDATA')) / 'WindowsSearchTool'
        self.config_file = self.config_dir / 'config.json'
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """
        加载配置

        如果用户配置文件存在,将其与默认配置合并;否则使用默认配置。

        Returns:
            合并后的配置字典
        """
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    return self._merge_config(copy.deepcopy(self.DEFAULT_CONFIG), user_config)
            except Exception as e:
                print(f'加载用户配置失败: {e},使用默认配置')
                return copy.deepcopy(self.DEFAULT_CONFIG)
        return copy.deepcopy(self.DEFAULT_CONFIG)

    def _merge_config(self, default: Dict, user: Dict) -> Dict:
        """
        递归合并配置

        用户配置会覆盖默认配置,但保留默认配置中用户未设置的值。

        Args:
            default: 默认配置字典
            user: 用户配置字典

        Returns:
            合并后的配置字典
        """
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        return result

    def save(self):
        """
        保存配置到文件

        配置文件将保存到 %APPDATA%/WindowsSearchTool/config.json
        如果目录不存在,将自动创建。
        """
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    def get(self, key: str, default=None) -> Any:
        """
        获取配置值(支持点分隔符,如 'app.name')

        Args:
            key: 配置键,支持点分隔的路径(例如 'app.name')
            default: 如果键不存在返回的默认值

        Returns:
            配置值或默认值
        """
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any):
        """
        设置配置值(支持点分隔符)

        Args:
            key: 配置键,支持点分隔的路径(例如 'app.name')
            value: 要设置的值
        """
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
