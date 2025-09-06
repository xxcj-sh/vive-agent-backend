#!/usr/bin/env python3
"""
检查数据库状态
"""

import sqlite3
import os

def check_database():
    """检查数据库状态"""
    db_path = 'vmatch_dev.db'
    
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return
    
    print("✅ 数据库文件存在")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 查看所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print("现有表:")
        for table in tables:
            table_name = table[0]
            print(f"  {table_name}")
            
            # 查看表结构
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            for col in columns:
                print(f"    {col[1]}: {col[2]}")
        
        # 查看用户数据
        if any(table[0] == 'users' for table in tables):
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            print(f"\n用户总数: {user_count}")
            
            if user_count > 0:
                cursor.execute("SELECT id, phone, nick_name FROM users LIMIT 5")
                users = cursor.fetchall()
                print("前5个用户:")
                for user in users:
                    print(f"  {user[0][:8]}...: {user[1]} - {user[2]}")
        
        # 查看卡片数据
        if any(table[0] == 'user_cards' for table in tables):
            cursor.execute("SELECT COUNT(*) FROM user_cards")
            card_count = cursor.fetchone()[0]
            print(f"\n卡片总数: {card_count}")
            
            if card_count > 0:
                cursor.execute("SELECT id, user_id, role_type, scene_type FROM user_cards LIMIT 5")
                cards = cursor.fetchall()
                print("前5个卡片:")
                for card in cards:
                    print(f"  {card[0][:8]}...: {card[1][:8]}... - {card[2]} - {card[3]}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 检查数据库时出错: {e}")

if __name__ == "__main__":
    check_database()