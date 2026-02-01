#!/usr/bin/env python3
"""
数据库表结构初始化脚本
基于SQLAlchemy模型定义创建数据库表结构
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from app.database import Base, engine
from app.config import settings
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_database():
    """创建数据库（如果不存在）"""
    try:
        # 获取数据库连接信息（不包含数据库名）
        database_url_without_db = settings.computed_database_url.rsplit('/', 1)[0]
        db_name = settings.MYSQL_DATABASE
        
        # 连接到mysql数据库（不指定具体数据库）
        temp_engine = create_engine(database_url_without_db)
        
        with temp_engine.connect() as conn:
            # 检查数据库是否存在
            result = conn.execute(text(f"SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '{db_name}'"))
            if not result.fetchone():
                # 创建数据库
                conn.execute(text(f"CREATE DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                conn.commit()
                logger.info(f"✅ 数据库 '{db_name}' 创建成功")
            else:
                logger.info(f"📋 数据库 '{db_name}' 已存在")
                
        temp_engine.dispose()
        return True
        
    except Exception as e:
        logger.error(f"❌ 创建数据库失败: {e}")
        return False

def init_all_tables():
    """初始化所有数据库表"""
    try:
        logger.info("🔄 开始导入所有模型...")
        
        # 导入所有模型，确保表被注册到Base.metadata
        from app.models.user import User
        from app.models.user_profile import UserProfile
        from app.models.user_card_db import UserCard
        from app.models.topic_card_db import TopicCard
        from app.models.vote_card_db import VoteCard
        from app.models.chat_message import ChatMessage, ChatSummary
        from app.models.user_profile_history import UserProfileHistory
        from app.models.user_profile_feedback import UserProfileFeedback
        from app.models.user_profile_score import UserProfileScore, UserProfileScoreHistory, UserProfileSkill
        from app.models.llm_usage_log import LLMUsageLog
        from app.models.order import MembershipOrder
        from app.models.content_moderation_db import ContentModeration
        from app.models.tag import Tag, UserTagRel
        from app.models.community_invitation import CommunityInvitation, InvitationUsage
        from app.models.tag_content import TagContent, ContentTagInteraction
        
        logger.info(f"📊 已注册的表: {list(Base.metadata.tables.keys())}")
        
        logger.info("🔄 开始创建数据库表...")
        
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ 所有数据库表创建成功")
        return True
        
    except Exception as e:
        logger.error(f"❌ 创建数据库表失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_optimization_indexes():
    """创建性能优化索引"""
    try:
        logger.info("🔄 开始创建优化索引...")
        
        with engine.connect() as conn:
            # 用户表索引
            indexes = [
                ("users", ["status"]),
                ("users", ["phone"]),
                ("user_profiles", ["user_id"]),
                ("user_profiles", ["updated_at"]),
                ("user_cards", ["user_id", "role_type"]),

                ("user_cards", ["is_active"]),
                ("user_cards", ["is_deleted"]),
                ("topic_cards", ["user_id"]),
                ("topic_cards", ["category"]),
                ("topic_cards", ["is_active"]),
                ("vote_cards", ["user_id"]),
                ("vote_cards", ["category"]),
                ("vote_cards", ["is_active"]),
                ("chat_messages", ["user_id", "created_at"]),
                ("chat_messages", ["card_id", "created_at"]),
                ("chat_messages", ["is_anonymous"]),
                ("chat_messages", ["sender_type"]),
                ("chat_messages", ["session_id"]),
                ("chat_messages", ["message_type"]),
                ("chat_summaries", ["user_id", "created_at"]),
                ("chat_summaries", ["card_id", "created_at"]),
                ("chat_summaries", ["is_read"]),
                ("chat_summaries", ["summary_type"]),
                ("llm_usage_logs", ["user_id", "created_at"]),
                ("llm_usage_logs", ["task_type"]),
                ("llm_usage_logs", ["provider"]),
                ("membership_orders", ["user_id"]),
                ("membership_orders", ["status"]),
                # 内容审核相关索引
                ("content_moderations", ["object_id", "object_type"]),
                ("content_moderations", ["overall_status"]),
                ("content_moderations", ["callback_received"]),
                ("content_moderations", ["result_updated_at"]),
            ]
            
            for table, columns in indexes:
                index_name = f"idx_{table}_{'_'.join(columns)}"
                column_list = ', '.join(columns)
                
                try:
                    conn.execute(text(f"CREATE INDEX {index_name} ON {table}({column_list})"))
                    logger.info(f"   ✅ 创建索引: {index_name}")
                except Exception as e:
                    if "Duplicate key name" in str(e):
                        logger.info(f"   📋 索引已存在: {index_name}")
                    else:
                        logger.warning(f"   ⚠️  创建索引失败 {index_name}: {e}")
            
            conn.commit()
            logger.info("✅ 优化索引创建完成")
            
    except Exception as e:
        logger.error(f"❌ 创建优化索引失败: {e}")

def verify_tables():
    """验证表创建结果"""
    try:
        logger.info("🔍 开始验证表创建结果...")
        
        with engine.connect() as conn:
            # 获取所有表
            result = conn.execute(text("""
                SELECT TABLE_NAME, TABLE_ROWS, CREATE_TIME
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = DATABASE()
                ORDER BY TABLE_NAME
            """))
            
            tables = result.fetchall()
            
            if not tables:
                logger.warning("⚠️  未找到任何表")
                return False
            
            logger.info("📊 数据库表列表:")
            for table_name, row_count, create_time in tables:
                table_name_str = table_name or "unknown"
                row_count_str = str(row_count) if row_count is not None else "0"
                create_time_str = str(create_time) if create_time else "unknown"
                logger.info(f"   📋 {table_name_str:25} | {row_count_str:6} 行 | 创建于: {create_time_str}")
                
            logger.info(f"✅ 总共创建了 {len(tables)} 张表")
            
            # 检查关键表是否存在
            expected_tables = [
                'users', 'user_profiles', 'user_cards', 'topic_cards',
                'vote_cards', 'chat_messages', 'chat_summaries', 'user_profile_history',
                'user_profile_feedback', 'user_profile_scores', 'user_profile_score_history',
                'user_profile_skills', 'llm_usage_logs', 'membership_orders',
                'content_moderations'
            ]
            
            existing_tables = [table[0] for table in tables]
            missing_tables = set(expected_tables) - set(existing_tables)
            
            if missing_tables:
                logger.warning(f"⚠️  缺失的表: {missing_tables}")
                # 不返回False，只作为警告
                return True
            else:
                logger.info("✅ 所有预期表都已成功创建")
                
            return True
            
    except Exception as e:
        logger.error(f"❌ 验证表创建结果失败: {e}")
        return False

def main():
    """主函数"""
    logger.info("🚀 开始数据库表结构初始化...")
    logger.info(f"📍 目标数据库: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}")
    logger.info(f"👤 数据库用户: {settings.MYSQL_USERNAME}")
    
    # 步骤1: 创建数据库（如果不存在）
    logger.info("\n📦 步骤1: 创建数据库...")
    if not create_database():
        logger.error("❌ 数据库创建失败，终止初始化")
        return False
    
    # 步骤2: 创建所有表
    logger.info("\n🏗️  步骤2: 创建数据库表...")
    if not init_all_tables():
        logger.error("❌ 表结构创建失败，终止初始化")
        return False
    
    # 步骤3: 创建优化索引
    logger.info("\n⚡ 步骤3: 创建性能优化索引...")
    create_optimization_indexes()
    
    # 步骤4: 验证创建结果
    logger.info("\n✅ 步骤4: 验证创建结果...")
    success = verify_tables()
    
    if success:
        logger.info("\n🎉 数据库表结构初始化完成！")
        logger.info("💡 提示：现在可以开始使用数据库了")
    else:
        logger.error("\n❌ 数据库初始化过程中出现问题，请检查日志")
        
    return success

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n🛑 用户中断初始化")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n💥 初始化过程发生未预期错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)