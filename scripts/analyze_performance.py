"""
数据库查询性能分析工具
用于分析和监控数据库查询性能，识别慢查询和优化机会
"""

import logging
import time
from datetime import datetime, timedelta
from sqlalchemy import text, create_engine
from sqlalchemy.orm import Session
from app.config import settings
from typing import Dict, List, Any, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabasePerformanceAnalyzer:
    """数据库性能分析器"""
    
    def __init__(self):
        self.engine = create_engine(settings.computed_database_url)
    
    def analyze_slow_queries(self, min_execution_time: float = 0.1) -> List[Dict[str, Any]]:
        """
        分析慢查询（需要MySQL慢查询日志支持）
        
        Args:
            min_execution_time: 最小执行时间（秒）
            
        Returns:
            慢查询列表
        """
        try:
            with self.engine.connect() as conn:
                # 检查是否启用慢查询日志
                result = conn.execute(text("SHOW VARIABLES LIKE 'slow_query_log%'"))
                slow_log_settings = dict(result.fetchall())
                
                logger.info("慢查询日志设置:")
                for key, value in slow_log_settings.items():
                    logger.info(f"  {key}: {value}")
                
                # 获取最近的慢查询
                result = conn.execute(text("""
                    SELECT 
                        start_time,
                        query_time,
                        lock_time,
                        rows_sent,
                        rows_examined,
                        sql_text
                    FROM mysql.slow_log 
                    WHERE start_time >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                    AND query_time >= :min_time
                    ORDER BY query_time DESC
                    LIMIT 20
                """), {"min_time": timedelta(seconds=min_execution_time)})
                
                slow_queries = []
                for row in result.fetchall():
                    slow_queries.append({
                        'start_time': row[0],
                        'query_time': float(row[1].total_seconds()) if hasattr(row[1], 'total_seconds') else float(row[1]),
                        'lock_time': float(row[2].total_seconds()) if hasattr(row[2], 'total_seconds') else float(row[2]),
                        'rows_sent': row[3],
                        'rows_examined': row[4],
                        'sql_text': row[5][:500]  # 限制长度
                    })
                
                return slow_queries
                
        except Exception as e:
            logger.error(f"慢查询分析失败: {str(e)}")
            return []
    
    def analyze_table_sizes(self) -> List[Dict[str, Any]]:
        """
        分析表大小和记录数
        
        Returns:
            表信息列表
        """
        try:
            with self.engine.connect() as conn:
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
                
                tables = []
                for row in result.fetchall():
                    tables.append({
                        'table_name': row[0],
                        'table_rows': row[1],
                        'data_length': row[2],
                        'index_length': row[3],
                        'total_size': row[4],
                        'data_mb': row[5],
                        'index_mb': row[6],
                        'total_mb': row[7]
                    })
                
                return tables
                
        except Exception as e:
            logger.error(f"表大小分析失败: {str(e)}")
            return []
    
    def analyze_index_usage(self) -> List[Dict[str, Any]]:
        """
        分析索引使用情况
        
        Returns:
            索引使用信息列表
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT 
                        table_name,
                        index_name,
                        cardinality,
                        sub_part,
                        packed,
                        nullable,
                        index_type,
                        comment
                    FROM information_schema.statistics 
                    WHERE table_schema = DATABASE()
                    ORDER BY table_name, index_name
                """))
                
                indexes = {}
                for row in result.fetchall():
                    table_name = row[0]
                    index_name = row[1]
                    
                    if table_name not in indexes:
                        indexes[table_name] = []
                    
                    indexes[table_name].append({
                        'index_name': index_name,
                        'cardinality': row[2],
                        'sub_part': row[3],
                        'packed': row[4],
                        'nullable': row[5],
                        'index_type': row[6],
                        'comment': row[7]
                    })
                
                # 分析索引效率
                index_analysis = []
                for table_name, table_indexes in indexes.items():
                    for index in table_indexes:
                        # 获取表的总行数
                        result = conn.execute(text(f"""
                            SELECT table_rows 
                            FROM information_schema.tables 
                            WHERE table_schema = DATABASE() 
                            AND table_name = '{table_name}'
                        """))
                        table_rows = result.scalar() or 0
                        
                        # 计算索引选择性
                        cardinality = index['cardinality'] or 0
                        selectivity = (cardinality / table_rows * 100) if table_rows > 0 else 0
                        
                        index_analysis.append({
                            'table_name': table_name,
                            'index_name': index['index_name'],
                            'cardinality': cardinality,
                            'table_rows': table_rows,
                            'selectivity': round(selectivity, 2),
                            'efficiency': 'HIGH' if selectivity > 80 else 'MEDIUM' if selectivity > 30 else 'LOW'
                        })
                
                return index_analysis
                
        except Exception as e:
            logger.error(f"索引使用分析失败: {str(e)}")
            return []
    
    def analyze_query_patterns(self) -> Dict[str, Any]:
        """
        分析常见查询模式
        
        Returns:
            查询模式分析结果
        """
        try:
            with self.engine.connect() as conn:
                # 分析表访问频率（如果启用了性能模式）
                result = conn.execute(text("""
                    SELECT 
                        object_schema,
                        object_name,
                        count_read,
                        count_write,
                        count_fetch,
                        count_insert,
                        count_update,
                        count_delete
                    FROM performance_schema.table_io_waits_summary_by_table 
                    WHERE object_schema = DATABASE()
                    ORDER BY count_read + count_write DESC
                    LIMIT 20
                """))
                
                table_io_stats = []
                for row in result.fetchall():
                    table_io_stats.append({
                        'schema': row[0],
                        'table': row[1],
                        'reads': row[2],
                        'writes': row[3],
                        'fetches': row[4],
                        'inserts': row[5],
                        'updates': row[6],
                        'deletes': row[7]
                    })
                
                return {
                    'table_io_stats': table_io_stats,
                    'analysis_time': datetime.now()
                }
                
        except Exception as e:
            logger.error(f"查询模式分析失败: {str(e)}")
            return {'table_io_stats': [], 'analysis_time': datetime.now()}
    
    def benchmark_common_queries(self) -> List[Dict[str, Any]]:
        """
        基准测试常见查询
        
        Returns:
            查询性能基准测试结果
        """
        # 常见查询模式
        test_queries = [
            {
                'name': '用户手机号查询',
                'sql': "SELECT * FROM users WHERE phone = :param LIMIT 1",
                'params': {'param': '13800138000'}
            },
            {
                'name': '用户卡片组合查询',
                'sql': """
                    SELECT * FROM user_cards 
                    WHERE user_id = :user_id 
                    AND scene_type = :scene_type 
                    AND role_type = :role_type 
                    AND is_deleted = 0 
                    AND is_active = 1
                """,
                'params': {
                    'user_id': 'test_user_123',
                    'scene_type': 'housing',
                    'role_type': 'housing_seeker'
                }
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
                'params': {}
            },
            {
                'name': '用户连接查询',
                'sql': """
                    SELECT * FROM user_connections 
                    WHERE from_user_id = :user_id 
                    AND status = 'ACCEPTED'
                    ORDER BY created_at DESC
                """,
                'params': {'user_id': 'test_user_123'}
            },
            {
                'name': '聊天消息查询',
                'sql': """
                    SELECT * FROM chat_messages 
                    WHERE user_id = :user_id 
                    AND created_at >= :start_time
                    ORDER BY created_at DESC
                    LIMIT 50
                """,
                'params': {
                    'user_id': 'test_user_123',
                    'start_time': datetime.now() - timedelta(hours=24)
                }
            }
        ]
        
        benchmark_results = []
        
        try:
            with self.engine.connect() as conn:
                for query_info in test_queries:
                    try:
                        # 预热查询计划缓存
                        conn.execute(text(query_info['sql']), query_info['params'])
                        
                        # 执行多次取平均值
                        execution_times = []
                        for _ in range(5):
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
                        
                    except Exception as e:
                        logger.error(f"查询基准测试失败 - {query_info['name']}: {str(e)}")
                        benchmark_results.append({
                            'query_name': query_info['name'],
                            'error': str(e)
                        })
                
                return benchmark_results
                
        except Exception as e:
            logger.error(f"基准测试执行失败: {str(e)}")
            return []
    
    def generate_performance_report(self) -> str:
        """
        生成性能分析报告
        
        Returns:
            性能分析报告
        """
        logger.info("开始生成数据库性能分析报告...")
        
        # 收集各项分析数据
        slow_queries = self.analyze_slow_queries()
        table_sizes = self.analyze_table_sizes()
        index_usage = self.analyze_index_usage()
        query_patterns = self.analyze_query_patterns()
        benchmarks = self.benchmark_common_queries()
        
        # 生成报告
        report = []
        report.append("=" * 60)
        report.append("数据库性能分析报告")
        report.append("=" * 60)
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 表大小分析
        report.append("📊 表大小分析")
        report.append("-" * 30)
        total_size_mb = sum(table['total_mb'] for table in table_sizes if table['total_mb'] is not None)
        report.append(f"总数据库大小: {total_size_mb:.2f} MB")
        report.append("")
        
        for table in table_sizes[:10]:  # 显示前10个大表
            if table['table_rows'] is not None and table['data_mb'] is not None and table['index_mb'] is not None:
                report.append(f"表: {table['table_name']}")
                report.append(f"  行数: {table['table_rows']:,}")
                report.append(f"  数据大小: {table['data_mb']:.2f} MB")
                report.append(f"  索引大小: {table['index_mb']:.2f} MB")
                report.append(f"  总大小: {table['total_mb']:.2f} MB")
                report.append("")
        
        # 索引使用分析
        report.append("🔍 索引使用分析")
        report.append("-" * 30)
        
        high_efficiency = [idx for idx in index_usage if idx['efficiency'] == 'HIGH']
        low_efficiency = [idx for idx in index_usage if idx['efficiency'] == 'LOW']
        
        report.append(f"高效索引数量: {len(high_efficiency)}")
        report.append(f"低效索引数量: {len(low_efficiency)}")
        report.append("")
        
        if low_efficiency:
            report.append("低效索引列表:")
            for idx in low_efficiency[:5]:  # 显示前5个低效索引
                report.append(f"  表: {idx['table_name']}, 索引: {idx['index_name']}")
                report.append(f"  选择性: {idx['selectivity']:.2f}%")
                report.append("")
        
        # 查询基准测试
        report.append("⚡ 查询性能基准测试")
        report.append("-" * 30)
        
        for benchmark in benchmarks:
            if 'error' not in benchmark:
                report.append(f"查询: {benchmark['query_name']}")
                report.append(f"  平均时间: {benchmark['avg_time']:.4f} 秒")
                report.append(f"  最短时间: {benchmark['min_time']:.4f} 秒")
                report.append(f"  最长时间: {benchmark['max_time']:.4f} 秒")
                report.append("")
            else:
                report.append(f"查询: {benchmark['query_name']} - 错误: {benchmark['error']}")
                report.append("")
        
        # 慢查询分析
        if slow_queries:
            report.append("🐌 慢查询分析（最近24小时）")
            report.append("-" * 30)
            report.append(f"发现 {len(slow_queries)} 个慢查询")
            report.append("")
            
            for query in slow_queries[:5]:  # 显示前5个慢查询
                report.append(f"执行时间: {query['query_time']:.4f} 秒")
                report.append(f"锁定时间: {query['lock_time']:.4f} 秒")
                report.append(f"扫描行数: {query['rows_examined']:,}")
                report.append(f"返回行数: {query['rows_sent']:,}")
                report.append(f"SQL: {query['sql_text'][:200]}...")
                report.append("")
        
        # 性能优化建议
        report.append("💡 性能优化建议")
        report.append("-" * 30)
        
        recommendations = []
        
        # 基于低效索引的建议
        if low_efficiency:
            recommendations.append("• 考虑重建或删除低效索引，特别是选择性低于30%的索引")
        
        # 基于表大小的建议
        large_tables = [t for t in table_sizes if t['total_mb'] > 100]
        if large_tables:
            recommendations.append("• 对大表考虑分区或归档历史数据")
        
        # 基于慢查询的建议
        if slow_queries:
            recommendations.append("• 优化慢查询，考虑添加合适的复合索引")
            recommendations.append("• 检查查询语句是否存在全表扫描")
        
        # 通用建议
        recommendations.extend([
            "• 定期更新表统计信息（ANALYZE TABLE）",
            "• 监控索引碎片率，必要时重建索引",
            "• 考虑为频繁查询的列组合创建复合索引",
            "• 定期清理不再需要的历史数据"
        ])
        
        for rec in recommendations:
            report.append(rec)
        
        report.append("")
        report.append("=" * 60)
        report.append("报告生成完成")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def close(self):
        """关闭数据库连接"""
        if self.engine:
            self.engine.dispose()

def main():
    """主函数"""
    analyzer = DatabasePerformanceAnalyzer()
    
    try:
        # 生成性能报告
        report = analyzer.generate_performance_report()
        
        # 保存报告到文件
        report_file = f"database_performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"性能分析报告已保存到: {report_file}")
        print("\n" + report)
        
    except Exception as e:
        logger.error(f"性能分析执行失败: {str(e)}")
    
    finally:
        analyzer.close()

if __name__ == "__main__":
    main()