# Windows Search Tool - 快速开始指南

## 🎯 项目当前状态

**版本:** 0.1.0 (开发中 - Phase 1 已完成)

### ✅ 已完成的功能

1. **项目基础架构**
   - ✓ 完整的项目目录结构
   - ✓ 项目管理系统 (ccpm)
   - ✓ 配置文件和依赖管理

2. **核心模块**
   - ✓ 配置管理模块 (`src/utils/config.py`)
   - ✓ 日志模块 (`src/utils/logger.py`)
   - ✓ 文档解析框架 (`src/parsers/base.py`)
   - ✓ 文本文件解析器 (`src/parsers/text_parser.py`)

3. **文档**
   - ✓ PRD (产品需求文档)
   - ✓ Epic Stories (史诗故事)
   - ✓ Solution Architecture (解决方案架构)
   - ✓ UX Specification (UX 规格)
   - ✓ User Stories (详细用户故事)

4. **测试**
   - ✓ 单元测试框架
   - ✓ 解析器测试用例

### 📊 项目统计

- **Python 文件:** 14 个
- **文档文件:** 6 个
- **代码行数:** ~1,500 行
- **测试覆盖率:** 目标 90%

---

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目（如果还没有）
cd windows-search-tool

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境 (Windows)
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 运行程序

```bash
# 运行主程序
python src/main.py
```

**预期输出:**
```
==================================================
Windows Search Tool 启动中...
版本: 0.1.0
==================================================
已注册解析器: ['text']
支持的文件类型: ['.txt', '.md', '.csv', '.log']
应用程序初始化完成
目前处于开发阶段，GUI 界面尚未实现
核心框架已就绪:
  ✓ 配置管理模块
  ✓ 日志模块
  ✓ 文档解析框架
  ✓ 文本文件解析器

支持的文件格式:
  - .txt
  - .md
  - .csv
  - .log

下一步开发计划:
  1. 实现 Office 文档解析器 (Word, Excel, PowerPoint)
  2. 实现 PDF 解析器和 OCR 功能
  3. 构建 SQLite FTS5 数据库
  4. 开发 GUI 界面

按 Ctrl+C 退出...
```

### 3. 运行测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

### 4. 查看项目状态

```bash
# 运行项目管理脚本
bash ccpm/scripts/pm/init.sh
```

---

## 📁 项目结构说明

```
windows-search-tool/
│
├── src/                      # 源代码目录
│   ├── parsers/             # ★ 文档解析器（已实现基础框架）
│   │   ├── base.py          # 解析器接口和工厂
│   │   └── text_parser.py   # 文本文件解析器
│   │
│   ├── utils/               # ★ 工具类（已完成）
│   │   ├── config.py        # 配置管理
│   │   └── logger.py        # 日志管理
│   │
│   ├── core/                # 核心业务逻辑（待开发）
│   ├── data/                # 数据访问层（待开发）
│   ├── services/            # 外部服务（待开发）
│   ├── ui/                  # 用户界面（待开发）
│   └── main.py              # ★ 主程序入口
│
├── tests/                    # 测试目录
│   ├── unit/                # ★ 单元测试
│   │   └── test_parser_framework.py  # 解析器测试
│   ├── integration/         # 集成测试（待开发）
│   └── fixtures/            # 测试数据（待添加）
│
├── docs/                     # ★ 完整的项目文档
│   ├── PRD.md
│   ├── epic-stories.md
│   ├── solution-architecture.md
│   ├── ux-specification.md
│   └── user-stories.md
│
├── ccpm/                     # ★ 项目管理系统
│   ├── scripts/pm/init.sh   # 初始化脚本
│   └── config/project.json  # 项目配置
│
├── resources/                # 资源文件
│   └── config/
│       └── config.json      # ★ 默认配置
│
├── requirements.txt          # ★ Python 依赖
├── pytest.ini               # ★ 测试配置
├── setup.py                 # ★ 安装脚本
├── .gitignore               # ★ Git 忽略规则
└── README.md                # ★ 项目说明
```

**★ = 已创建/完成**

---

## 🔧 开发指南

### 配置文件

配置文件位于: `resources/config/config.json`

主要配置项:
```json
{
  "app": {
    "name": "Windows Search Tool",
    "version": "0.1.0"
  },
  "indexing": {
    "parallel_workers": 4,
    "batch_size": 100
  },
  "logging": {
    "level": "INFO",
    "file": "logs/app.log"
  }
}
```

### 使用配置管理器

```python
from src.utils.config import get_config

config = get_config()
app_name = config.get('app.name')  # "Windows Search Tool"
workers = config.get('indexing.parallel_workers', 4)  # 默认值 4
```

### 使用日志

```python
from src.utils.logger import get_logger

logger = get_logger()
logger.info('这是一条信息')
logger.error('这是一个错误')
logger.exception('这是一个异常')  # 会记录堆栈跟踪
```

### 创建新的文档解析器

```python
from src.parsers.base import BaseParser, ParseResult

class MyParser(BaseParser):
    def __init__(self):
        super().__init__(supported_extensions=['.myext'])

    def _parse_impl(self, file_path: str) -> ParseResult:
        # 实现解析逻辑
        content = "extracted content"
        metadata = {"key": "value"}

        return ParseResult(
            success=True,
            content=content,
            metadata=metadata
        )

# 注册解析器
from src.parsers.base import get_parser_factory

factory = get_parser_factory()
factory.register_parser('myparser', ['.myext'], MyParser())
```

---

## 📝 下一步开发任务

### Sprint 1 (当前 - 预计 2 周)

1. **Story 1.2: Office 文档解析器**
   - [ ] 实现 DocxParser (Word)
   - [ ] 实现 XlsxParser (Excel)
   - [ ] 实现 PptxParser (PowerPoint)
   - [ ] 编写单元测试

2. **Story 1.3: PDF 解析器**
   - [ ] 实现 PdfParser
   - [ ] 集成 Tesseract OCR
   - [ ] 编写单元测试

3. **Story 1.4: 数据库模块**
   - [ ] 设计数据库模式
   - [ ] 实现 DBManager
   - [ ] 配置 FTS5
   - [ ] 编写单元测试

### Sprint 2 (预计 2 周)

- Story 1.5: 增量索引机制
- Story 1.6: 关键词搜索功能
- Story 1.7: 搜索结果排序和高亮
- Story 1.8: 索引保存和加载

### Sprint 3 (预计 2 周)

- Story 2.1: 主窗口框架
- Story 2.2: 索引管理界面
- Story 2.3: 搜索界面

---

## 🐛 常见问题

### Q: 如何安装 Tesseract OCR?

A: 下载并安装 [Tesseract OCR for Windows](https://github.com/UB-Mannheim/tesseract/wiki)，然后在配置文件中设置正确的路径。

### Q: 测试失败怎么办?

A: 确保已安装所有依赖，并激活了虚拟环境:
```bash
pip install -r requirements.txt
pytest -v
```

### Q: 如何修改日志级别?

A: 编辑 `resources/config/config.json`，将 `logging.level` 改为 `DEBUG`, `INFO`, `WARNING`, `ERROR` 或 `CRITICAL`。

### Q: 程序在哪里记录日志?

A: 日志文件位于 `logs/app.log`，同时也会输出到控制台。

---

## 📞 联系方式

如有问题或建议，请查看项目文档或提交 Issue。

---

**最后更新:** 2025-10-16
**当前阶段:** Phase 1 完成，准备开始 Phase 2 开发
