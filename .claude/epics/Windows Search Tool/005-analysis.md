---
issue: 5
task: 004
analyzed: 2025-10-16T09:37:23Z
agent_type: general-purpose
parallel_streams: 4
---

# Task 004 分析: 索引管理器实现

## 工作流分解

### Stream 1: IndexManager 核心类和文件扫描
**Agent类型:** general-purpose
**并行性:** 可立即开始
**依赖:** 无

**工作范围:**
- 实现 IndexManager 类框架
- 实现文件系统扫描功能 (scan_directory)
- 实现文件过滤功能 (根据扩展名、路径排除规则)
- 实现基础索引创建流程

**文件模式:**
- src/core/__init__.py
- src/core/index_manager.py (基础框架)
- tests/unit/core/__init__.py
- tests/unit/core/test_index_manager_scan.py

**预估时间:** 5-6 小时

---

### Stream 2: 文件解析和数据库写入
**Agent类型:** general-purpose
**并行性:** 依赖 Stream 1
**依赖:** Stream 1 完成后开始

**工作范围:**
- 实现文件解析调度 (调用 ParserFactory)
- 实现批量数据库写入 (使用 DBManager)
- 实现错误处理和日志记录
- 实现解析统计

**文件模式:**
- src/core/index_manager.py (解析和写入方法)
- tests/unit/core/test_index_manager_parse.py

**预估时间:** 5-6 小时

---

### Stream 3: 增量索引和哈希检测
**Agent类型:** general-purpose
**并行性:** 依赖 Stream 1 和 2
**依赖:** Stream 1 和 2 完成后开始

**工作范围:**
- 实现文件哈希计算 (SHA256)
- 实现增量索引逻辑 (检测文件变更)
- 实现刷新索引功能
- 实现索引更新和删除

**文件模式:**
- src/core/index_manager.py (增量索引方法)
- tests/unit/core/test_index_manager_incremental.py

**预估时间:** 4-5 小时

---

### Stream 4: 多进程并行处理和进度监控
**Agent类型:** general-purpose
**并行性:** 依赖 Stream 2
**依赖:** Stream 2 完成后开始 (可与 Stream 3 并行)

**工作范围:**
- 实现多进程并行处理 (multiprocessing.Pool)
- 实现进度回调机制
- 实现性能统计和监控
- 集成测试

**文件模式:**
- src/core/index_manager.py (并行处理方法)
- tests/unit/core/test_index_manager_parallel.py
- tests/integration/test_indexing.py

**预估时间:** 4-5 小时

---

## 并行策略

**阶段 1:** Stream 1 (框架和扫描) - 必须首先完成
**阶段 2:** Stream 2 (解析和写入) - 依赖 Stream 1
**阶段 3:** Stream 3 (增量) 和 Stream 4 (并行) 可并行执行

### 协调点
- 所有 Stream 共享 index_manager.py 文件
- Stream 3 和 4 都依赖 Stream 2 的解析逻辑
- 建议按顺序添加方法,在代码中用注释分隔

## 成功标准

- [ ] IndexManager 可以扫描目录并创建索引
- [ ] 支持多种文档格式解析
- [ ] 批量插入性能 ≥ 100 文件/分钟
- [ ] 增量索引正确检测文件变更
- [ ] 多进程并行处理工作正常
- [ ] 进度回调实时更新
- [ ] 单元测试覆盖率 ≥ 90%
- [ ] 集成测试验证端到端流程
