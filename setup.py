"""
Windows Search Tool 安装脚本
"""

from setuptools import setup, find_packages
import os

# 读取 README
def read_readme():
    with open('README.md', 'r', encoding='utf-8') as f:
        return f.read()

# 读取依赖
def read_requirements():
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='windows-search-tool',
    version='0.1.0',
    author='Windows Search Tool Team',
    author_email='',
    description='智能文件内容索引和搜索系统',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    url='',
    packages=find_packages(exclude=['tests*', 'docs*']),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Desktop Environment :: File Managers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: Microsoft :: Windows',
    ],
    python_requires='>=3.11',
    install_requires=read_requirements(),
    entry_points={
        'console_scripts': [
            'windows-search-tool=src.main:main',
        ],
    },
    include_package_data=True,
    package_data={
        '': ['resources/**/*'],
    },
)
