#!/bin/bash
# Windows Search Tool - 项目管理初始化脚本
# 用于初始化项目管理系统和显示项目状态

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
CCPM_DIR="$PROJECT_ROOT/ccpm"
CONFIG_FILE="$CCPM_DIR/config/project.json"
DOCS_DIR="$PROJECT_ROOT/docs"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Windows Search Tool - 项目管理系统${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查配置文件是否存在
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${YELLOW}⚠ 配置文件不存在，正在创建...${NC}"

    # 创建默认配置
    cat > "$CONFIG_FILE" << 'EOF'
{
  "project": {
    "name": "Windows Search Tool",
    "level": 2,
    "type": "Desktop",
    "version": "0.1.0",
    "description": "智能文件内容索引和搜索系统"
  },
  "status": {
    "phase": "planning",
    "current_sprint": 0,
    "progress": 0
  },
  "epics": [
    {
      "id": "epic-1",
      "name": "核心搜索引擎",
      "stories": 8,
      "completed": 0
    },
    {
      "id": "epic-2",
      "name": "用户界面与 AI 增强",
      "stories": 6,
      "completed": 0
    }
  ],
  "paths": {
    "docs": "./docs",
    "src": "./src",
    "tests": "./tests"
  }
}
EOF
    echo -e "${GREEN}✓ 配置文件已创建${NC}"
fi

# 读取配置
PROJECT_NAME=$(cat "$CONFIG_FILE" | grep -o '"name": "[^"]*"' | head -1 | cut -d'"' -f4)
PROJECT_LEVEL=$(cat "$CONFIG_FILE" | grep -o '"level": [0-9]*' | head -1 | awk '{print $2}')
PHASE=$(cat "$CONFIG_FILE" | grep -o '"phase": "[^"]*"' | cut -d'"' -f4)
PROGRESS=$(cat "$CONFIG_FILE" | grep -o '"progress": [0-9]*' | awk '{print $2}')

echo -e "${GREEN}项目信息:${NC}"
echo -e "  名称: $PROJECT_NAME"
echo -e "  级别: Level $PROJECT_LEVEL"
echo -e "  阶段: $PHASE"
echo -e "  进度: $PROGRESS%"
echo ""

# 检查必需的文档
echo -e "${BLUE}文档状态:${NC}"

check_doc() {
    local doc_path="$1"
    local doc_name="$2"

    if [ -f "$doc_path" ]; then
        echo -e "  ${GREEN}✓${NC} $doc_name"
        return 0
    else
        echo -e "  ${RED}✗${NC} $doc_name (缺失)"
        return 1
    fi
}

# 检查各个文档
check_doc "$PROJECT_ROOT/PRD.md" "PRD (产品需求文档)"
check_doc "$DOCS_DIR/epic-stories.md" "Epic Stories (史诗故事)"
check_doc "$DOCS_DIR/solution-architecture.md" "Solution Architecture (解决方案架构)"
check_doc "$DOCS_DIR/ux-specification.md" "UX Specification (用户体验规格)"
check_doc "$DOCS_DIR/user-stories.md" "User Stories (用户故事)"

echo ""

# 显示下一步建议
echo -e "${YELLOW}建议的下一步:${NC}"

if [ ! -f "$DOCS_DIR/epic-stories.md" ]; then
    echo -e "  1. 创建 epic-stories.md 文档"
fi

if [ ! -f "$DOCS_DIR/solution-architecture.md" ]; then
    echo -e "  2. 运行解决方案架构工作流: workflow solution-architecture"
fi

if [ ! -f "$DOCS_DIR/ux-specification.md" ]; then
    echo -e "  3. 创建 UX 规格文档: workflow plan-project"
fi

if [ ! -f "$DOCS_DIR/user-stories.md" ]; then
    echo -e "  4. 生成详细用户故事: workflow generate-stories"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}初始化完成!${NC}"
echo -e "${BLUE}========================================${NC}"
