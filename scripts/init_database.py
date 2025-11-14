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
        logger.info("开始初始化数据库...")
        
        # 导入所有模型，确保它们被注册到Base.metadata
        from app.models import (
            user, user_card_db, match, match_action, chat_message,
            user_profile, user_profile_history, user_profile_feedback, user_profile_score,
            activity_invitation, ai_skill, llm_usage_log, subscribe_message, order
        )
        
        logger.info(f"数据库连接URL: {settings.computed_database_url}")
        
        # 创建所有表
        logger.info("正在创建数据库表...")
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ 数据库表创建成功!")
        
        # 显示创建的表
        logger.info("已创建的表:")
        for table_name in Base.metadata.tables.keys():
            logger.info(f"  - {table_name}")
        
        # 验证数据库连接
        with engine.connect() as conn:
            result = conn.execute(text("SELECT DATABASE()"))
            db_name = result.scalar()
            logger.info(f"当前数据库: {db_name}")
            
            # 显示所有表
            result = conn.execute(text("SHOW TABLES"))
            tables = result.fetchall()
            logger.info(f"数据库中共有 {len(tables)} 张表:")
            for table in tables:
                logger.info(f"  - {table[0]}")
        
        logger.info("✅ 数据库初始化完成!")
        
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {str(e)}")
        raise

def drop_all_tables():
    """删除所有表（谨慎使用）"""
    try:
        logger.warning("⚠️  正在删除所有数据库表...")
        
        # 导入所有模型
        from app.models import (
            user, user_card_db, match, match_action, chat_message,
            user_profile, user_profile_history, user_profile_feedback, user_profile_score,
            activity_invitation, ai_skill, llm_usage_log, subscribe_message, order
        )
        
        # 删除所有表
        Base.metadata.drop_all(bind=engine)
        
        logger.warning("✅ 所有表已删除")
        
    except Exception as e:
        logger.error(f"❌ 删除表失败: {str(e)}")
        raise

def check_table_structure():
    """检查表结构"""
    try:
        logger.info("检查数据库表结构...")
        
        with engine.connect() as conn:
            # 获取所有表
            result = conn.execute(text("SHOW TABLES"))
            tables = result.fetchall()
            
            if not tables:
                logger.warning("数据库中没有表")
                return
            
            for table in tables:
                table_name = table[0]
                logger.info(f"\n表结构: {table_name}")
                
                # 获取表结构
                result = conn.execute(text(f"DESCRIBE {table_name}"))
                columns = result.fetchall()
                
                for column in columns:
                    logger.info(f"  {column[0]}: {column[1]} {column[2]} {column[3]}")
        
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
            logger.info("取消删除操作")
    elif args.check:
        check_table_structure()
    else:
        init_database()