"""
添加 UserCard 表新字段的迁移脚本
"""

import os
import sys
import sqlite3

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.config import settings

def add_new_columns():
    """添加新字段到 UserCard 表"""
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    
    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查并添加 trigger_and_output 字段
        cursor.execute("PRAGMA table_info(user_cards)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'trigger_and_output' not in columns:
            # 使用 JSON 类型而不是 TEXT 类型
            cursor.execute("ALTER TABLE user_cards ADD COLUMN trigger_and_output JSON")
            print("✅ 添加 trigger_and_output 字段成功")
        else:
            print("trigger_and_output 字段已存在")
            
        if 'profile_data' not in columns:
            # 使用 JSON 类型而不是 TEXT 类型
            cursor.execute("ALTER TABLE user_cards ADD COLUMN profile_data JSON")
            print("✅ 添加 profile_data 字段成功")
        else:
            print("profile_data 字段已存在")
        
        # 提交更改
        conn.commit()
        print("✅ 数据库迁移完成")
        
    except Exception as e:
        print(f"❌ 数据库迁移失败: {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def verify_columns():
    """验证字段是否添加成功"""
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(user_cards)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print("当前 UserCard 表字段:")
        for column in columns:
            print(f"- {column}")
            
        if 'trigger_and_output' in columns and 'profile_data' in columns:
            print("✅ 所有新字段都已成功添加")
        else:
            print("⚠️ 部分字段缺失")
            
    except Exception as e:
        print(f"❌ 验证失败: {str(e)}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("开始添加 UserCard 表新字段...")
    add_new_columns()
    print("\n验证字段添加结果:")
    verify_columns()