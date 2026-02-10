-- 更新数据库中的枚举值，将大写转换为小写
-- 创建时间: 2026-02-10
-- 描述: 将 tags 和 user_tag_rel 表中的状态值从大写更新为小写，以匹配代码中的枚举定义

-- 更新 tags 表中的状态值
UPDATE tags 
SET status = 'active' 
WHERE status = 'ACTIVE';

UPDATE tags 
SET status = 'deleted' 
WHERE status = 'DELETED';

-- 更新 user_tag_rel 表中的状态值
UPDATE user_tag_rel 
SET status = 'active' 
WHERE status = 'ACTIVE';

UPDATE user_tag_rel 
SET status = 'deleted' 
WHERE status = 'DELETED';

-- 验证更新结果
SELECT 'tags table status values:' AS info;
SELECT status, COUNT(*) as count FROM tags GROUP BY status;

SELECT 'user_tag_rel table status values:' AS info;
SELECT status, COUNT(*) as count FROM user_tag_rel GROUP BY status;
