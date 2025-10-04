#!/usr/bin/env python3
"""
数据库迁移脚本
用于在现有数据库上安全地添加新表或修改表结构

使用方法:
    python migrate_database.py [--check] [--dry-run]
    
参数:
    --check: 只检查需要迁移的内容，不执行实际迁移
    --dry-run: 模拟执行迁移，显示将要执行的SQL语句
"""

import os
import sys
import argparse
import pymysql
from typing import List, Dict, Tuple
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 数据库配置
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
MYSQL_USERNAME = os.getenv('MYSQL_USERNAME', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'vmatch_dev')

def get_connection():
    """获取数据库连接"""
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USERNAME,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def get_existing_tables() -> List[str]:
    """获取现有表列表"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = [list(table.values())[0] for table in cursor.fetchall()]
            return tables
    finally:
        conn.close()

def get_table_schema(table_name: str) -> Dict:
    """获取表结构信息"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            
            cursor.execute(f"SHOW INDEX FROM {table_name}")
            indexes = cursor.fetchall()
            
            return {
                'columns': columns,
                'indexes': indexes
            }
    finally:
        conn.close()

def check_column_exists(table_name: str, column_name: str) -> bool:
    """检查列是否存在"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            return any(col['Field'] == column_name for col in columns)
    except:
        return False
    finally:
        conn.close()

def check_table_exists(table_name: str) -> bool:
    """检查表是否存在"""
    existing_tables = get_existing_tables()
    return table_name in existing_tables

def get_migration_sql() -> List[Tuple[str, str]]:
    """获取迁移SQL语句列表 (sql, description)"""
    migrations = []
    existing_tables = get_existing_tables()
    
    # 检查并添加新表
    required_tables = {
        'users': """
            CREATE TABLE IF NOT EXISTS users (
                id VARCHAR(36) PRIMARY KEY,
                phone VARCHAR(20) UNIQUE,
                hashed_password TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                nick_name VARCHAR(100),
                avatar_url TEXT,
                gender TINYINT,
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
                INDEX idx_users_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        'user_cards': """
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
                INDEX idx_user_cards_is_active (is_active)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        'match_actions': """
            CREATE TABLE IF NOT EXISTS match_actions (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
                target_user_id VARCHAR(36) NOT NULL,
                target_card_id VARCHAR(36) NOT NULL,
                action_type VARCHAR(20) NOT NULL,
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
                INDEX idx_match_actions_user_id (user_id),
                INDEX idx_match_actions_target_user_id (target_user_id),
                INDEX idx_match_actions_action_type (action_type),
                INDEX idx_match_actions_scene_type (scene_type),
                INDEX idx_match_actions_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        'match_results': """
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
                FOREIGN KEY (user1_action_id) REFERENCES match_actions(id) ON DELETE CASCADE,
                FOREIGN KEY (user2_action_id) REFERENCES match_actions(id) ON DELETE CASCADE,
                INDEX idx_match_results_user1_id (user1_id),
                INDEX idx_match_results_user2_id (user2_id),
                INDEX idx_match_results_status (status),
                INDEX idx_match_results_is_active (is_active)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        'membership_orders': """
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
                INDEX idx_membership_orders_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        'llm_usage_logs': """
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
                INDEX idx_llm_usage_logs_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        'user_profiles': """
            CREATE TABLE IF NOT EXISTS user_profiles (
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
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
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
    }
    
    # 检查缺失的表
    for table_name, sql in required_tables.items():
        if not check_table_exists(table_name):
            migrations.append((sql, f"创建表: {table_name}"))
    
    # 检查表结构更新
    if check_table_exists('users'):
        # 检查是否需要添加新列
        new_columns = [
            ('users', 'register_at', "ALTER TABLE users ADD COLUMN register_at TIMESTAMP NULL AFTER points"),
            ('users', 'level', "ALTER TABLE users ADD COLUMN level TINYINT UNSIGNED DEFAULT 1 AFTER last_login"),
            ('users', 'points', "ALTER TABLE users ADD COLUMN points INT DEFAULT 0 AFTER level"),
        ]
        
        for table, column, sql in new_columns:
            if not check_column_exists(table, column):
                migrations.append((sql, f"添加列: {table}.{column}"))
    
    return migrations

def execute_migrations(migrations: List[Tuple[str, str]], dry_run: bool = False):
    """执行迁移"""
    if not migrations:
        logger.info("没有需要执行的迁移")
        return
    
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            for sql, description in migrations:
                logger.info(f"执行: {description}")
                if dry_run:
                    logger.info(f"SQL: {sql}")
                else:
                    cursor.execute(sql)
                    logger.info(f"✅ 完成: {description}")
        
        if not dry_run:
            conn.commit()
            logger.info("所有迁移执行完成")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"迁移失败: {e}")
        raise
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description='数据库迁移脚本')
    parser.add_argument('--check', action='store_true', help='只检查需要迁移的内容')
    parser.add_argument('--dry-run', action='store_true', help='模拟执行迁移，显示SQL语句')
    args = parser.parse_args()
    
    logger.info(f"开始数据库迁移检查: {MYSQL_DATABASE}")
    logger.info(f"MySQL主机: {MYSQL_HOST}:{MYSQL_PORT}")
    
    try:
        # 获取迁移列表
        migrations = get_migration_sql()
        
        if not migrations:
            logger.info("数据库已经是最新状态，无需迁移")
            return
        
        logger.info(f"发现 {len(migrations)} 个需要执行的迁移")
        
        for _, description in migrations:
            logger.info(f"  - {description}")
        
        if args.check:
            logger.info("检查完成，未执行实际迁移")
            return
        
        # 执行迁移
        execute_migrations(migrations, args.dry_run)
        
        if args.dry_run:
            logger.info("模拟执行完成，未对数据库进行实际修改")
        else:
            logger.info("数据库迁移完成")
            
    except Exception as e:
        logger.error(f"迁移过程出错: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()