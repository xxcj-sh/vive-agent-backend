-- 迁移 users 表：删除 age 列，添加 mbti 列

-- 1. 删除 age 列
ALTER TABLE users DROP COLUMN age;

-- 2. 添加 mbti 列
ALTER TABLE users ADD COLUMN mbti VARCHAR(10) DEFAULT NULL;
