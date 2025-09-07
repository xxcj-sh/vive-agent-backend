#!/usr/bin/env python3
"""
检查数据库中user_cards表的role_type脏数据情况
"""

import sqlite3
import os

# 有效的活动角色类型
VALID_ACTIVITY_ROLES = {
    'activity_organizer',
    'activity_participant'
}

# 数据库路径配置
DB_PATHS = [
    'vmatch_dev.db',  # 开发环境数据库
    'vmatch.db',      # 生产环境数据库
    'test_match.db'   # 测试数据库
]

def check_database(db_path):
    """检查指定数据库中的脏数据情况"""
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件 {db_path} 不存在")
        return
    
    print(f"\n🔍 检查数据库: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查user_cards表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_cards'")
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            print("   ❌ user_cards表不存在")
            conn.close()
            return
        
        # 查询总记录数
        cursor.execute("SELECT COUNT(*) FROM user_cards")
        total_records = cursor.fetchone()[0]
        print(f"   总记录数: {total_records}")
        
        # 查询活动场景的记录数
        cursor.execute("SELECT COUNT(*) FROM user_cards WHERE scene_type = 'activity'")
        activity_records = cursor.fetchone()[0]
        print(f"   活动场景记录数: {activity_records}")
        
        # 查询所有活动角色类型的分布
        cursor.execute("""
            SELECT role_type, COUNT(*) 
            FROM user_cards 
            WHERE scene_type = 'activity' 
            GROUP BY role_type
            ORDER BY COUNT(*) DESC
        """)
        role_distribution = cursor.fetchall()
        
        print("   角色类型分布:")
        for role_type, count in role_distribution:
            status = "✅ 有效" if role_type in VALID_ACTIVITY_ROLES else "❌ 脏数据"
            print(f"     {role_type}: {count}条 ({status})")
        
        # 查询脏数据记录详情
        cursor.execute("""
            SELECT id, user_id, role_type, scene_type, display_name 
            FROM user_cards 
            WHERE role_type LIKE 'activity_%' AND role_type NOT IN (?, ?)
            LIMIT 10
        """, tuple(VALID_ACTIVITY_ROLES))
        
        dirty_records = cursor.fetchall()
        dirty_count = len(dirty_records)
        
        if dirty_count > 0:
            print(f"\n   发现脏数据记录: {dirty_count}条")
            print("   示例脏数据记录:")
            for i, record in enumerate(dirty_records):
                card_id, user_id, role_type, scene_type, display_name = record
                print(f"     {i+1}. 卡片ID: {card_id[:8]}..., 用户ID: {user_id[:8]}..., 脏角色: '{role_type}', 显示名称: '{display_name}'")
        else:
            print("   ✅ 未发现脏数据记录")
        
        conn.close()
        
    except Exception as e:
        print(f"   ❌ 检查过程出错: {e}")

def main():
    """主函数"""
    print("🔍 开始检查activity_角色类型脏数据...")
    print(f"有效的活动角色类型: {', '.join(VALID_ACTIVITY_ROLES)}")
    
    # 遍历所有数据库
    for db_path in DB_PATHS:
        check_database(db_path)
    
    print("\n📝 检查完成!")
    print("   如需修复脏数据，请运行: python fix_activity_role_type.py")

if __name__ == "__main__":
    main()