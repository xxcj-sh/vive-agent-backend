# 数据库初始化脚本使用说明

这个目录包含了用于数据库初始化和管理的脚本工具。

## 脚本列表

### 1. `reset_database.py` - 数据库重置脚本
**功能**: 完全清空数据库并重新创建所有表结构
**使用场景**: 开发环境重置、测试环境初始化
**使用方法**:
```bash
# 交互模式（需要确认）
python scripts/reset_database.py

# 自动模式（跳过确认）
SKIP_CONFIRMATION=true python scripts/reset_database.py
```

**⚠️ 警告**: 此操作将删除所有数据，请谨慎使用！

### 2. `init_database_simple.py` - 简单初始化脚本
**功能**: 创建所有数据库表（如果表已存在则跳过）
**使用场景**: 新环境初始化、表结构更新
**使用方法**:
```bash
# 交互模式
python scripts/init_database_simple.py

# 自动模式
SKIP_CONFIRMATION=true python scripts/init_database_simple.py
```

### 3. `check_database.py` - 数据库检查脚本
**功能**: 检查数据库表结构、关系和数据统计
**使用场景**: 数据库验证、调试、文档生成
**使用方法**:
```bash
python scripts/check_database.py
```

## 环境配置

所有脚本都会自动读取项目的环境配置文件：
- 默认读取 `.env` 文件
- 可以通过设置 `ENV_FILE` 环境变量指定其他配置文件

示例:
```bash
ENV_FILE=.env.test python scripts/check_database.py
```

## 数据库连接

脚本会自动使用项目中配置的数据库连接信息：
- 数据库URL来自 `app.config.settings.DATABASE_URL`
- 支持 MySQL、PostgreSQL、SQLite 等数据库

## 安全提示

1. **生产环境慎用**: `reset_database.py` 会删除所有数据
2. **备份重要数据**: 在执行重置操作前请备份重要数据
3. **权限控制**: 确保数据库用户有足够的权限执行DDL操作

## 常见问题

### Q: 脚本执行失败怎么办？
A: 检查以下几点：
- 数据库连接是否正常
- 数据库用户是否有足够权限
- 环境配置是否正确
- 查看具体的错误信息进行排查

### Q: 如何只重置特定的表？
A: 目前脚本不支持选择性重置，可以修改脚本代码实现自定义逻辑。

### Q: 如何处理外键约束问题？
A: `reset_database.py` 会自动处理外键约束，先删除依赖表再删除主表。

## 扩展开发

如果需要添加新的初始化逻辑：
1. 在相应的模型文件中定义新的表结构
2. 脚本会自动发现并创建新表
3. 可以基于现有脚本模板创建自定义脚本