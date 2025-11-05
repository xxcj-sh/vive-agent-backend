#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：为user_profile_feedback表添加缺失的comment列
"""

import os
import sys
import pymysql
import logging
from pymysql.cursors import DictCursor
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

def get_db_config():
    """获取数据库配置"""
    return {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USERNAME', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DATABASE', 'vmatch_dev')
    }

def check_column_exists(cursor, table_name, column_name):
    """检查列是否存在"""
    cursor.execute(
        "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s AND COLUMN_NAME = %s",
        (table_name, column_name)
    )
    return cursor.fetchone() is not None

def add_comment_column():
    """为user_profile_feedback表添加comment列"""
    db_config = get_db_config()
    connection = None
    cursor = None
    
    try:
        # 连接数据库
        connection = pymysql.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database'],
            cursorclass=DictCursor
        )
        cursor = connection.cursor()
        logger.info(f"成功连接到数据库: {db_config['host']}:{db_config['port']}/{db_config['database']}")
        
        # 检查表是否存在
        cursor.execute("SHOW TABLES LIKE 'user_profile_feedback'")
        if not cursor.fetchone():
            logger.error("错误: user_profile_feedback表不存在")
            return False
        
        # 检查comment列是否已存在
        if check_column_exists(cursor, 'user_profile_feedback', 'comment'):
            logger.info("comment列已存在，无需添加")
            return True
        
        # 添加comment列
        logger.info("开始添加comment列到user_profile_feedback表...")
        cursor.execute("""
            ALTER TABLE user_profile_feedback 
            ADD COLUMN comment TEXT COMMENT '评价备注'
        """)
        connection.commit()
        logger.info("✅ comment列添加成功")
        
        # 验证列是否添加成功
        if check_column_exists(cursor, 'user_profile_feedback', 'comment'):
            logger.info("验证成功: comment列已存在于表中")
            return True
        else:
            logger.error("验证失败: comment列未添加成功")
            return False
            
    except Exception as e:
        logger.error(f"迁移过程中发生错误: {str(e)}")
        if connection:
            connection.rollback()
            logger.info("已回滚事务")
        return False
    finally:
        # 关闭连接
        if cursor:
            cursor.close()
        if connection:
            connection.close()
        logger.info("数据库连接已关闭")

def main():
    """主函数"""
    logger.info("===== 开始执行user_profile_feedback表comment列迁移 =====")
    success = add_comment_column()
    
    if success:
        logger.info("===== user_profile_feedback表comment列迁移成功 =====")
        sys.exit(0)
    else:
        logger.error("===== user_profile_feedback表comment列迁移失败 =====")
        sys.exit(1)

if __name__ == "__main__":
    main()