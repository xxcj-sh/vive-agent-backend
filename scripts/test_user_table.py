#!/usr/bin/env python3
"""
测试用户表结构更新
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.utils.db_config import DATABASE_URL

def test_user_table_structure():
    """测试用户表结构"""
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            print("=== 测试用户表结构 ===")
            
            # 获取表结构信息
            columns = conn.execute(text("PRAGMA table_info(users)"))
            
            print("用户表字段：")
            for column in columns:
                print(f"  {column[1]}: {column[2]} (nullable: {not column[3]}, default: {column[4]})")
            
            # 测试插入新用户
            print("\n=== 测试插入新用户 ===")
            test_user_sql = """
            INSERT INTO users (id, phone, nick_name, age, occupation, location, education, interests, wechat, email, status, level, points)
            VALUES ('test_user_001', '13800138000', '测试用户', 25, '工程师', '["北京市", "朝阳区"]', '本科', '["编程", "阅读", "旅游"]', 'test_wechat', 'test@example.com', 'active', 2, 100)
            """
            
            conn.execute(text(test_user_sql))
            conn.commit()
            print("✅ 测试用户插入成功")
            
            # 查询测试用户
            result = conn.execute(text("SELECT * FROM users WHERE id = 'test_user_001'"))
            user = result.fetchone()
            if user:
                print("✅ 测试用户查询成功")
                print(f"用户数据: {dict(zip([col[1] for col in conn.execute(text('PRAGMA table_info(users)'))], user))}")
            else:
                print("❌ 测试用户查询失败")
            
            # 清理测试数据
            conn.execute(text("DELETE FROM users WHERE id = 'test_user_001'"))
            conn.commit()
            print("✅ 测试数据清理完成")
            
            # 检查索引
            print("\n=== 检查索引 ===")
            indexes = conn.execute(text("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='users'"))
            print("用户表索引：")
            for index in indexes:
                print(f"  {index[0]}")
            
            print("\n✅ 所有测试完成")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        raise

if __name__ == "__main__":
    test_user_table_structure()