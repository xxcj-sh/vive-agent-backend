#!/usr/bin/env python3
"""
重建user_profiles表的脚本
不保存存量数据，直接删除旧表并创建新表
"""

import logging
from sqlalchemy import text
from app.database import engine, Base
from app.models.user_profile import UserProfile
from app.models.user_profile_history import UserProfileHistory

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recreate_user_profiles_table():
    """重建user_profiles表"""
    try:
        # 关闭外键检查
        with engine.connect() as conn:
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            conn.commit()
        
        # 删除旧表
        logger.info("正在删除旧的user_profiles表...")
        UserProfile.__table__.drop(engine)
        
        # 重新创建表
        logger.info("正在创建新的user_profiles表...")
        UserProfile.__table__.create(engine)
        
        # 恢复外键检查
        with engine.connect() as conn:
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
            conn.commit()
        
        logger.info("user_profiles表重建成功！")
        return True
        
    except Exception as e:
        logger.error(f"重建user_profiles表失败: {e}")
        return False

if __name__ == "__main__":
    success = recreate_user_profiles_table()
    exit(0 if success else 1)