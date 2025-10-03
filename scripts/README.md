# SQLite 数据库初始化脚本

这个目录包含了用于初始化 SQLite 数据库的脚本和工具。

## 文件说明

### 主要文件
- `init_sqlite_db.sql` - 数据库表结构定义SQL脚本
- `init_database.py` - Python数据库初始化脚本
- `database_config.py` - 数据库配置管理模块
- `test_database.py` - 数据库测试验证脚本

### 辅助文件
- `simple_init_test.py` - 简单的数据库初始化测试
- `README.md` - 使用说明文档

## 使用方法

### 1. 直接初始化数据库
```bash
# 进入脚本目录
cd scripts

# 运行初始化脚本
python init_database.py
```

### 2. 重置数据库（删除现有数据库）
```bash
# 强制重置（不询问确认）
python init_database.py --reset --force

# 交互式重置（会询问确认）
python init_database.py --reset
```

### 3. 自定义数据库路径
```bash
# 指定数据库文件路径
python init_database.py --db-path /path/to/your/database.db

# 指定SQL脚本路径
python init_database.py --sql-script /path/to/your/script.sql
```

### 4. 测试数据库
```bash
# 运行数据库测试
python test_database.py

# 或者运行简单测试
python simple_init_test.py
```

## 数据库结构

### 主要数据表

#### 用户相关表
- `users` - 用户基本信息表
- `user_cards` - 用户卡片信息表

#### 匹配相关表
- `match_actions` - 用户匹配操作记录表
- `match_results` - 匹配结果记录表



#### 其他表
- `membership_orders` - 会员订单表
- `llm_usage_logs` - LLM使用日志表
- `social_preferences` - 社交偏好表
- `social_profiles` - 社交档案表
- `social_match_criteria` - 社交匹配条件表

### 索引和约束

所有表都包含适当的索引以优化查询性能，包括：
- 主键索引
- 外键索引
- 常用查询字段索引
- 复合索引（针对多字段查询）

### 视图

- `user_statistics` - 用户统计视图
- `match_statistics` - 匹配统计视图

## 配置说明

### 数据库配置 (database_config.py)

```python
from app.core.database_config import get_db_manager, get_db_config

# 获取默认数据库管理器
manager = get_db_manager()

# 获取数据库配置
config = get_db_config()

# 执行查询
results = manager.execute_query("SELECT * FROM users LIMIT 10")

# 执行更新
row_count = manager.execute_update("UPDATE users SET status = ? WHERE id = ?", ('active', 'user123'))
```

### 连接参数

数据库连接使用以下优化参数：
- `isolation_level=None` - 自动提交模式
- `check_same_thread=False` - 允许多线程访问
- `timeout=30.0` - 连接超时时间30秒
- `PRAGMA foreign_keys = ON` - 启用外键约束
- `PRAGMA journal_mode = WAL` - 使用WAL日志模式
- `PRAGMA cache_size = -64000` - 64MB缓存

## 测试数据

初始化脚本会自动插入一些测试数据：

### 测试用户
- 系统管理员用户 (admin_user_001)
- 测试用户1 (test_user_001)
- 测试用户2 (test_user_002)

### 测试卡片
- 测试卡片1 (card_001) - 交友场景
- 测试卡片2 (card_002) - 活动场景

## 故障排除

### 常见问题

1. **数据库文件权限问题**
   - 确保有写入权限
   - 检查磁盘空间是否充足

2. **SQL语法错误**
   - 确认SQLite版本兼容性
   - 检查SQL脚本编码（UTF-8）

3. **外键约束失败**
   - 检查数据插入顺序
   - 确认外键关系正确性

### 调试方法

1. **查看数据库状态**
   ```bash
   python -c "from scripts.simple_init_test import main; main()"
   ```

2. **手动连接数据库**
   ```bash
   sqlite3 vmatch.db
   .tables
   .schema users
   ```

3. **检查日志输出**
   - 查看脚本运行时的错误信息
   - 检查Python异常堆栈

## 注意事项

1. **数据备份**
   - 在生产环境中使用前请备份现有数据
   - 重置操作会永久删除现有数据库

2. **性能优化**
   - 定期执行 `VACUUM` 命令优化数据库
   - 监控数据库大小和查询性能

3. **安全配置**
   - 在生产环境中设置适当的数据库文件权限
   - 考虑数据库加密（SQLCipher）

## 更新日志

### v1.0.0 (当前版本)
- 初始版本
- 包含完整的数据库表结构
- 支持索引和视图
- 包含测试数据
- 提供完整的测试和验证工具