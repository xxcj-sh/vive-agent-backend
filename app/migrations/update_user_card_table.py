"""
更新 UserCard 表结构脚本
"""

import os
import sys
from sqlalchemy import create_engine, inspect, Table, Column, String, Integer, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))  

from app.config import settings
from app.models.user_card_db import UserCard
from app.utils.db_config import engine, Base, SessionLocal


def check_table_structure():
    """检查 UserCard 表的当前结构"""
    inspector = inspect(engine)
    
    # 获取当前表的列信息
    if 'user_cards' in inspector.get_table_names():
        columns = inspector.get_columns('user_cards')
        print("当前 UserCard 表结构:")
        for column in columns:
            print(f"- {column['name']}: {column['type']}, nullable={column['nullable']}")
    else:
        print("UserCard 表不存在")


def update_table_structure():
    """更新 UserCard 表结构以匹配最新的模型定义"""
    # 创建会话
    db = SessionLocal()
    
    try:
        # 创建新的表（如果表不存在）或更新表结构
        # 使用 SQLAlchemy 的 Metadata 来更新表结构
        metadata = Base.metadata
        
        # 获取数据库连接
        connection = engine.connect()
        
        # 检查表是否存在
        inspector = inspect(engine)
        table_exists = 'user_cards' in inspector.get_table_names()
        
        if not table_exists:
            # 如果表不存在，创建新表
            UserCard.__table__.create(connection)
            print("✅ UserCard 表创建成功!")
        else:
            # 检查表结构是否需要更新
            # 在 SQLite 中，修改表结构比较复杂，我们可以创建一个新表，复制数据，然后替换旧表
            # 这里我们使用简单的方式，直接尝试创建表（SQLite 会忽略已存在的表）
            # 对于更复杂的结构变更，建议使用 Alembic 等迁移工具
            print("UserCard 表已存在，确保结构与模型一致...")
            
            # 对于 SQLite，我们可以执行一些特定的 ALTER TABLE 语句来添加缺失的列
            # 注意：SQLite 有限制，某些操作如更改列类型需要重新创建表
            
            # 检查并添加缺失的列
            existing_columns = [col['name'] for col in inspector.get_columns('user_cards')]
            model_columns = [col.name for col in UserCard.__table__.columns]
            
            for column in UserCard.__table__.columns:
                if column.name not in existing_columns:
                    # 构建 ALTER TABLE 语句来添加列
                    column_type = str(column.type)
                    nullable = "NULL" if column.nullable else "NOT NULL"
                    default = f"DEFAULT {column.default.arg}" if column.default else ""
                    
                    # 特殊处理 datetime 类型的默认值
                    if isinstance(column.type, DateTime) and column.default:
                        if hasattr(column.default, 'arg') and column.default.arg == func.now():
                            default = "DEFAULT CURRENT_TIMESTAMP"
                    
                    # 构建 SQL 语句
                    alter_sql = f"ALTER TABLE user_cards ADD COLUMN {column.name} {column_type}"
                    if not column.nullable:
                        alter_sql += " NOT NULL"
                    if default.strip():
                        alter_sql += f" {default}"
                    
                    try:
                        # 使用 text() 函数包装 SQL 语句
                        from sqlalchemy import text
                        connection.execute(text(alter_sql))
                        connection.commit()  # 提交更改
                        print(f"✅ 添加列 {column.name} 成功")
                    except Exception as e:
                        print(f"⚠️ 添加列 {column.name} 失败: {str(e)}")
                        # 尝试更简单的版本
                        try:
                            simple_alter_sql = f"ALTER TABLE user_cards ADD COLUMN {column.name} {column_type}"
                            connection.execute(text(simple_alter_sql))
                            connection.commit()  # 提交更改
                            print(f"✅ 添加列 {column.name} 成功（简化版本）")
                        except Exception as e2:
                            print(f"⚠️ 简化版本也失败: {str(e2)}")
            
            print("✅ UserCard 表结构检查完成")
        
        # 提交更改
        connection.commit()
        
    except Exception as e:
        print(f"❌ 更新 UserCard 表结构失败: {str(e)}")
        db.rollback()
    finally:
        connection.close()
        db.close()


def main():
    """主函数"""
    print("开始更新 UserCard 表结构...")
    
    # 检查当前表结构
    check_table_structure()
    
    # 更新表结构
    update_table_structure()
    
    # 再次检查更新后的表结构
    print("\n更新后的 UserCard 表结构:")
    check_table_structure()


if __name__ == "__main__":
    main()