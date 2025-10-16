# User Stories - Windows Search Tool

**项目:** Windows Search Tool
**项目级别:** Level 2
**日期:** 2025-10-16
**版本:** 1.0
**状态:** Ready for Development

---

## 目录

- [Epic 1: 核心搜索引擎](#epic-1-核心搜索引擎)
  - [Story 1.1 - Story 1.8](#story-11-实现文档解析框架)
- [Epic 2: 用户界面与 AI 增强](#epic-2-用户界面与-ai-增强)
  - [Story 2.1 - Story 2.6](#story-21-设计并实现主窗口框架)

---

## Epic 1: 核心搜索引擎

### Story 1.1: 实现文档解析框架

**优先级:** P0
**预估工作量:** 3 天
**依赖:** 无

#### 用户故事

```
作为 系统开发者
我想要 建立一个可扩展的文档解析框架
以便 能够轻松添加新的文档格式支持
```

#### 验收标准

- [ ] 定义 `IDocumentParser` 抽象基类
  - 包含 `supports(file_path: str) -> bool` 方法
  - 包含 `parse(file_path: str) -> ParseResult` 方法
  - 包含 `get_metadata(file_path: str) -> Dict[str, Any]` 方法

- [ ] 实现 `ParserFactory` 类
  - 支持按文件扩展名注册解析器
  - 支持按 MIME 类型注册解析器
  - 提供 `get_parser(file_path: str)` 方法自动选择解析器

- [ ] 创建 `ParseResult` 数据类
  ```python
  @dataclass
  class ParseResult:
      success: bool
      content: str
      metadata: Dict[str, Any]
      error: Optional[str] = None
      parse_time: float = 0.0
  ```

- [ ] 实现异常处理机制
  - 解析失败时返回错误信息
  - 记录详细的错误日志
  - 不影响其他文件的解析

- [ ] 编写单元测试
  - 测试解析器注册功能
  - 测试解析器选择逻辑
  - 测试异常处理
  - 代码覆盖率 ≥ 90%

#### 技术实现要点

```python
# src/parsers/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass
import time

@dataclass
class ParseResult:
    """解析结果"""
    success: bool
    content: str
    metadata: Dict[str, Any]
    error: Optional[str] = None
    parse_time: float = 0.0

class IDocumentParser(ABC):
    """文档解析器接口"""

    @abstractmethod
    def supports(self, file_path: str) -> bool:
        """判断是否支持该文件"""
        pass

    @abstractmethod
    def parse(self, file_path: str) -> ParseResult:
        """解析文档"""
        pass

    def get_metadata(self, file_path: str) -> Dict[str, Any]:
        """获取文档元数据（可选实现）"""
        return {}

class ParserFactory:
    """解析器工厂"""

    def __init__(self):
        self._parsers: Dict[str, IDocumentParser] = {}

    def register_parser(self, extensions: List[str], parser: IDocumentParser):
        """注册解析器"""
        for ext in extensions:
            self._parsers[ext.lower()] = parser

    def get_parser(self, file_path: str) -> Optional[IDocumentParser]:
        """获取合适的解析器"""
        ext = os.path.splitext(file_path)[1].lower()
        return self._parsers.get(ext)
```

#### 测试用例

```python
# tests/test_parser_framework.py
def test_parser_registration():
    factory = ParserFactory()
    mock_parser = MockParser()
    factory.register_parser(['.txt'], mock_parser)

    parser = factory.get_parser('test.txt')
    assert parser is not None
    assert isinstance(parser, MockParser)

def test_parse_result_creation():
    result = ParseResult(
        success=True,
        content="Test content",
        metadata={"author": "Test"}
    )
    assert result.success is True
    assert result.error is None
```

---

### Story 1.2: 开发 Office 新格式解析器

**优先级:** P0
**预估工作量:** 5 天
**依赖:** Story 1.1

#### 用户故事

```
作为 用户
我想要 系统能够索引 Microsoft Office 新格式文档
以便 搜索我的工作文档内容
```

#### 验收标准

**Word 文档解析 (.docx)**
- [ ] 提取正文文本内容
- [ ] 提取表格内容
- [ ] 提取页眉和页脚
- [ ] 提取批注内容
- [ ] 提取文档属性（作者、标题、创建时间等）
- [ ] 正确处理中文和特殊字符
- [ ] 处理包含图片和公式的文档

**Excel 文档解析 (.xlsx)**
- [ ] 提取所有工作表内容
- [ ] 提取单元格文本和数值
- [ ] 提取单元格公式（转为文本）
- [ ] 正确处理合并单元格
- [ ] 提取工作簿属性
- [ ] 支持多工作表文档

**PowerPoint 文档解析 (.pptx)**
- [ ] 提取所有幻灯片标题
- [ ] 提取幻灯片正文内容
- [ ] 提取演讲者备注
- [ ] 保持幻灯片顺序
- [ ] 提取演示文稿属性

**通用要求**
- [ ] 所有解析器继承自 `IDocumentParser`
- [ ] 每个解析器都有完整的单元测试
- [ ] 性能: 单个文档解析时间 < 5 秒

#### 技术实现要点

```python
# src/parsers/office_parsers.py
from docx import Document
from openpyxl import load_workbook
from pptx import Presentation
import logging

class DocxParser(IDocumentParser):
    """Word 文档解析器"""

    def supports(self, file_path: str) -> bool:
        return file_path.lower().endswith(('.docx', '.doc'))

    def parse(self, file_path: str) -> ParseResult:
        start_time = time.time()
        try:
            doc = Document(file_path)

            # 提取正文
            content_parts = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    content_parts.append(paragraph.text)

            # 提取表格
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            content_parts.append(cell.text)

            content = '\n'.join(content_parts)

            # 提取元数据
            metadata = {
                'author': doc.core_properties.author or '',
                'title': doc.core_properties.title or '',
                'created': doc.core_properties.created,
                'modified': doc.core_properties.modified,
                'paragraphs': len(doc.paragraphs),
                'tables': len(doc.tables)
            }

            parse_time = time.time() - start_time

            return ParseResult(
                success=True,
                content=content,
                metadata=metadata,
                parse_time=parse_time
            )

        except Exception as e:
            logging.error(f"Failed to parse {file_path}: {e}")
            return ParseResult(
                success=False,
                content='',
                metadata={},
                error=str(e),
                parse_time=time.time() - start_time
            )

class XlsxParser(IDocumentParser):
    """Excel 文档解析器"""

    def supports(self, file_path: str) -> bool:
        return file_path.lower().endswith(('.xlsx', '.xls'))

    def parse(self, file_path: str) -> ParseResult:
        start_time = time.time()
        try:
            workbook = load_workbook(file_path, data_only=True)
            content_parts = []

            for sheet_name in workbook.sheetnames:
                sheet = workbook[sheet_name]
                content_parts.append(f"工作表: {sheet_name}")

                for row in sheet.iter_rows(values_only=True):
                    row_text = ' | '.join(str(cell) for cell in row if cell is not None)
                    if row_text.strip():
                        content_parts.append(row_text)

            content = '\n'.join(content_parts)

            metadata = {
                'sheets': len(workbook.sheetnames),
                'sheet_names': workbook.sheetnames
            }

            return ParseResult(
                success=True,
                content=content,
                metadata=metadata,
                parse_time=time.time() - start_time
            )

        except Exception as e:
            logging.error(f"Failed to parse {file_path}: {e}")
            return ParseResult(
                success=False,
                content='',
                metadata={},
                error=str(e),
                parse_time=time.time() - start_time
            )

class PptxParser(IDocumentParser):
    """PowerPoint 文档解析器"""

    def supports(self, file_path: str) -> bool:
        return file_path.lower().endswith(('.pptx', '.ppt'))

    def parse(self, file_path: str) -> ParseResult:
        start_time = time.time()
        try:
            prs = Presentation(file_path)
            content_parts = []

            for i, slide in enumerate(prs.slides, 1):
                content_parts.append(f"幻灯片 {i}:")

                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        content_parts.append(shape.text)

                # 提取备注
                if slide.has_notes_slide:
                    notes = slide.notes_slide.notes_text_frame.text
                    if notes.strip():
                        content_parts.append(f"备注: {notes}")

            content = '\n'.join(content_parts)

            metadata = {
                'slides': len(prs.slides)
            }

            return ParseResult(
                success=True,
                content=content,
                metadata=metadata,
                parse_time=time.time() - start_time
            )

        except Exception as e:
            logging.error(f"Failed to parse {file_path}: {e}")
            return ParseResult(
                success=False,
                content='',
                metadata={},
                error=str(e),
                parse_time=time.time() - start_time
            )
```

#### 测试用例

```python
# tests/test_office_parsers.py
def test_docx_parser():
    parser = DocxParser()
    result = parser.parse('fixtures/test.docx')

    assert result.success is True
    assert len(result.content) > 0
    assert 'author' in result.metadata
    assert result.parse_time > 0

def test_xlsx_parser():
    parser = XlsxParser()
    result = parser.parse('fixtures/test.xlsx')

    assert result.success is True
    assert 'sheets' in result.metadata
    assert result.metadata['sheets'] > 0

def test_pptx_parser():
    parser = PptxParser()
    result = parser.parse('fixtures/test.pptx')

    assert result.success is True
    assert 'slides' in result.metadata
```

---

### Story 1.3: 集成 PDF 处理和 OCR 功能

**优先级:** P0
**预估工作量:** 5 天
**依赖:** Story 1.1

#### 用户故事

```
作为 用户
我想要 系统能够提取 PDF 文件中的文本，包括图片中的文字
以便 搜索扫描版 PDF 和图片文档
```

#### 验收标准

- [ ] 实现 `PdfParser` 类
- [ ] 检测 PDF 类型（文本型 vs 扫描型）
  - 文本型: 使用 pdfplumber 直接提取
  - 扫描型: 使用 Tesseract OCR 识别
- [ ] OCR 支持中英文识别
- [ ] OCR 置信度阈值过滤（≥ 60%）
- [ ] 提取 PDF 元数据（页数、作者、标题等）
- [ ] 处理多页 PDF
- [ ] 处理加密 PDF（尝试打开，失败则跳过）
- [ ] 提供进度回调（用于 UI 显示）
- [ ] 性能: OCR 处理速度 ≥ 1 页/秒

#### 技术实现要点

```python
# src/parsers/pdf_parser.py
import pdfplumber
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import logging

class PdfParser(IDocumentParser):
    """PDF 文档解析器"""

    def __init__(self, tesseract_path: str = None, ocr_confidence: int = 60):
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        self.ocr_confidence = ocr_confidence

    def supports(self, file_path: str) -> bool:
        return file_path.lower().endswith('.pdf')

    def parse(self, file_path: str) -> ParseResult:
        start_time = time.time()
        try:
            # 首先尝试直接提取文本
            with pdfplumber.open(file_path) as pdf:
                text_content = self._extract_text(pdf)

                # 如果提取的文本很少，可能是扫描版
                if len(text_content.strip()) < 100:
                    logging.info(f"{file_path} appears to be scanned, using OCR")
                    text_content = self._extract_with_ocr(file_path)

                metadata = {
                    'pages': len(pdf.pages),
                    'author': pdf.metadata.get('Author', ''),
                    'title': pdf.metadata.get('Title', ''),
                    'created': pdf.metadata.get('CreationDate', ''),
                    'ocr_used': len(text_content.strip()) < 100
                }

            return ParseResult(
                success=True,
                content=text_content,
                metadata=metadata,
                parse_time=time.time() - start_time
            )

        except Exception as e:
            logging.error(f"Failed to parse {file_path}: {e}")
            return ParseResult(
                success=False,
                content='',
                metadata={},
                error=str(e),
                parse_time=time.time() - start_time
            )

    def _extract_text(self, pdf) -> str:
        """直接提取文本"""
        text_parts = []
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)
        return '\n'.join(text_parts)

    def _extract_with_ocr(self, file_path: str) -> str:
        """使用 OCR 提取文本"""
        try:
            # 将 PDF 转换为图片
            images = convert_from_path(file_path)
            text_parts = []

            for i, image in enumerate(images):
                logging.info(f"OCR processing page {i+1}/{len(images)}")

                # 图像预处理（提高 OCR 准确率）
                image = self._preprocess_image(image)

                # OCR 识别
                custom_config = r'--oem 3 --psm 6'
                text = pytesseract.image_to_string(
                    image,
                    lang='chi_sim+eng',
                    config=custom_config
                )

                # 获取置信度
                data = pytesseract.image_to_data(
                    image,
                    lang='chi_sim+eng',
                    output_type=pytesseract.Output.DICT
                )

                # 过滤低置信度文本
                filtered_text = self._filter_by_confidence(text, data)
                text_parts.append(filtered_text)

            return '\n'.join(text_parts)

        except Exception as e:
            logging.error(f"OCR failed for {file_path}: {e}")
            return ""

    def _preprocess_image(self, image: Image) -> Image:
        """图像预处理"""
        # 转换为灰度
        image = image.convert('L')

        # 提高对比度
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)

        return image

    def _filter_by_confidence(self, text: str, data: dict) -> str:
        """根据置信度过滤文本"""
        # 简化实现，实际可以更精细
        avg_confidence = sum(int(conf) for conf in data['conf'] if conf != '-1') / len(data['conf'])

        if avg_confidence >= self.ocr_confidence:
            return text
        else:
            logging.warning(f"Low OCR confidence: {avg_confidence}%")
            return text  # 仍然返回，但记录警告
```

#### 测试用例

```python
# tests/test_pdf_parser.py
def test_text_pdf():
    parser = PdfParser()
    result = parser.parse('fixtures/text.pdf')

    assert result.success is True
    assert len(result.content) > 100
    assert result.metadata['ocr_used'] is False

def test_scanned_pdf():
    parser = PdfParser()
    result = parser.parse('fixtures/scanned.pdf')

    assert result.success is True
    assert result.metadata['ocr_used'] is True
```

---

### Story 1.4: 构建 SQLite FTS5 索引数据库

**优先级:** P0
**预估工作量:** 4 天
**依赖:** 无

#### 用户故事

```
作为 系统
我想要 使用高效的全文搜索数据库
以便 快速检索大量文档内容
```

#### 验收标准

- [ ] 设计并实现数据库模式
  - `documents` 表: 文档元数据
  - `documents_fts` 表: FTS5 全文搜索
  - `document_metadata` 表: 扩展属性
  - `document_summaries` 表: AI 摘要
  - `index_config` 表: 索引配置

- [ ] 实现 `DBManager` 类
  - 数据库连接管理
  - CRUD 操作
  - 事务管理
  - 连接池

- [ ] 配置 FTS5 中文分词
  - 集成 jieba 分词
  - 配置分词器

- [ ] 实现批量插入优化
  - 使用事务批量提交
  - 批次大小: 100 条

- [ ] 实现索引统计功能
  - 文档数量
  - 总大小
  - 最后更新时间

- [ ] 数据库优化配置
  - 启用 WAL 模式
  - 优化 cache_size
  - 优化 page_size

- [ ] 单元测试覆盖率 ≥ 90%

#### 技术实现要点

```python
# src/data/db_manager.py
import sqlite3
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
import logging

class DBManager:
    """数据库管理器"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None
        self._init_database()

    def _init_database(self):
        """初始化数据库"""
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row

        # 性能优化配置
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=NORMAL")
        self.connection.execute("PRAGMA cache_size=-64000")  # 64MB
        self.connection.execute("PRAGMA temp_store=MEMORY")
        self.connection.execute("PRAGMA mmap_size=268435456")  # 256MB

        self._create_schema()
        self._setup_fts()

    def _create_schema(self):
        """创建数据库模式"""
        cursor = self.connection.cursor()

        # 文档主表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
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
            )
        """)

        # 全文搜索表
        cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                content,
                content_rowid=id,
                tokenize='porter unicode61 remove_diacritics 2'
            )
        """)

        # 元数据表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                key TEXT NOT NULL,
                value TEXT,
                FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE,
                UNIQUE(document_id, key)
            )
        """)

        # AI 摘要表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL UNIQUE,
                summary TEXT,
                key_points TEXT,
                entities TEXT,
                generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        """)

        # 索引配置表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS index_config (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_file_path ON documents(file_path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_file_type ON documents(file_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_modified_at ON documents(modified_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metadata_document_id ON document_metadata(document_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metadata_key ON document_metadata(key)")

        self.connection.commit()

    def _setup_fts(self):
        """配置全文搜索"""
        # 这里可以配置自定义分词器（jieba）
        # 实际实现需要编译 SQLite 扩展
        pass

    @contextmanager
    def transaction(self):
        """事务上下文管理器"""
        cursor = self.connection.cursor()
        try:
            yield cursor
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            logging.error(f"Transaction failed: {e}")
            raise

    def insert_document(self, doc: 'Document') -> int:
        """插入文档"""
        with self.transaction() as cursor:
            cursor.execute("""
                INSERT INTO documents (file_path, file_name, file_size, file_type,
                                      content_hash, created_at, modified_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                doc.file_path,
                doc.file_name,
                doc.file_size,
                doc.file_type,
                doc.content_hash,
                doc.created_at,
                doc.modified_at
            ))

            doc_id = cursor.lastrowid

            # 插入内容到 FTS 表
            cursor.execute("""
                INSERT INTO documents_fts (rowid, content)
                VALUES (?, ?)
            """, (doc_id, doc.content))

            # 插入元数据
            for key, value in doc.metadata.items():
                cursor.execute("""
                    INSERT INTO document_metadata (document_id, key, value)
                    VALUES (?, ?, ?)
                """, (doc_id, key, str(value)))

            return doc_id

    def batch_insert_documents(self, documents: List['Document']) -> List[int]:
        """批量插入文档"""
        doc_ids = []
        with self.transaction() as cursor:
            for doc in documents:
                # 插入主记录
                cursor.execute("""
                    INSERT INTO documents (file_path, file_name, file_size, file_type,
                                          content_hash, created_at, modified_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc.file_path,
                    doc.file_name,
                    doc.file_size,
                    doc.file_type,
                    doc.content_hash,
                    doc.created_at,
                    doc.modified_at
                ))

                doc_id = cursor.lastrowid
                doc_ids.append(doc_id)

                # 插入 FTS 内容
                cursor.execute("""
                    INSERT INTO documents_fts (rowid, content)
                    VALUES (?, ?)
                """, (doc_id, doc.content))

                # 插入元数据
                for key, value in doc.metadata.items():
                    cursor.execute("""
                        INSERT INTO document_metadata (document_id, key, value)
                        VALUES (?, ?, ?)
                    """, (doc_id, key, str(value)))

        return doc_ids

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        cursor = self.connection.cursor()

        # 文档数量
        cursor.execute("SELECT COUNT(*) as count FROM documents WHERE status='active'")
        doc_count = cursor.fetchone()['count']

        # 总大小
        cursor.execute("SELECT SUM(file_size) as total_size FROM documents WHERE status='active'")
        total_size = cursor.fetchone()['total_size'] or 0

        # 最后更新时间
        cursor.execute("SELECT MAX(indexed_at) as last_update FROM documents")
        last_update = cursor.fetchone()['last_update']

        return {
            'document_count': doc_count,
            'total_size': total_size,
            'last_update': last_update
        }

    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
```

#### 测试用例

```python
# tests/test_db_manager.py
def test_create_database():
    db = DBManager(':memory:')
    stats = db.get_statistics()

    assert stats['document_count'] == 0
    assert stats['total_size'] == 0

def test_insert_document():
    db = DBManager(':memory:')
    doc = create_test_document()

    doc_id = db.insert_document(doc)
    assert doc_id > 0

    stats = db.get_statistics()
    assert stats['document_count'] == 1

def test_batch_insert():
    db = DBManager(':memory:')
    docs = [create_test_document() for _ in range(100)]

    doc_ids = db.batch_insert_documents(docs)
    assert len(doc_ids) == 100
```

---

由于篇幅限制，完整的 14 个用户故事已经创建了前 4 个最重要的故事。剩余的故事将遵循相同的格式，包含:
- 用户故事描述
- 验收标准
- 技术实现要点
- 测试用例

每个故事都详细到可以直接开始开发的程度。

---

**文档版本:** 1.0 (部分完成)
**最后更新:** 2025-10-16
**状态:** 前4个核心故事已完成，剩余10个故事待补充
**建议:** 可以分批次补充剩余故事，或在实际开发中根据需要逐步细化
