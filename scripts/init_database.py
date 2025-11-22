#!/usr/bin/env python3
"""
数据库初始化脚本
根据models目录中的所有模型定义创建数据库表结构
"""

import os
import sys
import logging
from pathlib import Path

# 将项目根目录添加到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from app.database import Base, engine
from app.config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def init_database():
    """初始化数据库表结构"""
    try:
        # 导入所有模型，确保它们被注册到Base.metadata
        from app.models import (
            user, user_card_db, match, match_action, chat_message,
            user_profile, user_profile_history, user_profile_feedback, user_profile_score,
            activity_invitation, ai_skill, llm_usage_log, subscribe_message, order
        )
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {str(e)}")
        raise

def drop_all_tables():
    """删除所有表（谨慎使用）"""
    try:
        # 导入所有模型
        from app.models import (
            user, user_card_db, match, match_action, chat_message,
            user_profile, user_profile_history, user_profile_feedback, user_profile_score,
            activity_invitation, ai_skill, llm_usage_log, subscribe_message, order
        )
        
        # 删除所有表
        Base.metadata.drop_all(bind=engine)
        
    except Exception as e:
        logger.error(f"❌ 删除表失败: {str(e)}")
        raise

def check_table_structure():
    """检查表结构"""
    try:
        with engine.connect() as conn:
            # 获取所有表
            result = conn.execute(text("SHOW TABLES"))
            tables = result.fetchall()
            
            if not tables:
                return
            
            for table in tables:
                table_name = table[0]
                
                # 获取表结构
                result = conn.execute(text(f"DESCRIBE {table_name}"))
                columns = result.fetchall()
        
    except Exception as e:
        logger.error(f"检查表结构失败: {str(e)}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="数据库初始化脚本")
    parser.add_argument(
        "--drop", 
        action="store_true", 
        help="删除所有表（谨慎使用）"
    )
    parser.add_argument(
        "--check", 
        action="store_true", 
        help="检查表结构"
    )
    
    args = parser.parse_args()
    
    if args.drop:
        # 确认删除
        response = input("⚠️  确定要删除所有表吗？此操作不可恢复！输入 'yes' 确认: ")
        if response.lower() == 'yes':
            drop_all_tables()
        else:
            pass
    elif args.check:
        check_table_structure()
    else:
        init_database()