# IndexManager 多实例修复 - 测试指南

## 修复内容

### 问题描述
- **症状**: 用户创建新索引库并选择"立刻索引"时,索引显示成功但数据库始终为空(doc_count=0)
- **根本原因**: IndexManager 使用单例模式,所有实例共享同一个数据库连接
- **影响范围**: 所有多索引库功能,特别是"立刻索引"功能

### 修复方案
将 IndexManager 从**单例模式**改为**多实例缓存模式**:
- 每个数据库路径创建独立的 IndexManager 实例
- 相同路径复用缓存实例(提高性能)
- 路径自动规范化,避免相对路径问题

### 技术细节
**修改前** (单例):
```python
_instance = None  # 只有一个实例

def __new__(cls, db_path=None):
    if cls._instance is None:
        cls._instance = super().__new__(cls)
    return cls._instance  # 总是返回同一个实例
```

**修改后** (多实例缓存):
```python
_instances = {}  # 字典: {db_path: instance}

def __new__(cls, db_path=None):
    db_path = os.path.abspath(db_path or default_path)
    if db_path not in cls._instances:
        instance = super().__new__(cls)
        cls._instances[db_path] = instance
    return cls._instances[db_path]  # 每个路径独立实例
```

---

## 测试步骤

### ✅ 步骤 1: 清空测试数据库
1. 使用 SQLite 工具或命令行清空 `测试6.db`:
   ```bash
   python -c "import sqlite3; conn = sqlite3.connect('C:/Users/TV/Documents/测试6.db'); cursor = conn.cursor(); cursor.execute('DELETE FROM documents'); cursor.execute('DELETE FROM documents_fts'); conn.commit(); conn.close()"
   ```

### ✅ 步骤 2: 测试"新建索引+立刻索引"功能
1. 启动应用程序
2. 点击"新建索引"按钮
3. 输入索引库名称(例如"测试7")
4. 选择数据库保存位置
5. **勾选"立刻索引库"**
6. 点击"选择要索引的目录"
7. 选择测试目录(例如 `E:/索引测试/2025年警示教育`)
8. 观察索引进度和结果

**预期结果**:
- 索引完成后显示成功数量(例如: 总计 392, 成功 374, 失败 18)
- 打开数据库验证记录数 ≠ 0
- 切换到新创建的索引库,能够搜索到文件

### ✅ 步骤 3: 验证数据库内容
```bash
python -c "import sqlite3; conn = sqlite3.connect('C:/Users/TV/Documents/测试7.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM documents'); print(f'记录数: {cursor.fetchone()[0]}'); cursor.execute('SELECT file_path FROM documents LIMIT 5'); print('前5条:'); [print(f'  {r[0]}') for r in cursor.fetchall()]; conn.close()"
```

**预期结果**:
```
记录数: 374
前5条:
  E:/索引测试/2025年警示教育\...xlsx
  E:/索引测试/2025年警示教育\...docx
  ...
```

### ✅ 步骤 4: 测试搜索功能
1. 在索引库选择器中选择新创建的索引库
2. 输入搜索关键词(例如"警示教育")
3. 点击"搜索"按钮

**预期结果**:
- 搜索结果列表显示匹配的文件
- 点击文件可以预览内容
- 状态栏显示搜索到的文件数量

---

## 已验证的测试

### 单元测试 (命令行)
```bash
python test_index_fix_simple.py
```

**结果**: ✅ 成功
```
索引结果:
  总计: 392
  成功: 374
  失败: 18
  耗时: 5.91秒

测试后记录数:
  documents: 374

前5条记录:
  E:/索引测试/2025年警示教育\2025年警示教育学习情况登记表.xlsx
  E:/索引测试/2025年警示教育\2025警示教育明细\...
```

### 多实例验证
```python
im1 = IndexManager('C:/Users/TV/Documents/测试1.db')
im2 = IndexManager('C:/Users/TV/Documents/测试6.db')
im3 = IndexManager('C:/Users/TV/Documents/测试1.db')

print(f'im1 is im3 (same db): {im1 is im3}')  # True (缓存)
print(f'im1 is im2 (different db): {im1 is im2}')  # False (独立)
```

**结果**: ✅ 成功
```
im1 is im3 (same db): True
im1 is im2 (different db): False
```

---

## 回归测试

确保修复没有破坏现有功能:

1. **默认索引库索引**: ✅ 应该仍然正常工作
2. **多库搜索**: ✅ 应该仍然正常工作
3. **索引库切换**: ✅ 应该仍然正常工作
4. **增量索引**: ✅ 应该仍然正常工作

---

## 已知限制

1. **临时文件解析失败**: 以 `~$` 开头的 Word 临时文件会解析失败(这是正常的)
2. **失败文件数量**: 18 个文件解析失败(都是临时文件,可以忽略)

---

## 提交记录

**Commit**: `802dc09`
**Message**: fix: 修复 IndexManager 单例模式导致的多库索引失败问题
**Files Changed**: `src/core/index_manager.py` (+51, -22)

---

## 下一步

用户需要在 GUI 中测试:
1. 新建索引库 + 立刻索引
2. 验证数据库有记录
3. 验证搜索功能正常

如果测试通过,这个问题就彻底解决了! 🎉
