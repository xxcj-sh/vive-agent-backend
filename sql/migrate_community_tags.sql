-- 社群邀请和标签内容推送数据库迁移脚本
-- 创建时间: 2025-02-01
-- 描述: 创建 community_invitations、invitation_usage、tag_contents 和 content_tag_interactions 表

-- 1. 创建 community_invitations 表
CREATE TABLE IF NOT EXISTS `community_invitations` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键',
    `code` VARCHAR(36) NOT NULL COMMENT '邀请码',
    `tag_id` INT NOT NULL COMMENT '社群标签ID',
    `inviter_user_id` VARCHAR(36) NOT NULL COMMENT '邀请人用户ID',
    `description` VARCHAR(255) DEFAULT '' COMMENT '邀请描述',
    `max_uses` INT DEFAULT NULL COMMENT '最大使用次数，NULL表示无限制',
    `used_count` INT DEFAULT 0 COMMENT '已使用次数',
    `expires_at` DATETIME DEFAULT NULL COMMENT '过期时间',
    `status` ENUM('pending', 'used', 'expired', 'cancelled') DEFAULT 'pending' COMMENT '状态',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE INDEX `uk_code` (`code`),
    INDEX `idx_invitation_tag_id` (`tag_id`),
    INDEX `idx_invitation_inviter` (`inviter_user_id`),
    INDEX `idx_invitation_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='社群邀请表';

-- 2. 创建 invitation_usage 表
CREATE TABLE IF NOT EXISTS `invitation_usage` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键',
    `invitation_id` INT NOT NULL COMMENT '邀请ID',
    `invited_user_id` VARCHAR(36) NOT NULL COMMENT '被邀请用户ID',
    `used_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '使用时间',
    PRIMARY KEY (`id`),
    INDEX `idx_usage_invitation` (`invitation_id`),
    INDEX `idx_usage_user` (`invited_user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='邀请使用记录表';

-- 3. 创建 tag_contents 表
CREATE TABLE IF NOT EXISTS `tag_contents` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键',
    `title` VARCHAR(100) NOT NULL COMMENT '内容标题',
    `content` TEXT NOT NULL COMMENT '内容详情',
    `content_type` ENUM('card', 'topic', 'article', 'link') NOT NULL COMMENT '内容类型',
    `target_id` VARCHAR(36) DEFAULT NULL COMMENT '关联目标ID（如用户卡片ID）',
    `cover_image` VARCHAR(500) DEFAULT '' COMMENT '封面图URL',
    `tag_ids` JSON NOT NULL COMMENT '关联的标签ID列表',
    `priority` INT DEFAULT 0 COMMENT '推送优先级，数值越大越优先',
    `status` ENUM('draft', 'published', 'archived') DEFAULT 'draft' COMMENT '状态',
    `view_count` INT DEFAULT 0 COMMENT '浏览次数',
    `like_count` INT DEFAULT 0 COMMENT '点赞次数',
    `share_count` INT DEFAULT 0 COMMENT '分享次数',
    `created_by` VARCHAR(36) NOT NULL COMMENT '创建者用户ID',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE COMMENT '更新时间',
    `published_at` DATETIME DEFAULT NULL COMMENT '发布时间',
    PRIMARY KEY (`id`),
    INDEX `idx_content_type` (`content_type`),
    INDEX `idx_content_status` (`status`),
    INDEX `idx_content_created_by` (`created_by`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='标签推送内容表';

-- 4. 创建 content_tag_interactions 表
CREATE TABLE IF NOT EXISTS `content_tag_interactions` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键',
    `content_id` INT NOT NULL COMMENT '内容ID',
    `user_id` VARCHAR(36) NOT NULL COMMENT '用户ID',
    `interaction_type` VARCHAR(20) NOT NULL COMMENT '交互类型：view/like/share',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '交互时间',
    PRIMARY KEY (`id`),
    INDEX `idx_interaction_content` (`content_id`),
    INDEX `idx_interaction_user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='内容和标签的交互记录表';

-- 5. 添加外键约束（如果需要）
-- ALTER TABLE `community_invitations` ADD CONSTRAINT `fk_invitation_tag` FOREIGN KEY (`tag_id`) REFERENCES `tags`(`id`) ON DELETE CASCADE;
-- ALTER TABLE `invitation_usage` ADD CONSTRAINT `fk_usage_invitation` FOREIGN KEY (`invitation_id`) REFERENCES `community_invitations`(`id`) ON DELETE CASCADE;
-- 注意：如果外键约束导致问题，可以暂时不加，依赖业务逻辑保证数据完整性
