-- 添加 adjustment_text 列到 user_profiles 表
ALTER TABLE user_profiles 
ADD COLUMN adjustment_text TEXT 
AFTER accuracy_rating;

-- 创建索引以优化查询性能
CREATE INDEX idx_user_profiles_adjustment_text 
ON user_profiles(adjustment_text(100));

-- 验证列添加成功
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = DATABASE() 
AND TABLE_NAME = 'user_profiles' 
AND COLUMN_NAME = 'adjustment_text';

-- 检查索引创建成功
SHOW INDEX FROM user_profiles WHERE Column_name = 'adjustment_text';