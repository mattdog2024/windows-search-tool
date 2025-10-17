#!/bin/bash

# 颜色定义
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# 获取 epic 目录
EPIC_DIR=".claude/epics/Windows Search Tool"

if [ ! -d "$EPIC_DIR" ]; then
    echo -e "${RED}错误: Epic 目录不存在${NC}"
    exit 1
fi

# 打印标题
echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}  ${CYAN}${BOLD}进行中的任务${NC} - Windows Search Tool  ${BLUE}║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""

# 查找所有任务文件
TASK_FILES=$(find "$EPIC_DIR" -name "[0-9]*.md" | sort)

# 统计变量
OPEN_COUNT=0
BLOCKED_COUNT=0
IN_PROGRESS_COUNT=0

# 临时文件用于存储任务信息
OPEN_TASKS=$(mktemp)
BLOCKED_TASKS=$(mktemp)
IN_PROGRESS_TASKS=$(mktemp)

# 遍历任务文件
while IFS= read -r file; do
    # 提取 frontmatter
    STATUS=$(grep "^status:" "$file" | head -1 | sed 's/status: //')
    NAME=$(grep "^name:" "$file" | head -1 | sed 's/name: //')
    GITHUB=$(grep "^github:" "$file" | head -1 | sed 's/github: //' | sed 's#.*/issues/##')
    CREATED=$(grep "^created:" "$file" | head -1 | sed 's/created: //')
    UPDATED=$(grep "^updated:" "$file" | head -1 | sed 's/updated: //')

    # 根据状态分类
    case "$STATUS" in
        "in-progress")
            IN_PROGRESS_COUNT=$((IN_PROGRESS_COUNT + 1))
            echo "$NAME|$GITHUB|$UPDATED|$file" >> "$IN_PROGRESS_TASKS"
            ;;
        "open")
            OPEN_COUNT=$((OPEN_COUNT + 1))
            echo "$NAME|$GITHUB|$CREATED|$file" >> "$OPEN_TASKS"
            ;;
        "blocked")
            BLOCKED_COUNT=$((BLOCKED_COUNT + 1))
            echo "$NAME|$GITHUB|$UPDATED|$file" >> "$BLOCKED_TASKS"
            ;;
    esac
done <<< "$TASK_FILES"

# 显示进行中的任务
if [ $IN_PROGRESS_COUNT -gt 0 ]; then
    echo -e "${YELLOW}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}${BOLD}🔄 进行中的任务 (${IN_PROGRESS_COUNT})${NC}"
    echo -e "${YELLOW}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    while IFS='|' read -r name github updated file; do
        # 提取文件编号
        file_num=$(basename "$file" | sed 's/\.md$//' | sed 's/-.*//')

        # 检查是否有更新记录
        UPDATE_DIR="$EPIC_DIR/updates/$github"
        if [ -d "$UPDATE_DIR" ]; then
            # 获取最新的 stream 文件
            LATEST_STREAM=$(ls "$UPDATE_DIR"/*.md 2>/dev/null | tail -1)
            if [ -n "$LATEST_STREAM" ]; then
                STREAM_NAME=$(basename "$LATEST_STREAM" .md)
                echo -e "${CYAN}${BOLD}Issue #${github}${NC} - ${name}"
                echo -e "  📝 最新进度: ${STREAM_NAME}"
                echo -e "  📅 更新时间: ${updated}"
                echo -e "  📂 任务文件: ${file}"
                echo ""
            fi
        else
            echo -e "${CYAN}${BOLD}Issue #${github}${NC} - ${name}"
            echo -e "  📅 更新时间: ${updated}"
            echo -e "  📂 任务文件: ${file}"
            echo ""
        fi
    done < "$IN_PROGRESS_TASKS"
else
    echo -e "${GREEN}✓ 当前没有进行中的任务${NC}"
    echo ""
fi

# 显示待开始的任务
if [ $OPEN_COUNT -gt 0 ]; then
    echo -e "${BLUE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}${BOLD}⧖ 待开始的任务 (${OPEN_COUNT})${NC}"
    echo -e "${BLUE}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    while IFS='|' read -r name github created file; do
        # 检查依赖
        DEPENDS=$(grep "^depends_on:" "$file" | sed 's/depends_on: //' | sed 's/\[//' | sed 's/\]//' | sed 's/, /,/g')

        echo -e "${CYAN}${BOLD}Issue #${github}${NC} - ${name}"
        echo -e "  📅 创建时间: ${created}"

        if [ -n "$DEPENDS" ] && [ "$DEPENDS" != "" ]; then
            echo -e "  🔗 依赖任务: ${DEPENDS}"
        fi

        echo -e "  📂 任务文件: ${file}"
        echo ""
    done < "$OPEN_TASKS"
fi

# 显示被阻塞的任务
if [ $BLOCKED_COUNT -gt 0 ]; then
    echo -e "${RED}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}${BOLD}🚫 被阻塞的任务 (${BLOCKED_COUNT})${NC}"
    echo -e "${RED}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    while IFS='|' read -r name github updated file; do
        echo -e "${CYAN}${BOLD}Issue #${github}${NC} - ${name}"
        echo -e "  📅 更新时间: ${updated}"
        echo -e "  📂 任务文件: ${file}"
        echo ""
    done < "$BLOCKED_TASKS"
fi

# 总结
echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}  ${BOLD}任务状态总结${NC}                              ${BLUE}║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${YELLOW}🔄 进行中:${NC} ${IN_PROGRESS_COUNT}"
echo -e "  ${BLUE}⧖ 待开始:${NC} ${OPEN_COUNT}"
echo -e "  ${RED}🚫 被阻塞:${NC} ${BLOCKED_COUNT}"
echo ""

# 建议下一步操作
if [ $IN_PROGRESS_COUNT -eq 0 ] && [ $OPEN_COUNT -gt 0 ]; then
    echo -e "${GREEN}${BOLD}💡 建议:${NC} 使用 ${CYAN}/pm:issue-start <issue_number>${NC} 开始一个新任务"
    echo ""
elif [ $IN_PROGRESS_COUNT -gt 0 ]; then
    echo -e "${GREEN}${BOLD}💡 建议:${NC}"
    echo -e "  - 使用 ${CYAN}/pm:issue-sync <issue_number>${NC} 同步进度到 GitHub"
    echo -e "  - 使用 ${CYAN}/pm:issue-complete <issue_number>${NC} 完成任务"
    echo ""
fi

# 清理临时文件
rm -f "$OPEN_TASKS" "$BLOCKED_TASKS" "$IN_PROGRESS_TASKS"

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}  ${GREEN}${BOLD}任务状态查询完成!${NC}                        ${BLUE}║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
