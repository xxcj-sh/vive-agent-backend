"""
数据库性能优化 - 添加关键索引 (修复版)
基于查询分析为高频查询场景添加复合索引
"""

import logging
from sqlalchemy import text, create_engine
from sqlalchemy.orm import Session
import os
import sys

# 添加项目根目录到Python路径
sys.path.append('/Users/liukun/Documents/workspace/codebase/VMatch/vive-agent-backend')

from app.config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def drop_index_if_exists(conn, index_name, table_name):
    """安全地删除索引（如果存在）"""
    try:
        # 先检查索引是否存在
        result = conn.execute(text(f"""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.STATISTICS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = '{table_name}' 
            AND INDEX_NAME = '{index_name}'
        """))
        
        exists = result.scalar() > 0
        
        if exists:
            conn.execute(text(f"DROP INDEX {index_name} ON {table_name}"))
            logger.info(f"✓ 已删除现有索引: {index_name} ON {table_name}")
            return True
        else:
            logger.info(f"ℹ 索引不存在，跳过删除: {index_name} ON {table_name}")
            return False
            
    except Exception as e:
        logger.warning(f"⚠ 删除索引失败 {index_name} ON {table_name}: {str(e)}")
        return False

def create_performance_indexes():
    """创建性能优化索引"""
    
    # 获取数据库连接
    engine = create_engine(settings.computed_database_url)
    
    # 索引创建配置 - 使用单独的DROP和CREATE操作
    index_configs = [
        # 1. 用户表索引优化
        {
            "name": "用户微信openid查询优化",
            "table": "users",
            "index_name": "idx_users_wechat_openid",
            "columns": ["wechat_open_id"]
        },
        
        {
            "name": "用户状态和时间查询优化", 
            "table": "users",
            "index_name": "idx_users_status_created",
            "columns": ["status", "created_at"]
        },
        
        # 2. 用户卡片表索引优化
        {
            "name": "用户卡片组合查询优化（最频繁查询）",
            "table": "user_cards",
            "index_name": "idx_user_cards_user_scene_role",
            "columns": ["user_id", "scene_type", "role_type", "is_deleted", "is_active"]
        },
        
        {
            "name": "用户卡片公开列表查询优化",
            "table": "user_cards",
            "index_name": "idx_user_cards_public_list",
            "columns": ["is_public", "is_active", "is_deleted", "created_at"]
        },
        
        {
            "name": "用户卡片场景类型查询优化",
            "table": "user_cards",
            "index_name": "idx_user_cards_scene_type",
            "columns": ["scene_type", "is_active", "is_deleted"]
        },
        
        {
            "name": "用户卡片搜索码查询优化",
            "table": "user_cards",
            "index_name": "idx_user_cards_search_code",
            "columns": ["search_code"]
        },
        
        # 3. 话题卡片表索引优化
        {
            "name": "话题卡片创建者查询优化",
            "table": "topic_cards",
            "index_name": "idx_topic_cards_creator_status",
            "columns": ["creator_id", "status", "is_deleted", "created_at"]
        },
        
        {
            "name": "话题卡片状态查询优化",
            "table": "topic_cards",
            "index_name": "idx_topic_cards_status_time",
            "columns": ["status", "is_deleted", "created_at"]
        },
        
        {
            "name": "话题卡片搜索码查询优化",
            "table": "topic_cards",
            "index_name": "idx_topic_cards_search_code",
            "columns": ["search_code"]
        },
        
        # 4. 投票卡片表索引优化
        {
            "name": "投票卡片创建者查询优化",
            "table": "vote_cards",
            "index_name": "idx_vote_cards_creator_status",
            "columns": ["creator_id", "status", "is_deleted", "created_at"]
        },
        
        {
            "name": "投票卡片状态查询优化",
            "table": "vote_cards",
            "index_name": "idx_vote_cards_status_time",
            "columns": ["status", "is_deleted", "created_at"]
        },
        
        {
            "name": "投票卡片搜索码查询优化",
            "table": "vote_cards",
            "index_name": "idx_vote_cards_search_code",
            "columns": ["search_code"]
        },
        
        # 5. 匹配记录表索引优化
        {
            "name": "用户匹配记录查询优化",
            "table": "matches",
            "index_name": "idx_matches_user_status",
            "columns": ["user_id", "status", "created_at"]
        },
        
        {
            "name": "匹配目标用户查询优化",
            "table": "matches",
            "index_name": "idx_matches_target_user",
            "columns": ["target_user_id", "status", "created_at"]
        },
        
        {
            "name": "匹配状态查询优化",
            "table": "matches",
            "index_name": "idx_matches_status_time",
            "columns": ["status", "created_at"]
        },
        
        # 6. 用户连接关系表索引优化
        {
            "name": "用户连接关系查询优化",
            "table": "user_connections",
            "index_name": "idx_user_connections_users",
            "columns": ["user_id", "target_user_id", "connection_type", "status"]
        },
        
        {
            "name": "目标用户连接查询优化",
            "table": "user_connections",
            "index_name": "idx_user_connections_target",
            "columns": ["target_user_id", "connection_type", "status"]
        },
        
        {
            "name": "连接状态查询优化",
            "table": "user_connections",
            "index_name": "idx_user_connections_status",
            "columns": ["status", "connection_type", "created_at"]
        },
        
        # 7. 聊天消息表索引优化
        {
            "name": "卡片消息查询优化",
            "table": "chat_messages",
            "index_name": "idx_chat_messages_card_time",
            "columns": ["card_id", "created_at"]
        },
        
        {
            "name": "会话消息查询优化",
            "table": "chat_messages",
            "index_name": "idx_chat_messages_session_time",
            "columns": ["session_id", "created_at"]
        },
        
        {
            "name": "消息类型查询优化",
            "table": "chat_messages",
            "index_name": "idx_chat_messages_type_sender",
            "columns": ["message_type", "sender_type", "created_at"]
        },
        
        # 8. 话题讨论表索引优化
        {
            "name": "话题讨论查询优化",
            "table": "topic_discussions",
            "index_name": "idx_topic_discussions_card_time",
            "columns": ["topic_card_id", "created_at"]
        },
        
        {
            "name": "用户讨论查询优化",
            "table": "topic_discussions",
            "index_name": "idx_topic_discussions_participant_time",
            "columns": ["participant_id", "created_at"]
        },
        
        {
            "name": "主持人讨论查询优化",
            "table": "topic_discussions",
            "index_name": "idx_topic_discussions_host_time",
            "columns": ["host_id", "created_at"]
        },
        
        # 9. 投票记录表索引优化
        {
            "name": "投票记录用户查询优化",
            "table": "vote_records",
            "index_name": "idx_vote_records_user_vote",
            "columns": ["user_id", "vote_card_id", "created_at"]
        },
        
        {
            "name": "投票记录投票卡片查询优化",
            "table": "vote_records",
            "index_name": "idx_vote_records_vote_time",
            "columns": ["vote_card_id", "created_at"]
        },
        
        {
            "name": "投票记录选项查询优化",
            "table": "vote_records",
            "index_name": "idx_vote_records_option_time",
            "columns": ["vote_option_id", "created_at"]
        },
        
        # 10. 话题观点总结表索引优化
        {
            "name": "用户观点总结查询优化",
            "table": "topic_opinion_summaries",
            "index_name": "idx_opinion_summaries_user_topic",
            "columns": ["user_id", "topic_card_id", "is_deleted"]
        },
        
        {
            "name": "话题观点总结查询优化",
            "table": "topic_opinion_summaries",
            "index_name": "idx_opinion_summaries_topic_time",
            "columns": ["topic_card_id", "created_at"]
        },
        
        # 11. 用户卡片话题关联表索引优化
        {
            "name": "用户卡片话题关联查询优化",
            "table": "user_card_topic_relations",
            "index_name": "idx_user_card_topic_relations_card",
            "columns": ["user_card_id", "topic_card_id", "is_deleted"]
        },
        
        {
            "name": "话题用户卡片关联查询优化",
            "table": "user_card_topic_relations",
            "index_name": "idx_user_card_topic_relations_topic",
            "columns": ["topic_card_id", "relation_type", "is_deleted"]
        },
        
        # 12. 用户卡片投票关联表索引优化
        {
            "name": "用户卡片投票关联查询优化",
            "table": "user_card_vote_relations",
            "index_name": "idx_user_card_vote_relations_card",
            "columns": ["user_card_id", "vote_card_id", "is_deleted"]
        },
        
        {
            "name": "投票用户卡片关联查询优化",
            "table": "user_card_vote_relations",
            "index_name": "idx_user_card_vote_relations_vote",
            "columns": ["vote_card_id", "relation_type", "is_deleted"]
        }
    ]
    
    # 执行索引创建
    with engine.connect() as conn:
        try:
            logger.info("开始创建性能优化索引...")
            
            success_count = 0
            skip_count = 0
            error_count = 0
            
            for i, config in enumerate(index_configs, 1):
                logger.info(f"处理索引 {i}/{len(index_configs)}: {config['name']}")
                
                try:
                    # 第一步：检查并删除现有索引
                    dropped = drop_index_if_exists(conn, config['index_name'], config['table'])
                    
                    # 第二步：创建新索引
                    columns_str = ', '.join(config['columns'])
                    create_sql = f"CREATE INDEX {config['index_name']} ON {config['table']}({columns_str})"
                    
                    conn.execute(text(create_sql))
                    logger.info(f"✅ 成功创建索引: {config['index_name']} ON {config['table']}")
                    success_count += 1
                    
                    # 每创建几个索引后提交一次，避免长事务
                    if i % 5 == 0:
                        conn.commit()
                        logger.info(f"已提交 {i} 个索引处理")
                        
                except Exception as e:
                    error_msg = str(e)
                    if "Duplicate key name" in error_msg or "already exists" in error_msg:
                        logger.info(f"⚠ 索引已存在，跳过: {config['index_name']}")
                        skip_count += 1
                    else:
                        logger.error(f"❌ 创建失败 - {config['name']}: {error_msg}")
                        error_count += 1
                    # 不中断整个过程，继续创建其他索引
            
            # 最终提交
            conn.commit()
            logger.info("=" * 60)
            logger.info("✅ 性能优化索引处理完成！")
            logger.info(f"📊 统计结果:")
            logger.info(f"  成功创建: {success_count} 个")
            logger.info(f"  已存在跳过: {skip_count} 个")
            logger.info(f"  创建失败: {error_count} 个")
            logger.info(f"  总计处理: {success_count + skip_count + error_count} 个")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"索引创建过程失败: {str(e)}")
            raise e
        
        finally:
            conn.close()
    
    engine.dispose()
    logger.info("数据库连接已关闭")

def analyze_table_indexes():
    """分析现有表的索引情况"""
    
    engine = create_engine(settings.computed_database_url)
    
    # 需要分析的表
    tables = [
        'users', 'user_cards', 'topic_cards', 'vote_cards', 
        'matches', 'user_connections', 'chat_messages',
        'topic_discussions', 'vote_records', 'topic_opinion_summaries',
        'user_card_topic_relations', 'user_card_vote_relations'
    ]
    
    with engine.connect() as conn:
        try:
            logger.info("开始分析现有索引情况...")
            
            for table in tables:
                try:
                    # 检查表是否存在
                    result = conn.execute(text(f"SHOW TABLES LIKE '{table}'"))
                    if not result.fetchone():
                        logger.warning(f"⚠️ 表 {table} 不存在，跳过")
                        continue
                    
                    # 获取表的索引信息
                    result = conn.execute(text(f"""
                        SELECT 
                            INDEX_NAME,
                            COLUMN_NAME,
                            NON_UNIQUE,
                            SEQ_IN_INDEX,
                            COLLATION,
                            CARDINALITY,
                            SUB_PART
                        FROM INFORMATION_SCHEMA.STATISTICS 
                        WHERE TABLE_SCHEMA = DATABASE() 
                        AND TABLE_NAME = '{table}'
                        ORDER BY INDEX_NAME, SEQ_IN_INDEX
                    """))
                    
                    indexes = result.fetchall()
                    
                    if indexes:
                        logger.info(f"\n📊 表 {table} 的索引:")
                        current_index = ""
                        for idx in indexes:
                            if idx[0] != current_index:
                                current_index = idx[0]
                                logger.info(f"  📌 索引: {idx[0]} (唯一: {'否' if idx[2] else '是'})")
                            logger.info(f"     列: {idx[1]} (位置: {idx[3]})")
                    else:
                        logger.info(f"⚠️ 表 {table} 暂无索引")
                        
                except Exception as e:
                    logger.error(f"分析表 {table} 失败: {str(e)}")
            
            logger.info("\n✅ 索引分析完成！")
            
        except Exception as e:
            logger.error(f"索引分析失败: {str(e)}")
            raise e
        
        finally:
            conn.close()
    
    engine.dispose()

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("数据库性能优化 - 索引创建工具")
    logger.info("=" * 60)
    
    try:
        # 1. 创建性能优化索引
        create_performance_indexes()
        
        logger.info("\n" + "=" * 60)
        
        # 2. 分析现有索引情况
        analyze_table_indexes()
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 所有任务执行完成！")
        
    except Exception as e:
        logger.error(f"❌ 执行失败: {str(e)}")
        sys.exit(1)