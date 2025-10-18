# -*- mode: python ; coding: utf-8 -*-
"""
Windows Search Tool - 便携版打包配置
支持 Windows 10 和 Windows 7
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# 项目根目录
project_root = os.path.abspath(SPECPATH)

# 收集所有数据文件
datas = []

# 1. Tesseract 便携版 (如果存在)
tesseract_dir = os.path.join(project_root, 'portable', 'tesseract')
if os.path.exists(tesseract_dir):
    datas += [(tesseract_dir, 'portable/tesseract')]

# 收集隐藏导入
hiddenimports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'pdfplumber',
    'pytesseract',
    'PIL',
    'PIL._imaging',
    'openpyxl',
    'python-docx',
    'python-pptx',
    'lxml',
    'chardet',
]

# 添加所有解析器
hiddenimports += collect_submodules('src.parsers')
hiddenimports += collect_submodules('openpyxl')
hiddenimports += collect_submodules('pptx')
hiddenimports += collect_submodules('docx')

a = Analysis(
    [os.path.join(project_root, 'src', 'main.py')],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'IPython',
        'jupyter',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='WindowsSearchTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加图标文件
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WindowsSearchTool',
)
