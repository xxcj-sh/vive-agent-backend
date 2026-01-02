#!/usr/bin/env python3
"""
验证user_profiles表是否成功重建
"""

import logging
from sqlalchemy import text
from app.database import engine

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_user_profiles_table():
    """验证user_profiles表结构"""
    try:
        with engine.connect() as conn:
            # 检查表是否存在
            result = conn.execute(text("SHOW TABLES LIKE 'user_profiles'"))
            if not result.fetchone():
                logger.error("user_profiles表不存在")
                return False
            
            # 检查表结构
            result = conn.execute(text("DESCRIBE user_profiles"))
            columns = result.fetchall()
            
            logger.info("user_profiles表结构:")
            for column in columns:
                logger.info(f"  {column[0]}: {column[1]} (nullable: {column[2]})")
            
            # 检查必要字段
            required_columns = ['id', 'user_id', 'raw_profile', 'profile_summary', 'updated_at', 'created_at']
            existing_columns = [col[0] for col in columns]
            
            missing_columns = [col for col in required_columns if col not in existing_columns]
            if missing_columns:
                logger.error(f"缺少必要字段: {missing_columns}")
                return False
            
            logger.info("user_profiles表验证成功！")
            return True
            
    except Exception as e:
        logger.error(f"验证user_profiles表失败: {e}")
        return False

if __name__ == "__main__":
    success = verify_user_profiles_table()
    exit(0 if success else 1)