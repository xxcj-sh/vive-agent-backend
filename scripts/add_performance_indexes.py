"""
数据库性能优化 - 添加关键索引
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

def create_performance_indexes():
    """创建性能优化索引"""
    
    # 获取数据库连接
    engine = create_engine(settings.computed_database_url)
    
    # 索引创建SQL语句 - 使用正确的MySQL语法
    index_sqls = [
        # 1. 用户表索引优化
        {
            "name": "用户微信openid查询优化",
            "sql": """
                DROP INDEX IF EXISTS idx_users_wechat_openid ON users;
                CREATE INDEX idx_users_wechat_openid ON users(wechat_open_id);
            """
        },
        
        {
            "name": "用户状态和时间查询优化", 
            "sql": """
                DROP INDEX IF EXISTS idx_users_status_created ON users;
                CREATE INDEX idx_users_status_created ON users(status, created_at);
            """
        },
        
        # 2. 用户卡片表索引优化
        {
            "name": "用户卡片组合查询优化（最频繁查询）",
            "sql": """
                DROP INDEX IF EXISTS idx_user_cards_user_scene_role ON user_cards;
                CREATE INDEX idx_user_cards_user_scene_role ON user_cards(user_id, scene_type, role_type, is_deleted, is_active);
            """
        },
        
        {
            "name": "公开卡片列表查询优化",
            "sql": """
                DROP INDEX IF EXISTS idx_user_cards_public_list ON user_cards;
                CREATE INDEX idx_user_cards_public_list ON user_cards(visibility, is_deleted, is_active, created_at);
            """
        },
        
        {
            "name": "场景类型查询优化",
            "sql": """
                DROP INDEX IF EXISTS idx_user_cards_scene_type ON user_cards;
                CREATE INDEX idx_user_cards_scene_type ON user_cards(scene_type, is_deleted, is_active);
            """
        },
        
        {
            "name": "搜索码查询优化",
            "sql": """
                DROP INDEX IF EXISTS idx_user_cards_search_code ON user_cards;
                CREATE INDEX idx_user_cards_search_code ON user_cards(search_code, is_deleted, is_active);
            """
        },
        
        # 3. 话题卡片表索引优化
        {
            "name": "话题卡片创建者查询优化",
            "sql": """
                DROP INDEX IF EXISTS idx_topic_cards_user_status ON topic_cards;
                CREATE INDEX idx_topic_cards_user_status ON topic_cards(user_id, is_deleted, is_active, created_at);
            """
        },
        
        {
            "name": "话题分类查询优化",
            "sql": """
                DROP INDEX IF EXISTS idx_topic_cards_category ON topic_cards;
                CREATE INDEX idx_topic_cards_category ON topic_cards(category, is_deleted, is_active, created_at);
            """
        },
        
        {
            "name": "话题可见性查询优化",
            "sql": """
                DROP INDEX IF EXISTS idx_topic_cards_visibility ON topic_cards;
                CREATE INDEX idx_topic_cards_visibility ON topic_cards(visibility, is_deleted, is_active, created_at);
            """
        },
        
        {
            "name": "话题活跃度查询优化（点赞、讨论、浏览）",
            "sql": """
                DROP INDEX IF EXISTS idx_topic_cards_popularity ON topic_cards;
                CREATE INDEX idx_topic_cards_popularity ON topic_cards(like_count, discussion_count, view_count);
            """
        },
        
        # 4. 投票卡片表索引优化
        {
            "name": "投票卡片创建者查询优化",
            "sql": """
                DROP INDEX IF EXISTS idx_vote_cards_user_status ON vote_cards;
                CREATE INDEX idx_vote_cards_user_status ON vote_cards(user_id, is_deleted, is_active, created_at);
            """
        },
        
        {
            "name": "投票分类查询优化",
            "sql": """
                DROP INDEX IF EXISTS idx_vote_cards_category ON vote_cards;
                CREATE INDEX idx_vote_cards_category ON vote_cards(category, is_deleted, is_active, created_at);
            """
        },
        
        {
            "name": "投票状态查询优化（实时结果、匿名等）",
            "sql": """
                DROP INDEX IF EXISTS idx_vote_cards_features ON vote_cards;
                CREATE INDEX idx_vote_cards_features ON vote_cards(is_realtime_result, is_anonymous, is_deleted, is_active);
            """
        },
        
        # 5. 匹配表索引优化
        {
            "name": "用户匹配记录查询优化",
            "sql": """
                DROP INDEX IF EXISTS idx_matches_user_type_status ON matches;
                CREATE INDEX idx_matches_user_type_status ON matches(user_id, match_type, status, is_active, created_at);
            """
        },
        
        {
            "name": "匹配类型和状态查询优化",
            "sql": """
                DROP INDEX IF EXISTS idx_matches_type_status ON matches;
                CREATE INDEX idx_matches_type_status ON matches(match_type, status, is_active, created_at);
            """
        },
        
        {
            "name": "匹配分数查询优化",
            "sql": """
                DROP INDEX IF EXISTS idx_matches_score ON matches;
                CREATE INDEX idx_matches_score ON matches(score, match_type, status);
            """
        },
        
        # 6. 用户连接表索引优化
        {
            "name": "用户关系双向查询优化",
            "sql": """
                DROP INDEX IF EXISTS idx_user_connections_from_user ON user_connections;
                CREATE INDEX idx_user_connections_from_user ON user_connections(from_user_id, status, connection_type, created_at);
            """
        },
        
        {
            "name": "用户关系反向查询优化",
            "sql": """
                DROP INDEX IF EXISTS idx_user_connections_to_user ON user_connections;
                CREATE INDEX idx_user_connections_to_user ON user_connections(to_user_id, status, connection_type, created_at);
            """
        },
        
        {
            "name": "用户关系组合查询优化（防止重复关系）",
            "sql": """
                DROP INDEX IF EXISTS idx_user_connections_unique ON user_connections;
                CREATE INDEX idx_user_connections_unique ON user_connections(from_user_id, to_user_id, connection_type);
            """
        },
        
        # 7. 聊天消息表索引优化
        {
            "name": "用户消息查询优化",
            "sql": """
                DROP INDEX IF EXISTS idx_chat_messages_user_time ON chat_messages;
                CREATE INDEX idx_chat_messages_user_time ON chat_messages(user_id, created_at);
            """
        },
        
        {
            "name": "卡片消息查询优化",
            "sql": """
                DROP INDEX IF EXISTS idx_chat_messages_card_time ON chat_messages;
                CREATE INDEX idx_chat_messages_card_time ON chat_messages(card_id, created_at);
            """
        },
        
        {
            "name": "会话消息查询优化",
            "sql": """
                DROP INDEX IF EXISTS idx_chat_messages_session_time ON chat_messages;
                CREATE INDEX idx_chat_messages_session_time ON chat_messages(session_id, created_at);
            """
        },
        
        {
            "name": "消息类型查询优化",
            "sql": """
                DROP INDEX IF EXISTS idx_chat_messages_type_sender ON chat_messages;
                CREATE INDEX idx_chat_messages_type_sender ON chat_messages(message_type, sender_type, created_at);
            """
        },
        
        # 8. 话题讨论表索引优化
        {
            "name": "话题讨论查询优化",
            "sql": """
                DROP INDEX IF EXISTS idx_topic_discussions_card_time ON topic_discussions;
                CREATE INDEX idx_topic_discussions_card_time ON topic_discussions(topic_card_id, created_at);
            """
        },
        
        {
            "name": "用户讨论查询优化",
            "sql": """
                DROP INDEX IF EXISTS idx_topic_discussions_participant_time ON topic_discussions;
                CREATE INDEX idx_topic_discussions_participant_time ON topic_discussions(participant_id, created_at);
            """
        },
        
        {
            "name": "主持人讨论查询优化",
            "sql": """
                DROP INDEX IF EXISTS idx_topic_discussions_host_time ON topic_discussions;
                CREATE INDEX idx_topic_discussions_host_time ON topic_discussions(host_id, created_at);
            """
        },
        
        # 9. 投票记录表索引优化
        {
            "name": "投票记录查询优化（防止重复投票）",
            "sql": """
                DROP INDEX IF EXISTS idx_vote_records_user_vote ON vote_records;
                CREATE INDEX idx_vote_records_user_vote ON vote_records(user_id, vote_card_id, is_deleted);
            """
        },
        
        {
            "name": "投票选项查询优化",
            "sql": """
                DROP INDEX IF EXISTS idx_vote_records_option_time ON vote_records;
                CREATE INDEX idx_vote_records_option_time ON vote_records(option_id, created_at);
            """
        },
        
        {
            "name": "投票卡片统计查询优化",
            "sql": """
                DROP INDEX IF EXISTS idx_vote_records_vote_card_time ON vote_records;
                CREATE INDEX idx_vote_records_vote_card_time ON vote_records(vote_card_id, created_at);
            """
        },
        
        # 10. 观点总结表索引优化
        {
            "name": "用户观点总结查询优化",
            "sql": """
                DROP INDEX IF EXISTS idx_opinion_summaries_user_topic ON topic_opinion_summaries;
                CREATE INDEX idx_opinion_summaries_user_topic ON topic_opinion_summaries(user_id, topic_card_id, is_deleted);
            """
        },
        
        {
            "name": "话题观点总结查询优化",
            "sql": """
                DROP INDEX IF EXISTS idx_opinion_summaries_topic_time ON topic_opinion_summaries;
                CREATE INDEX idx_opinion_summaries_topic_time ON topic_opinion_summaries(topic_card_id, created_at);
            """
        },
        
        # 11. 用户卡片关联表索引优化
        {
            "name": "用户卡片话题关联查询优化",
            "sql": """
                DROP INDEX IF EXISTS idx_user_card_topic_relations_card ON user_card_topic_relations;
                CREATE INDEX idx_user_card_topic_relations_card ON user_card_topic_relations(user_card_id, topic_card_id, is_deleted);
            """
        },
        
        {
            "name": "话题用户卡片关联查询优化",
            "sql": """
                DROP INDEX IF EXISTS idx_user_card_topic_relations_topic ON user_card_topic_relations;
                CREATE INDEX idx_user_card_topic_relations_topic ON user_card_topic_relations(topic_card_id, relation_type, is_deleted);
            """
        },
        
        # 12. 用户卡片投票关联表索引优化
        {
            "name": "用户卡片投票关联查询优化",
            "sql": """
                DROP INDEX IF EXISTS idx_user_card_vote_relations_card ON user_card_vote_relations;
                CREATE INDEX idx_user_card_vote_relations_card ON user_card_vote_relations(user_card_id, vote_card_id, is_deleted);
            """
        },
        
        {
            "name": "投票用户卡片关联查询优化",
            "sql": """
                DROP INDEX IF EXISTS idx_user_card_vote_relations_vote ON user_card_vote_relations;
                CREATE INDEX idx_user_card_vote_relations_vote ON user_card_vote_relations(vote_card_id, relation_type, is_deleted);
            """
        }
    ]
    
    # 执行索引创建
    with engine.connect() as conn:
        try:
            logger.info("开始创建性能优化索引...")
            
            for i, index_info in enumerate(index_sqls, 1):
                logger.info(f"创建索引 {i}/{len(index_sqls)}: {index_info['name']}")
                
                try:
                    # 执行SQL语句
                    conn.execute(text(index_info['sql']))
                    logger.info(f"✓ 成功创建: {index_info['name']}")
                    
                except Exception as e:
                    error_msg = str(e)
                    if "Duplicate key name" in error_msg or "already exists" in error_msg:
                        logger.info(f"⚠ 索引已存在，跳过: {index_info['name']}")
                    else:
                        logger.error(f"✗ 创建失败 - {index_info['name']}: {error_msg}")
                        # 不中断整个过程，继续创建其他索引
                
                # 每创建几个索引后提交一次，避免长事务
                if i % 5 == 0:
                    conn.commit()
                    logger.info(f"已提交 {i} 个索引创建")
            
            # 最终提交
            conn.commit()
            logger.info("✅ 所有性能优化索引创建完成！")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"索引创建失败: {str(e)}")
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

def drop_performance_indexes():
    """删除性能优化索引（回滚用）"""
    
    engine = create_engine(settings.computed_database_url)
    
    # 要删除的索引列表
    indexes_to_drop = [
        'idx_users_wechat_openid',
        'idx_users_status_created',
        'idx_user_cards_user_scene_role',
        'idx_user_cards_public_list',
        'idx_user_cards_scene_type',
        'idx_user_cards_search_code',
        'idx_topic_cards_user_status',
        'idx_topic_cards_category',
        'idx_topic_cards_visibility',
        'idx_topic_cards_popularity',
        'idx_vote_cards_user_status',
        'idx_vote_cards_category',
        'idx_vote_cards_features',
        'idx_matches_user_type_status',
        'idx_matches_type_status',
        'idx_matches_score',
        'idx_user_connections_from_user',
        'idx_user_connections_to_user',
        'idx_user_connections_unique',
        'idx_chat_messages_user_time',
        'idx_chat_messages_card_time',
        'idx_chat_messages_session_time',
        'idx_chat_messages_type_sender',
        'idx_topic_discussions_card_time',
        'idx_topic_discussions_participant_time',
        'idx_topic_discussions_host_time',
        'idx_vote_records_user_vote',
        'idx_vote_records_option_time',
        'idx_vote_records_vote_card_time',
        'idx_opinion_summaries_user_topic',
        'idx_opinion_summaries_topic_time',
        'idx_user_card_topic_relations_card',
        'idx_user_card_topic_relations_topic',
        'idx_user_card_vote_relations_card',
        'idx_user_card_vote_relations_vote'
    ]
    
    tables_with_indexes = {
        'users': ['idx_users_wechat_openid', 'idx_users_status_created'],
        'user_cards': ['idx_user_cards_user_scene_role', 'idx_user_cards_public_list', 'idx_user_cards_scene_type', 'idx_user_cards_search_code'],
        'topic_cards': ['idx_topic_cards_user_status', 'idx_topic_cards_category', 'idx_topic_cards_visibility', 'idx_topic_cards_popularity'],
        'vote_cards': ['idx_vote_cards_user_status', 'idx_vote_cards_category', 'idx_vote_cards_features'],
        'matches': ['idx_matches_user_type_status', 'idx_matches_type_status', 'idx_matches_score'],
        'user_connections': ['idx_user_connections_from_user', 'idx_user_connections_to_user', 'idx_user_connections_unique'],
        'chat_messages': ['idx_chat_messages_user_time', 'idx_chat_messages_card_time', 'idx_chat_messages_session_time', 'idx_chat_messages_type_sender'],
        'topic_discussions': ['idx_topic_discussions_card_time', 'idx_topic_discussions_participant_time', 'idx_topic_discussions_host_time'],
        'vote_records': ['idx_vote_records_user_vote', 'idx_vote_records_option_time', 'idx_vote_records_vote_card_time'],
        'topic_opinion_summaries': ['idx_opinion_summaries_user_topic', 'idx_opinion_summaries_topic_time'],
        'user_card_topic_relations': ['idx_user_card_topic_relations_card', 'idx_user_card_topic_relations_topic'],
        'user_card_vote_relations': ['idx_user_card_vote_relations_card', 'idx_user_card_vote_relations_vote']
    }
    
    with engine.connect() as conn:
        try:
            logger.info("开始删除性能优化索引...")
            
            for table, indexes in tables_with_indexes.items():
                for index_name in indexes:
                    try:
                        conn.execute(text(f"DROP INDEX IF EXISTS {index_name} ON {table}"))
                        logger.info(f"✓ 已删除索引: {index_name} (表: {table})")
                    except Exception as e:
                        if "doesn't exist" in str(e) or "Check that" in str(e):
                            logger.info(f"⚠ 索引不存在，跳过: {index_name}")
                        else:
                            logger.error(f"✗ 删除索引失败 {index_name}: {str(e)}")
            
            conn.commit()
            logger.info("✅ 性能优化索引删除完成！")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"索引删除失败: {str(e)}")
            raise e
        
        finally:
            conn.close()
    
    engine.dispose()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "analyze":
            analyze_table_indexes()
        elif sys.argv[1] == "drop":
            drop_performance_indexes()
        else:
            logger.info("用法: python add_performance_indexes.py [analyze|drop]")
            logger.info("  无参数: 创建性能优化索引")
            logger.info("  analyze: 分析现有索引情况")
            logger.info("  drop: 删除性能优化索引")
    else:
        create_performance_indexes()