"""
数据库初始化模块
负责创建所有数据表和初始化必要的数据
"""

import logging
import os
import uuid
from datetime import datetime

from sqlalchemy import text, create_engine
from sqlalchemy.orm import Session

from app.database import Base, engine
from app.config import settings

# 导入所有模型
from app.models.user import User
from app.models.match import Match, MatchDetail, MatchType, MatchStatus
from app.models.match_action import MatchAction, MatchResult
from app.models.user_card_db import UserCard
from app.models.llm_usage_log import LLMUsageLog
from app.models.order import MembershipOrder
from app.models.chat_message import ChatMessage
from app.models.subscribe_message import SubscribeMessage, UserSubscribeSetting
from app.models.user_profile import UserProfile
from app.models.user_profile_history import UserProfileHistory
from app.models.user_profile_feedback import UserProfileFeedback
from app.models.user_profile_score import (
    UserProfileScore, 
    UserProfileScoreHistory, 
    UserProfileSkill,
    ScoreType,
    SkillLevel
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_database_if_not_exists():
    """
    检查并创建数据库（如果不存在）
    注意：需要有足够的权限执行此操作
    """
    try:
        # 先创建一个不指定数据库的连接
        root_db_url = f"mysql+pymysql://{settings.MYSQL_USERNAME}:{settings.MYSQL_PASSWORD}@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/mysql"
        root_engine = create_engine(root_db_url)
        
        with root_engine.connect() as conn:
            # 检查数据库是否存在
            result = conn.execute(
                text(f"SHOW DATABASES LIKE '{settings.MYSQL_DATABASE}'")
            )
            if not result.fetchone():
                conn.execute(text(f"CREATE DATABASE {settings.MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                conn.commit()
            else:
                pass
        
        root_engine.dispose()
        return True
    except Exception as e:
        # 继续执行，可能用户没有创建数据库的权限，但数据库已存在
        return False

def create_tables():
    """
    创建所有数据表
    """
    try:
        # 获取所有继承自Base的模型类
        all_tables = Base.metadata.sorted_tables
        
        # 创建表
        Base.metadata.create_all(bind=engine)
        return True
    except Exception as e:
        raise

def init_database():
    """
    完整的数据库初始化流程
    1. 检查并创建数据库
    2. 创建所有数据表
    3. 初始化基础数据（如果需要）
    """
    # 步骤1: 创建数据库（如果不存在）
    create_database_if_not_exists()
    
    # 步骤2: 创建数据表
    create_tables()
    
    # 步骤3: 初始化基础数据（如有需要）
    # init_base_data()
    
    return True

def drop_all_tables():
    """
    删除所有数据表（谨慎使用！仅用于开发环境）
    """
    if settings.ENVIRONMENT == "production":
        raise RuntimeError("禁止在生产环境中删除数据表")
    
    try:
        Base.metadata.drop_all(bind=engine)
        return True
    except Exception as e:
        raise

def get_db_connection_stats():
    """
    获取数据库连接统计信息
    """
    try:
        with engine.connect() as conn:
            # 获取连接池状态
            pool_size = engine.pool.size()
            pool_overflow = engine.pool.overflow()
            pool_checkout = engine.pool.checkedout()
            
            # 获取数据库中的表数量
            result = conn.execute(text("SHOW TABLES"))
            tables = result.fetchall()
            
            return {
                "pool_size": pool_size,
                "pool_overflow": pool_overflow,
                "pool_checkout": pool_checkout,
                "table_count": len(tables),
                "tables": [table[0] for table in tables]
            }
    except Exception as e:
        return None

def init_db():
    """
    简化版初始化函数（兼容原有接口）
    """
    return init_database()

if __name__ == "__main__":
    try:
        init_database()
        
        # 显示数据库统计信息
        stats = get_db_connection_stats()
        if stats:
            pass
            
    except Exception as e:
        raise