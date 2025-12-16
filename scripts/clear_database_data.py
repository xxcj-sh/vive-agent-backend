#!/usr/bin/env python3
"""
清空数据库数据脚本
安全地清空vmatch_dev数据库中的所有表数据，处理外键约束
"""

import os
import sys
import logging
from pathlib import Path

# 将项目根目录添加到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database import Base, engine
from app.config import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_real_tables():
    """获取真实表名（排除视图）"""
    try:
        with engine.connect() as conn:
            # 获取所有真实表
            result = conn.execute(text("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE'"))
            tables = [row[0] for row in result.fetchall()]
            return tables
    except Exception as e:
        logger.error(f"获取真实表名失败: {str(e)}")
        raise

def get_table_names():
    """获取所有表名，按依赖关系排序"""
    try:
        tables = get_real_tables()
        
        # 按依赖关系排序（子表先删除）
        table_order = [
            # 子表（有外键约束的表）
            'topic_trigger_conditions',  # 依赖 topic_cards
            'topic_cards',               # 依赖 users
            'match_actions',             # 依赖 matches 和 users
            'chat_messages',             # 依赖 matches 和 users
            'user_profile_histories',    # 依赖 user_profiles
            'user_profile_feedbacks',    # 依赖 user_profiles
            'user_profile_scores',       # 依赖 user_profiles


            'llm_usage_logs',            # 依赖 users
            'subscribe_messages',        # 依赖 users
            'orders',                    # 依赖 users
            'user_cards',                # 依赖 users
            'user_profiles',             # 依赖 users
            'matches',                   # 依赖 users
            # 主表
            'users'
        ]
        
        # 只返回存在的表，并按正确顺序排列
        ordered_tables = []
        for table in table_order:
            if table in tables:
                ordered_tables.append(table)
        
        # 添加剩余的表
        for table in tables:
            if table not in ordered_tables:
                ordered_tables.append(table)
        
        return ordered_tables
        
    except Exception as e:
        logger.error(f"获取表名失败: {str(e)}")
        raise

def disable_foreign_key_checks():
    """禁用外键检查"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            conn.commit()
            logger.info("已禁用外键检查")
    except Exception as e:
        logger.error(f"禁用外键检查失败: {str(e)}")
        raise

def enable_foreign_key_checks():
    """启用外键检查"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
            conn.commit()
            logger.info("已启用外键检查")
    except Exception as e:
        logger.error(f"启用外键检查失败: {str(e)}")
        raise

def clear_table_data(table_name):
    """清空单个表的数据"""
    try:
        with engine.connect() as conn:
            # 使用DELETE删除数据（处理外键约束）
            result = conn.execute(text(f"DELETE FROM {table_name}"))
            conn.commit()
            deleted_rows = result.rowcount
            logger.info(f"已清空表: {table_name}, 删除 {deleted_rows} 行数据")
    except Exception as e:
        logger.error(f"清空表 {table_name} 失败: {str(e)}")
        raise

def get_table_counts():
    """获取各表的数据量"""
    try:
        with engine.connect() as conn:
            tables = get_real_tables()
            counts = {}
            
            for table in tables:
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    counts[table] = count
                except Exception as e:
                    counts[table] = f"错误: {str(e)}"
            
            return counts
    except Exception as e:
        logger.error(f"获取表数据量失败: {str(e)}")
        return {}

def print_table_status(before=True):
    """打印表状态"""
    counts = get_table_counts()
    total_rows = sum(count for count in counts.values() if isinstance(count, int))
    
    if before:
        logger.info(f"清理前 - 总数据行数: {total_rows}")
        logger.info("各表数据量:")
    else:
        logger.info(f"清理后 - 总数据行数: {total_rows}")
        logger.info("各表数据量:")
    
    for table, count in counts.items():
        logger.info(f"  {table}: {count} 行")

def clear_all_data():
    """清空所有表数据"""
    try:
        logger.info("开始清空数据库数据...")
        
        # 显示清理前的状态
        print_table_status(before=True)
        
        # 禁用外键检查
        disable_foreign_key_checks()
        
        # 获取所有表名
        tables = get_table_names()
        logger.info(f"发现 {len(tables)} 张表")
        
        # 按顺序清空表数据
        for table in tables:
            clear_table_data(table)
        
        # 启用外键检查
        enable_foreign_key_checks()
        
        # 显示清理后的状态
        print_table_status(before=False)
        
        logger.info("✅ 数据库数据清空完成！")
        
    except Exception as e:
        logger.error(f"❌ 清空数据失败: {str(e)}")
        # 确保外键检查被重新启用
        try:
            enable_foreign_key_checks()
        except:
            pass
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="清空数据库数据脚本")
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="跳过确认直接执行"
    )
    parser.add_argument(
        "--dry-run", 
        action="store_true", 
        help="只显示将要清空的表和数据量，不实际执行"
    )
    
    args = parser.parse_args()
    
    # 显示环境配置
    logger.info("=== 配置摘要 ===")
    logger.info(f"数据库: {settings.MYSQL_DATABASE}")
    logger.info(f"主机: {settings.MYSQL_HOST}")
    logger.info(f"用户: {settings.MYSQL_USERNAME}")
    
    if args.dry_run:
        logger.info("=== 模拟运行模式 ===")
        print_table_status(before=True)
        logger.info("模拟运行完成，未实际清空数据")
    else:
        if not args.force:
            # 确认删除
            response = input("⚠️  确定要清空所有表数据吗？此操作不可恢复！输入 'yes' 确认: ")
            if response.lower() != 'yes':
                logger.info("操作已取消")
                sys.exit(0)
        
        clear_all_data()