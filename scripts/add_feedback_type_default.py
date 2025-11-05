#!/usr/bin/env python3
"""
数据库迁移脚本：为 user_profile_feedback 表的 feedback_type 字段添加默认值
"""

import pymysql
import pymysql.cursors
import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def get_db_config():
    """从环境变量获取数据库配置"""
    # 加载环境变量
    load_dotenv()
    
    return {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USERNAME', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'db': os.getenv('MYSQL_DATABASE', 'vmatch_dev'),
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor
    }

def update_feedback_type_default():
    """为 user_profile_feedback 表的 feedback_type 字段添加默认值"""
    table_name = 'user_profile_feedback'
    column_name = 'feedback_type'
    default_value = 'general'
    
    start_time = datetime.now()
    logger.info(f"===== 开始执行 {table_name} 表 {column_name} 字段默认值设置 =====")
    
    conn = None
    try:
        # 获取数据库配置并连接
        db_config = get_db_config()
        conn = pymysql.connect(**db_config)
        logger.info(f"成功连接到数据库: {db_config['host']}:{db_config['port']}/{db_config['db']}")
        
        # 使用事务
        with conn.cursor() as cursor:
            # 开始事务
            cursor.execute("START TRANSACTION")
            
            try:
                # 检查字段是否存在
                cursor.execute(f"SHOW COLUMNS FROM {table_name} LIKE '{column_name}'")
                if not cursor.fetchone():
                    raise Exception(f"表 {table_name} 中不存在字段 {column_name}")
                
                # 检查字段是否已经有默认值
                cursor.execute(f"SHOW FULL COLUMNS FROM {table_name} WHERE Field = '{column_name}'")
                column_info = cursor.fetchone()
                
                if column_info and column_info['Default'] is None:
                    # 修改字段添加默认值
                    alter_query = f"ALTER TABLE {table_name} ALTER COLUMN {column_name} SET DEFAULT %s"
                    cursor.execute(alter_query, (default_value,))
                    logger.info(f"✅ 成功为字段 {column_name} 设置默认值: {default_value}")
                else:
                    logger.info(f"ℹ️  字段 {column_name} 已经有默认值: {column_info['Default']}")
                
                # 提交事务
                conn.commit()
                logger.info("事务提交成功")
                
                # 验证设置
                cursor.execute(f"SHOW FULL COLUMNS FROM {table_name} WHERE Field = '{column_name}'")
                updated_column_info = cursor.fetchone()
                if updated_column_info and updated_column_info['Default'] == default_value:
                    logger.info(f"验证成功: {column_name} 字段默认值已设置为 {default_value}")
                else:
                    logger.warning(f"验证结果: {column_name} 字段默认值为 {updated_column_info['Default']}")
                    
            except Exception as e:
                # 回滚事务
                conn.rollback()
                logger.error(f"迁移过程中发生错误: {e}")
                logger.info("已回滚事务")
                raise
    
    except Exception as e:
        logger.error(f"===== {table_name} 表 {column_name} 字段默认值设置失败 =====")
        raise
    
    finally:
        if conn:
            conn.close()
            logger.info("数据库连接已关闭")
        
        # 计算执行时间
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        logger.info(f"===== {table_name} 表 {column_name} 字段默认值设置完成 =====")
        logger.info(f"执行时间: {execution_time:.2f}秒")

if __name__ == "__main__":
    try:
        update_feedback_type_default()
        sys.exit(0)
    except Exception as e:
        logger.error(f"错误: {e}")
        sys.exit(1)