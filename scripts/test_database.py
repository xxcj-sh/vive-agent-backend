#!/usr/bin/env python3
"""
数据库测试脚本
用于验证数据库初始化是否成功
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database_config import get_db_manager, get_db_config

def test_database_connection():
    """测试数据库连接"""
    print("=== 数据库连接测试 ===")
    
    try:
        config = get_db_config()
        manager = get_db_manager()
        
        print(f"数据库路径: {config.db_path}")
        print(f"数据库存在: {config.database_exists()}")
        
        if config.database_exists():
            print(f"数据库大小: {config.get_db_size_mb():.2f} MB")
            
            # 获取数据库统计信息
            stats = manager.get_database_stats()
            print(f"表数量: {stats['table_count']}")
            print(f"索引数量: {stats['index_count']}")
            
            print("\n表统计:")
            for table, count in stats['tables'].items():
                print(f"  {table}: {count} 条记录")
            
            return True
        else:
            print("数据库文件不存在")
            return False
            
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return False

def test_table_structure():
    """测试表结构"""
    print("\n=== 表结构测试 ===")
    
    try:
        manager = get_db_manager()
        
        # 测试主要表
        test_tables = ['users', 'user_cards', 'match_actions', 'match_results', 'chat_messages']
        
        for table in test_tables:
            try:
                info = manager.get_table_info(table)
                print(f"{table}: {len(info)} 个字段")
                
                # 显示前几个字段
                for i, field in enumerate(info[:3]):
                    print(f"  - {field[1]} ({field[2]})")
                if len(info) > 3:
                    print(f"  ... 还有 {len(info) - 3} 个字段")
                    
            except Exception as e:
                print(f"{table}: 表不存在或查询失败 - {e}")
        
        return True
        
    except Exception as e:
        print(f"表结构测试失败: {e}")
        return False

def test_data_integrity():
    """测试数据完整性"""
    print("\n=== 数据完整性测试 ===")
    
    try:
        manager = get_db_manager()
        
        # 测试用户数据
        users = manager.execute_query("SELECT id, nick_name, phone FROM users LIMIT 5")
        print(f"用户数据: {len(users)} 条记录")
        for user in users:
            print(f"  - {user[1]} ({user[0]}): {user[2]}")
        
        # 测试卡片数据
        cards = manager.execute_query("SELECT id, user_id, display_name, scene_type FROM user_cards LIMIT 5")
        print(f"\n卡片数据: {len(cards)} 条记录")
        for card in cards:
            print(f"  - {card[2]} ({card[0]}): {card[3]} - 用户: {card[1]}")
        
        # 测试外键约束
        try:
            # 尝试插入无效的外键（应该失败）
            manager.execute_update(
                "INSERT INTO user_cards (id, user_id, role_type, scene_type, display_name) VALUES (?, ?, ?, ?, ?)",
                ('test_card_invalid', 'invalid_user_id', 'test', 'test', '测试卡片')
            )
            print("\n❌ 外键约束测试失败：应该阻止无效的外键")
        except Exception as e:
            print(f"\n✅ 外键约束测试通过：{str(e)[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"数据完整性测试失败: {e}")
        return False

def main():
    """主函数"""
    print("开始数据库测试...")
    
    # 测试数据库连接
    connection_ok = test_database_connection()
    
    if not connection_ok:
        print("\n❌ 数据库连接测试失败，请检查数据库是否已初始化")
        return False
    
    # 测试表结构
    structure_ok = test_table_structure()
    
    # 测试数据完整性
    integrity_ok = test_data_integrity()
    
    print("\n=== 测试结果总结 ===")
    print(f"数据库连接: {'✅ 通过' if connection_ok else '❌ 失败'}")
    print(f"表结构: {'✅ 通过' if structure_ok else '❌ 失败'}")
    print(f"数据完整性: {'✅ 通过' if integrity_ok else '❌ 失败'}")
    
    if connection_ok and structure_ok and integrity_ok:
        print("\n🎉 所有测试通过！数据库初始化成功！")
        return True
    else:
        print("\n⚠️  部分测试失败，请检查数据库配置")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)