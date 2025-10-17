#!/bin/bash
# Windows Search Tool - 项目管理下一步脚本
# 分析当前进度并建议下一步行动

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
DOCS_DIR="$PROJECT_ROOT/docs"
SRC_DIR="$PROJECT_ROOT/src"
TESTS_DIR="$PROJECT_ROOT/tests"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  项目管理 - 下一步建议${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 分析已完成的工作
echo -e "${CYAN}${BOLD}📊 分析当前进度...${NC}"
echo ""

# 检查已实现的核心模块
echo -e "${YELLOW}已完成模块:${NC}"

# 核心模块检查
if [ -f "$SRC_DIR/parsers/base.py" ]; then
    echo -e "  ${GREEN}✓${NC} 解析器框架 (parsers/base.py)"
else
    echo -e "  ${RED}○${NC} 解析器框架 (未实现)"
fi

if [ -f "$SRC_DIR/parsers/text_parser.py" ]; then
    echo -e "  ${GREEN}✓${NC} 文本解析器"
else
    echo -e "  ${RED}○${NC} 文本解析器 (未实现)"
fi

if [ -f "$SRC_DIR/parsers/office_parsers.py" ]; then
    echo -e "  ${GREEN}✓${NC} Office解析器"
else
    echo -e "  ${RED}○${NC} Office解析器 (未实现)"
fi

if [ -f "$SRC_DIR/parsers/pdf_parser.py" ]; then
    echo -e "  ${GREEN}✓${NC} PDF解析器"
else
    echo -e "  ${RED}○${NC} PDF解析器 (未实现)"
fi

if [ -f "$SRC_DIR/data/db_manager.py" ]; then
    echo -e "  ${GREEN}✓${NC} 数据库管理器 (data/db_manager.py)"
else
    echo -e "  ${RED}○${NC} 数据库管理器 (未实现)"
fi

if [ -f "$SRC_DIR/data/models.py" ]; then
    echo -e "  ${GREEN}✓${NC} 数据模型"
else
    echo -e "  ${RED}○${NC} 数据模型 (未实现)"
fi

if [ -f "$SRC_DIR/core/index_manager.py" ]; then
    echo -e "  ${GREEN}✓${NC} 索引管理器 (core/index_manager.py)"
else
    echo -e "  ${RED}○${NC} 索引管理器 (未实现)"
fi

if [ -f "$SRC_DIR/core/search_engine.py" ]; then
    echo -e "  ${GREEN}✓${NC} 搜索引擎 (core/search_engine.py)"
else
    echo -e "  ${RED}○${NC} 搜索引擎 (未实现)"
fi

echo ""

# 统计测试覆盖率
echo -e "${CYAN}${BOLD}🧪 检查测试状态...${NC}"
if command -v pytest &> /dev/null; then
    cd "$PROJECT_ROOT"

    # 运行测试并获取覆盖率
    if pytest --cov=src --cov-report=term-missing --quiet 2>/dev/null; then
        echo -e "${GREEN}✓ 所有测试通过${NC}"
    else
        echo -e "${YELLOW}⚠ 部分测试失败或需要更新${NC}"
    fi
else
    echo -e "${YELLOW}⚠ pytest 未安装，无法运行测试${NC}"
fi

echo ""

# 分析 Git 提交历史
echo -e "${CYAN}${BOLD}📝 最近完成的工作:${NC}"
git log --oneline -5 --color=always 2>/dev/null | sed 's/^/  /'
echo ""

# 检查用户故事文档
echo -e "${CYAN}${BOLD}📖 Story 进度分析:${NC}"
echo ""

# Story 1.1-1.4 状态
echo -e "${YELLOW}Epic 1: 核心搜索引擎${NC}"
echo ""

echo -e "  ${BOLD}Story 1.1${NC} - 实现文档解析框架"
if [ -f "$SRC_DIR/parsers/base.py" ]; then
    echo -e "    ${GREEN}✓ 状态: 已完成${NC}"
    echo -e "    ├─ ParseResult 数据类"
    echo -e "    ├─ IDocumentParser 接口"
    echo -e "    └─ ParserFactory 工厂类"
else
    echo -e "    ${RED}✗ 状态: 未开始${NC}"
fi
echo ""

echo -e "  ${BOLD}Story 1.2${NC} - 开发 Office 新格式解析器"
if [ -f "$SRC_DIR/parsers/office_parsers.py" ]; then
    echo -e "    ${GREEN}✓ 状态: 已完成${NC}"
    echo -e "    ├─ DocxParser (Word文档)"
    echo -e "    ├─ XlsxParser (Excel文档)"
    echo -e "    └─ PptxParser (PowerPoint文档)"
else
    echo -e "    ${YELLOW}◐ 状态: 进行中${NC}"
    echo -e "    └─ ${RED}待实现: Office解析器${NC}"
fi
echo ""

echo -e "  ${BOLD}Story 1.3${NC} - 集成 PDF 处理和 OCR 功能"
if [ -f "$SRC_DIR/parsers/pdf_parser.py" ]; then
    echo -e "    ${GREEN}✓ 状态: 已完成${NC}"
    echo -e "    ├─ PDF文本提取"
    echo -e "    └─ OCR扫描版支持"
else
    echo -e "    ${YELLOW}◐ 状态: 进行中${NC}"
    echo -e "    └─ ${RED}待实现: PDF解析器${NC}"
fi
echo ""

echo -e "  ${BOLD}Story 1.4${NC} - 构建 SQLite FTS5 索引数据库"
if [ -f "$SRC_DIR/data/db_manager.py" ]; then
    echo -e "    ${GREEN}✓ 状态: 已完成${NC}"
    echo -e "    ├─ 数据库模式设计"
    echo -e "    ├─ DBManager 类"
    echo -e "    ├─ FTS5 全文搜索"
    echo -e "    └─ 批量操作优化"
else
    echo -e "    ${RED}✗ 状态: 未开始${NC}"
fi
echo ""

echo -e "  ${BOLD}Story 1.5${NC} - 实现索引管理器"
if [ -f "$SRC_DIR/core/index_manager.py" ]; then
    echo -e "    ${GREEN}✓ 状态: 已完成${NC}"
    echo -e "    ├─ 文件扫描"
    echo -e "    ├─ 增量索引"
    echo -e "    ├─ 多进程并行处理"
    echo -e "    └─ 进度监控"
else
    echo -e "    ${RED}✗ 状态: 未开始${NC}"
fi
echo ""

echo -e "  ${BOLD}Story 1.6${NC} - 开发搜索引擎核心"
if [ -f "$SRC_DIR/core/search_engine.py" ]; then
    echo -e "    ${GREEN}✓ 状态: 已完成${NC}"
    echo -e "    ├─ FTS5 全文搜索"
    echo -e "    ├─ 高级搜索功能"
    echo -e "    ├─ 搜索缓存"
    echo -e "    └─ 搜索建议"
else
    echo -e "    ${YELLOW}◐ 状态: 进行中${NC}"
    echo -e "    └─ ${RED}待实现: SearchEngine 类${NC}"
fi
echo ""

# 建议下一步行动
echo -e "${BLUE}========================================${NC}"
echo -e "${CYAN}${BOLD}🎯 建议的下一步行动:${NC}"
echo ""

next_actions=0

# 检查是否需要完成解析器
if [ ! -f "$SRC_DIR/parsers/office_parsers.py" ]; then
    next_actions=$((next_actions + 1))
    echo -e "${YELLOW}${next_actions}.${NC} ${BOLD}实现 Office 文档解析器${NC}"
    echo -e "   ├─ 文件: src/parsers/office_parsers.py"
    echo -e "   ├─ 实现: DocxParser, XlsxParser, PptxParser"
    echo -e "   ├─ 依赖: python-docx, openpyxl, python-pptx"
    echo -e "   └─ Story: 1.2"
    echo ""
fi

if [ ! -f "$SRC_DIR/parsers/pdf_parser.py" ]; then
    next_actions=$((next_actions + 1))
    echo -e "${YELLOW}${next_actions}.${NC} ${BOLD}实现 PDF 解析器和 OCR${NC}"
    echo -e "   ├─ 文件: src/parsers/pdf_parser.py"
    echo -e "   ├─ 实现: PdfParser 类"
    echo -e "   ├─ 依赖: pdfplumber, pytesseract, pdf2image"
    echo -e "   └─ Story: 1.3"
    echo ""
fi

# 检查是否需要完成搜索引擎高级功能
if [ -f "$SRC_DIR/core/search_engine.py" ]; then
    next_actions=$((next_actions + 1))
    echo -e "${YELLOW}${next_actions}.${NC} ${BOLD}完善搜索引擎高级功能${NC}"
    echo -e "   ├─ 实现语义搜索 (使用 sentence-transformers)"
    echo -e "   ├─ 实现搜索结果排序优化"
    echo -e "   ├─ 添加搜索历史记录"
    echo -e "   └─ Story: 1.6 扩展"
    echo ""
fi

# 检查是否需要开始 UI 开发
if [ $next_actions -eq 0 ] || [ -f "$SRC_DIR/core/search_engine.py" ]; then
    next_actions=$((next_actions + 1))
    echo -e "${YELLOW}${next_actions}.${NC} ${BOLD}开始用户界面开发 (Epic 2)${NC}"
    echo -e "   ├─ 技术选型: PyQt6 或 Tkinter"
    echo -e "   ├─ 实现主窗口框架"
    echo -e "   ├─ 实现搜索界面"
    echo -e "   └─ Story: 2.1"
    echo ""
fi

# 持续改进
next_actions=$((next_actions + 1))
echo -e "${YELLOW}${next_actions}.${NC} ${BOLD}持续改进和优化${NC}"
echo -e "   ├─ 提高测试覆盖率 (目标 >95%)"
echo -e "   ├─ 性能优化和基准测试"
echo -e "   ├─ 完善文档和注释"
echo -e "   └─ 代码重构和质量提升"
echo ""

# 快速命令参考
echo -e "${BLUE}========================================${NC}"
echo -e "${CYAN}${BOLD}⚡ 快速命令参考:${NC}"
echo ""
echo -e "  ${GREEN}pytest --cov=src${NC}           运行测试并查看覆盖率"
echo -e "  ${GREEN}pytest -v${NC}                  详细测试输出"
echo -e "  ${GREEN}git status${NC}                 查看当前状态"
echo -e "  ${GREEN}git log --oneline -10${NC}      查看提交历史"
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}${BOLD}✨ 继续加油! 项目进展顺利!${NC}"
echo -e "${BLUE}========================================${NC}"
