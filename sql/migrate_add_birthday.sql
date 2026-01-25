-- Migration script to add birthday column to users table
-- Run this SQL in your database management tool (MySQL)

ALTER TABLE users ADD COLUMN birthday VARCHAR(20) DEFAULT NULL COMMENT '用户出生日期';

-- Verify the column was added
-- SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_COMMENT
-- FROM INFORMATION_SCHEMA.COLUMNS
-- WHERE TABLE_NAME = 'users' AND TABLE_SCHEMA = 'your_database_name';
