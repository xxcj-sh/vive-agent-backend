#!/usr/bin/env python3
"""
MySQL 数据库表重置脚本
用于创建或重置所有数据库表结构

使用方法:
    python reset_mysql_tables.py [--force] [--test]
    
参数:
    --force: 强制删除现有表并重新创建
    --test: 使用测试数据库 (vmatch_test)
"""

import os
import sys
import argparse
import pymysql
from typing import Optional, List
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

def get_connection(database: Optional[str] = None):
    """获取数据库连接"""
    try:
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USERNAME,
            password=MYSQL_PASSWORD,
            database=database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        sys.exit(1)

def create_database(database_name: str):
    """创建数据库"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # 创建数据库
            cursor.execute(f"""
                CREATE DATABASE IF NOT EXISTS {database_name} 
                CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
            """)
            logger.info(f"数据库 '{database_name}' 创建成功")
    finally:
        conn.close()

def drop_tables(conn, force: bool = False):
    """删除所有表（如果存在）"""
    if not force:
        return
        
    try:
        with conn.cursor() as cursor:
            # 获取所有表
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            if not tables:
                logger.info("没有找到现有表")
                return
            
            # 禁用外键检查
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            
            # 删除所有表
            for table in tables:
                table_name = list(table.values())[0]
                cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
                logger.info(f"删除表: {table_name}")
            
            # 启用外键检查
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            
            logger.info("所有表已删除")
    except Exception as e:
        logger.error(f"删除表失败: {e}")
        raise

def create_tables(conn):
    """创建所有表"""
    sql_statements = get_table_creation_sql()
    
    try:
        with conn.cursor() as cursor:
            for statement in sql_statements:
                if statement.strip():
                    cursor.execute(statement)
            
            logger.info("所有表创建完成")
    except Exception as e:
        logger.error(f"创建表失败: {e}")
        raise

def get_table_creation_sql() -> List[str]:
    """获取所有表的创建SQL语句"""
    return [
        # 用户表
        """
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
        
        # 用户卡片表
        """
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
        
        # 匹配操作记录表
        """
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
            INDEX idx_match_actions_user_id (user_id),
            INDEX idx_match_actions_target_user_id (target_user_id),
            INDEX idx_match_actions_action_type (action_type),
            INDEX idx_match_actions_scene_type (scene_type),
            INDEX idx_match_actions_created_at (created_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """,
        
        # 匹配结果记录表
        """
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
        
        # 会员订单表
        """
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
        
        # LLM使用日志表
        """
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
        
        # 用户画像表
        """
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
    ]

def verify_tables(conn):
    """验证表是否创建成功"""
    try:
        with conn.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            table_names = [list(table.values())[0] for table in tables]
            logger.info(f"已创建的表: {', '.join(table_names)}")
            
            return len(table_names)
    except Exception as e:
        logger.error(f"验证表失败: {e}")
        return 0

def main():
    parser = argparse.ArgumentParser(description='MySQL数据库表重置脚本')
    parser.add_argument('--force', action='store_true', help='强制删除现有表并重新创建')
    parser.add_argument('--test', action='store_true', help='使用测试数据库 (vmatch_test)')
    args = parser.parse_args()
    
    # 设置数据库名称
    database_name = 'vmatch_test' if args.test else MYSQL_DATABASE
    
    logger.info(f"开始处理数据库: {database_name}")
    logger.info(f"MySQL主机: {MYSQL_HOST}:{MYSQL_PORT}")
    
    try:
        # 创建数据库
        create_database(database_name)
        
        # 连接到目标数据库
        conn = get_connection(database_name)
        
        try:
            # 删除现有表（如果指定了--force）
            drop_tables(conn, args.force)
            
            # 创建所有表
            create_tables(conn)
            
            # 验证表创建
            table_count = verify_tables(conn)
            
            # 提交事务
            conn.commit()
            
            logger.info(f"数据库表重置完成！共创建 {table_count} 个表")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"操作失败: {e}")
            sys.exit(1)
        finally:
            conn.close()
            
    except KeyboardInterrupt:
        logger.info("操作被用户中断")
        sys.exit(0)
    except Exception as e:
        logger.error(f"发生错误: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()