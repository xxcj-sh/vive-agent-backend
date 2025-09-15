#!/usr/bin/env python3
"""
直接删除用户卡片数据的脚本
"""

import sqlite3
import os
import sys
from datetime import datetime

def delete_user_cards_by_phone(phone_number):
    """根据手机号删除用户卡片数据"""
    
    # 使用开发数据库
    db_path = '../vmatch_dev.db'
    
    if not os.path.exists(db_path):
        print(f"❌ 开发数据库文件 {db_path} 不存在")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        print(f"=== 连接到开发数据库: {db_path} ===")
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("❌ users 表不存在")
            conn.close()
            return False
            
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_cards'")
        if not cursor.fetchone():
            print("❌ user_cards 表不存在")
            conn.close()
            return False
        
        # 查找用户ID
        cursor.execute("SELECT id FROM users WHERE phone = ?", (phone_number,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ 手机号 {phone_number} 对应的用户不存在")
            conn.close()
            return False
        
        user_id = user['id']
        print(f"✅ 找到用户ID: {user_id}")
        
        # 统计现有卡片数量
        cursor.execute("SELECT COUNT(*) as count FROM user_cards WHERE user_id = ?", (user_id,))
        card_count = cursor.fetchone()['count']
        print(f"📊 当前用户卡片数量: {card_count}")
        
        if card_count == 0:
            print(f"ℹ️ 用户 {phone_number} 没有卡片数据需要删除")
            conn.close()
            return True
        
        # 显示卡片详情
        cursor.execute("""
            SELECT id, role_type, scene_type, bio, created_at 
            FROM user_cards 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        """, (user_id,))
        
        cards = cursor.fetchall()
        print("\n=== 用户卡片详情 ===")
        for card in cards:
            print(f"ID: {card['id']}")
            print(f"角色类型: {card['role_type']}")
            print(f"场景类型: {card['scene_type']}")
            print(f"简介: {card['bio'][:50]}...")
            print(f"创建时间: {card['created_at']}")
            print("-" * 40)
        
        # 确认删除
        confirm = input(f"\n⚠️  确认删除用户 {phone_number} 的 {card_count} 张卡片？(y/N): ")
        if confirm.lower() != 'y':
            print("❌ 操作已取消")
            conn.close()
            return False
        
        # 开始事务删除
        cursor.execute("BEGIN TRANSACTION")
        
        # 删除用户卡片
        cursor.execute("DELETE FROM user_cards WHERE user_id = ?", (user_id,))
        deleted_count = cursor.rowcount
        
        conn.commit()
        
        print(f"✅ 成功删除 {deleted_count} 张用户卡片")
        
        # 验证删除结果
        cursor.execute("SELECT COUNT(*) as count FROM user_cards WHERE user_id = ?", (user_id,))
        remaining = cursor.fetchone()['count']
        print(f"📊 剩余卡片数量: {remaining}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 删除失败: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def main():
    """主函数"""
    if len(sys.argv) != 2:
        print("用法: python delete_user_cards_direct.py <手机号>")
        print("示例: python delete_user_cards_direct.py 18900189000")
        return
    
    phone_number = sys.argv[1]
    
    if not phone_number.isdigit() or len(phone_number) != 11:
        print("❌ 请输入有效的11位手机号")
        return
    
    print(f"🗑️  开始删除用户 {phone_number} 的卡片数据...")
    
    success = delete_user_cards_by_phone(phone_number)
    
    if success:
        print("🎉 操作完成！")
    else:
        print("❌ 操作失败！")

if __name__ == "__main__":
    main()