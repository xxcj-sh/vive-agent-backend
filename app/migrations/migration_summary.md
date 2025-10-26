# 数据库迁移总结

## 执行时间
2024年1月

## 迁移内容

### 1. user_profiles 表更新
- **添加字段**:
  - `accuracy_rating` VARCHAR(20) - 准确率评价 (accurate, partial, inaccurate)
  - `adjustment_text` TEXT - 调整建议
- **索引**: 
  - `idx_user_profiles_accuracy_rating`
  - `idx_user_profiles_adjustment_text`

### 2. user_profile_history 表更新  
- **添加字段**:
  - `accuracy_rating` VARCHAR(20) - 准确率评价
  - `adjustment_text` TEXT - 调整建议
  - `previous_accuracy_rating` VARCHAR(20) - 变更前的准确率评价
  - `previous_adjustment_text` TEXT - 变更前的调整建议
  - `current_accuracy_rating` VARCHAR(20) - 变更后的准确率评价
  - `current_adjustment_text` TEXT - 变更后的调整建议
- **索引**:
  - `idx_user_profile_history_accuracy_rating`
  - `idx_user_profile_history_previous_accuracy_rating`
  - `idx_user_profile_history_current_accuracy_rating`

## 迁移文件
- `/app/migrations/add_accuracy_rating_column.sql` - user_profiles 表accuracy_rating字段
- `/app/migrations/add_adjustment_text_column.sql` - user_profiles 表adjustment_text字段
- `/app/migrations/update_user_profile_history_table.sql` - user_profile_history 表完整更新

## 验证结果
✅ 所有字段成功添加
✅ 所有索引创建成功
✅ 后端服务正常运行
✅ 数据库连接正常

## 注意事项
- 所有新字段均为可空字段，确保向后兼容
- 索引已优化常用查询场景
- 迁移过程无数据丢失