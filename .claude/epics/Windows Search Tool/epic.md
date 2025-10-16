---
name: Windows Search Tool
status: backlog
created: 2025-10-16T08:13:40Z
progress: 0%
prd: .claude/prds/Windows Search Tool.md
github: Will be updated when synced to GitHub
---

# Epic: Windows Search Tool

## Overview

实现一个智能文件内容索引和搜索系统,核心功能包括多格式文档解析、持久化索引、全文搜索和 AI 增强。采用分层架构(PyQt6 UI + 业务逻辑层 + SQLite FTS5 数据库),重点利用现有 Python 生态系统库来简化开发,避免重复造轮子。

**核心技术路径:**
- 使用成熟的文档解析库(python-docx, openpyxl, python-pptx, pdfplumber)
- 利用 SQLite FTS5 提供的内置全文搜索能力
- 通过 PyQt6 快速构建桌面 UI
- 集成 Tesseract OCR 和 DeepSeek API 作为增强功能

## Architecture Decisions

### 1. 分层架构 (Layered Architecture)

**决策:** 采用经典三层架构
**理由:**
- 关注点分离,便于维护和测试
- UI 与业务逻辑解耦,便于未来扩展
- 各层可独立演进

**架构层次:**
```
表示层 (UI)          → PyQt6 图形界面
  ↓
业务逻辑层 (Core)    → 索引管理、搜索引擎、文档解析
  ↓
数据访问层 (Data)    → SQLite FTS5 数据库操作
  ↓
存储层 (Storage)     → .db 文件、配置文件
```

### 2. 技术栈选择

| 组件 | 技术选择 | 理由 |
|------|---------|------|
| **GUI 框架** | PyQt6 | 成熟稳定、美观、跨平台、丰富的组件 |
| **数据库** | SQLite FTS5 | 零配置、轻量级、内置全文搜索、BM25 排序 |
| **Office 解析** | python-docx/openpyxl/python-pptx | 官方推荐库、文档齐全、稳定可靠 |
| **PDF 解析** | pdfplumber | 比 PyPDF2 更强大、支持表格提取 |
| **OCR** | Tesseract + pytesseract | 开源免费、多语言支持、社区活跃 |
| **中文分词** | jieba | 轻量级、准确率高、易于集成 |
| **AI 服务** | DeepSeek API | 性价比高、中文优化、API 简单 |
| **并发处理** | multiprocessing | Python 标准库、绕过 GIL 限制 |

### 3. 设计模式

- **工厂模式 (ParserFactory):** 根据文件类型动态选择解析器
- **策略模式 (Search Modes):** 支持精确/模糊搜索策略切换
- **观察者模式 (Progress Updates):** UI 订阅索引进度更新
- **单例模式 (ConfigManager, DBManager):** 全局唯一配置和数据库连接

### 4. 性能优化策略

**索引阶段:**
- 多进程并行处理文件(multiprocessing.Pool)
- 批量数据库插入(每 100 条一次事务)
- SQLite WAL 模式提高并发性能
- 文件哈希检测避免重复索引

**搜索阶段:**
- FTS5 BM25 算法提供相关度排序
- LRU 缓存最近查询结果
- 结果分页(每页 20 条)
- 延迟加载完整文档内容

## Technical Approach

### Frontend Components (UI 层)

**基于 PyQt6 的桌面应用:**

1. **MainWindow (主窗口)**
   - QMainWindow 作为应用容器
   - 菜单栏: 文件、编辑、视图、帮助
   - 工具栏: 新建索引、刷新、设置等快捷按钮
   - 状态栏: 索引统计信息显示
   - 分割布局: 左侧索引列表 + 右侧搜索面板

2. **IndexPanel (索引管理面板)**
   - QTreeWidget 显示索引列表
   - 右键菜单: 打开、刷新、删除、属性
   - 新建索引对话框(QDialog): 选择路径、配置选项
   - 进度条(QProgressBar): 实时显示索引进度

3. **SearchPanel (搜索面板)**
   - QLineEdit: 搜索输入框 + 搜索历史自动补全
   - QComboBox: 搜索模式选择(精确/模糊)
   - QTableView: 搜索结果列表(文件名、匹配度、修改时间)
   - QTextBrowser: 文档内容查看器(支持高亮)

**UI 交互流程:**
- 后台线程(QThread)执行耗时操作
- 信号槽机制更新 UI(避免界面冻结)
- QMessageBox 提供友好的错误提示

### Backend Services (业务逻辑层)

**核心模块设计:**

1. **ParserFactory (文档解析工厂)**
```python
class IDocumentParser(ABC):
    @abstractmethod
    def supports(self, file_path: str) -> bool: ...
    @abstractmethod
    def parse(self, file_path: str) -> ParseResult: ...

class ParserFactory:
    def __init__(self):
        self._parsers = {
            '.docx': DocxParser(),
            '.xlsx': XlsxParser(),
            '.pptx': PptxParser(),
            '.pdf': PdfParser(),
            '.txt': TextParser(),
        }

    def get_parser(self, file_path: str) -> IDocumentParser:
        ext = os.path.splitext(file_path)[1].lower()
        return self._parsers.get(ext)
```

2. **IndexManager (索引管理器)**
```python
class IndexManager:
    def create_index(self, name, path, options):
        # 1. 创建 SQLite 数据库
        # 2. 扫描目录获取文件列表
        # 3. 多进程并行解析文件
        # 4. 批量插入数据库
        # 5. 更新索引统计

    def refresh_index(self, index_id):
        # 增量更新: 检测文件变更(通过哈希)
        # 仅处理新增/修改的文件
```

3. **SearchEngine (搜索引擎)**
```python
class SearchEngine:
    def search(self, query, options):
        # 1. 构建 FTS5 查询语法
        # 2. 执行数据库查询
        # 3. 计算相关度分数
        # 4. 可选: AI 语义重排序
        # 5. 生成结果摘要和高亮
```

4. **AIService (AI 增强服务)**
```python
class AIService:
    def __init__(self, api_key):
        self.client = httpx.Client(base_url="https://api.deepseek.com/v1")
        self.cache = {}  # 简单字典缓存

    def generate_summary(self, content):
        # 检查缓存 → 调用 API → 保存结果

    def is_online(self):
        # 快速健康检查(超时 2 秒)
```

### Data Models & Schema (数据层)

**核心实体:**

```python
@dataclass
class Document:
    id: int
    file_path: str
    file_name: str
    file_size: int
    file_type: str
    content: str
    content_hash: str  # SHA256
    created_at: datetime
    modified_at: datetime
    indexed_at: datetime
    metadata: Dict[str, Any]

@dataclass
class Index:
    id: str  # UUID
    name: str
    path: str
    db_path: str
    created_at: datetime
    updated_at: datetime
    document_count: int
    total_size: int
```

**数据库模式:**

```sql
-- 文档主表
CREATE TABLE documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL UNIQUE,
    file_name TEXT NOT NULL,
    file_size INTEGER,
    file_type TEXT,
    content_hash TEXT,
    created_at DATETIME,
    modified_at DATETIME,
    indexed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active'
);

-- FTS5 全文搜索表
CREATE VIRTUAL TABLE documents_fts USING fts5(
    content,
    content_rowid=id,
    tokenize='porter unicode61 remove_diacritics 2'
);

-- 元数据表(键值对)
CREATE TABLE document_metadata (
    id INTEGER PRIMARY KEY,
    document_id INTEGER,
    key TEXT,
    value TEXT,
    FOREIGN KEY(document_id) REFERENCES documents(id)
);

-- AI 摘要表(可选)
CREATE TABLE document_summaries (
    id INTEGER PRIMARY KEY,
    document_id INTEGER UNIQUE,
    summary TEXT,
    entities TEXT,  -- JSON
    generated_at DATETIME,
    FOREIGN KEY(document_id) REFERENCES documents(id)
);

-- 性能优化配置
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=-64000;  -- 64MB
```

### Infrastructure (基础设施)

**部署方案:**
- 使用 PyInstaller 打包成单个 .exe 文件
- 内嵌 SQLite(无需额外安装)
- 依赖 Tesseract OCR(需单独安装)

**配置管理:**
- JSON 配置文件存储用户设置
- Windows Credential Manager 存储 API Key
- 默认数据路径: `%APPDATA%/WindowsSearchTool/`

**日志记录:**
- RotatingFileHandler(最大 10MB,保留 5 个文件)
- 日志级别: INFO(用户操作) + ERROR(异常)
- 日志路径: `%APPDATA%/WindowsSearchTool/logs/`

**错误处理:**
- 解析失败: 记录错误但继续处理其他文件
- API 失败: 自动切换到离线模式
- 数据库损坏: 提示用户修复或重建索引

## Implementation Strategy

### 开发阶段划分

**Phase 1: 核心基础 (2 周)**
- 搭建项目结构
- 实现配置管理和日志模块
- 实现文档解析框架
- 实现基础文本文件解析器
- 单元测试覆盖率 ≥ 80%

**Phase 2: 索引与搜索 (2 周)**
- 实现 Office 和 PDF 解析器
- 实现 SQLite FTS5 数据库
- 实现索引管理器(创建、增量更新)
- 实现搜索引擎(关键词搜索、结果排序)
- 集成测试

**Phase 3: 用户界面 (2 周)**
- 实现主窗口框架
- 实现索引管理面板
- 实现搜索和结果展示面板
- UI/UX 优化(进度条、高亮、分页)
- 用户测试

**Phase 4: AI 增强与优化 (1-2 周)**
- 集成 Tesseract OCR
- 集成 DeepSeek API
- 实现混合模式切换
- 性能优化和打包
- 端到端测试

### 风险缓解

**技术风险:**
1. **OCR 准确率低**
   - 缓解: 图像预处理(灰度化、对比度增强)
   - 备选: 仅支持文本型 PDF,OCR 作为可选功能

2. **大文件索引性能问题**
   - 缓解: 多进程并行 + 批量插入优化
   - 备选: 限制单个文件大小(如 100MB)

3. **API 依赖导致功能不可用**
   - 缓解: 混合模式设计,离线时基础功能仍可用
   - 备选: 集成本地 AI 模型(如 sentence-transformers)

**资源风险:**
- 单人开发时间紧张 → 优先实现核心功能,AI 功能可后期迭代

### 测试策略

**单元测试 (pytest):**
- 各个解析器的正确性测试
- 数据库 CRUD 操作测试
- 搜索算法测试

**集成测试:**
- 端到端索引创建流程
- 端到端搜索流程
- 多索引管理测试

**性能测试:**
- 索引 10,000 个文件的速度测试
- 搜索 100,000 文档的响应时间测试
- 内存占用监控

**用户验收测试:**
- 按照 PRD 用户旅程验证功能
- 收集真实用户反馈

## Task Breakdown Preview

基于 IMPORTANT 要求,将任务数量控制在 10 个以内,通过合并相关功能简化实现:

- [ ] **Task 1: 项目基础架构搭建**
  - 创建项目结构(src/, tests/, resources/)
  - 配置管理模块(JSON 配置读写)
  - 日志模块(RotatingFileHandler)
  - 单元测试框架搭建

- [ ] **Task 2: 文档解析引擎实现**
  - 实现 IDocumentParser 抽象基类和 ParserFactory
  - 实现 Office 文档解析器(docx, xlsx, pptx)
  - 实现 PDF 解析器(pdfplumber)
  - 实现文本文件解析器(.txt, .csv, .md)
  - 异常处理和日志记录

- [ ] **Task 3: SQLite FTS5 数据库实现**
  - 设计数据库模式(documents, documents_fts, metadata)
  - 实现 DBManager 类(CRUD 操作)
  - 配置 FTS5 性能优化(WAL, cache_size)
  - 实现批量插入和事务管理

- [ ] **Task 4: 索引管理器实现**
  - 实现 IndexManager 类
  - 实现创建索引功能(目录扫描、文件解析、数据库插入)
  - 实现增量索引功能(文件哈希检测变更)
  - 实现多进程并行处理(multiprocessing.Pool)
  - 实现进度回调机制

- [ ] **Task 5: 搜索引擎实现**
  - 实现 SearchEngine 类
  - 实现 FTS5 查询构建(精确/模糊搜索)
  - 实现结果排序(BM25 相关度)
  - 实现关键词高亮和摘要提取
  - 实现结果缓存(LRU cache)

- [ ] **Task 6: PyQt6 主窗口和索引管理界面**
  - 实现 MainWindow 主窗口框架
  - 实现菜单栏和工具栏
  - 实现 IndexPanel 索引列表(QTreeWidget)
  - 实现新建索引对话框(路径选择、选项配置)
  - 实现进度条显示(QProgressBar + 后台线程)

- [ ] **Task 7: PyQt6 搜索界面实现**
  - 实现 SearchPanel 搜索面板
  - 实现搜索输入框和模式选择
  - 实现结果列表展示(QTableView)
  - 实现文档内容查看器(QTextBrowser + HTML 高亮)
  - 实现结果分页加载

- [ ] **Task 8: Tesseract OCR 集成**
  - 实现 PDF 类型检测(文本型 vs 扫描型)
  - 集成 pytesseract 进行 OCR 识别
  - 实现图像预处理(灰度化、对比度增强)
  - 配置中英文语言包(chi_sim + eng)
  - OCR 置信度过滤

- [ ] **Task 9: DeepSeek AI 服务集成**
  - 实现 AIService 类和 DeepSeek API 客户端
  - 实现在线状态检测
  - 实现文档摘要生成
  - 实现关键信息提取(人名、日期、金额)
  - 实现摘要缓存和数据库存储

- [ ] **Task 10: 打包部署和端到端测试**
  - 配置 PyInstaller 打包脚本
  - 生成独立 .exe 文件
  - 编写用户手册和安装说明
  - 执行完整的端到端测试
  - 性能基准测试和优化

**简化说明:**
- 将原本 14+ 个故事合并为 10 个大任务
- 每个任务包含多个相关子功能,减少任务切换开销
- 优先利用现有库(python-docx, pdfplumber, PyQt6),避免从零实现
- AI 和 OCR 作为独立任务,可根据进度灵活调整优先级

## Dependencies

### 外部依赖

**必需依赖:**
- Python 3.11+ 运行环境
- PyQt6 6.5+ (GUI 框架)
- python-docx 1.1+ (Word 解析)
- openpyxl 3.1+ (Excel 解析)
- python-pptx 0.6+ (PowerPoint 解析)
- pdfplumber 0.10+ (PDF 解析)
- SQLite 3.35+ (内置 FTS5,Python 标准库)
- jieba 0.42+ (中文分词)

**可选依赖(增强功能):**
- Tesseract OCR 5.0+ (OCR 文字识别)
- pytesseract 0.3+ (Tesseract Python 绑定)
- Pillow 10.0+ (图像处理)
- httpx 0.24+ (DeepSeek API 调用)
- pdf2image (PDF 转图片,用于 OCR)
- Poppler (pdf2image 依赖)

**开发依赖:**
- pytest 7.4+ (单元测试)
- pytest-qt (PyQt 测试)
- pytest-cov (覆盖率)
- black (代码格式化)
- pylint (代码检查)
- PyInstaller 5.13+ (应用打包)

### 内部依赖

无(独立项目)

### 前置工作

- 确认 Python 3.11+ 已安装
- 安装 Tesseract OCR(可选)
- 获取 DeepSeek API Key(可选)

## Success Criteria (Technical)

### 功能完整性
- [x] 支持所有目标文档格式(docx, xlsx, pptx, pdf, txt, csv, md)
- [x] Office 文档元数据正确提取(作者、标题、创建时间)
- [x] PDF OCR 识别准确率 ≥ 85%(测试集)
- [x] 搜索结果准确率 ≥ 95%(相关性测试)
- [x] 增量索引正确检测文件变更(基于哈希)
- [x] 多索引联合搜索功能正常
- [x] AI 摘要生成正确(人工评估)

### 性能基准
- [x] 索引速度 ≥ 100 文件/分钟(混合文档类型)
- [x] 搜索响应时间 < 2 秒(100,000 文档索引)
- [x] 内存占用 < 500MB(索引期间)
- [x] 内存占用 < 200MB(搜索期间)
- [x] UI 响应时间 < 100ms(用户操作反馈)

### 稳定性
- [x] 连续运行 24 小时无崩溃
- [x] 索引 10,000 文件无内存泄漏
- [x] 单元测试覆盖率 ≥ 90%
- [x] 集成测试覆盖核心流程 100%
- [x] 异常文件处理不中断索引过程

### 用户体验
- [x] 5 分钟内完成首次索引创建(1000 文件)
- [x] 3 分钟内找到所需内容(用户测试)
- [x] 所有操作有即时进度反馈
- [x] 错误提示友好且可操作
- [x] 界面符合 Windows 设计规范

### 代码质量
- [x] 核心模块有完整的单元测试
- [x] 代码通过 pylint 检查(评分 ≥ 8.0)
- [x] 代码通过 black 格式化
- [x] 关键函数有类型注解(mypy 检查)
- [x] 关键流程有集成测试

## Estimated Effort

### 总体时间线
- **总工期:** 6-8 周
- **开发阶段:** 5-6 周
- **测试优化:** 1-2 周

### 资源需求
- **开发人员:** 1 人(全职)
- **测试人员:** 1 人(兼职,最后 2 周)
- **硬件需求:**
  - 开发机: Windows 10/11, 16GB RAM, SSD
  - 测试数据: 10,000+ 文档样本

### 关键路径

```
Week 1-2: 项目基础 + 文档解析引擎 + 数据库
   ↓
Week 3-4: 索引管理器 + 搜索引擎
   ↓
Week 5-6: PyQt6 UI + OCR + AI 集成
   ↓
Week 7-8: 测试、优化、打包
```

**风险缓冲:**
- OCR 集成可能遇到问题 → 预留 3-5 天调试
- UI 细节优化较耗时 → 优先保证核心功能,细节可后续迭代
- 性能优化可能需要额外时间 → 预留 1 周性能测试和调优

### 里程碑

- **Week 2:** 文档解析和数据库模块完成,单元测试通过
- **Week 4:** 索引和搜索核心功能完成,集成测试通过
- **Week 6:** UI 完成,可进行端到端用户测试
- **Week 8:** 发布 MVP 版本

---

## Tasks Created

- [ ] 001.md - 项目基础架构搭建 (parallel: true, S, 8-12h)
- [ ] 002.md - 文档解析引擎实现 (parallel: false, L, 16-20h)
- [ ] 003.md - SQLite FTS5 数据库实现 (parallel: true, M, 12-16h)
- [ ] 004.md - 索引管理器实现 (parallel: false, L, 18-24h)
- [ ] 005.md - 搜索引擎实现 (parallel: true, M, 12-16h)
- [ ] 006.md - PyQt6 主窗口和索引管理界面 (parallel: false, L, 16-20h)
- [ ] 007.md - PyQt6 搜索界面实现 (parallel: false, M, 14-18h)
- [ ] 008.md - Tesseract OCR 集成 (parallel: true, M, 12-16h)
- [ ] 009.md - DeepSeek AI 服务集成 (parallel: true, M, 10-14h)
- [ ] 010.md - 打包部署和端到端测试 (parallel: false, L, 16-20h)

**任务统计:**
- 总任务数: 10
- 并行任务: 5 个 (001, 003, 005, 008, 009)
- 顺序任务: 5 个 (002, 004, 006, 007, 010)
- 总估算工时: 147-186 小时(约 6-8 周)

**任务依赖关系:**
- Phase 1 (Week 1-2): Task 001 ← 基础 → Task 002, 003 (可并行)
- Phase 2 (Week 3-4): Task 004 (依赖 002, 003), Task 005 (依赖 003, 可与 004 并行)
- Phase 3 (Week 5-6): Task 006 (依赖 004), Task 007 (依赖 005, 006), Task 008, 009 (可并行)
- Phase 4 (Week 7-8): Task 010 (依赖 006, 007, 008, 009)

**关键路径:** 001 → 002 → 004 → 006 → 007 → 010

---

**创建时间:** 2025-10-16T08:13:40Z
**任务分解完成时间:** 2025-10-16T08:21:20Z
**状态:** 任务分解完成,待开始开发
**下一步:** 准备同步到 GitHub? 运行: /pm:epic-sync Windows Search Tool
