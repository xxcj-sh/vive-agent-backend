-- 添加 raw_profile_embedding 列到 user_profiles 表
-- 创建时间: 2026-02-10
-- 描述: 为用户画像表添加语义向量列，用于存储豆包模型生成的1024维向量

-- 检查列是否存在，如果不存在则添加
SET @dbname = DATABASE();
SET @tablename = 'user_profiles';
SET @columnname = 'raw_profile_embedding';

SET @sql = CONCAT(
    'SELECT COUNT(*) INTO @exists FROM information_schema.COLUMNS ',
    'WHERE TABLE_SCHEMA = ''', @dbname, ''' ',
    'AND TABLE_NAME = ''', @tablename, ''' ',
    'AND COLUMN_NAME = ''', @columnname, ''''
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 如果列不存在，则添加
SET @add_column_sql = IF(@exists = 0,
    'ALTER TABLE user_profiles ADD COLUMN raw_profile_embedding TEXT NULL COMMENT ''用户画像语义向量（1024维，豆包模型生成）''',
    'SELECT ''Column raw_profile_embedding already exists'' AS message'
);

PREPARE stmt FROM @add_column_sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 验证列是否添加成功
SELECT COLUMN_NAME, DATA_TYPE, COLUMN_COMMENT 
FROM information_schema.COLUMNS 
WHERE TABLE_SCHEMA = DATABASE() 
AND TABLE_NAME = 'user_profiles' 
AND COLUMN_NAME = 'raw_profile_embedding';
