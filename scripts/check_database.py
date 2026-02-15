#!/usr/bin/env python3
"""
数据库表结构检查脚本
用于检查数据库中所有表的结构和关系
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, inspect, text
from app.config import settings
from app.database import Base
import warnings

# 忽略SQLAlchemy警告
warnings.filterwarnings("ignore", category=DeprecationWarning)

def check_database_tables():
    """检查数据库表结构"""
    print("正在检查数据库表结构...")
    
    # 创建数据库引擎
    engine = create_engine(settings.computed_database_url, echo=False)
    
    print(f"连接到数据库: {settings.computed_database_url.split('@')[-1]}")
    
    # 获取inspector
    inspector = inspect(engine)
    
    # 获取所有表名
    tables = inspector.get_table_names()
    
    print(f"\n数据库中共有 {len(tables)} 个表:")
    
    if not tables:
        print("⚠️  数据库中没有找到任何表")
        return
    
    # 详细检查每个表
    for table_name in sorted(tables):
        print(f"\n{'='*60}")
        print(f"表名: {table_name}")
        print(f"{'='*60}")
        
        # 获取列信息
        columns = inspector.get_columns(table_name)
        print(f"列数: {len(columns)}")
        print("\n列详情:")
        for col in columns:
            print(f"  - {col['name']}: {col['type']}", end="")
            if col.get('nullable') is False:
                print(" NOT NULL", end="")
            if col.get('default') is not None:
                print(f" DEFAULT {col['default']}", end="")
            if col.get('autoincrement'):
                print(" AUTO_INCREMENT", end="")
            print()
        
        # 获取主键信息
        pk_constraint = inspector.get_pk_constraint(table_name)
        if pk_constraint and pk_constraint.get('constrained_columns'):
            print(f"\n主键: {', '.join(pk_constraint['constrained_columns'])}")
        
        # 获取外键信息
        foreign_keys = inspector.get_foreign_keys(table_name)
        if foreign_keys:
            print(f"\n外键约束:")
            for fk in foreign_keys:
                print(f"  - {fk['name']}: {', '.join(fk['constrained_columns'])}")
                print(f"    引用: {fk['referred_table']}.{', '.join(fk['referred_columns'])}")
        
        # 获取索引信息
        indexes = inspector.get_indexes(table_name)
        if indexes:
            print(f"\n索引:")
            for idx in indexes:
                print(f"  - {idx['name']}: {', '.join(idx['column_names'])}")
                if idx.get('unique'):
                    print("    UNIQUE")
    
    # 检查表之间的关系
    print(f"\n{'='*60}")
    print("表关系概览:")
    print(f"{'='*60}")
    
    # 构建关系图
    relationships = {}
    for table_name in tables:
        foreign_keys = inspector.get_foreign_keys(table_name)
        if foreign_keys:
            relationships[table_name] = []
            for fk in foreign_keys:
                relationships[table_name].append({
                    'columns': fk['constrained_columns'],
                    'referenced_table': fk['referred_table'],
                    'referenced_columns': fk['referred_columns']
                })
    
    if relationships:
        for table, rels in relationships.items():
            print(f"\n{table} 依赖于:")
            for rel in rels:
                print(f"  - {rel['columns']} -> {rel['referenced_table']}.{rel['referenced_columns']}")
    else:
        print("没有找到表间依赖关系")
    
    # 检查是否有孤立的表（没有被其他表引用）
    print(f"\n{'='*60}")
    print("孤立表检查:")
    print(f"{'='*60}")
    
    referenced_tables = set()
    for table_name in tables:
        foreign_keys = inspector.get_foreign_keys(table_name)
        for fk in foreign_keys:
            referenced_tables.add(fk['referred_table'])
    
    isolated_tables = [table for table in tables if table not in referenced_tables]
    
    if isolated_tables:
        print("以下表没有被其他表引用（可能是主表）:")
        for table in isolated_tables:
            print(f"  - {table}")
    else:
        print("所有表都被其他表引用")

def check_table_row_counts():
    """检查表的行数"""
    print(f"\n{'='*60}")
    print("表数据量统计:")
    print(f"{'='*60}")
    
    engine = create_engine(settings.computed_database_url, echo=False)
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    with engine.connect() as conn:
        for table_name in sorted(tables):
            try:
                result = conn.execute(text(f"SELECT COUNT(*) FROM `{table_name}`"))
                count = result.scalar()
                print(f"{table_name}: {count} 行")
            except Exception as e:
                print(f"{table_name}: 无法获取行数 - {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("数据库表结构检查工具")
    print("=" * 60)
    
    try:
        # 检查表结构
        check_database_tables()
        
        # 检查数据量
        check_table_row_counts()
        
        print("\n" + "=" * 60)
        print("✅ 数据库表结构检查完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()