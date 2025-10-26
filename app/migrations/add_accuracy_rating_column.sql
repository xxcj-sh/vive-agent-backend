-- 添加 accuracy_rating 列到 user_profiles 表
-- 创建时间: 2025年10月27日
-- 目的: 添加缺失的 accuracy_rating 字段以支持用户画像评价功能

ALTER TABLE user_profiles 
ADD COLUMN accuracy_rating VARCHAR(20) NULL COMMENT '准确率评价(accurate, partial, inaccurate)' 
AFTER confidence_score;

-- 添加索引以提高查询性能
CREATE INDEX idx_user_profiles_accuracy_rating ON user_profiles(accuracy_rating);

-- 验证列添加成功
DESCRIBE user_profiles;

-- 检查添加后的数据
SELECT 
    COUNT(*) as total_records,
    COUNT(accuracy_rating) as records_with_rating,
    COUNT(*) - COUNT(accuracy_rating) as records_without_rating
FROM user_profiles;