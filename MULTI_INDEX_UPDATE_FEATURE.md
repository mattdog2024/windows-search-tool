# 多索引库更新进度界面功能

## 功能概述

实现了一个专业的多索引库更新进度对话框，在点击"更新索引"按钮后会显示，分别显示每个索引库的更新状态和进度。

## 核心功能

### 1. **多索引库独立进度显示**
- 每个索引库有独立的进度条和状态显示
- 实时显示当前处理的文件名
- 显示处理进度（已处理/总文件数）

### 2. **智能目录检查**
- 自动检查索引目录是否存在
- **目录不存在时**：跳过更新，保留原有索引内容（软删除机制）
- **目录存在时**：正常执行增量更新

### 3. **状态分类**
每个索引库可能处于以下状态之一：

| 状态 | 图标 | 说明 |
|------|------|------|
| 等待中 | ● | 灰色，等待轮到该库更新 |
| 检查目录 | ◉ | 蓝色，正在检查索引目录是否存在 |
| 更新中 | ◉ | 橙色，正在处理文件 |
| 完成 | ✓ | 绿色，更新完成并显示统计 |
| 已跳过 | ○ | 灰色，目录不存在已跳过 |
| 错误 | ✗ | 红色，更新失败 |

### 4. **总体进度**
- 顶部显示所有索引库的总体进度
- 实时更新当前正在处理的库名
- 显示已完成/总数量

### 5. **统计信息**
更新完成后显示每个库的详细统计：
- 新增文件数
- 更新文件数
- 删除文件数（软删除，内容保留）

## UI 设计

```
┌─────────────────────────────────────────────────┐
│ 索引库更新进度                                  │
├─────────────────────────────────────────────────┤
│ 正在更新 3 个索引库                             │
├─────────────────────────────────────────────────┤
│ 总体进度                                        │
│ ████████████████░░░░░░░░░  67%                 │
│ 正在更新: 测试索引库2 | 总进度: 2/3            │
├─────────────────────────────────────────────────┤
│                                                 │
│ ┌─ 测试索引库1 ─────────────────────────────┐ │
│ │ ✓ 完成                                     │ │
│ │ ████████████████████████████████  100%     │ │
│ │ 新增: 2 | 更新: 5 | 删除: 1                │ │
│ └────────────────────────────────────────────┘ │
│                                                 │
│ ┌─ 测试索引库2 ─────────────────────────────┐ │
│ │ ◉ 更新中                                   │ │
│ │ ████████████░░░░░░░░░░░░░  50%            │ │
│ │ 处理中: document.pdf (15/30)               │ │
│ └────────────────────────────────────────────┘ │
│                                                 │
│ ┌─ 测试索引库3 ─────────────────────────────┐ │
│ │ ○ 已跳过 - 索引目录不存在，保留原有内容    │ │
│ │ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░  0%          │ │
│ │ 已跳过 - 目录不存在                        │ │
│ └────────────────────────────────────────────┘ │
│                                                 │
│                                    [关闭]       │
└─────────────────────────────────────────────────┘
```

## 技术实现

### 文件结构

1. **UI 组件**: [src/ui/multi_index_update_dialog.py](src/ui/multi_index_update_dialog.py)
   - `MultiIndexUpdateDialog`: 主对话框类
   - `UpdateStatus`: 状态枚举
   - `LibraryUpdateState`: 库状态数据类

2. **控制器集成**: [src/ui/app_controller.py](src/ui/app_controller.py)
   - `handle_update_index()`: 多线程更新逻辑
   - 目录存在性检查
   - 进度回调映射

3. **核心逻辑**: [src/core/index_manager.py](src/core/index_manager.py#L1003)
   - 软删除实现 (`hard_delete=False`)

### 关键代码片段

#### 1. 创建更新对话框
```python
from src.ui.multi_index_update_dialog import MultiIndexUpdateDialog, UpdateStatus

enabled_libraries = self.library_manager.get_enabled_libraries()
update_dialog = MultiIndexUpdateDialog(
    self.main_window.root,
    enabled_libraries,
    on_close=lambda: self._on_update_dialog_close()
)
update_dialog.show()
```

#### 2. 更新库状态
```python
# 检查目录
update_dialog.update_library_status(
    library.name,
    UpdateStatus.CHECKING
)

# 更新中
update_dialog.update_library_status(
    library.name,
    UpdateStatus.UPDATING,
    progress=50,
    current_file="document.pdf",
    total_files=100,
    processed_files=50
)

# 完成
update_dialog.update_library_status(
    library.name,
    UpdateStatus.COMPLETED,
    progress=100,
    stats={'added': 10, 'updated': 20, 'deleted': 5}
)

# 跳过（目录不存在）
update_dialog.update_library_status(
    library.name,
    UpdateStatus.SKIPPED,
    directory_exists=False
)
```

#### 3. 目录存在性检查
```python
# 提取所有唯一的根目录并检查是否存在
unique_dirs = set()
for row in rows:
    file_path = row['file_path']
    dir_path = os.path.dirname(file_path)
    # ... 提取根目录

# 过滤出存在的目录
existing_dirs = [d for d in unique_dirs if os.path.exists(d)]

if not existing_dirs:
    # 目录不存在，跳过更新但保留索引内容
    update_dialog.update_library_status(
        library.name,
        UpdateStatus.SKIPPED,
        directory_exists=False
    )
    continue
```

## 使用场景

### 场景 1: 全部索引库正常更新
1. 用户点击"更新索引"
2. 对话框显示3个启用的索引库
3. 依次检查、更新每个库
4. 显示完成统计：新增10，更新20，删除5

### 场景 2: 部分目录不存在
1. 用户有外接硬盘的索引库
2. 硬盘未连接时点击"更新索引"
3. 系统检查发现该库的目录不存在
4. **跳过更新，保留原有索引内容**
5. 其他库正常更新

### 场景 3: 混合情况
- 索引库A: 正常更新 ✓
- 索引库B: 目录不存在，跳过 ○
- 索引库C: 更新出错 ✗

## 优势

1. **可视化**: 清晰展示每个库的更新状态
2. **数据保护**: 目录不存在时保留原有内容，不丢失数据
3. **并发友好**: 虽然串行更新，但UI响应流畅
4. **错误隔离**: 一个库失败不影响其他库
5. **用户友好**: 实时反馈，进度透明

## 测试

运行对话框测试代码：
```bash
python src/ui/multi_index_update_dialog.py
```

这会显示一个模拟的更新过程，展示所有状态变化。

## 与软删除的协同

当索引目录不存在时：
1. 更新对话框显示"已跳过"
2. 数据库中的文件保持原状态
3. 目录恢复后下次更新会正常处理
4. 已删除文件的状态为 `deleted`，内容完整保留
5. 用户可以继续搜索历史内容

## 未来改进

- [ ] 支持暂停/恢复更新
- [ ] 支持取消单个库的更新
- [ ] 显示更详细的错误信息
- [ ] 添加更新完成后的通知声音
- [ ] 支持后台静默更新模式
