#!/usr/bin/env python3
"""
检查并修复 user_cards 表的模式
"""

import sqlite3
import os

def check_schema():
    """检查 user_cards 表的模式"""
    db_path = "vmatch_dev.db"
    
    if not os.path.exists(db_path):
        print(f"数据库文件 {db_path} 不存在")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取表结构
        cursor.execute("PRAGMA table_info(user_cards)")
        columns = cursor.fetchall()
        
        print("当前 user_cards 表结构:")
        print("=" * 50)
        for col in columns:
            col_id, name, col_type, not_null, default, pk = col
            print(f"{name:20} {col_type:15} {'NOT NULL' if not_null else 'NULL':10} {'PRIMARY KEY' if pk else ''}")
        
        # 检查是否有数据
        cursor.execute("SELECT COUNT(*) FROM user_cards")
        count = cursor.fetchone()[0]
        print(f"\n表中现有 {count} 条记录")
        
        # 如果有数据，检查 trigger_and_output 字段的内容类型
        if count > 0:
            cursor.execute("SELECT id, user_id, typeof(trigger_and_output) FROM user_cards LIMIT 5")
            sample_data = cursor.fetchall()
            print("\n前5条记录的 trigger_and_output 字段类型:")
            for row in sample_data:
                print(f"ID: {row[0]}, UserID: {row[1]}, Type: {row[2]}")
        
        conn.close()
        
    except Exception as e:
        print(f"检查模式时出错: {str(e)}")

def fix_column_types():
    """修复列类型"""
    db_path = "vmatch_dev.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查当前列类型
        cursor.execute("PRAGMA table_info(user_cards)")
        columns = {col[1]: col[2] for col in cursor.fetchall()}
        
        # 如果列是 TEXT 类型，我们需要转换为 JSON 类型
        if 'trigger_and_output' in columns and columns['trigger_and_output'] == 'TEXT':
            print("正在修复 trigger_and_output 列类型...")
            
            # SQLite 不支持直接修改列类型，我们需要重建表
            cursor.execute("BEGIN TRANSACTION")
            
            # 创建新表
            cursor.execute('''
                CREATE TABLE user_cards_new (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    role_type TEXT NOT NULL,
                    scene_type TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    avatar_url TEXT,
                    bio TEXT,
                    trigger_and_output JSON,
                    profile_data JSON,
                    preferences JSON,
                    visibility TEXT DEFAULT 'public',
                    is_active INTEGER DEFAULT 1,
                    is_deleted INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 复制数据
            cursor.execute('''
                INSERT INTO user_cards_new (
                    id, user_id, role_type, scene_type, display_name, avatar_url, bio,
                    trigger_and_output, profile_data, preferences, visibility,
                    is_active, is_deleted, created_at, updated_at
                )
                SELECT 
                    id, user_id, role_type, scene_type, display_name, avatar_url, bio,
                    CASE 
                        WHEN trigger_and_output IS NULL OR trigger_and_output = '' THEN NULL
                        ELSE trigger_and_output
                    END,
                    CASE 
                        WHEN profile_data IS NULL OR profile_data = '' THEN NULL
                        ELSE profile_data
                    END,
                    preferences, visibility, is_active, is_deleted, created_at, updated_at
                FROM user_cards
            ''')
            
            # 删除旧表，重命名新表
            cursor.execute("DROP TABLE user_cards")
            cursor.execute("ALTER TABLE user_cards_new RENAME TO user_cards")
            
            conn.commit()
            print("✅ 列类型修复完成")
        
        conn.close()
        
    except Exception as e:
        print(f"修复列类型时出错: {str(e)}")
        if conn:
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    print("检查 user_cards 表模式...")
    check_schema()
    
    print("\n修复列类型...")
    fix_column_types()
    
    print("\n再次检查模式...")
    check_schema()