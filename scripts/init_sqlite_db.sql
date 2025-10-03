-- SQLite 数据库初始化脚本
-- 用于创建所有必要的表结构

-- 用户表
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    phone TEXT UNIQUE,
    hashed_password TEXT,
    is_active BOOLEAN DEFAULT 1,
    nick_name TEXT,
    avatar_url TEXT,
    gender INTEGER,
    age INTEGER,
    bio TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    occupation TEXT,
    location TEXT,
    education TEXT,
    interests TEXT,
    wechat TEXT,
    wechat_open_id TEXT,
    email TEXT,
    status TEXT DEFAULT 'pending',
    last_login TIMESTAMP,
    level INTEGER DEFAULT 1,
    points INTEGER DEFAULT 0,
    register_at TIMESTAMP
);

-- 用户卡片表
CREATE TABLE user_cards (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    role_type TEXT NOT NULL,
    scene_type TEXT NOT NULL,
    display_name TEXT NOT NULL,
    avatar_url TEXT,
    bio TEXT,
    trigger_and_output TEXT,
    profile_data TEXT,
    preferences TEXT,
    visibility TEXT DEFAULT 'public',
    is_active INTEGER DEFAULT 1,
    is_deleted INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    search_code TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 匹配操作记录表
CREATE TABLE match_actions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    target_user_id TEXT NOT NULL,
    target_card_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    scene_type TEXT NOT NULL,
    scene_context TEXT,
    source TEXT DEFAULT 'user',
    is_processed BOOLEAN DEFAULT 0,
    processed_at TIMESTAMP,
    extra TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (target_user_id) REFERENCES users(id)
);

-- 匹配结果记录表
CREATE TABLE match_results (
    id TEXT PRIMARY KEY,
    user1_id TEXT NOT NULL,
    user2_id TEXT NOT NULL,
    user1_card_id TEXT NOT NULL,
    user2_card_id TEXT NOT NULL,
    scene_type TEXT NOT NULL,
    status TEXT DEFAULT 'matched',
    user1_action_id TEXT NOT NULL,
    user2_action_id TEXT NOT NULL,
    matched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    first_message_at TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    is_blocked BOOLEAN DEFAULT 0,
    expiry_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user1_id) REFERENCES users(id),
    FOREIGN KEY (user2_id) REFERENCES users(id),
    FOREIGN KEY (user1_action_id) REFERENCES match_actions(id),
    FOREIGN KEY (user2_action_id) REFERENCES match_actions(id)
);



-- 会员订单表
CREATE TABLE membership_orders (
    id TEXT PRIMARY KEY,
    plan_name TEXT NOT NULL,
    amount REAL NOT NULL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending',
    user_id TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- LLM使用日志表
CREATE TABLE llm_usage_logs (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    task_type TEXT NOT NULL,
    provider TEXT NOT NULL,
    llm_model_name TEXT NOT NULL,
    prompt_tokens INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    prompt_content TEXT,
    response_content TEXT,
    request_duration REAL NOT NULL,
    response_time REAL NOT NULL,
    request_params TEXT,
    response_metadata TEXT,
    status TEXT DEFAULT 'success',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 社交偏好表
CREATE TABLE social_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    social_purposes TEXT,
    current_industry TEXT,
    target_industries TEXT,
    professional_level TEXT,
    company_size_preference TEXT,
    social_interests TEXT,
    skills_to_offer TEXT,
    skills_to_learn TEXT,
    preferred_activities TEXT,
    preferred_meeting_formats TEXT,
    preferred_connection_types TEXT,
    experience_level_preference TEXT,
    available_time_slots TEXT,
    preferred_frequency TEXT,
    preferred_locations TEXT,
    remote_preference BOOLEAN DEFAULT 1,
    languages TEXT,
    group_size_preference TEXT,
    budget_range TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 社交档案表
CREATE TABLE social_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    headline TEXT,
    summary TEXT,
    current_role TEXT,
    current_company TEXT,
    company_size TEXT,
    industry TEXT,
    professional_level TEXT,
    years_experience INTEGER,
    skills TEXT,
    expertise_areas TEXT,
    social_interests TEXT,
    social_purposes TEXT,
    value_offerings TEXT,
    mentorship_areas TEXT,
    learning_goals TEXT,
    skill_gaps TEXT,
    preferred_contact_methods TEXT,
    activity_level TEXT DEFAULT 'moderate',
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 社交匹配条件表
CREATE TABLE social_match_criteria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    industry_weight INTEGER DEFAULT 3,
    experience_weight INTEGER DEFAULT 3,
    skills_weight INTEGER DEFAULT 4,
    interests_weight INTEGER DEFAULT 3,
    location_weight INTEGER DEFAULT 2,
    min_experience_gap INTEGER DEFAULT 0,
    max_experience_gap INTEGER DEFAULT 10,
    exclude_competitors BOOLEAN DEFAULT 0,
    exclude_same_company BOOLEAN DEFAULT 0,
    preferred_connection_types TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 用户画像表
CREATE TABLE user_profiles (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    preferences TEXT,
    personality_traits TEXT,
    mood_state TEXT,
    behavior_patterns TEXT,
    interest_tags TEXT,
    social_preferences TEXT,
    match_preferences TEXT,
    data_source TEXT,
    confidence_score INTEGER,
    update_reason TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1,
    is_active INTEGER DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 创建索引
CREATE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_users_wechat_open_id ON users(wechat_open_id);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_user_cards_user_id ON user_cards(user_id);
CREATE INDEX idx_user_cards_scene_type ON user_cards(scene_type);
CREATE INDEX idx_user_cards_is_active ON user_cards(is_active);

-- 用户画像表索引
CREATE INDEX idx_user_profiles_user_id ON user_profiles(user_id);
CREATE INDEX idx_user_profiles_is_active ON user_profiles(is_active);
CREATE INDEX idx_user_profiles_created_at ON user_profiles(created_at);
CREATE INDEX idx_user_profiles_updated_at ON user_profiles(updated_at);
CREATE INDEX idx_match_actions_user_id ON match_actions(user_id);
CREATE INDEX idx_match_actions_target_user_id ON match_actions(target_user_id);
CREATE INDEX idx_match_actions_action_type ON match_actions(action_type);
CREATE INDEX idx_match_actions_scene_type ON match_actions(scene_type);
CREATE INDEX idx_match_actions_created_at ON match_actions(created_at);
CREATE INDEX idx_match_results_user1_id ON match_results(user1_id);
CREATE INDEX idx_match_results_user2_id ON match_results(user2_id);
CREATE INDEX idx_match_results_status ON match_results(status);
CREATE INDEX idx_match_results_is_active ON match_results(is_active);

CREATE INDEX idx_membership_orders_user_id ON membership_orders(user_id);
CREATE INDEX idx_membership_orders_status ON membership_orders(status);
CREATE INDEX idx_llm_usage_logs_user_id ON llm_usage_logs(user_id);
CREATE INDEX idx_llm_usage_logs_created_at ON llm_usage_logs(created_at);
CREATE INDEX idx_social_preferences_user_id ON social_preferences(user_id);
CREATE INDEX idx_social_profiles_user_id ON social_profiles(user_id);
CREATE INDEX idx_social_match_criteria_user_id ON social_match_criteria(user_id);

-- 创建视图（可选）
-- 用户统计视图
CREATE VIEW user_statistics AS
SELECT 
    u.id,
    u.nick_name,
    u.status,
    COUNT(uc.id) as card_count,
    COUNT(ma.id) as action_count,
    COUNT(DISTINCT mr.id) as match_count
FROM users u
LEFT JOIN user_cards uc ON u.id = uc.user_id AND uc.is_active = 1
LEFT JOIN match_actions ma ON u.id = ma.user_id
LEFT JOIN match_results mr ON (u.id = mr.user1_id OR u.id = mr.user2_id) AND mr.is_active = 1
GROUP BY u.id, u.nick_name, u.status;

-- 匹配统计视图
CREATE VIEW match_statistics AS
SELECT 
    mr.scene_type,
    mr.status,
    COUNT(*) as total_matches,
    COUNT(CASE WHEN mr.is_active = 1 THEN 1 END) as active_matches,
    AVG(julianday('now') - julianday(mr.matched_at)) as avg_match_days
FROM match_results mr
GROUP BY mr.scene_type, mr.status;