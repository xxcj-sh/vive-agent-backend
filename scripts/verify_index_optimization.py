"""
数据库索引优化验证报告
"""

import logging
from datetime import datetime
from sqlalchemy import text, create_engine
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

def generate_index_optimization_report():
    """生成索引优化报告"""
    
    engine = create_engine(settings.computed_database_url)
    
    report = []
    report.append("=" * 80)
    report.append("数据库索引优化验证报告")
    report.append("=" * 80)
    report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    with engine.connect() as conn:
        try:
            # 1. 分析表大小
            report.append("📊 数据库表大小分析")
            report.append("-" * 50)
            
            result = conn.execute(text("""
                SELECT 
                    table_name,
                    table_rows,
                    ROUND(data_length / 1024 / 1024, 2) as data_mb,
                    ROUND(index_length / 1024 / 1024, 2) as index_mb,
                    ROUND((data_length + index_length) / 1024 / 1024, 2) as total_mb
                FROM information_schema.tables 
                WHERE table_schema = DATABASE()
                ORDER BY total_mb DESC
            """))
            
            tables = result.fetchall()
            
            total_size = 0
            total_indexes = 0
            
            for table in tables:
                table_name = table[0]
                rows = table[1] or 0
                data_mb = table[2] or 0
                index_mb = table[3] or 0
                total_mb = table[4] or 0
                
                total_size += total_mb
                total_indexes += index_mb
                
                report.append(f"表: {table_name}")
                report.append(f"  行数: {rows:,}")
                report.append(f"  数据: {data_mb:.2f} MB")
                report.append(f"  索引: {index_mb:.2f} MB")
                report.append(f"  总计: {total_mb:.2f} MB")
                report.append("")
            
            report.append(f"数据库总大小: {total_size:.2f} MB")
            report.append(f"索引总大小: {total_indexes:.2f} MB")
            report.append(f"索引占比: {(total_indexes/total_size*100):.1f}%")
            report.append("")
            
            # 2. 分析索引创建情况
            report.append("🔍 性能优化索引创建情况")
            report.append("-" * 50)
            
            # 我们创建的性能优化索引列表
            performance_indexes = {
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
            
            created_count = 0
            failed_count = 0
            
            for table, expected_indexes in performance_indexes.items():
                try:
                    # 检查表是否存在
                    result = conn.execute(text(f"SHOW TABLES LIKE '{table}'"))
                    if not result.fetchone():
                        report.append(f"⚠️ 表 {table} 不存在，跳过")
                        continue
                    
                    # 获取实际索引
                    result = conn.execute(text(f"""
                        SELECT INDEX_NAME
                        FROM INFORMATION_SCHEMA.STATISTICS 
                        WHERE TABLE_SCHEMA = DATABASE() 
                        AND TABLE_NAME = '{table}'
                    """))
                    
                    actual_indexes = [row[0] for row in result.fetchall()]
                    
                    report.append(f"\n表: {table}")
                    
                    for expected_idx in expected_indexes:
                        if expected_idx in actual_indexes:
                            report.append(f"  ✅ {expected_idx} - 已创建")
                            created_count += 1
                        else:
                            report.append(f"  ❌ {expected_idx} - 未创建")
                            failed_count += 1
                    
                except Exception as e:
                    report.append(f"  ⚠️ 分析表 {table} 失败: {str(e)}")
            
            report.append(f"\n📈 索引创建统计:")
            report.append(f"  成功创建: {created_count} 个")
            report.append(f"  创建失败: {failed_count} 个")
            report.append(f"  成功率: {((created_count/(created_count+failed_count))*100):.1f}%")
            report.append("")
            
            # 3. 分析索引效率
            report.append("⚡ 索引效率分析")
            report.append("-" * 50)
            
            # 获取表行数
            result = conn.execute(text("""
                SELECT 
                    table_name,
                    table_rows
                FROM information_schema.tables 
                WHERE table_schema = DATABASE()
            """))
            
            table_rows = dict(result.fetchall())
            
            # 分析每个表的索引效率
            for table in performance_indexes.keys():
                try:
                    # 获取索引信息
                    result = conn.execute(text(f"""
                        SELECT 
                            INDEX_NAME,
                            COLUMN_NAME,
                            CARDINALITY,
                            NON_UNIQUE
                        FROM INFORMATION_SCHEMA.STATISTICS 
                        WHERE TABLE_SCHEMA = DATABASE() 
                        AND TABLE_NAME = '{table}'
                        AND INDEX_NAME IN ({','.join([f"'{idx}'" for idx in performance_indexes[table]])})
                        ORDER BY INDEX_NAME, SEQ_IN_INDEX
                    """))
                    
                    indexes_info = result.fetchall()
                    
                    if indexes_info:
                        rows = table_rows.get(table, 0)
                        report.append(f"\n表: {table} (行数: {rows:,})")
                        
                        current_index = ""
                        for idx_info in indexes_info:
                            index_name = idx_info[0]
                            column_name = idx_info[1]
                            cardinality = idx_info[2] or 0
                            
                            if index_name != current_index:
                                current_index = index_name
                                selectivity = (cardinality / rows * 100) if rows > 0 else 0
                                efficiency = "高" if selectivity > 80 else "中" if selectivity > 30 else "低"
                                
                                report.append(f"  索引: {index_name}")
                                report.append(f"    列: {column_name}")
                                report.append(f"    基数: {cardinality:,}")
                                report.append(f"    选择性: {selectivity:.2f}%")
                                report.append(f"    效率: {efficiency}")
                                report.append("")
                
                except Exception as e:
                    report.append(f"  ⚠️ 分析索引效率失败 - {table}: {str(e)}")
            
            # 4. 查询性能建议
            report.append("💡 性能优化建议")
            report.append("-" * 50)
            report.append("基于索引分析，提供以下建议：")
            report.append("")
            report.append("1. 索引创建建议:")
            report.append("   - 已成功创建大部分性能优化索引")
            report.append("   - 部分索引创建失败，可能是因为表不存在或语法兼容性问题")
            report.append("   - 建议检查失败原因并手动创建重要索引")
            report.append("")
            report.append("2. 索引维护建议:")
            report.append("   - 定期更新表统计信息: ANALYZE TABLE")
            report.append("   - 监控索引使用情况，删除未使用的索引")
            report.append("   - 对于选择性低的索引，考虑调整列顺序或删除")
            report.append("")
            report.append("3. 查询优化建议:")
            report.append("   - 确保查询语句使用创建的复合索引")
            report.append("   - 避免在索引列上使用函数或表达式")
            report.append("   - 对于大表查询，确保WHERE条件匹配索引前缀")
            report.append("")
            report.append("4. 监控建议:")
            report.append("   - 启用MySQL慢查询日志监控慢查询")
            report.append("   - 定期检查索引碎片率")
            report.append("   - 监控数据库连接数和查询响应时间")
            
        except Exception as e:
            report.append(f"\n❌ 分析失败: {str(e)}")
        
        finally:
            conn.close()
    
    engine.dispose()
    
    # 保存报告到文件
    report_file = f"index_optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))
    
    logger.info(f"\n报告已保存到: {report_file}")
    return '\n'.join(report)

if __name__ == "__main__":
    logger.info("开始生成索引优化验证报告...")
    report = generate_index_optimization_report()
    print("\n" + report)