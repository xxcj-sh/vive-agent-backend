-- MySQL 数据库初始化脚本
-- 用于创建所有必要的表结构

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS vmatch_dev CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE vmatch_dev;

-- 1. 用户相关表

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    phone VARCHAR(20) UNIQUE,
    hashed_password TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    nick_name VARCHAR(100),
    avatar_url TEXT,
    gender TINYINT DEFAULT 0,
    age TINYINT UNSIGNED,
    bio TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    occupation VARCHAR(100),
    location VARCHAR(100),
    education VARCHAR(100),
    interests TEXT,
    wechat VARCHAR(100),
    wechat_open_id VARCHAR(100),
    email VARCHAR(255),
    status VARCHAR(20) DEFAULT 'pending',
    last_login TIMESTAMP NULL,
    level TINYINT UNSIGNED DEFAULT 1,
    points INT DEFAULT 0,
    register_at TIMESTAMP NULL,
    INDEX idx_users_phone (phone),
    INDEX idx_users_wechat_open_id (wechat_open_id),
    INDEX idx_users_status (status),
    INDEX idx_users_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用户画像表
CREATE TABLE IF NOT EXISTS user_profiles (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL UNIQUE,
    preferences TEXT,
    personality_traits TEXT,
    mood_state VARCHAR(50),
    behavior_patterns TEXT,
    interest_tags TEXT,
    social_preferences TEXT,
    match_preferences TEXT,
    data_source VARCHAR(50),
    confidence_score TINYINT UNSIGNED,
    update_reason TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version TINYINT UNSIGNED DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_profiles_user_id (user_id),
    INDEX idx_user_profiles_is_active (is_active),
    INDEX idx_user_profiles_created_at (created_at),
    INDEX idx_user_profiles_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用户画像历史表
CREATE TABLE IF NOT EXISTS user_profile_history (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    profile_id VARCHAR(36) NOT NULL,
    change_type VARCHAR(50) NOT NULL,
    old_data TEXT,
    new_data TEXT,
    change_reason TEXT,
    updated_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (profile_id) REFERENCES user_profiles(id) ON DELETE CASCADE,
    INDEX idx_user_profile_history_user_id (user_id),
    INDEX idx_user_profile_history_profile_id (profile_id),
    INDEX idx_user_profile_history_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用户画像反馈表
CREATE TABLE IF NOT EXISTS user_profile_feedback (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    profile_id VARCHAR(36) NOT NULL,
    feedback_type VARCHAR(50) NOT NULL,
    feedback_content TEXT,
    rating TINYINT UNSIGNED,
    is_processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (profile_id) REFERENCES user_profiles(id) ON DELETE CASCADE,
    INDEX idx_user_profile_feedback_user_id (user_id),
    INDEX idx_user_profile_feedback_profile_id (profile_id),
    INDEX idx_user_profile_feedback_feedback_type (feedback_type),
    INDEX idx_user_profile_feedback_is_processed (is_processed)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. 用户卡片相关表

-- 用户卡片表
CREATE TABLE IF NOT EXISTS user_cards (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    role_type VARCHAR(50) NOT NULL,
    scene_type VARCHAR(50) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    avatar_url TEXT,
    bio TEXT,
    trigger_and_output TEXT,
    profile_data TEXT,
    preferences TEXT,
    visibility VARCHAR(20) DEFAULT 'public',
    is_active BOOLEAN DEFAULT TRUE,
    is_deleted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    search_code VARCHAR(100),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_cards_user_id (user_id),
    INDEX idx_user_cards_scene_type (scene_type),
    INDEX idx_user_cards_role_type (role_type),
    INDEX idx_user_cards_is_active (is_active),
    INDEX idx_user_cards_is_deleted (is_deleted),
    INDEX idx_user_cards_created_at (created_at),
    INDEX idx_user_cards_search_code (search_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. 匹配系统相关表

-- 匹配操作记录表
CREATE TABLE IF NOT EXISTS match_actions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    target_user_id VARCHAR(36) NOT NULL,
    target_card_id VARCHAR(36) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    scene_type VARCHAR(50) NOT NULL,
    scene_context TEXT,
    source VARCHAR(20) DEFAULT 'user',
    is_processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP NULL,
    extra TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (target_user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (target_card_id) REFERENCES user_cards(id) ON DELETE CASCADE,
    INDEX idx_match_actions_user_id (user_id),
    INDEX idx_match_actions_target_user_id (target_user_id),
    INDEX idx_match_actions_target_card_id (target_card_id),
    INDEX idx_match_actions_action_type (action_type),
    INDEX idx_match_actions_scene_type (scene_type),
    INDEX idx_match_actions_created_at (created_at),
    INDEX idx_match_actions_is_processed (is_processed)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 匹配结果记录表
CREATE TABLE IF NOT EXISTS match_results (
    id VARCHAR(36) PRIMARY KEY,
    user1_id VARCHAR(36) NOT NULL,
    user2_id VARCHAR(36) NOT NULL,
    user1_card_id VARCHAR(36) NOT NULL,
    user2_card_id VARCHAR(36) NOT NULL,
    scene_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'matched',
    user1_action_id VARCHAR(36) NOT NULL,
    user2_action_id VARCHAR(36) NOT NULL,
    matched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    first_message_at TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_blocked BOOLEAN DEFAULT FALSE,
    expiry_date TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user1_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (user2_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (user1_card_id) REFERENCES user_cards(id) ON DELETE CASCADE,
    FOREIGN KEY (user2_card_id) REFERENCES user_cards(id) ON DELETE CASCADE,
    FOREIGN KEY (user1_action_id) REFERENCES match_actions(id) ON DELETE CASCADE,
    FOREIGN KEY (user2_action_id) REFERENCES match_actions(id) ON DELETE CASCADE,
    INDEX idx_match_results_user1_id (user1_id),
    INDEX idx_match_results_user2_id (user2_id),
    INDEX idx_match_results_user1_card_id (user1_card_id),
    INDEX idx_match_results_user2_card_id (user2_card_id),
    INDEX idx_match_results_status (status),
    INDEX idx_match_results_is_active (is_active),
    INDEX idx_match_results_is_blocked (is_blocked),
    INDEX idx_match_results_matched_at (matched_at),
    INDEX idx_match_results_last_activity_at (last_activity_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. 聊天消息相关表

-- 聊天消息表
CREATE TABLE IF NOT EXISTS chat_messages (
    id VARCHAR(36) PRIMARY KEY,
    sender_id VARCHAR(36) NOT NULL,
    receiver_id VARCHAR(36) NOT NULL,
    content TEXT NOT NULL,
    message_type VARCHAR(20) DEFAULT 'text',
    match_result_id VARCHAR(36) NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP NULL,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (match_result_id) REFERENCES match_results(id) ON DELETE CASCADE,
    INDEX idx_chat_messages_sender_id (sender_id),
    INDEX idx_chat_messages_receiver_id (receiver_id),
    INDEX idx_chat_messages_match_result_id (match_result_id),
    INDEX idx_chat_messages_created_at (created_at),
    INDEX idx_chat_messages_is_read (is_read),
    INDEX idx_chat_messages_is_deleted (is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. 订单相关表

-- 会员订单表
CREATE TABLE IF NOT EXISTS membership_orders (
    id VARCHAR(36) PRIMARY KEY,
    plan_name VARCHAR(100) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',
    user_id VARCHAR(36) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_membership_orders_user_id (user_id),
    INDEX idx_membership_orders_status (status),
    INDEX idx_membership_orders_date (date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. AI系统相关表

-- LLM使用日志表
CREATE TABLE IF NOT EXISTS llm_usage_logs (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36),
    task_type VARCHAR(50) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    llm_model_name VARCHAR(100) NOT NULL,
    prompt_tokens INT DEFAULT 0,
    completion_tokens INT DEFAULT 0,
    total_tokens INT DEFAULT 0,
    prompt_content TEXT,
    response_content TEXT,
    request_duration DECIMAL(10,3) NOT NULL,
    response_time DECIMAL(10,3) NOT NULL,
    request_params TEXT,
    response_metadata TEXT,
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_llm_usage_logs_user_id (user_id),
    INDEX idx_llm_usage_logs_task_type (task_type),
    INDEX idx_llm_usage_logs_provider (provider),
    INDEX idx_llm_usage_logs_created_at (created_at),
    INDEX idx_llm_usage_logs_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. 订阅消息相关表

-- 订阅消息表
CREATE TABLE IF NOT EXISTS subscribe_messages (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    template_id VARCHAR(100) NOT NULL,
    template_name VARCHAR(200) NOT NULL,
    message_data TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    send_result TEXT,
    error_message TEXT,
    sent_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_subscribe_messages_user_id (user_id),
    INDEX idx_subscribe_messages_template_id (template_id),
    INDEX idx_subscribe_messages_status (status),
    INDEX idx_subscribe_messages_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 用户订阅设置表
CREATE TABLE IF NOT EXISTS user_subscribe_settings (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    template_id VARCHAR(100) NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE,
    is_subscribed BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uk_user_template (user_id, template_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_subscribe_settings_user_id (user_id),
    INDEX idx_user_subscribe_settings_template_id (template_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. 社交相关表（可选，根据需求创建）

-- 社交偏好表
CREATE TABLE IF NOT EXISTS social_preferences (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL UNIQUE,
    social_purposes TEXT,
    current_industry VARCHAR(100),
    target_industries TEXT,
    professional_level VARCHAR(50),
    company_size_preference VARCHAR(50),
    social_interests TEXT,
    skills_to_offer TEXT,
    skills_to_learn TEXT,
    preferred_activities TEXT,
    preferred_meeting_formats TEXT,
    preferred_connection_types TEXT,
    experience_level_preference VARCHAR(50),
    available_time_slots TEXT,
    preferred_frequency VARCHAR(50),
    preferred_locations TEXT,
    remote_preference BOOLEAN DEFAULT TRUE,
    languages TEXT,
    group_size_preference VARCHAR(50),
    budget_range VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_social_preferences_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 社交档案表
CREATE TABLE IF NOT EXISTS social_profiles (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL UNIQUE,
    headline VARCHAR(255),
    summary TEXT,
    current_role VARCHAR(100),
    current_company VARCHAR(100),
    company_size VARCHAR(50),
    industry VARCHAR(100),
    professional_level VARCHAR(50),
    years_experience TINYINT UNSIGNED,
    skills TEXT,
    expertise_areas TEXT,
    social_interests TEXT,
    social_purposes TEXT,
    value_offerings TEXT,
    mentorship_areas TEXT,
    learning_goals TEXT,
    skill_gaps TEXT,
    preferred_contact_methods TEXT,
    activity_level VARCHAR(20) DEFAULT 'moderate',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_social_profiles_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 社交匹配条件表
CREATE TABLE IF NOT EXISTS social_match_criteria (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL UNIQUE,
    industry_weight TINYINT UNSIGNED DEFAULT 3,
    experience_weight TINYINT UNSIGNED DEFAULT 3,
    skills_weight TINYINT UNSIGNED DEFAULT 4,
    interests_weight TINYINT UNSIGNED DEFAULT 3,
    location_weight TINYINT UNSIGNED DEFAULT 2,
    min_experience_gap TINYINT UNSIGNED DEFAULT 0,
    max_experience_gap TINYINT UNSIGNED DEFAULT 10,
    exclude_competitors BOOLEAN DEFAULT FALSE,
    exclude_same_company BOOLEAN DEFAULT FALSE,
    preferred_connection_types TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_social_match_criteria_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 创建视图（可选）
-- 用户统计视图
CREATE OR REPLACE VIEW user_statistics AS
SELECT 
    u.id,
    u.nick_name,
    u.is_active as status,
    COUNT(DISTINCT uc.id) as card_count,
    COUNT(DISTINCT ma.id) as action_count,
    COUNT(DISTINCT mr.id) as match_count,
    MAX(u.created_at) as created_at,
    MAX(u.last_login) as last_login
FROM users u
LEFT JOIN user_cards uc ON u.id = uc.user_id AND uc.is_active = TRUE AND uc.is_deleted = FALSE
LEFT JOIN match_actions ma ON u.id = ma.user_id
LEFT JOIN match_results mr ON (u.id = mr.user1_id OR u.id = mr.user2_id) AND mr.is_active = TRUE
GROUP BY u.id, u.nick_name, u.is_active;

-- 匹配统计视图
CREATE OR REPLACE VIEW match_statistics AS
SELECT 
    mr.scene_type,
    mr.status,
    COUNT(*) as total_matches,
    COUNT(CASE WHEN mr.is_active = TRUE THEN 1 END) as active_matches,
    COUNT(CASE WHEN mr.is_blocked = TRUE THEN 1 END) as blocked_matches,
    AVG(TIMESTAMPDIFF(DAY, mr.matched_at, NOW())) as avg_match_days,
    MAX(mr.matched_at) as latest_match,
    MIN(mr.matched_at) as earliest_match
FROM match_results mr
GROUP BY mr.scene_type, mr.status;

-- 用户活跃度视图
CREATE OR REPLACE VIEW user_activity_statistics AS
SELECT 
    u.id,
    u.nick_name,
    u.created_at as register_date,
    u.last_login,
    COUNT(DISTINCT cm.id) as messages_sent,
    COUNT(DISTINCT ma.id) as match_actions,
    COUNT(DISTINCT mr.id) as successful_matches,
    TIMESTAMPDIFF(DAY, u.created_at, NOW()) as days_since_register,
    CASE 
        WHEN u.last_login IS NULL THEN 'never_login'
        WHEN TIMESTAMPDIFF(DAY, u.last_login, NOW()) <= 1 THEN 'active_today'
        WHEN TIMESTAMPDIFF(DAY, u.last_login, NOW()) <= 7 THEN 'active_week'
        WHEN TIMESTAMPDIFF(DAY, u.last_login, NOW()) <= 30 THEN 'active_month'
        ELSE 'inactive'
    END as activity_status
FROM users u
LEFT JOIN chat_messages cm ON u.id = cm.sender_id
LEFT JOIN match_actions ma ON u.id = ma.user_id
LEFT JOIN match_results mr ON (u.id = mr.user1_id OR u.id = mr.user2_id) AND mr.is_active = TRUE
GROUP BY u.id, u.nick_name, u.created_at, u.last_login;