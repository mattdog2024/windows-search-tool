#!/bin/bash
# Windows Search Tool - Epic 状态查看脚本
# 显示所有 Epic 的详细进度状态

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
MAGENTA='\033[0;35m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SRC_DIR="$PROJECT_ROOT/src"
TESTS_DIR="$PROJECT_ROOT/tests"
DOCS_DIR="$PROJECT_ROOT/docs"

# 项目名称参数
PROJECT_NAME="${1:-Windows Search Tool}"

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}  ${CYAN}${BOLD}Epic 状态报告${NC} - ${PROJECT_NAME}  ${BLUE}║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo ""

# 计算整体进度
calculate_progress() {
    local total=$1
    local completed=$2
    local percentage=$((completed * 100 / total))
    echo "$percentage"
}

# 绘制进度条
draw_progress_bar() {
    local percentage=$1
    local bar_length=30
    local filled=$((percentage * bar_length / 100))
    local empty=$((bar_length - filled))

    # 选择颜色
    local color=$GREEN
    if [ $percentage -lt 30 ]; then
        color=$RED
    elif [ $percentage -lt 70 ]; then
        color=$YELLOW
    fi

    echo -n -e "${color}["
    for ((i=0; i<filled; i++)); do echo -n "█"; done
    for ((i=0; i<empty; i++)); do echo -n "░"; done
    echo -e "]${NC} ${BOLD}${percentage}%${NC}"
}

# Epic 1: 核心搜索引擎
echo -e "${MAGENTA}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}${BOLD}Epic 1: 核心搜索引擎${NC}"
echo -e "${MAGENTA}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Story 计数
EPIC1_TOTAL=8
EPIC1_COMPLETED=0

# Story 1.1: 文档解析框架
echo -e "${CYAN}${BOLD}Story 1.1${NC} - 实现文档解析框架"
if [ -f "$SRC_DIR/parsers/base.py" ]; then
    echo -e "  状态: ${GREEN}✓ 已完成${NC}"
    EPIC1_COMPLETED=$((EPIC1_COMPLETED + 1))
    echo -e "  文件: [src/parsers/base.py](src/parsers/base.py)"

    # 检查关键组件
    if grep -q "class ParseResult" "$SRC_DIR/parsers/base.py" 2>/dev/null; then
        echo -e "  ├─ ${GREEN}✓${NC} ParseResult 数据类"
    fi
    if grep -q "class IDocumentParser" "$SRC_DIR/parsers/base.py" 2>/dev/null; then
        echo -e "  ├─ ${GREEN}✓${NC} IDocumentParser 接口"
    fi
    if grep -q "class ParserRegistry" "$SRC_DIR/parsers/base.py" 2>/dev/null; then
        echo -e "  └─ ${GREEN}✓${NC} ParserRegistry 注册器"
    fi
else
    echo -e "  状态: ${RED}✗ 未完成${NC}"
fi
echo ""

# Story 1.2: Office 格式解析器
echo -e "${CYAN}${BOLD}Story 1.2${NC} - 开发 Office 新格式解析器"
if [ -f "$SRC_DIR/parsers/office_parsers.py" ]; then
    echo -e "  状态: ${GREEN}✓ 已完成${NC}"
    EPIC1_COMPLETED=$((EPIC1_COMPLETED + 1))
    echo -e "  文件: [src/parsers/office_parsers.py](src/parsers/office_parsers.py)"

    # 检查解析器
    if grep -q "class DocxParser" "$SRC_DIR/parsers/office_parsers.py" 2>/dev/null; then
        echo -e "  ├─ ${GREEN}✓${NC} DocxParser (Word文档)"
    fi
    if grep -q "class XlsxParser" "$SRC_DIR/parsers/office_parsers.py" 2>/dev/null; then
        echo -e "  ├─ ${GREEN}✓${NC} XlsxParser (Excel文档)"
    fi
    if grep -q "class PptxParser" "$SRC_DIR/parsers/office_parsers.py" 2>/dev/null; then
        echo -e "  └─ ${GREEN}✓${NC} PptxParser (PowerPoint文档)"
    fi
else
    echo -e "  状态: ${RED}✗ 未完成${NC}"
fi
echo ""

# Story 1.3: PDF 处理和 OCR
echo -e "${CYAN}${BOLD}Story 1.3${NC} - 集成 PDF 处理和 OCR 功能"
if [ -f "$SRC_DIR/parsers/pdf_parser.py" ]; then
    echo -e "  状态: ${GREEN}✓ 已完成${NC}"
    EPIC1_COMPLETED=$((EPIC1_COMPLETED + 1))
    echo -e "  文件: [src/parsers/pdf_parser.py](src/parsers/pdf_parser.py)"

    if grep -q "class PdfParser" "$SRC_DIR/parsers/pdf_parser.py" 2>/dev/null; then
        echo -e "  ├─ ${GREEN}✓${NC} PdfParser 类"
    fi
    if grep -q "pytesseract\|tesseract" "$SRC_DIR/parsers/pdf_parser.py" 2>/dev/null; then
        echo -e "  └─ ${GREEN}✓${NC} OCR 支持 (Tesseract)"
    fi
else
    echo -e "  状态: ${RED}✗ 未完成${NC}"
fi
echo ""

# Story 1.4: SQLite FTS5 数据库
echo -e "${CYAN}${BOLD}Story 1.4${NC} - 构建 SQLite FTS5 索引数据库"
if [ -f "$SRC_DIR/data/db_manager.py" ]; then
    echo -e "  状态: ${GREEN}✓ 已完成${NC}"
    EPIC1_COMPLETED=$((EPIC1_COMPLETED + 1))
    echo -e "  文件: [src/data/db_manager.py](src/data/db_manager.py)"

    if grep -q "class DBManager" "$SRC_DIR/data/db_manager.py" 2>/dev/null; then
        echo -e "  ├─ ${GREEN}✓${NC} DBManager 类"
    fi
    if grep -q "fts5\|FTS5" "$SRC_DIR/data/db_manager.py" 2>/dev/null; then
        echo -e "  ├─ ${GREEN}✓${NC} FTS5 全文搜索"
    fi
    if grep -q "batch_insert\|批量" "$SRC_DIR/data/db_manager.py" 2>/dev/null; then
        echo -e "  └─ ${GREEN}✓${NC} 批量操作优化"
    fi
else
    echo -e "  状态: ${RED}✗ 未完成${NC}"
fi
echo ""

# Story 1.5: 索引管理器
echo -e "${CYAN}${BOLD}Story 1.5${NC} - 实现索引管理器"
if [ -f "$SRC_DIR/core/index_manager.py" ]; then
    echo -e "  状态: ${GREEN}✓ 已完成${NC}"
    EPIC1_COMPLETED=$((EPIC1_COMPLETED + 1))
    echo -e "  文件: [src/core/index_manager.py](src/core/index_manager.py)"

    if grep -q "class IndexManager" "$SRC_DIR/core/index_manager.py" 2>/dev/null; then
        echo -e "  ├─ ${GREEN}✓${NC} IndexManager 类"
    fi
    if grep -q "scan_directory\|扫描" "$SRC_DIR/core/index_manager.py" 2>/dev/null; then
        echo -e "  ├─ ${GREEN}✓${NC} 文件扫描功能"
    fi
    if grep -q "incremental\|增量" "$SRC_DIR/core/index_manager.py" 2>/dev/null; then
        echo -e "  ├─ ${GREEN}✓${NC} 增量索引"
    fi
    if grep -q "multiprocessing\|ProcessPoolExecutor" "$SRC_DIR/core/index_manager.py" 2>/dev/null; then
        echo -e "  ├─ ${GREEN}✓${NC} 多进程并行处理"
    fi
    if grep -q "progress\|进度" "$SRC_DIR/core/index_manager.py" 2>/dev/null; then
        echo -e "  └─ ${GREEN}✓${NC} 进度监控"
    fi
else
    echo -e "  状态: ${RED}✗ 未完成${NC}"
fi
echo ""

# Story 1.6: 搜索引擎核心
echo -e "${CYAN}${BOLD}Story 1.6${NC} - 开发搜索引擎核心"
if [ -f "$SRC_DIR/core/search_engine.py" ]; then
    echo -e "  状态: ${GREEN}✓ 已完成${NC}"
    EPIC1_COMPLETED=$((EPIC1_COMPLETED + 1))
    echo -e "  文件: [src/core/search_engine.py](src/core/search_engine.py)"

    if grep -q "class SearchEngine" "$SRC_DIR/core/search_engine.py" 2>/dev/null; then
        echo -e "  ├─ ${GREEN}✓${NC} SearchEngine 类"
    fi
    if grep -q "fts\|全文搜索" "$SRC_DIR/core/search_engine.py" 2>/dev/null; then
        echo -e "  ├─ ${GREEN}✓${NC} FTS5 全文搜索"
    fi
    if grep -q "cache\|缓存" "$SRC_DIR/core/search_engine.py" 2>/dev/null; then
        echo -e "  ├─ ${GREEN}✓${NC} 搜索缓存"
    fi
    if grep -q "suggest\|建议" "$SRC_DIR/core/search_engine.py" 2>/dev/null; then
        echo -e "  └─ ${GREEN}✓${NC} 搜索建议"
    fi
else
    echo -e "  状态: ${RED}✗ 未完成${NC}"
fi
echo ""

# Story 1.7: 语义搜索
echo -e "${CYAN}${BOLD}Story 1.7${NC} - 集成 AI 语义搜索"
if [ -f "$SRC_DIR/ai/semantic_search.py" ]; then
    echo -e "  状态: ${GREEN}✓ 已完成${NC}"
    EPIC1_COMPLETED=$((EPIC1_COMPLETED + 1))
else
    echo -e "  状态: ${YELLOW}⧖ 待开始${NC}"
fi
echo ""

# Story 1.8: 文档摘要
echo -e "${CYAN}${BOLD}Story 1.8${NC} - 实现文档智能摘要"
if [ -f "$SRC_DIR/ai/summarizer.py" ]; then
    echo -e "  状态: ${GREEN}✓ 已完成${NC}"
    EPIC1_COMPLETED=$((EPIC1_COMPLETED + 1))
else
    echo -e "  状态: ${YELLOW}⧖ 待开始${NC}"
fi
echo ""

# Epic 1 总进度
EPIC1_PROGRESS=$(calculate_progress $EPIC1_TOTAL $EPIC1_COMPLETED)
echo -e "${BOLD}Epic 1 总进度:${NC} ($EPIC1_COMPLETED/$EPIC1_TOTAL 个 Story)"
draw_progress_bar $EPIC1_PROGRESS
echo ""
echo ""

# Epic 2: 用户界面与 AI 增强
echo -e "${MAGENTA}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${MAGENTA}${BOLD}Epic 2: 用户界面与 AI 增强${NC}"
echo -e "${MAGENTA}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

EPIC2_TOTAL=6
EPIC2_COMPLETED=0

# Story 2.1: 主窗口框架
echo -e "${CYAN}${BOLD}Story 2.1${NC} - 设计并实现主窗口框架"
if [ -f "$SRC_DIR/ui/main_window.py" ]; then
    echo -e "  状态: ${GREEN}✓ 已完成${NC}"
    EPIC2_COMPLETED=$((EPIC2_COMPLETED + 1))
else
    echo -e "  状态: ${YELLOW}⧖ 待开始${NC}"
    echo -e "  ${RED}→ 建议: 选择 UI 框架 (PyQt6/Tkinter)${NC}"
fi
echo ""

# Story 2.2-2.6
for i in {2..6}; do
    echo -e "${CYAN}${BOLD}Story 2.$i${NC} - Epic 2 其他 Story"
    echo -e "  状态: ${YELLOW}⧖ 待开始${NC}"
    echo ""
done

# Epic 2 总进度
EPIC2_PROGRESS=$(calculate_progress $EPIC2_TOTAL $EPIC2_COMPLETED)
echo -e "${BOLD}Epic 2 总进度:${NC} ($EPIC2_COMPLETED/$EPIC2_TOTAL 个 Story)"
draw_progress_bar $EPIC2_PROGRESS
echo ""
echo ""

# 整体项目进度
echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}  ${BOLD}整体项目进度${NC}                              ${BLUE}║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""

TOTAL_STORIES=$((EPIC1_TOTAL + EPIC2_TOTAL))
TOTAL_COMPLETED=$((EPIC1_COMPLETED + EPIC2_COMPLETED))
TOTAL_PROGRESS=$(calculate_progress $TOTAL_STORIES $TOTAL_COMPLETED)

echo -e "${BOLD}已完成:${NC} $TOTAL_COMPLETED/$TOTAL_STORIES 个 Story"
draw_progress_bar $TOTAL_PROGRESS
echo ""

# 统计信息
echo -e "${CYAN}${BOLD}📊 统计信息:${NC}"
echo -e "  Epic 1 (核心搜索引擎): ${GREEN}$EPIC1_COMPLETED${NC}/${EPIC1_TOTAL} (${EPIC1_PROGRESS}%)"
echo -e "  Epic 2 (用户界面): ${YELLOW}$EPIC2_COMPLETED${NC}/${EPIC2_TOTAL} (${EPIC2_PROGRESS}%)"
echo ""

# 测试覆盖率
echo -e "${CYAN}${BOLD}🧪 测试覆盖率:${NC}"
if command -v pytest &> /dev/null; then
    cd "$PROJECT_ROOT"
    COVERAGE_OUTPUT=$(pytest --cov=src --cov-report=term-missing -q 2>&1 || true)

    # 提取覆盖率百分比
    if echo "$COVERAGE_OUTPUT" | grep -q "TOTAL"; then
        COVERAGE_PCT=$(echo "$COVERAGE_OUTPUT" | grep "TOTAL" | awk '{print $NF}' | sed 's/%//')
        echo -e "  总体覆盖率: ${BOLD}${COVERAGE_PCT}%${NC}"

        if [ "$COVERAGE_PCT" -ge 80 ]; then
            echo -e "  ${GREEN}✓ 覆盖率良好${NC}"
        elif [ "$COVERAGE_PCT" -ge 60 ]; then
            echo -e "  ${YELLOW}⚠ 需要提高覆盖率${NC}"
        else
            echo -e "  ${RED}✗ 覆盖率较低${NC}"
        fi
    else
        echo -e "  ${YELLOW}⚠ 无法获取覆盖率数据${NC}"
    fi
else
    echo -e "  ${YELLOW}⚠ pytest 未安装${NC}"
fi
echo ""

# 最近提交
echo -e "${CYAN}${BOLD}📝 最近 5 次提交:${NC}"
git log --oneline -5 --color=always 2>/dev/null | sed 's/^/  /' || echo -e "  ${RED}无法获取 Git 历史${NC}"
echo ""

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}  ${GREEN}${BOLD}Epic 状态报告完成!${NC}                        ${BLUE}║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
