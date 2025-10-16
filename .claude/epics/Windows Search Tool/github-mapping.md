# GitHub Issues Mapping - Windows Search Tool

This file tracks the mapping between local task files and their corresponding GitHub Issues.

## Epic

- **Epic:** Windows Search Tool
  - **Local:** `.claude/epics/Windows Search Tool/epic.md`
  - **GitHub:** https://github.com/mattdog2024/windows-search-tool/issues/1
  - **Status:** open
  - **Labels:** epic, enhancement

## Tasks

### Task 001: 项目基础架构搭建
- **Local:** `.claude/epics/Windows Search Tool/001.md`
- **GitHub:** https://github.com/mattdog2024/windows-search-tool/issues/2
- **Status:** open
- **Labels:** task, epic:windows-search-tool
- **Dependencies:** None
- **Parallel:** true

### Task 002: 文档解析引擎实现
- **Local:** `.claude/epics/Windows Search Tool/002.md`
- **GitHub:** https://github.com/mattdog2024/windows-search-tool/issues/3
- **Status:** open
- **Labels:** task, epic:windows-search-tool
- **Dependencies:** 001
- **Parallel:** false

### Task 003: SQLite FTS5 数据库实现
- **Local:** `.claude/epics/Windows Search Tool/003.md`
- **GitHub:** https://github.com/mattdog2024/windows-search-tool/issues/4
- **Status:** open
- **Labels:** task, epic:windows-search-tool
- **Dependencies:** 001
- **Parallel:** true

### Task 004: 索引管理器实现
- **Local:** `.claude/epics/Windows Search Tool/004.md`
- **GitHub:** https://github.com/mattdog2024/windows-search-tool/issues/5
- **Status:** open
- **Labels:** task, epic:windows-search-tool
- **Dependencies:** 002, 003
- **Parallel:** false

### Task 005: 搜索引擎实现
- **Local:** `.claude/epics/Windows Search Tool/005.md`
- **GitHub:** https://github.com/mattdog2024/windows-search-tool/issues/6
- **Status:** open
- **Labels:** task, epic:windows-search-tool
- **Dependencies:** 003
- **Parallel:** true

### Task 006: PyQt6 主窗口和索引管理界面
- **Local:** `.claude/epics/Windows Search Tool/006.md`
- **GitHub:** https://github.com/mattdog2024/windows-search-tool/issues/7
- **Status:** open
- **Labels:** task, epic:windows-search-tool
- **Dependencies:** 004
- **Parallel:** false

### Task 007: PyQt6 搜索界面实现
- **Local:** `.claude/epics/Windows Search Tool/007.md`
- **GitHub:** https://github.com/mattdog2024/windows-search-tool/issues/8
- **Status:** open
- **Labels:** task, epic:windows-search-tool
- **Dependencies:** 005, 006
- **Parallel:** false

### Task 008: Tesseract OCR 集成
- **Local:** `.claude/epics/Windows Search Tool/008.md`
- **GitHub:** https://github.com/mattdog2024/windows-search-tool/issues/9
- **Status:** open
- **Labels:** task, epic:windows-search-tool
- **Dependencies:** 002
- **Parallel:** true

### Task 009: DeepSeek AI 服务集成
- **Local:** `.claude/epics/Windows Search Tool/009.md`
- **GitHub:** https://github.com/mattdog2024/windows-search-tool/issues/10
- **Status:** open
- **Labels:** task, epic:windows-search-tool
- **Dependencies:** 003
- **Parallel:** true

### Task 010: 打包部署和端到端测试
- **Local:** `.claude/epics/Windows Search Tool/010.md`
- **GitHub:** https://github.com/mattdog2024/windows-search-tool/issues/11
- **Status:** open
- **Labels:** task, epic:windows-search-tool
- **Dependencies:** 006, 007, 008, 009
- **Parallel:** false

---

## Summary

- **Total Issues Created:** 11 (1 epic + 10 tasks)
- **Repository:** https://github.com/mattdog2024/windows-search-tool
- **Created Date:** 2025-10-16
- **Sync Method:** Manual (gh CLI)

## Task Execution Order

### Phase 1 (Parallel)
- Task 001: 项目基础架构搭建

### Phase 2 (After Task 001)
- Task 002: 文档解析引擎实现 (sequential)
- Task 003: SQLite FTS5 数据库实现 (parallel with 002)

### Phase 3 (After Task 002 & 003)
- Task 004: 索引管理器实现 (sequential)
- Task 005: 搜索引擎实现 (parallel with 004)

### Phase 4 (After Task 004 & 005)
- Task 006: PyQt6 主窗口和索引管理界面 (sequential)
- Task 008: Tesseract OCR 集成 (parallel with 006)
- Task 009: DeepSeek AI 服务集成 (parallel with 006)

### Phase 5 (After Task 005 & 006)
- Task 007: PyQt6 搜索界面实现 (sequential)

### Phase 6 (After Task 006, 007, 008, 009)
- Task 010: 打包部署和端到端测试 (final)

**Critical Path:** 001 → 002 → 004 → 006 → 007 → 010
