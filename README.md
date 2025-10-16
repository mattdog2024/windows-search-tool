# Windows Search Tool

智能文件内容索引和搜索系统 - 一个专为解决文件删除或移动后无法查找历史内容而设计的工具。

## 📋 项目概述

Windows Search Tool 是一个桌面应用程序，通过创建持久化的内容索引，使用户即使在源文件不存在的情况下，仍能搜索和查看完整的文档内容。系统采用混合模式架构：在线时通过 DeepSeek API 提供语义搜索和智能摘要功能，离线时保证基础关键词搜索始终可用。

### 核心特性

- 🔍 **全文搜索** - 快速搜索所有索引文档的内容
- 💾 **持久化索引** - 即使源文件删除也能查看内容
- 📄 **多格式支持** - Word, Excel, PowerPoint, PDF, 文本文件
- 🤖 **AI 增强** - 智能摘要和关键信息提取（在线模式）
- 📸 **OCR 识别** - 扫描版 PDF 和图片文字识别
- 🌓 **混合模式** - 在线/离线自动切换

## 🚀 快速开始

### 系统要求

- **操作系统:** Windows 10/11 64位
- **Python:** 3.11 或更高版本
- **内存:** 4GB RAM（推荐 8GB）
- **硬盘:** 100MB（程序）+ 索引空间

### 安装步骤

1. **克隆仓库**

```bash
git clone <repository-url>
cd windows-search-tool
```

2. **创建虚拟环境**

```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. **安装依赖**

```bash
pip install -r requirements.txt
```

4. **安装 Tesseract OCR（可选，用于 PDF OCR）**

下载并安装 [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)

5. **运行程序**

```bash
python src/main.py
```

## 📁 项目结构

```
windows-search-tool/
├── src/                    # 源代码
│   ├── ui/                # 用户界面
│   ├── core/              # 核心业务逻辑
│   ├── parsers/           # 文档解析器
│   ├── services/          # 外部服务
│   ├── data/              # 数据访问层
│   ├── utils/             # 工具类
│   └── main.py            # 程序入口
├── tests/                  # 测试
│   ├── unit/              # 单元测试
│   ├── integration/       # 集成测试
│   └── fixtures/          # 测试数据
├── docs/                   # 文档
│   ├── PRD.md             # 产品需求文档
│   ├── epic-stories.md    # 史诗故事
│   ├── solution-architecture.md  # 解决方案架构
│   ├── ux-specification.md       # UX 规格
│   └── user-stories.md    # 详细用户故事
├── resources/              # 资源文件
│   ├── icons/             # 图标
│   ├── themes/            # 主题
│   └── config/            # 配置文件
├── ccpm/                   # 项目管理
│   ├── scripts/           # 管理脚本
│   └── config/            # 项目配置
├── logs/                   # 日志文件
├── requirements.txt        # Python 依赖
└── README.md              # 本文件
```

## 🔧 开发指南

### 运行测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行测试并生成覆盖率报告
pytest --cov=src tests/
```

### 代码格式化

```bash
# 格式化代码
black src/ tests/

# 检查代码质量
pylint src/

# 类型检查
mypy src/
```

### 项目管理

```bash
# 初始化项目管理系统
bash ccpm/scripts/pm/init.sh

# 查看项目状态
bash ccpm/scripts/pm/status.sh  # (待实现)
```

## 📖 文档

- [产品需求文档 (PRD)](./PRD.md)
- [Epic Stories](./docs/epic-stories.md)
- [解决方案架构](./docs/solution-architecture.md)
- [UX 规格说明](./docs/ux-specification.md)
- [详细用户故事](./docs/user-stories.md)

## 🛣️ 开发路线图

### ✅ Phase 1: 基础框架（已完成）

- [x] 项目结构搭建
- [x] 配置管理模块
- [x] 日志模块
- [x] 文档解析框架
- [x] 文本文件解析器

### 🚧 Phase 2: 核心功能（进行中）

- [ ] Office 文档解析器 (Word, Excel, PowerPoint)
- [ ] PDF 解析器和 OCR 功能
- [ ] SQLite FTS5 数据库
- [ ] 索引管理器
- [ ] 搜索引擎

### 📅 Phase 3: 用户界面（计划中）

- [ ] 主窗口框架
- [ ] 索引管理界面
- [ ] 搜索界面
- [ ] 结果展示

### 🔮 Phase 4: AI 增强（计划中）

- [ ] DeepSeek API 集成
- [ ] 智能摘要生成
- [ ] 关键信息提取
- [ ] 混合模式切换

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

## 📄 许可证

待定

## 👥 团队

Windows Search Tool Team

---

**当前版本:** 0.1.0 (开发中)
**最后更新:** 2025-10-16
