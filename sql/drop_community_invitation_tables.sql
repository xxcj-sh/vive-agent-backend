-- 删除社群邀请相关数据表
-- 执行时间: 2026-02-08
-- 说明: 社群邀请功能未被使用，删除相关数据表

-- 先删除外键约束（如果存在）
-- MySQL 会自动处理外键约束，但显式删除更安全

-- 删除邀请使用记录表（有外键依赖，先删除）
DROP TABLE IF EXISTS invitation_usage;

-- 删除社群邀请表
DROP TABLE IF EXISTS community_invitations;

-- 验证删除结果
SHOW TABLES LIKE '%invitation%';
