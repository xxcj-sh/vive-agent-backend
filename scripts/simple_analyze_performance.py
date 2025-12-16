"""
简化版数据库性能分析工具
用于验证索引优化效果
"""

import logging
from datetime import datetime
from sqlalchemy import text, create_engine
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

def analyze_table_sizes():
    """分析表大小和记录数"""
    
    engine = create_engine(settings.computed_database_url)
    
    with engine.connect() as conn:
        try:
            logger.info("开始分析表大小...")
            
            result = conn.execute(text("""
                SELECT 
                    table_name,
                    table_rows,
                    data_length,
                    index_length,
                    data_length + index_length as total_size,
                    ROUND(data_length / 1024 / 1024, 2) as data_mb,
                    ROUND(index_length / 1024 / 1024, 2) as index_mb,
                    ROUND((data_length + index_length) / 1024 / 1024, 2) as total_mb
                FROM information_schema.tables 
                WHERE table_schema = DATABASE()
                ORDER BY total_size DESC
            """))
            
            tables = result.fetchall()
            
            logger.info("\n📊 表大小分析:")
            logger.info("-" * 50)
            
            total_size_mb = 0
            for table in tables:
                table_name = table[0]
                table_rows = table[1] or 0
                data_mb = table[5] or 0
                index_mb = table[6] or 0
                total_mb = table[7] or 0
                total_size_mb += total_mb
                
                logger.info(f"表: {table_name}")
                logger.info(f"  行数: {table_rows:,}")
                logger.info(f"  数据大小: {data_mb:.2f} MB")
                logger.info(f"  索引大小: {index_mb:.2f} MB")
                logger.info(f"  总大小: {total_mb:.2f} MB")
                logger.info("")
            
            logger.info(f"总数据库大小: {total_size_mb:.2f} MB")
            
        except Exception as e:
            logger.error(f"表大小分析失败: {str(e)}")
        
        finally:
            conn.close()
    
    engine.dispose()

def benchmark_common_queries():
    """基准测试常见查询"""
    
    engine = create_engine(settings.computed_database_url)
    
    # 常见查询模式（只测试存在的表）
    test_queries = [
        {
            'name': '用户手机号查询',
            'sql': "SELECT * FROM users WHERE phone = %s LIMIT 1",
            'params': ('13800138000',)
        },
        {
            'name': '用户微信openid查询',
            'sql': "SELECT * FROM users WHERE wechat_open_id = %s LIMIT 1",
            'params': ('test_openid_123',)
        },
        {
            'name': '用户卡片组合查询',
            'sql': """
                SELECT * FROM user_cards 
                WHERE user_id = %s 
                AND scene_type = %s 
                AND role_type = %s 
                AND is_deleted = 0 
                AND is_active = 1
            """,
            'params': ('test_user_123', 'housing', 'housing_seeker')
        },
        {
            'name': '话题列表查询',
            'sql': """
                SELECT tc.*, u.nick_name as creator_nickname 
                FROM topic_cards tc
                JOIN users u ON tc.user_id = u.id
                WHERE tc.is_deleted = 0 AND tc.is_active = 1
                ORDER BY tc.created_at DESC
                LIMIT 10
            """,
            'params': ()
        },
        {
            'name': '用户连接查询',
            'sql': """
                SELECT * FROM user_connections 
                WHERE from_user_id = %s 
                AND status = 'ACCEPTED'
                ORDER BY created_at DESC
            """,
            'params': ('test_user_123',)
        }
    ]
    
    benchmark_results = []
    
    with engine.connect() as conn:
        try:
            logger.info("开始查询基准测试...")
            
            for query_info in test_queries:
                try:
                    # 检查表是否存在
                    table_check = query_info['sql'].split('FROM')[1].split(' ')[1].strip()
                    result = conn.execute(text(f"SHOW TABLES LIKE '{table_check}'"))
                    if not result.fetchone():
                        logger.info(f"⚠️ 表 {table_check} 不存在，跳过查询: {query_info['name']}")
                        continue
                    
                    # 预热查询计划缓存
                    conn.execute(text(query_info['sql']), query_info['params'])
                    
                    # 执行多次取平均值
                    execution_times = []
                    import time
                    for _ in range(3):
                        start_time = time.time()
                        result = conn.execute(text(query_info['sql']), query_info['params'])
                        list(result.fetchall())  # 强制获取所有结果
                        end_time = time.time()
                        execution_times.append(end_time - start_time)
                    
                    avg_time = sum(execution_times) / len(execution_times)
                    min_time = min(execution_times)
                    max_time = max(execution_times)
                    
                    benchmark_results.append({
                        'query_name': query_info['name'],
                        'avg_time': round(avg_time, 4),
                        'min_time': round(min_time, 4),
                        'max_time': round(max_time, 4),
                        'execution_times': [round(t, 4) for t in execution_times]
                    })
                    
                    logger.info(f"✓ {query_info['name']}: 平均 {avg_time:.4f}s, 最小 {min_time:.4f}s, 最大 {max_time:.4f}s")
                    
                except Exception as e:
                    logger.error(f"查询基准测试失败 - {query_info['name']}: {str(e)}")
                    benchmark_results.append({
                        'query_name': query_info['name'],
                        'error': str(e)
                    })
            
            logger.info("\n✅ 查询基准测试完成！")
            
        except Exception as e:
            logger.error(f"基准测试执行失败: {str(e)}")
        
        finally:
            conn.close()
    
    engine.dispose()
    
    return benchmark_results

def analyze_index_efficiency():
    """分析索引效率"""
    
    engine = create_engine(settings.computed_database_url)
    
    with engine.connect() as conn:
        try:
            logger.info("开始分析索引效率...")
            
            # 获取所有表的索引信息
            result = conn.execute(text("""
                SELECT 
                    TABLE_NAME,
                    INDEX_NAME,
                    COLUMN_NAME,
                    NON_UNIQUE,
                    CARDINALITY,
                    SUB_PART
                FROM INFORMATION_SCHEMA.STATISTICS 
                WHERE TABLE_SCHEMA = DATABASE()
                ORDER BY TABLE_NAME, INDEX_NAME, SEQ_IN_INDEX
            """))
            
            indexes = result.fetchall()
            
            # 按表分组索引
            table_indexes = {}
            for idx in indexes:
                table_name = idx[0]
                index_name = idx[1]
                
                if table_name not in table_indexes:
                    table_indexes[table_name] = {}
                
                if index_name not in table_indexes[table_name]:
                    table_indexes[table_name][index_name] = {
                        'columns': [],
                        'cardinality': idx[4],
                        'unique': not idx[3]
                    }
                
                table_indexes[table_name][index_name]['columns'].append(idx[2])
            
            # 获取表行数
            result = conn.execute(text("""
                SELECT 
                    table_name,
                    table_rows
                FROM information_schema.tables 
                WHERE table_schema = DATABASE()
            """))
            
            table_rows = dict(result.fetchall())
            
            logger.info("\n🔍 索引效率分析:")
            logger.info("-" * 50)
            
            for table_name, indexes in table_indexes.items():
                rows = table_rows.get(table_name, 0)
                logger.info(f"\n表: {table_name} (行数: {rows:,})")
                
                for index_name, index_info in indexes.items():
                    cardinality = index_info['cardinality'] or 0
                    selectivity = (cardinality / rows * 100) if rows > 0 else 0
                    
                    logger.info(f"  索引: {index_name}")
                    logger.info(f"    列: {', '.join(index_info['columns'])}")
                    logger.info(f"    基数: {cardinality:,}")
                    logger.info(f"    选择性: {selectivity:.2f}%")
                    logger.info(f"    效率: {'高' if selectivity > 80 else '中' if selectivity > 30 else '低'}")
            
        except Exception as e:
            logger.error(f"索引效率分析失败: {str(e)}")
        
        finally:
            conn.close()
    
    engine.dispose()

def main():
    """主函数"""
    
    logger.info("=" * 60)
    logger.info("数据库性能分析工具")
    logger.info("=" * 60)
    logger.info(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")
    
    try:
        # 1. 分析表大小
        analyze_table_sizes()
        
        # 2. 分析索引情况
        analyze_table_indexes()
        
        # 3. 分析索引效率
        analyze_index_efficiency()
        
        # 4. 基准测试查询性能
        benchmark_common_queries()
        
        logger.info("\n" + "=" * 60)
        logger.info("性能分析完成！")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"性能分析执行失败: {str(e)}")

if __name__ == "__main__":
    main()