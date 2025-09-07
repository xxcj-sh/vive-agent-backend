#!/usr/bin/env python3
"""
修复user_cards表中role_type为"activity_"的脏数据
"""

import sqlite3
import os
from datetime import datetime

# 有效的活动角色类型
VALID_ACTIVITY_ROLES = {
    'activity_organizer',
    'activity_participant'
}

# 默认修复映射 - 当无法确定正确角色时使用
DEFAULT_ROLE_FIX = 'activity_participant'  # 默认修复为活动参与者

# 数据库路径配置
DB_PATHS = [
    'vmatch_dev.db',  # 开发环境数据库
    'vmatch.db',      # 生产环境数据库
    'test_match.db'   # 测试数据库
]

def backup_database(db_path):
    """创建数据库备份"""
    if not os.path.exists(db_path):
        return None
    
    backup_path = f"{db_path}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ 已创建数据库备份: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"❌ 创建备份失败: {e}")
        return None

def check_and_fix_activity_roles(db_path):
    """检查并修复数据库中的活动角色类型"""
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件 {db_path} 不存在")
        return False
    
    print(f"\n🔍 开始检查数据库: {db_path}")
    
    # 创建数据库备份
    backup_path = backup_database(db_path)
    if not backup_path:
        # 如果是测试数据库，可以继续；否则终止操作
        if 'test' in db_path.lower():
            print("⚠️  测试数据库未创建备份，继续操作")
        else:
            print("❌ 非测试数据库未创建备份，终止操作")
            return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 开始事务
        cursor.execute("BEGIN TRANSACTION")
        
        # 检查user_cards表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_cards'")
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            print("❌ user_cards表不存在")
            conn.rollback()
            conn.close()
            return False
        
        # 查询脏数据记录
        cursor.execute("""
            SELECT id, user_id, role_type, scene_type, display_name 
            FROM user_cards 
            WHERE role_type LIKE 'activity_%' AND role_type NOT IN (?, ?)
        """, tuple(VALID_ACTIVITY_ROLES))
        
        dirty_records = cursor.fetchall()
        total_dirty = len(dirty_records)
        
        print(f"📊 发现 {total_dirty} 条脏数据记录")
        
        if total_dirty > 0:
            # 显示前5条脏数据记录
            print("\n示例脏数据记录:")
            for i, record in enumerate(dirty_records[:5]):
                card_id, user_id, role_type, scene_type, display_name = record
                print(f"  {i+1}. 卡片ID: {card_id[:8]}..., 用户ID: {user_id[:8]}..., 脏角色: '{role_type}', 场景: '{scene_type}', 显示名称: '{display_name}'")
            
            # 询问是否继续修复
            if 'test' not in db_path.lower():
                # 自动确认修复，避免交互式输入问题
                print("\n⚠️  自动确认修复脏数据")
                response = 'y'
                # 如果需要交互式确认，取消下面的注释并注释上面的自动确认行
                # response = input("\n⚠️  是否继续修复这些脏数据？(y/N): ")
                if response.lower() != 'y':
                    print("❌ 操作已取消")
                    conn.rollback()
                    conn.close()
                    return False
            
            # 执行修复
            print("\n🛠️  开始修复脏数据...")
            
            # 记录修复情况
            fixed_count = 0
            for record in dirty_records:
                card_id, _, role_type, scene_type, _ = record
                
                # 尝试根据上下文确定正确的角色类型
                # 这里可以添加更复杂的逻辑，根据其他字段推断正确角色
                fixed_role = DEFAULT_ROLE_FIX  # 默认修复策略
                
                try:
                    # 更新记录
                    cursor.execute(
                        "UPDATE user_cards SET role_type = ? WHERE id = ?",
                        (fixed_role, card_id)
                    )
                    fixed_count += 1
                    print(f"  ✅ 修复卡片 {card_id[:8]}...: '{role_type}' -> '{fixed_role}'")
                except Exception as e:
                    print(f"  ❌ 修复卡片 {card_id[:8]}... 失败: {e}")
            
            # 提交事务
            conn.commit()
            print(f"\n✅ 修复完成: 共修复 {fixed_count}/{total_dirty} 条记录")
        else:
            print("✅ 未发现脏数据记录")
        
        # 验证修复结果
        print("\n🔍 验证修复结果:")
        cursor.execute("""
            SELECT COUNT(*) 
            FROM user_cards 
            WHERE role_type LIKE 'activity_%' AND role_type NOT IN (?, ?)
        """, tuple(VALID_ACTIVITY_ROLES))
        remaining_dirty = cursor.fetchone()[0]
        
        print(f"   剩余脏数据记录数: {remaining_dirty}")
        
        if remaining_dirty == 0:
            print("✅ 所有脏数据已成功修复")
        else:
            print(f"⚠️  仍有 {remaining_dirty} 条脏数据未修复")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 修复过程出错: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def main():
    """主函数"""
    print("🧹 开始清理activity_角色类型脏数据...")
    print(f"\n有效的活动角色类型: {', '.join(VALID_ACTIVITY_ROLES)}")
    
    # 遍历所有数据库
    for db_path in DB_PATHS:
        check_and_fix_activity_roles(db_path)
    
    print("\n🎉 脏数据清理脚本执行完成!")
    print("📝 注意事项:")
    print("   1. 如有数据问题，请检查备份文件进行恢复")
    print("   2. 建议在生产环境执行前先在测试环境验证")

if __name__ == "__main__":
    main()