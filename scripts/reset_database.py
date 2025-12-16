#!/usr/bin/env python3
"""
数据库重置脚本
用于清空所有数据库表并重新创建表结构
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.database import Base, get_db
from app.models import *
import warnings

# 忽略SQLAlchemy警告
warnings.filterwarnings("ignore", category=DeprecationWarning)

def get_database_engine():
    """获取数据库引擎"""
    return create_engine(settings.DATABASE_URL, echo=False)

def drop_all_tables(engine):
    """删除所有数据库表"""
    print("正在删除所有数据库表...")
    
    # 获取数据库连接
    with engine.connect() as conn:
        # 获取数据库inspector
        inspector = inspect(engine)
        
        # 获取所有表名
        tables = inspector.get_table_names()
        print(f"发现 {len(tables)} 个表: {tables}")
        
        # 禁用外键检查（MySQL）
        if 'mysql' in settings.DATABASE_URL:
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        
        # 按依赖关系排序删除表
        # 先删除有外键依赖的表
        tables_to_drop = []
        
        # 优先删除这些可能有依赖关系的表
        priority_tables = [
            'activity_participants',
            'user_cards', 
            'topic_card_opinions',
            'topic_cards',
            'activities',
            'users'
        ]
        
        # 按优先级排序
        for table in priority_tables:
            if table in tables:
                tables_to_drop.append(table)
        
        # 添加剩余的表
        for table in tables:
            if table not in tables_to_drop:
                tables_to_drop.append(table)
        
        # 删除表
        for table in tables_to_drop:
            try:
                print(f"正在删除表: {table}")
                conn.execute(text(f"DROP TABLE IF EXISTS `{table}`"))
                print(f"✓ 已删除表: {table}")
            except Exception as e:
                print(f"✗ 删除表 {table} 失败: {e}")
        
        # 重新启用外键检查
        if 'mysql' in settings.DATABASE_URL:
            conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        
        # 提交更改
        conn.commit()
    
    print("所有表删除完成")

def create_all_tables(engine):
    """创建所有数据库表"""
    print("正在创建所有数据库表...")
    
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    print("所有表创建完成")

def verify_tables(engine):
    """验证表是否创建成功"""
    print("正在验证表结构...")
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"数据库中共有 {len(tables)} 个表:")
    for table in sorted(tables):
        print(f"  - {table}")
        
        # 显示表的列信息
        columns = inspector.get_columns(table)
        print(f"    列数: {len(columns)}")
        
        # 显示主键信息
        pk_constraint = inspector.get_pk_constraint(table)
        if pk_constraint and pk_constraint.get('constrained_columns'):
            print(f"    主键: {pk_constraint['constrained_columns']}")

def main():
    """主函数"""
    print("=" * 50)
    print("数据库重置脚本")
    print("=" * 50)
    
    # 确认操作
    print("⚠️  警告: 此操作将删除所有数据库表并重新创建！")
    print("这将清除所有数据，请确保您已备份重要数据。")
    
    # 检查是否有环境变量跳过确认（用于自动化）
    if os.environ.get('SKIP_CONFIRMATION') != 'true':
        confirmation = input("\n请输入 'yes' 确认要继续: ")
        if confirmation.lower() != 'yes':
            print("操作已取消")
            return
    
    try:
        # 获取数据库引擎
        engine = get_database_engine()
        
        print(f"\n连接到数据库: {settings.DATABASE_URL.split('@')[-1]}")
        
        # 步骤1: 删除所有表
        drop_all_tables(engine)
        
        # 步骤2: 创建所有表
        create_all_tables(engine)
        
        # 步骤3: 验证表结构
        verify_tables(engine)
        
        print("\n" + "=" * 50)
        print("✅ 数据库重置成功！")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ 数据库重置失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()