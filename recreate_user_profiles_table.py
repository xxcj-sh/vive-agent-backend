#!/usr/bin/env python3
"""
重建user_profiles表的脚本
不保存存量数据，直接删除旧表并创建新表
支持阿里云 RDS MySQL 8.0 VECTOR 类型
"""

import logging
from sqlalchemy import text
from app.database import engine, Base
from app.models.user_profile import UserProfile, VECTOR_TYPE_AVAILABLE, VECTOR_DIMENSION

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recreate_user_profiles_table():
    """重建user_profiles表"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            conn.commit()
        
        logger.info("正在删除旧的user_profiles表...")
        UserProfile.__table__.drop(engine)
        
        logger.info("正在创建新的user_profiles表...")
        UserProfile.__table__.create(engine)
        
        if VECTOR_TYPE_AVAILABLE:
            logger.info("SQLAlchemy 支持 VECTOR 类型，尝试升级列为 VECTOR...")
        else:
            logger.info("SQLAlchemy 不支持 VECTOR 类型，使用 ALTER TABLE 直接修改...")
            
        try:
            with engine.connect() as conn:
                if VECTOR_TYPE_AVAILABLE:
                    logger.info("修改列为 VECTOR(1024) NOT NULL 类型...")
                    conn.execute(text(f"""
                        ALTER TABLE user_profiles 
                        MODIFY COLUMN raw_profile_embedding VECTOR({VECTOR_DIMENSION}) NOT NULL COMMENT '用户画像语义向量（{VECTOR_DIMENSION}维，豆包模型生成）'
                    """))
                else:
                    logger.info("修改列为 VECTOR(1024) NOT NULL 类型...")
                    conn.execute(text(f"""
                        ALTER TABLE user_profiles 
                        MODIFY COLUMN raw_profile_embedding VECTOR({VECTOR_DIMENSION}) NOT NULL COMMENT '用户画像语义向量（{VECTOR_DIMENSION}维，豆包模型生成）'
                    """))
                conn.commit()
                logger.info("列类型修改成功！")
        except Exception as e:
            logger.warning(f"修改列类型失败（数据库可能不支持）: {e}")
        
        logger.info("正在创建向量索引...")
        try:
            with engine.connect() as conn:
                conn.execute(text(f"""
                    CREATE VECTOR INDEX idx_raw_profile_embedding 
                    ON user_profiles(raw_profile_embedding) 
                    M=16 DISTANCE=COSINE
                """))
                conn.commit()
            logger.info("向量索引创建成功！")
        except Exception as e:
            logger.warning(f"创建向量索引失败（可能是数据库不支持）: {e}")
            logger.info("如需使用向量检索功能，请确保使用阿里云 RDS MySQL 8.0（内核小版本>=20251031）")
            logger.info("手动执行: CREATE VECTOR INDEX idx_raw_profile_embedding ON user_profiles(raw_profile_embedding) M=16 DISTANCE=COSINE")
        
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