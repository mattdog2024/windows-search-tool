"""
配置管理器单元测试
"""

import json
import os
import tempfile
from pathlib import Path
import pytest
from src.utils.config import ConfigManager


class TestConfigManager:
    """ConfigManager 类单元测试"""

    def test_init_creates_config_with_defaults(self, monkeypatch):
        """测试初始化时使用默认配置"""
        # 使用临时目录
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv('APPDATA', tmpdir)

            config_manager = ConfigManager()

            # 验证配置目录和文件路径
            assert config_manager.config_dir == Path(tmpdir) / 'WindowsSearchTool'
            assert config_manager.config_file == Path(tmpdir) / 'WindowsSearchTool' / 'config.json'

            # 验证默认配置已加载
            assert config_manager.config == ConfigManager.DEFAULT_CONFIG

    def test_save_creates_directory_and_file(self, monkeypatch):
        """测试保存配置时自动创建目录和文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv('APPDATA', tmpdir)

            config_manager = ConfigManager()
            config_manager.save()

            # 验证目录已创建
            assert config_manager.config_dir.exists()
            assert config_manager.config_dir.is_dir()

            # 验证文件已创建
            assert config_manager.config_file.exists()
            assert config_manager.config_file.is_file()

    def test_save_and_load_config(self, monkeypatch):
        """测试保存和加载配置"""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv('APPDATA', tmpdir)

            # 创建并保存配置
            config_manager1 = ConfigManager()
            config_manager1.set('app.name', 'Test App')
            config_manager1.set('app.version', '2.0.0')
            config_manager1.save()

            # 重新加载配置
            config_manager2 = ConfigManager()

            # 验证配置已正确加载
            assert config_manager2.get('app.name') == 'Test App'
            assert config_manager2.get('app.version') == '2.0.0'
            # 验证其他默认值仍然存在
            assert config_manager2.get('app.theme') == 'light'

    def test_get_with_dot_notation(self, monkeypatch):
        """测试使用点分隔符获取配置值"""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv('APPDATA', tmpdir)

            config_manager = ConfigManager()

            # 测试一级键
            assert config_manager.get('app') == ConfigManager.DEFAULT_CONFIG['app']

            # 测试二级键
            assert config_manager.get('app.name') == 'Windows Search Tool'
            assert config_manager.get('app.version') == '1.0.0'
            assert config_manager.get('database.cache_size_mb') == 64

            # 测试不存在的键
            assert config_manager.get('nonexistent.key') is None
            assert config_manager.get('nonexistent.key', 'default') == 'default'

    def test_set_with_dot_notation(self, monkeypatch):
        """测试使用点分隔符设置配置值"""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv('APPDATA', tmpdir)

            config_manager = ConfigManager()

            # 测试设置已存在的键
            config_manager.set('app.name', 'New App Name')
            assert config_manager.get('app.name') == 'New App Name'

            # 测试设置嵌套的新键
            config_manager.set('new.nested.key', 'value')
            assert config_manager.get('new.nested.key') == 'value'

            # 测试设置列表值
            config_manager.set('indexing.excluded_extensions', ['.txt', '.log'])
            assert config_manager.get('indexing.excluded_extensions') == ['.txt', '.log']

    def test_merge_config(self, monkeypatch):
        """测试配置合并功能"""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv('APPDATA', tmpdir)

            config_manager = ConfigManager()

            # 创建部分用户配置
            user_config = {
                'app': {
                    'name': 'Custom App',
                    'version': '2.0.0'
                    # theme 未设置,应使用默认值
                },
                'new_section': {
                    'key': 'value'
                }
            }

            merged = config_manager._merge_config(ConfigManager.DEFAULT_CONFIG, user_config)

            # 验证合并后的配置
            assert merged['app']['name'] == 'Custom App'
            assert merged['app']['version'] == '2.0.0'
            assert merged['app']['theme'] == 'light'  # 默认值保留
            assert merged['new_section']['key'] == 'value'  # 新section添加
            assert 'database' in merged  # 默认section保留

    def test_load_config_with_user_config(self, monkeypatch):
        """测试加载用户配置文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv('APPDATA', tmpdir)

            # 手动创建用户配置文件
            config_dir = Path(tmpdir) / 'WindowsSearchTool'
            config_dir.mkdir(parents=True, exist_ok=True)
            config_file = config_dir / 'config.json'

            user_config = {
                'app': {
                    'name': 'User App',
                    'theme': 'dark'
                }
            }

            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(user_config, f)

            # 初始化ConfigManager
            config_manager = ConfigManager()

            # 验证用户配置已加载并合并
            assert config_manager.get('app.name') == 'User App'
            assert config_manager.get('app.theme') == 'dark'
            assert config_manager.get('app.version') == '1.0.0'  # 默认值保留

    def test_load_config_with_invalid_json(self, monkeypatch):
        """测试加载无效JSON文件时的错误处理"""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv('APPDATA', tmpdir)

            # 创建无效的JSON文件
            config_dir = Path(tmpdir) / 'WindowsSearchTool'
            config_dir.mkdir(parents=True, exist_ok=True)
            config_file = config_dir / 'config.json'

            with open(config_file, 'w', encoding='utf-8') as f:
                f.write('{ invalid json }')

            # 初始化ConfigManager,应回退到默认配置
            config_manager = ConfigManager()

            # 验证使用了默认配置
            assert config_manager.config == ConfigManager.DEFAULT_CONFIG

    def test_set_creates_nested_keys(self, monkeypatch):
        """测试set方法能够创建嵌套键"""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv('APPDATA', tmpdir)

            config_manager = ConfigManager()

            # 设置深层嵌套的新键
            config_manager.set('level1.level2.level3.key', 'deep_value')

            # 验证键已创建
            assert config_manager.get('level1.level2.level3.key') == 'deep_value'
            assert isinstance(config_manager.config['level1'], dict)
            assert isinstance(config_manager.config['level1']['level2'], dict)

    def test_default_config_structure(self, monkeypatch):
        """测试默认配置结构的完整性"""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv('APPDATA', tmpdir)

            config_manager = ConfigManager()
            config = config_manager.config

        # 验证所有必需的顶级键存在
        assert 'app' in config
        assert 'database' in config
        assert 'indexing' in config
        assert 'search' in config
        assert 'ocr' in config

        # 验证app配置
        assert config['app']['name'] == 'Windows Search Tool'
        assert config['app']['version'] == '1.0.0'
        assert config['app']['theme'] == 'light'

        # 验证database配置
        assert config['database']['cache_size_mb'] == 64
        assert config['database']['page_size'] == 4096
        assert config['database']['wal_mode'] is True

        # 验证indexing配置
        assert config['indexing']['parallel_workers'] == 4
        assert config['indexing']['batch_size'] == 100
        assert isinstance(config['indexing']['excluded_extensions'], list)
        assert isinstance(config['indexing']['excluded_paths'], list)

        # 验证search配置
        assert config['search']['results_per_page'] == 20
        assert config['search']['snippet_length'] == 100
        assert config['search']['cache_size'] == 100

        # 验证ocr配置
        assert isinstance(config['ocr']['tesseract_path'], str)
        assert isinstance(config['ocr']['languages'], list)
        assert config['ocr']['confidence_threshold'] == 60

    def test_config_file_encoding(self, monkeypatch):
        """测试配置文件使用UTF-8编码"""
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setenv('APPDATA', tmpdir)

            config_manager = ConfigManager()
            config_manager.set('app.name', '中文应用名称')
            config_manager.save()

            # 读取文件内容验证编码
            with open(config_manager.config_file, 'r', encoding='utf-8') as f:
                content = json.load(f)

            assert content['app']['name'] == '中文应用名称'
