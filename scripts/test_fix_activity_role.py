#!/usr/bin/env python3
"""
测试修复activity_角色类型脏数据的脚本
"""

import sqlite3
import os
import tempfile
import subprocess

# 测试用例
def run_test():
    """运行测试"""
    print("🧪 开始测试修复activity_角色类型脏数据脚本...")
    
    # 创建临时数据库文件
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        test_db_path = temp_db.name
    
    try:
        # 初始化测试数据库
        init_test_db(test_db_path)
        
        # 运行修复脚本
        print(f"\n🔧 运行修复脚本处理测试数据库: {test_db_path}")
        fix_script_path = os.path.join(os.path.dirname(__file__), 'fix_activity_role_type.py')
        
        # 由于是测试，我们直接调用脚本的主要函数而不是通过命令行
        # 这样可以避免用户交互提示
        from fix_activity_role_type import check_and_fix_activity_roles
        result = check_and_fix_activity_roles(test_db_path)
        
        # 验证修复结果
        print("\n✅ 开始验证修复结果...")
        verify_fix_result(test_db_path)
        
        print("\n🎉 所有测试通过!")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    finally:
        # 清理临时文件
        if os.path.exists(test_db_path):
            os.unlink(test_db_path)
            print(f"🧹 已清理临时测试数据库")


def init_test_db(db_path):
    """初始化测试数据库并插入测试数据"""
    print(f"📋 初始化测试数据库: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 创建user_cards表
    cursor.execute('''
        CREATE TABLE user_cards (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            role_type TEXT NOT NULL,
            scene_type TEXT NOT NULL,
            display_name TEXT NOT NULL,
            avatar_url TEXT,
            bio TEXT,
            profile_data TEXT,
            preferences TEXT,
            visibility TEXT DEFAULT 'public',
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 插入测试数据
    # 1. 正常数据 - activity_organizer
    # 2. 正常数据 - activity_participant
    # 3. 脏数据 - activity_
    # 4. 脏数据 - activity_invalid
    # 5. 脏数据 - activity_someother
    test_data = [
        ('card_001', 'user_001', 'activity_organizer', 'activity', '活动组织者1', None, None, None, None, 'public', 1, None, None),
        ('card_002', 'user_002', 'activity_participant', 'activity', '活动参与者1', None, None, None, None, 'public', 1, None, None),
        ('card_003', 'user_003', 'activity_', 'activity', '脏数据1', None, None, None, None, 'public', 1, None, None),
        ('card_004', 'user_004', 'activity_invalid', 'activity', '脏数据2', None, None, None, None, 'public', 1, None, None),
        ('card_005', 'user_005', 'activity_someother', 'activity', '脏数据3', None, None, None, None, 'public', 1, None, None)
    ]
    
    cursor.executemany(
        '''INSERT INTO user_cards 
           (id, user_id, role_type, scene_type, display_name, avatar_url, bio, profile_data, preferences, visibility, is_active, created_at, updated_at) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        test_data
    )
    
    conn.commit()
    conn.close()
    
    print(f"✅ 已插入测试数据: {len(test_data)}条记录")
    print(f"   - 正常记录: 2条")
    print(f"   - 脏数据记录: 3条")


def verify_fix_result(db_path):
    """验证修复结果"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 查询所有记录
    cursor.execute("SELECT id, role_type FROM user_cards")
    all_records = cursor.fetchall()
    
    # 统计结果
    normal_organizer = sum(1 for _, role in all_records if role == 'activity_organizer')
    normal_participant = sum(1 for _, role in all_records if role == 'activity_participant')
    remaining_dirty = sum(1 for _, role in all_records if role.startswith('activity_') and role not in ['activity_organizer', 'activity_participant'])
    
    print(f"📊 修复结果统计:")
    print(f"   - activity_organizer: {normal_organizer}")
    print(f"   - activity_participant: {normal_participant}")
    print(f"   - 剩余脏数据: {remaining_dirty}")
    
    # 验证没有脏数据
    assert remaining_dirty == 0, f"❌ 仍有 {remaining_dirty} 条脏数据未修复"
    
    # 验证修复后的记录
    # 原始的脏数据应该被修复为activity_participant
    expected_total_participants = 2 + 3  # 原来的2个加上3个修复的
    assert normal_participant == expected_total_participants, f"❌ 修复后的参与者数量不符合预期: {normal_participant} != {expected_total_participants}"
    
    print("✅ 验证通过: 所有脏数据已被成功修复")
    
    conn.close()


if __name__ == "__main__":
    run_test()