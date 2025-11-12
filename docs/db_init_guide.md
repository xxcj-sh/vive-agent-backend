# 数据库初始化指南

## 概述

本文档详细说明了 VMatch 后端项目的数据库初始化系统，包括初始化脚本的功能、使用方法以及注意事项。

## 初始化脚本功能

`app/utils/db_init.py` 是数据库初始化的核心模块，提供以下主要功能：

1. **数据库创建检查**：自动检查并创建数据库（如不存在）
2. **数据表创建**：基于 SQLAlchemy 模型创建所有必要的数据表
3. **生产环境保护**：在生产环境中禁止危险操作
4. **连接统计**：提供数据库连接池和表信息统计
5. **兼容性支持**：保留原有的 `init_db()` 函数接口

## 支持的数据模型

初始化脚本会自动创建以下数据表（基于项目中定义的模型）：

- **users**：用户信息表
- **user_profiles**：用户画像表
- **user_profile_history**：用户画像历史记录表
- **user_profile_feedback**：用户画像反馈表
- **user_profile_scores**：用户画像评分表
- **user_profile_score_history**：用户画像评分历史表
- **user_profile_skills**：用户画像技能表
- **matches**：匹配信息表
- **match_details**：匹配详情表
- **match_actions**：匹配操作记录表
- **match_results**：匹配结果表
- **user_cards**：用户卡片表
- **chat_messages**：聊天消息表
- **membership_orders**：会员订单表
- **llm_usage_logs**：LLM 使用日志表
- **subscribe_messages**：订阅消息表
- **user_subscribe_settings**：用户订阅设置表

## 使用方法

### 方式一：通过执行脚本运行

项目根目录下的 `run_db_init.py` 提供了手动触发数据库初始化的方法：

```bash
python run_db_init.py
```

该脚本会执行完整的数据库初始化流程，并输出详细日志和统计信息。

### 方式二：在应用代码中调用

可以在应用的启动代码中调用初始化函数：

```python
from app.utils.db_init import init_database

# 执行初始化
success = init_database()
if success:
    print("数据库初始化成功")
else:
    print("数据库初始化失败")
```

### 方式三：使用兼容接口

为保持向后兼容性，可以使用原有的 `init_db()` 函数：

```python
from app.utils.db_init import init_db

# 执行初始化
init_db()
```

## 配置参数

数据库连接配置位于 `app/config.py`，主要参数包括：

- `MYSQL_HOST`：数据库主机地址
- `MYSQL_PORT`：数据库端口
- `MYSQL_DATABASE`：数据库名称
- `MYSQL_USERNAME`：用户名
- `MYSQL_PASSWORD`：密码
- `MYSQL_CHARSET`：字符集设置
- `ENVIRONMENT`：环境标识（development/production）

## 安全注意事项

1. **生产环境保护**：在生产环境中，系统禁止执行 `drop_all_tables()` 操作
2. **错误处理**：初始化过程中的错误会被捕获并记录，防止应用崩溃
3. **连接安全**：使用参数化查询防止 SQL 注入
4. **日志记录**：所有关键操作都会记录日志，便于审计和问题排查

## 单元测试

项目中的 `tests/test_db_init.py` 提供了完整的单元测试覆盖，包括：

- 数据库创建功能测试
- 数据表创建测试
- 环境保护机制测试
- 连接统计功能测试
- 错误处理测试

运行测试：

```bash
pytest tests/test_db_init.py -v
```

## 最佳实践

1. **开发环境**：在开发环境中可以放心使用全部功能
2. **测试环境**：建议使用独立的测试数据库进行初始化
3. **生产环境**：
   - 初始化操作应当在应用部署前完成
   - 应当定期备份数据库
   - 避免在运行中的生产环境执行初始化
4. **日志监控**：定期检查数据库初始化日志，确保系统正常运行

## 故障排查

常见问题及解决方案：

1. **连接失败**：检查数据库地址、端口和凭据是否正确
2. **权限不足**：确保数据库用户有创建数据库和表的权限
3. **表已存在**：系统会自动跳过已存在的表，无需担心重复创建
4. **外键约束错误**：检查表之间的依赖关系，确保按照正确顺序创建

## 更新日志

### 最新更新
- 增强了数据库初始化功能，添加自动创建数据库支持
- 改进了错误处理和日志记录
- 添加了数据库连接统计功能
- 增加了生产环境保护机制
- 编写了完整的单元测试用例
- 创建了便于使用的执行脚本

---

文档编写日期：2024-01-20