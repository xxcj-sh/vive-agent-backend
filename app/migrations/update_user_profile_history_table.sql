-- 更新 user_profile_history 表结构，添加缺失的字段

-- 添加准确率评价相关字段
ALTER TABLE user_profile_history 
ADD COLUMN accuracy_rating VARCHAR(20) NULL COMMENT '准确率评价(accurate, partial, inaccurate)';

ALTER TABLE user_profile_history 
ADD COLUMN adjustment_text TEXT NULL COMMENT '调整建议';

-- 添加变更前的用户评价字段
ALTER TABLE user_profile_history 
ADD COLUMN previous_accuracy_rating VARCHAR(20) NULL COMMENT '变更前的准确率评价';

ALTER TABLE user_profile_history 
ADD COLUMN previous_adjustment_text TEXT NULL COMMENT '变更前的调整建议';

-- 添加变更后的用户评价字段  
ALTER TABLE user_profile_history 
ADD COLUMN current_accuracy_rating VARCHAR(20) NULL COMMENT '变更后的准确率评价';

ALTER TABLE user_profile_history 
ADD COLUMN current_adjustment_text TEXT NULL COMMENT '变更后的调整建议';

-- 创建索引优化查询性能
CREATE INDEX idx_user_profile_history_accuracy_rating ON user_profile_history(accuracy_rating);
CREATE INDEX idx_user_profile_history_previous_accuracy_rating ON user_profile_history(previous_accuracy_rating);
CREATE INDEX idx_user_profile_history_current_accuracy_rating ON user_profile_history(current_accuracy_rating);

-- 验证字段添加成功
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = DATABASE() 
AND TABLE_NAME = 'user_profile_history' 
AND COLUMN_NAME IN ('accuracy_rating', 'adjustment_text', 'previous_accuracy_rating', 
                    'previous_adjustment_text', 'current_accuracy_rating', 'current_adjustment_text');

-- 检查索引创建成功
SHOW INDEX FROM user_profile_history 
WHERE Column_name IN ('accuracy_rating', 'previous_accuracy_rating', 'current_accuracy_rating');