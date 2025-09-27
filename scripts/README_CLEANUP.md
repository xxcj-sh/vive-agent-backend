# 测试数据清理脚本使用说明

本目录包含三个用于清理数据库中测试卡片数据的Python脚本，适用于不同的使用场景。

## 脚本列表

### 1. delete_test_cards.py - 基础清理脚本
适合简单的测试数据清理需求，提供交互式确认。

**特点:**
- 自动识别包含"测试"、"test"等关键词的卡片
- 支持按显示名称、简介、搜索代码等多字段识别
- 交互式确认，避免误删
- 安全的软删除（将is_deleted设置为1）

**使用方法:**
```bash
python scripts/delete_test_cards.py
```

### 2. cleanup_test_data.py - 高级清理工具
功能最强大的清理工具，支持多种清理模式和详细报告。

**特点:**
- 三种清理模式：保守、激进、自定义
- 置信度评分系统，精确识别测试数据
- 支持清理相关数据（匹配记录、聊天记录）
- 生成详细的清理报告
- 支持干运行模式（dry-run）

**使用方法:**
```bash
# 保守模式（推荐）
python scripts/cleanup_test_data.py --mode conservative --dry-run

# 激进模式（谨慎使用）
python scripts/cleanup_test_data.py --mode aggressive --force

# 自定义模式（基于时间）
python scripts/cleanup_test_data.py --mode custom --cleanup-related

# 生成报告
python scripts/cleanup_test_data.py --mode conservative --output-report cleanup_report.txt
```

**参数说明:**
- `--mode`: 清理模式 (conservative/aggressive/custom)
- `--dry-run`: 只显示要删除的数据，不实际删除
- `--force`: 强制删除，不询问确认
- `--cleanup-related`: 同时清理相关的匹配和聊天记录
- `--output-report`: 输出报告到指定文件

### 3. quick_cleanup.py - 一键快速清理
最简单的使用方式，一键清理常见的测试数据。

**特点:**
- 一键执行，操作简单
- 自动显示当前数据库统计
- 清理后显示剩余数据情况
- 适合日常维护使用

**使用方法:**
```bash
python scripts/quick_cleanup.py
```

## 安全说明

### 数据安全
1. **软删除机制**: 所有脚本都使用软删除，将`is_deleted`字段设置为1，而不是物理删除数据
2. **事务支持**: 删除操作在一个事务中完成，确保数据一致性
3. **备份建议**: 建议在执行清理前备份数据库

### 识别规则
测试数据的识别基于以下规则：
- 显示名称包含"测试"、"test"、"demo"等关键词
- 简介中包含测试相关词汇
- 搜索代码包含测试关键词
- 卡片ID符合测试模式（如包含"test"）
- 用户ID或用户名包含测试关键词

### 清理模式对比

| 模式 | 识别精度 | 删除数量 | 适用场景 |
|------|----------|----------|----------|
| 保守模式 | 高 | 少 | 生产环境，谨慎清理 |
| 激进模式 | 中 | 多 | 开发环境，彻底清理 |
| 自定义模式 | 可调 | 可调 | 特殊需求，灵活配置 |

## 数据库环境配置

脚本会自动检测数据库配置：
1. 优先使用`DATABASE_URL`环境变量
2. 默认使用项目根目录下的`vmatch_dev.db`文件
3. 支持相对路径和绝对路径

**设置环境变量:**
```bash
export DATABASE_URL="sqlite:///./vmatch_dev.db"
python scripts/quick_cleanup.py
```

## 最佳实践

### 开发环境
```bash
# 日常清理
python scripts/quick_cleanup.py

# 深度清理
python scripts/cleanup_test_data.py --mode aggressive --cleanup-related
```

### 测试环境
```bash
# 干运行确认
python scripts/cleanup_test_data.py --mode conservative --dry-run

# 执行清理并生成报告
python scripts/cleanup_test_data.py --mode conservative --output-report test_cleanup_report.txt
```

### 生产环境（谨慎使用）
```bash
# 强烈建议先干运行
python scripts/cleanup_test_data.py --mode conservative --dry-run

# 确认无误后执行
python scripts/cleanup_test_data.py --mode conservative
```

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库文件是否存在
   - 确认`DATABASE_URL`环境变量设置正确
   - 检查文件权限

2. **找不到测试数据**
   - 尝试使用激进模式
   - 检查数据是否符合识别规则
   - 手动查询数据库确认

3. **删除后数据仍然存在**
   - 确认使用的是软删除（检查`is_deleted`字段）
   - 检查查询条件是否包含`is_deleted = 0`

### 手动验证
```sql
-- 查看测试卡片
SELECT id, display_name, bio, is_deleted 
FROM user_cards 
WHERE display_name LIKE '%测试%' AND is_deleted = 0;

-- 查看已删除的卡片
SELECT COUNT(*) FROM user_cards WHERE is_deleted = 1;
```

## 注意事项

1. **备份重要数据**: 执行清理前建议备份数据库
2. **谨慎使用激进模式**: 可能误删有用的测试数据
3. **生产环境慎用**: 生产环境建议使用保守模式并先干运行
4. **监控清理结果**: 清理后检查应用功能是否正常
5. **定期维护**: 建议定期清理测试数据，保持数据库整洁