-- 用户标签系统数据库迁移脚本
-- 创建时间: 2025-01-28
-- 描述: 创建 tags 和 user_tag_rel 表

-- 1. 创建 tags 表
CREATE TABLE IF NOT EXISTS `tags` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键',
    `name` VARCHAR(50) NOT NULL COMMENT '标签名称',
    `desc` VARCHAR(255) DEFAULT '' COMMENT '标签描述',
    `icon` VARCHAR(500) DEFAULT '' COMMENT '标签图标URL',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE COMMENT '更新时间',
    `tag_type` ENUM('user_profile', 'user_safety', 'user_credit', 'user_community', 'user_feedback') NOT NULL COMMENT '标签类型',
    `create_user_id` VARCHAR(36) NOT NULL COMMENT '创建用户ID',
    `status` ENUM('ACTIVE', 'DELETED') DEFAULT 'ACTIVE' COMMENT '状态：active-正常，deleted-已删除',
    `max_members` INT DEFAULT NULL COMMENT '标签最大成员数，NULL表示无限制',
    `is_public` TINYINT DEFAULT 1 COMMENT '是否公开可见：1-是 0-否',
    PRIMARY KEY (`id`),
    INDEX `idx_create_user_id` (`create_user_id`),
    INDEX `idx_tag_type` (`tag_type`),
    INDEX `idx_status` (`status`),
    UNIQUE INDEX `uk_name_type` (`name`, `tag_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户标签表';

-- 2. 创建 user_tag_rel 表
CREATE TABLE IF NOT EXISTS `user_tag_rel` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键',
    `user_id` VARCHAR(36) NOT NULL COMMENT '用户ID',
    `tag_id` INT NOT NULL COMMENT '标签ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE COMMENT '更新时间',
    `status` ENUM('ACTIVE', 'DELETED') DEFAULT 'ACTIVE' COMMENT '状态：active-正常，deleted-已删除',
    `granted_by_user_id` VARCHAR(36) DEFAULT NULL COMMENT '授予该标签的用户ID',
    PRIMARY KEY (`id`),
    INDEX `idx_user_id` (`user_id`),
    INDEX `idx_tag_id` (`tag_id`),
    INDEX `idx_status` (`status`),
    UNIQUE INDEX `uk_user_tag` (`user_id`, `tag_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户标签关联表';

-- 3. 添加外键约束（如果需要）
-- ALTER TABLE `tags` ADD CONSTRAINT `fk_tags_create_user` FOREIGN KEY (`create_user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE;
-- ALTER TABLE `user_tag_rel` ADD CONSTRAINT `fk_user_tag_rel_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE;
-- ALTER TABLE `user_tag_rel` ADD CONSTRAINT `fk_user_tag_rel_tag` FOREIGN KEY (`tag_id`) REFERENCES `tags`(`id`) ON DELETE CASCADE;
-- 注意：如果外键约束导致问题，可以暂时不加，依赖业务逻辑保证数据完整性
