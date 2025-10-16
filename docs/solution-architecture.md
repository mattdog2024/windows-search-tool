# Solution Architecture - Windows Search Tool

**项目:** Windows Search Tool
**项目级别:** Level 2
**日期:** 2025-10-16
**版本:** 1.0
**状态:** Draft

---

## 1. 执行摘要

### 1.1 架构概述

Windows Search Tool 是一个桌面应用程序，采用分层架构设计，由以下主要组件构成：

- **表示层 (Presentation Layer):** PyQt6 图形用户界面
- **业务逻辑层 (Business Logic Layer):** 索引管理、搜索引擎、文档处理
- **数据访问层 (Data Access Layer):** SQLite 数据库操作
- **外部服务层 (External Services):** DeepSeek API 集成

### 1.2 关键技术决策

| 决策领域 | 选择 | 理由 |
|---------|------|------|
| 编程语言 | Python 3.11+ | 丰富的文档处理库，快速开发 |
| GUI 框架 | PyQt6 | 成熟稳定，跨平台，美观 |
| 数据库 | SQLite FTS5 | 轻量级，全文搜索性能优异 |
| 中文分词 | jieba | 成熟的中文分词库 |
| OCR 引擎 | Tesseract | 开源免费，支持多语言 |
| AI 服务 | DeepSeek API | 性价比高，中文支持好 |
| 打包工具 | PyInstaller | 生成独立可执行文件 |

### 1.3 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      用户界面层 (UI Layer)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  主窗口      │  │  索引管理    │  │  搜索界面    │       │
│  │ MainWindow   │  │ IndexPanel   │  │ SearchPanel  │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────────┐
│                   业务逻辑层 (Business Layer)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  索引管理器  │  │  搜索引擎    │  │  AI 服务     │       │
│  │IndexManager  │  │SearchEngine  │  │ AIService    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  文档解析器  │  │  进度管理    │  │  配置管理    │       │
│  │ ParserFactory│  │ProgressMgr   │  │ ConfigMgr    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────────┐
│                  数据访问层 (Data Access Layer)               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  数据库管理  │  │  缓存管理    │  │  文件系统    │       │
│  │  DBManager   │  │ CacheManager │  │ FileSystem   │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────────┐
│                     存储层 (Storage Layer)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ SQLite DB    │  │  本地缓存    │  │  配置文件    │       │
│  │  .db 文件    │  │  .cache/     │  │  .json       │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 系统架构

### 2.1 整体架构模式

采用 **分层架构 (Layered Architecture)** 模式，具有以下优势：

- **关注点分离:** 每层负责特定职责
- **可维护性:** 层间依赖单向，易于修改
- **可测试性:** 各层可独立测试
- **可扩展性:** 易于添加新功能

### 2.2 架构原则

1. **单一职责:** 每个模块只负责一个功能
2. **依赖倒置:** 高层模块不依赖低层模块，都依赖抽象
3. **开闭原则:** 对扩展开放，对修改关闭
4. **接口隔离:** 使用小而专的接口
5. **松耦合:** 组件间通过接口通信

### 2.3 核心组件

#### 2.3.1 用户界面层

**主窗口 (MainWindow)**
- 职责：应用程序主入口，协调各个面板
- 技术：PyQt6 QMainWindow
- 关键功能：
  - 菜单栏和工具栏管理
  - 状态栏更新
  - 窗口状态保存/恢复
  - 主题切换

**索引管理面板 (IndexPanel)**
- 职责：索引的创建、加载、删除
- 技术：PyQt6 QWidget + QTreeWidget
- 关键功能：
  - 索引列表展示
  - 新建索引向导
  - 进度显示
  - 索引统计

**搜索面板 (SearchPanel)**
- 职责：搜索输入和结果展示
- 技术：PyQt6 QWidget + QTableView + QTextBrowser
- 关键功能：
  - 搜索输入和历史
  - 结果列表展示
  - 详细内容查看
  - 关键词高亮

#### 2.3.2 业务逻辑层

**索引管理器 (IndexManager)**
```python
class IndexManager:
    """管理索引的生命周期"""

    def create_index(self, name: str, path: str, options: IndexOptions) -> Index:
        """创建新索引"""

    def load_index(self, index_path: str) -> Index:
        """加载已有索引"""

    def delete_index(self, index_id: str) -> bool:
        """删除索引"""

    def refresh_index(self, index_id: str) -> None:
        """增量更新索引"""

    def merge_indexes(self, index_ids: List[str]) -> Index:
        """合并多个索引"""
```

**搜索引擎 (SearchEngine)**
```python
class SearchEngine:
    """执行搜索操作"""

    def search(self, query: str, options: SearchOptions) -> SearchResults:
        """执行搜索"""

    def search_in_indexes(self, query: str, index_ids: List[str]) -> SearchResults:
        """在多个索引中搜索"""

    def rank_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """结果排序"""

    def highlight_keywords(self, content: str, keywords: List[str]) -> str:
        """关键词高亮"""
```

**文档解析工厂 (ParserFactory)**
```python
class IDocumentParser(ABC):
    """文档解析器接口"""

    @abstractmethod
    def supports(self, file_path: str) -> bool:
        """判断是否支持该文件"""

    @abstractmethod
    def parse(self, file_path: str) -> ParseResult:
        """解析文档"""

class ParserFactory:
    """解析器工厂"""

    def __init__(self):
        self._parsers: Dict[str, IDocumentParser] = {}
        self._register_default_parsers()

    def register_parser(self, extensions: List[str], parser: IDocumentParser):
        """注册解析器"""

    def get_parser(self, file_path: str) -> Optional[IDocumentParser]:
        """根据文件类型获取解析器"""
```

**AI 服务 (AIService)**
```python
class AIService:
    """DeepSeek API 集成"""

    def __init__(self, api_key: str):
        self.client = DeepSeekClient(api_key)
        self.cache = LRUCache(maxsize=100)
        self.online = False

    def generate_summary(self, content: str) -> Summary:
        """生成文档摘要"""

    def extract_entities(self, content: str) -> Entities:
        """提取关键信息"""

    def semantic_search(self, query: str, documents: List[str]) -> List[float]:
        """语义搜索评分"""

    def check_online_status(self) -> bool:
        """检查在线状态"""
```

#### 2.3.3 数据访问层

**数据库管理器 (DBManager)**
```python
class DBManager:
    """SQLite 数据库操作"""

    def __init__(self, db_path: str):
        self.connection = sqlite3.connect(db_path)
        self._init_schema()

    def insert_document(self, doc: Document) -> int:
        """插入文档"""

    def update_document(self, doc_id: int, doc: Document) -> bool:
        """更新文档"""

    def delete_document(self, doc_id: int) -> bool:
        """删除文档"""

    def search_fts(self, query: str) -> List[SearchResult]:
        """全文搜索"""

    def get_statistics(self) -> Statistics:
        """获取统计信息"""
```

---

## 3. 数据模型

### 3.1 核心实体

#### 3.1.1 Document (文档)

```python
@dataclass
class Document:
    """文档实体"""
    id: Optional[int] = None
    file_path: str
    file_name: str
    file_size: int
    file_type: str
    content: str
    content_hash: str
    created_at: datetime
    modified_at: datetime
    indexed_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
```

#### 3.1.2 Index (索引)

```python
@dataclass
class Index:
    """索引实体"""
    id: str
    name: str
    path: str
    db_path: str
    created_at: datetime
    updated_at: datetime
    document_count: int
    total_size: int
    options: IndexOptions
```

#### 3.1.3 SearchResult (搜索结果)

```python
@dataclass
class SearchResult:
    """搜索结果"""
    document_id: int
    file_path: str
    file_name: str
    content_snippet: str
    relevance_score: float
    match_count: int
    highlighted_content: str
    metadata: Dict[str, Any]
```

### 3.2 数据库模式

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
    status TEXT DEFAULT 'active' -- active, deleted, error
);

-- 全文搜索表（FTS5）
CREATE VIRTUAL TABLE documents_fts USING fts5(
    content,
    content_rowid=id,
    tokenize='porter unicode61 remove_diacritics 2'
);

-- 文档元数据表
CREATE TABLE document_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT,
    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE,
    UNIQUE(document_id, key)
);

-- AI 生成的摘要表
CREATE TABLE document_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL UNIQUE,
    summary TEXT,
    key_points TEXT, -- JSON array
    entities TEXT,   -- JSON object
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
);

-- 索引配置表
CREATE TABLE index_config (
    key TEXT PRIMARY KEY,
    value TEXT
);

-- 创建索引以提高查询性能
CREATE INDEX idx_documents_file_path ON documents(file_path);
CREATE INDEX idx_documents_file_type ON documents(file_type);
CREATE INDEX idx_documents_modified_at ON documents(modified_at);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_metadata_document_id ON document_metadata(document_id);
CREATE INDEX idx_metadata_key ON document_metadata(key);
```

---

## 4. 技术栈详细说明

### 4.1 核心技术

#### 4.1.1 Python 生态

| 组件 | 库/框架 | 版本 | 用途 |
|------|---------|------|------|
| GUI | PyQt6 | 6.5+ | 图形界面 |
| 数据库 | sqlite3 | 3.35+ | 数据存储和FTS |
| Office | python-docx | 1.1+ | Word 文档解析 |
| Office | openpyxl | 3.1+ | Excel 文档解析 |
| Office | python-pptx | 0.6+ | PowerPoint 解析 |
| PDF | PyPDF2 | 3.0+ | PDF 文本提取 |
| PDF | pdfplumber | 0.10+ | PDF 高级解析 |
| OCR | pytesseract | 0.3+ | OCR 文字识别 |
| OCR | Pillow | 10.0+ | 图像处理 |
| 中文 | jieba | 0.42+ | 中文分词 |
| HTTP | httpx | 0.24+ | API 调用 |
| 测试 | pytest | 7.4+ | 单元测试 |
| 打包 | PyInstaller | 5.13+ | 应用打包 |

#### 4.1.2 外部依赖

**Tesseract OCR**
- 版本：5.0+
- 安装位置：`C:\Program Files\Tesseract-OCR\`
- 语言包：中文简体 (chi_sim)、英文 (eng)
- 配置：通过环境变量 `TESSDATA_PREFIX` 指定

**DeepSeek API**
- 端点：`https://api.deepseek.com/v1`
- 认证：API Key (通过环境变量配置)
- 模型：`deepseek-chat`
- 超时：10 秒

### 4.2 开发工具

| 工具 | 用途 |
|------|------|
| VS Code | 主要 IDE |
| Python Extension | Python 支持 |
| Black | 代码格式化 |
| Pylint | 代码检查 |
| mypy | 类型检查 |
| Git | 版本控制 |

---

## 5. 关键流程设计

### 5.1 索引创建流程

```
用户选择目录
    ↓
验证路径有效性
    ↓
配置索引选项（文件类型、排除规则等）
    ↓
创建数据库文件
    ↓
扫描目录树（递归）
    ↓
┌─────────────────────────┐
│ 对每个文件：             │
│  1. 检查是否已索引       │
│  2. 计算文件哈希         │
│  3. 选择解析器           │
│  4. 解析文档内容         │
│  5. 插入数据库           │
│  6. 更新FTS索引          │
│  7. 更新进度             │
└─────────────────────────┘
    ↓
提交事务
    ↓
生成索引统计
    ↓
保存索引配置
    ↓
完成
```

**性能优化策略:**
1. **并行处理:** 使用多进程池处理文件（最多 CPU 核心数）
2. **批量插入:** 每 100 个文档批量提交一次
3. **异步 I/O:** 使用异步读取文件内容
4. **增量更新:** 跳过未修改的文件

### 5.2 搜索流程

```
用户输入查询
    ↓
解析查询语法
    ↓
选择搜索模式（精确/模糊）
    ↓
┌─────────────────────────────┐
│ 如果在线模式：               │
│   ↓                          │
│ 调用 AI 进行语义理解         │
│   ↓                          │
│ 扩展查询关键词               │
└─────────────────────────────┘
    ↓
执行 FTS 查询
    ↓
获取匹配文档列表
    ↓
计算相关度分数（BM25）
    ↓
┌─────────────────────────────┐
│ 如果在线模式：               │
│   ↓                          │
│ 使用 AI 重新排序结果         │
└─────────────────────────────┘
    ↓
提取内容片段（snippet）
    ↓
高亮关键词
    ↓
返回结果列表
    ↓
显示给用户
```

### 5.3 AI 摘要生成流程

```
用户请求摘要
    ↓
检查缓存（是否已生成）
    ↓
如果存在 → 返回缓存结果
    ↓
如果不存在：
    ↓
检查在线状态
    ↓
如果离线 → 显示错误提示
    ↓
如果在线：
    ↓
获取文档内容
    ↓
如果内容过长（>4000字）
    ↓
分段处理
    ↓
构建 AI Prompt
    ↓
调用 DeepSeek API
    ↓
解析 API 响应
    ↓
提取摘要和关键信息
    ↓
保存到数据库
    ↓
更新缓存
    ↓
返回结果
```

---

## 6. 安全性设计

### 6.1 数据安全

**敏感信息保护:**
- API Key 存储在系统密钥链（Windows Credential Manager）
- 数据库文件可选加密（使用 SQLCipher）
- 不索引系统关键目录（C:\Windows, C:\Program Files 等）

**文件访问控制:**
- 遵循操作系统权限
- 处理访问被拒绝的文件时记录警告但不中断索引

### 6.2 输入验证

- 搜索查询长度限制：1000 字符
- 文件路径验证：防止路径遍历攻击
- SQL 注入防护：使用参数化查询

### 6.3 错误处理

```python
class ErrorHandler:
    """统一错误处理"""

    @staticmethod
    def handle_parse_error(file_path: str, error: Exception):
        """处理解析错误"""
        logger.error(f"Failed to parse {file_path}: {error}")
        # 记录到错误日志表
        # 继续处理其他文件

    @staticmethod
    def handle_api_error(error: Exception):
        """处理 API 错误"""
        if isinstance(error, TimeoutError):
            # 切换到离线模式
            pass
        elif isinstance(error, AuthenticationError):
            # 提示用户检查 API Key
            pass
```

---

## 7. 性能优化

### 7.1 索引性能

**目标:**
- 索引速度：≥ 100 个文件/分钟
- 内存占用：< 500MB（索引 10 万文件时）

**优化措施:**
1. **多进程并行:** 使用 `multiprocessing.Pool` 并行处理文件
2. **批量提交:** 每 100 个文档一次事务提交
3. **WAL 模式:** 启用 SQLite WAL 模式提高并发性能
4. **缓冲区优化:** 设置合适的 `cache_size` 和 `page_size`

```python
# 数据库性能配置
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=-64000;  # 64MB
PRAGMA temp_store=MEMORY;
PRAGMA mmap_size=268435456; # 256MB
```

### 7.2 搜索性能

**目标:**
- 搜索响应时间：< 2 秒（10 万文档）
- 内存占用：< 200MB

**优化措施:**
1. **FTS5 优化:** 使用 BM25 排序算法
2. **结果分页:** 每页返回 20 条结果
3. **查询缓存:** LRU 缓存最近 100 次查询结果
4. **索引优化:** 在常用字段上创建索引

### 7.3 UI 响应性

**措施:**
1. **后台线程:** 所有耗时操作在后台线程执行
2. **进度反馈:** 实时更新进度条
3. **虚拟滚动:** 大量结果使用虚拟滚动优化
4. **懒加载:** 详细内容按需加载

---

## 8. 可扩展性设计

### 8.1 插件式解析器

新增文档格式支持只需：
1. 实现 `IDocumentParser` 接口
2. 在 `ParserFactory` 中注册

示例：
```python
class MarkdownParser(IDocumentParser):
    def supports(self, file_path: str) -> bool:
        return file_path.endswith('.md')

    def parse(self, file_path: str) -> ParseResult:
        # 实现解析逻辑
        pass

# 注册
parser_factory.register_parser(['.md', '.markdown'], MarkdownParser())
```

### 8.2 自定义 AI 服务

支持切换不同的 AI 服务提供商：

```python
class IAIProvider(ABC):
    @abstractmethod
    def generate_summary(self, content: str) -> Summary:
        pass

class DeepSeekProvider(IAIProvider):
    # 实现 DeepSeek API

class OpenAIProvider(IAIProvider):
    # 实现 OpenAI API

# 配置中选择
ai_service = AIService(provider=DeepSeekProvider())
```

---

## 9. 部署架构

### 9.1 应用结构

```
windows-search-tool/
├── src/
│   ├── ui/                  # 用户界面
│   │   ├── main_window.py
│   │   ├── index_panel.py
│   │   └── search_panel.py
│   ├── core/                # 核心业务逻辑
│   │   ├── index_manager.py
│   │   ├── search_engine.py
│   │   └── parser_factory.py
│   ├── parsers/             # 文档解析器
│   │   ├── base.py
│   │   ├── office_parsers.py
│   │   ├── pdf_parser.py
│   │   └── text_parser.py
│   ├── services/            # 外部服务
│   │   ├── ai_service.py
│   │   └── deepseek_client.py
│   ├── data/                # 数据访问
│   │   ├── db_manager.py
│   │   ├── cache_manager.py
│   │   └── models.py
│   ├── utils/               # 工具类
│   │   ├── config.py
│   │   ├── logger.py
│   │   └── progress.py
│   └── main.py              # 应用入口
├── tests/                   # 测试
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── resources/               # 资源文件
│   ├── icons/
│   ├── themes/
│   └── config/
├── docs/                    # 文档
├── requirements.txt         # 依赖
├── setup.py                 # 安装脚本
└── README.md
```

### 9.2 打包和分发

使用 PyInstaller 打包成独立可执行文件：

```bash
pyinstaller --name="WindowsSearchTool" \
            --onefile \
            --windowed \
            --icon=resources/icons/app.ico \
            --add-data="resources:resources" \
            src/main.py
```

**分发包内容:**
- `WindowsSearchTool.exe` - 主程序
- `README.txt` - 使用说明
- `LICENSE.txt` - 许可证
- `config-sample.json` - 配置文件示例

### 9.3 系统要求

**最低要求:**
- 操作系统：Windows 10 64位
- CPU：双核 2.0GHz
- 内存：4GB RAM
- 硬盘：100MB（程序）+ 索引空间
- .NET Framework 4.8（Tesseract 依赖）

**推荐配置:**
- 操作系统：Windows 11 64位
- CPU：四核 3.0GHz 或更高
- 内存：8GB RAM 或更高
- 硬盘：SSD
- 网络：互联网连接（AI 功能）

---

## 10. 监控和日志

### 10.1 日志策略

```python
import logging
from logging.handlers import RotatingFileHandler

# 日志配置
logger = logging.getLogger('WindowsSearchTool')
logger.setLevel(logging.INFO)

# 文件处理器（最大10MB，保留5个备份）
handler = RotatingFileHandler(
    'logs/app.log',
    maxBytes=10*1024*1024,
    backupCount=5
)
handler.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)
logger.addHandler(handler)
```

**日志级别:**
- `DEBUG`: 详细的调试信息
- `INFO`: 一般信息（索引创建、搜索请求等）
- `WARNING`: 警告信息（文件访问失败等）
- `ERROR`: 错误信息（解析失败、API 错误等）
- `CRITICAL`: 严重错误（数据库损坏等）

### 10.2 性能监控

```python
class PerformanceMonitor:
    """性能监控"""

    def monitor_indexing(self):
        """监控索引性能"""
        return {
            'files_per_second': 0,
            'memory_usage_mb': 0,
            'cpu_usage_percent': 0
        }

    def monitor_search(self):
        """监控搜索性能"""
        return {
            'query_time_ms': 0,
            'results_count': 0,
            'cache_hit_rate': 0
        }
```

---

## 11. 测试策略

### 11.1 测试金字塔

```
         ┌──────────┐
         │  E2E测试  │  10%
         ├──────────┤
         │ 集成测试  │  20%
         ├──────────┤
         │ 单元测试  │  70%
         └──────────┘
```

### 11.2 测试覆盖率目标

- 单元测试覆盖率：≥ 90%
- 集成测试覆盖率：≥ 60%
- 关键路径测试：100%

### 11.3 测试类型

**单元测试 (Unit Tests)**
- 解析器测试
- 搜索算法测试
- 数据库操作测试

**集成测试 (Integration Tests)**
- 索引创建端到端测试
- 搜索流程测试
- AI 服务集成测试

**UI 测试 (UI Tests)**
- 主要用户流程测试
- 界面交互测试

---

## 12. 未来扩展方向

### 12.1 短期扩展 (3-6 个月)

1. **更多文档格式支持**
   - RTF, ODT, EPUB
   - 图片 OCR (JPG, PNG)

2. **高级搜索功能**
   - 正则表达式搜索
   - 同义词搜索
   - 时间范围过滤

3. **性能优化**
   - GPU 加速 OCR
   - 分布式索引

### 12.2 中期扩展 (6-12 个月)

1. **云同步功能**
   - 索引云端备份
   - 多设备同步

2. **知识图谱**
   - 文档关系可视化
   - 智能推荐

3. **团队协作**
   - 共享索引
   - 权限管理

### 12.3 长期扩展 (1年+)

1. **跨平台支持**
   - macOS 版本
   - Linux 版本

2. **Web 版本**
   - 浏览器访问
   - 移动端支持

3. **企业版功能**
   - 中央管理控制台
   - 审计日志
   - 合规性支持

---

## 13. 技术债务管理

### 13.1 已知限制

1. **FTS5 中文分词:**
   - 当前使用 jieba，可能不如专业分词引擎精确
   - 解决方案：未来考虑集成 HanLP

2. **OCR 准确率:**
   - Tesseract 对低质量图像识别率有限
   - 解决方案：增加图像预处理步骤

3. **内存占用:**
   - 处理大文件时内存占用较高
   - 解决方案：实现流式处理

### 13.2 技术改进计划

- [ ] 引入异步 I/O (asyncio)
- [ ] 优化数据库查询（添加更多索引）
- [ ] 实现更智能的缓存策略
- [ ] 添加性能基准测试

---

## 14. 参考资料

### 14.1 技术文档

- [SQLite FTS5 Documentation](https://www.sqlite.org/fts5.html)
- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [Tesseract OCR Documentation](https://tesseract-ocr.github.io/)
- [DeepSeek API Documentation](https://platform.deepseek.com/docs)

### 14.2 设计模式

- 《设计模式：可复用面向对象软件的基础》
- 《架构整洁之道》
- 《Python 设计模式》

---

## 附录 A: 配置文件示例

```json
{
  "app": {
    "name": "Windows Search Tool",
    "version": "1.0.0",
    "theme": "light"
  },
  "database": {
    "cache_size_mb": 64,
    "page_size": 4096,
    "wal_mode": true
  },
  "indexing": {
    "parallel_workers": 4,
    "batch_size": 100,
    "excluded_extensions": [".exe", ".dll", ".sys"],
    "excluded_paths": ["C:\\Windows", "C:\\Program Files"]
  },
  "search": {
    "results_per_page": 20,
    "snippet_length": 100,
    "cache_size": 100
  },
  "ai": {
    "provider": "deepseek",
    "api_endpoint": "https://api.deepseek.com/v1",
    "model": "deepseek-chat",
    "timeout_seconds": 10,
    "max_retries": 3
  },
  "ocr": {
    "tesseract_path": "C:\\Program Files\\Tesseract-OCR\\tesseract.exe",
    "languages": ["chi_sim", "eng"],
    "confidence_threshold": 60
  }
}
```

---

**文档版本:** 1.0
**最后更新:** 2025-10-16
**审核状态:** Draft
**下一步:** 创建 UX 规格文档和详细用户故事
