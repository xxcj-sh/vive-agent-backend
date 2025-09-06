#!/usr/bin/env python3
"""
更新用户表结构，添加新的字段以支持完整的用户资料
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.utils.db_config import DATABASE_URL

def update_user_table():
    """更新用户表结构"""
    engine = create_engine(DATABASE_URL)
    
    # 添加新的字段到users表（兼容SQLite语法）
    alter_table_sql = """
    -- 添加教育背景字段
    ALTER TABLE users ADD COLUMN education VARCHAR(100);
    
    -- 添加兴趣爱好字段，使用TEXT格式存储JSON
    ALTER TABLE users ADD COLUMN interests TEXT;
    
    -- 添加联系方式字段
    ALTER TABLE users ADD COLUMN wechat VARCHAR(100);
    ALTER TABLE users ADD COLUMN email VARCHAR(255);
    
    -- 添加个人简介字段（扩展长度）
    ALTER TABLE users ADD COLUMN bio TEXT;
    
    -- 添加位置字段（标准化为TEXT格式存储JSON）
    ALTER TABLE users ADD COLUMN location TEXT;
    
    -- 添加职业字段
    ALTER TABLE users ADD COLUMN occupation VARCHAR(100);
    
    -- 添加用户状态字段
    ALTER TABLE users ADD COLUMN status VARCHAR(20) DEFAULT 'active';
    
    -- 添加最后登录时间
    ALTER TABLE users ADD COLUMN last_login TIMESTAMP;
    
    -- 添加用户等级字段
    ALTER TABLE users ADD COLUMN level INTEGER DEFAULT 1;
    
    -- 添加积分字段
    ALTER TABLE users ADD COLUMN points INTEGER DEFAULT 0;
    """
    
    # 创建索引以优化查询
    create_indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_users_gender ON users(gender);",
        "CREATE INDEX IF NOT EXISTS idx_users_age ON users(age);",
        "CREATE INDEX IF NOT EXISTS idx_users_location ON users(location);",
        "CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);",
        "CREATE INDEX IF NOT EXISTS idx_users_level ON users(level);"
    ]
    
    try:
        with engine.connect() as conn:
            print("开始更新用户表结构...")
            
            # 检查现有字段，避免重复添加
            existing_columns = conn.execute(text("PRAGMA table_info(users)"))
            existing_col_names = {row[1] for row in existing_columns}
            
            # 执行表结构更新
            for statement in alter_table_sql.strip().split(';\n'):
                if statement.strip():
                    # 提取字段名
                    if 'ADD COLUMN' in statement.upper():
                        # 提取要添加的字段名
                        parts = statement.split()
                        col_name = None
                        for i, part in enumerate(parts):
                            if part.upper() == 'COLUMN':
                                col_name = parts[i+1]
                                break
                        
                        if col_name and col_name in existing_col_names:
                            print(f"字段 {col_name} 已存在，跳过")
                            continue
                    
                    try:
                        conn.execute(text(statement))
                        print(f"执行: {statement.strip()}")
                    except Exception as e:
                        if "duplicate column name" in str(e).lower():
                            print(f"字段已存在，跳过: {statement.strip()}")
                        else:
                            print(f"执行出错: {statement.strip()} - {e}")
            
            # 创建索引
            for index_sql in create_indexes_sql:
                try:
                    conn.execute(text(index_sql))
                    print(f"创建索引: {index_sql}")
                except Exception as e:
                    if "already exists" in str(e).lower():
                        print(f"索引已存在，跳过: {index_sql}")
                    else:
                        print(f"创建索引出错: {index_sql} - {e}")
            
            conn.commit()
            print("用户表结构更新成功！")
            
    except Exception as e:
        print(f"更新用户表结构时出错: {e}")
        raise

def migrate_existing_data():
    """迁移现有数据"""
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            print("开始迁移现有数据...")
            
            # 将现有的location字符串转换为JSON格式（SQLite兼容）
            migrate_location_sql = """
            UPDATE users 
            SET location = CASE 
                WHEN location IS NOT NULL AND location != '' 
                THEN '[' || '"' || location || '"' || ']' 
                ELSE NULL 
            END
            WHERE location IS NOT NULL AND location NOT LIKE '[%';
            """
            
            # 将现有的interests字符串转换为JSON格式（SQLite兼容）
            migrate_interests_sql = """
            UPDATE users 
            SET interests = CASE 
                WHEN interests IS NOT NULL AND interests != '' 
                THEN '[' || '"' || interests || '"' || ']' 
                ELSE '[]' 
            END;
            """
            
            # 执行数据迁移
            conn.execute(text(migrate_location_sql))
            conn.execute(text(migrate_interests_sql))
            
            conn.commit()
            print("现有数据迁移成功！")
            
    except Exception as e:
        print(f"迁移现有数据时出错: {e}")
        # 不抛出异常，允许继续执行

if __name__ == "__main__":
    update_user_table()
    migrate_existing_data()
    print("用户表结构更新完成！")