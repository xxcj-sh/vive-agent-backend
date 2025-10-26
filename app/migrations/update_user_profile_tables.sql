-- 用户画像表结构更新迁移脚本
-- 更新于: 2025年10月26日
-- 目的: 使数据库表结构与SQLAlchemy模型定义保持一致

-- 1. 更新 user_profiles 表
-- 修改 mood_state 字段类型从 varchar(50) 改为 text，以匹配JSON数据存储需求
ALTER TABLE user_profiles 
MODIFY COLUMN mood_state TEXT COMMENT '心情状态分析';

-- 2. 更新 user_profile_history 表
-- 确保所有JSON字段使用正确的数据类型
-- MySQL 5.7+ 中JSON类型存储，如果版本较低则使用TEXT类型

-- 检查MySQL版本，决定使用JSON还是TEXT类型
-- MySQL 5.7.8 开始支持JSON类型
SET @mysql_version = (SELECT VERSION());

-- 由于MySQL版本检查复杂，直接使用TEXT类型存储JSON数据（兼容性最好）
-- 所有JSON字段已经正确设置为对应的数据类型，无需修改

-- 3. 添加缺失的索引（如果需要）
-- user_profiles 表索引检查
-- 已存在索引: PRIMARY KEY, user_id, is_active, created_at, updated_at
-- 可能需要添加的索引:

-- 根据查询模式，可能需要添加复合索引
-- CREATE INDEX idx_user_profiles_confidence ON user_profiles(confidence_score);
-- CREATE INDEX idx_user_profiles_data_source ON user_profiles(data_source);

-- 4. 更新表注释
ALTER TABLE user_profiles 
COMMENT = '用户画像数据表 - 存储模型预测得到的用户偏好、个性、心情等数据';

ALTER TABLE user_profile_history 
COMMENT = '用户画像历史记录表 - 用于存储用户画像的变更历史，支持版本回溯和变更追踪';

-- 5. 验证更新后的表结构
-- 可以通过以下命令验证:
-- DESCRIBE user_profiles;
-- DESCRIBE user_profile_history;

-- 6. 添加外键约束验证（如果尚未添加）
-- 确保 user_profile_history.profile_id 正确引用 user_profiles.id
-- 这个约束应该已经存在，可以通过SHOW CREATE TABLE验证

-- 迁移完成后的验证查询
SELECT 
    'user_profiles' as table_name,
    COUNT(*) as record_count,
    MAX(created_at) as latest_created,
    MAX(updated_at) as latest_updated
FROM user_profiles
UNION ALL
SELECT 
    'user_profile_history' as table_name,
    COUNT(*) as record_count,
    MAX(created_at) as latest_created,
    NULL as latest_updated
FROM user_profile_history;