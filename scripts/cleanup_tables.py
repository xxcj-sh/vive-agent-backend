#!/usr/bin/env python3
"""
清理用户表和卡片表中的存量数据
"""

import sqlite3
import os
from datetime import datetime

def cleanup_tables():
    """清理users和user_cards表中的存量数据"""
    
    db_path = "vmatch_dev.db"
    backup_path = f"vmatch_dev_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    # 创建数据库备份
    if os.path.exists(db_path):
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ 已创建数据库备份: {backup_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 开始事务
        cursor.execute("BEGIN TRANSACTION")
        
        # 获取清理前的数据量
        cursor.execute("SELECT COUNT(*) FROM users")
        users_count_before = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM user_cards")
        cards_count_before = cursor.fetchone()[0]
        
        print(f"📊 清理前数据量:")
        print(f"   users表: {users_count_before}条记录")
        print(f"   user_cards表: {cards_count_before}条记录")
        
        # 删除user_cards表数据（先删除子表）
        cursor.execute("DELETE FROM user_cards")
        deleted_cards = cursor.rowcount
        
        # 删除users表数据
        cursor.execute("DELETE FROM users")
        deleted_users = cursor.rowcount
        
        # 重置自增ID（SQLite使用sqlite_sequence，如果不存在则跳过）
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('users', 'user_cards')")
        except sqlite3.OperationalError:
            # sqlite_sequence表不存在，跳过
            pass
        
        # 提交事务
        conn.commit()
        
        # 验证清理结果
        cursor.execute("SELECT COUNT(*) FROM users")
        users_count_after = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM user_cards")
        cards_count_after = cursor.fetchone()[0]
        
        print(f"\n✅ 清理完成:")
        print(f"   已删除users表: {deleted_users}条记录")
        print(f"   已删除user_cards表: {deleted_cards}条记录")
        print(f"   users表现在: {users_count_after}条记录")
        print(f"   user_cards表现在: {cards_count_after}条记录")
        
        # 显示表结构信息
        print(f"\n📋 表结构验证:")
        for table in ['users', 'user_cards']:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            print(f"   {table}表字段: {[col[1] for col in columns]}")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 清理失败: {e}")
        raise
    finally:
        conn.close()

def verify_cleanup():
    """验证清理结果"""
    try:
        conn = sqlite3.connect("vmatch_dev.db")
        cursor = conn.cursor()
        
        # 检查表是否为空
        cursor.execute("SELECT COUNT(*) FROM users")
        users_empty = cursor.fetchone()[0] == 0
        
        cursor.execute("SELECT COUNT(*) FROM user_cards")
        cards_empty = cursor.fetchone()[0] == 0
        
        # 检查自增ID是否重置
        cursor.execute("SELECT seq FROM sqlite_sequence WHERE name='users'")
        users_seq = cursor.fetchone()
        
        cursor.execute("SELECT seq FROM sqlite_sequence WHERE name='user_cards'")
        cards_seq = cursor.fetchone()
        
        print(f"\n🔍 验证结果:")
        print(f"   users表是否为空: {'✅' if users_empty else '❌'}")
        print(f"   user_cards表是否为空: {'✅' if cards_empty else '❌'}")
        print(f"   users自增ID: {users_seq[0] if users_seq else '已重置'}")
        print(f"   user_cards自增ID: {cards_seq[0] if cards_seq else '已重置'}")
        
        conn.close()
        return users_empty and cards_empty
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

if __name__ == "__main__":
    print("🧹 开始清理数据库表数据...")
    
    # 确认操作
    response = input("⚠️  这将删除users和user_cards表中的所有数据，是否继续？(y/N): ")
    if response.lower() == 'y':
        cleanup_tables()
        verify_cleanup()
        print("\n🎉 数据库清理完成！")
    else:
        print("❌ 操作已取消")