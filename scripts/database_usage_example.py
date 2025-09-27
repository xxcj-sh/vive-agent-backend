#!/usr/bin/env python3
"""
数据库使用示例
展示如何使用数据库配置和工具模块
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database_config import get_db_manager, get_db_config
from app.core.database_config import DatabaseConfig, DatabaseManager

def example_basic_usage():
    """基本使用示例"""
    print("=== 基本使用示例 ===")
    
    # 获取默认的数据库管理器
    manager = get_db_manager()
    config = get_db_config()
    
    print(f"数据库路径: {config.db_path}")
    print(f"数据库存在: {config.database_exists()}")
    print(f"数据库大小: {config.get_db_size_mb():.2f} MB")
    
    # 获取数据库统计信息
    stats = manager.get_database_stats()
    print(f"表数量: {stats['table_count']}")
    print(f"索引数量: {stats['index_count']}")
    
    return True

def example_query_data():
    """查询数据示例"""
    print("\n=== 查询数据示例 ===")
    
    manager = get_db_manager()
    
    # 查询用户数据
    users = manager.execute_query(
        "SELECT id, nick_name, phone, created_at FROM users LIMIT 5"
    )
    
    print("用户数据:")
    for user in users:
        user_id, nick_name, phone, created_at = user
        print(f"  - {nick_name} ({user_id}): {phone}")
    
    # 查询卡片数据
    cards = manager.execute_query("""
        SELECT uc.id, uc.display_name, uc.scene_type, u.nick_name 
        FROM user_cards uc 
        JOIN users u ON uc.user_id = u.id 
        LIMIT 5
    """)
    
    print("\n卡片数据:")
    for card in cards:
        card_id, display_name, scene_type, user_name = card
        print(f"  - {display_name} ({card_id}): {scene_type} - 创建者: {user_name}")
    
    return True

def example_insert_data():
    """插入数据示例"""
    print("\n=== 插入数据示例 ===")
    
    manager = get_db_manager()
    
    # 插入新用户
    new_user_id = f"demo_user_{int(datetime.now().timestamp())}"
    result = manager.execute_update(
        """INSERT INTO users (id, phone, nick_name, age, bio, occupation, location, status, is_active) 
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (new_user_id, "13800138099", "演示用户", 25, "这是一个演示用户", "软件工程师", "北京", "active", 1)
    )
    
    print(f"插入用户结果: 影响 {result} 行")
    
    # 插入新卡片
    new_card_id = f"demo_card_{int(datetime.now().timestamp())}"
    result = manager.execute_update(
        """INSERT INTO user_cards (id, user_id, role_type, scene_type, display_name, bio, is_active) 
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (new_card_id, new_user_id, "demo_provider", "demo", "演示卡片", "这是一个演示卡片", 1)
    )
    
    print(f"插入卡片结果: 影响 {result} 行")
    
    # 验证插入的数据
    user = manager.execute_query("SELECT nick_name, phone FROM users WHERE id = ?", (new_user_id,))
    if user:
        print(f"验证用户: {user[0][0]} - {user[0][1]}")
    
    return True

def example_update_data():
    """更新数据示例"""
    print("\n=== 更新数据示例 ===")
    
    manager = get_db_manager()
    
    # 更新用户状态
    result = manager.execute_update(
        "UPDATE users SET status = ?, updated_at = datetime('now') WHERE status = ?",
        ("inactive", "pending")
    )
    
    print(f"更新用户状态: 影响 {result} 行")
    
    # 更新卡片可见性
    result = manager.execute_update(
        "UPDATE user_cards SET visibility = ? WHERE visibility = ?",
        ("private", "public")
    )
    
    print(f"更新卡片可见性: 影响 {result} 行")
    
    return True

def example_delete_data():
    """删除数据示例（谨慎使用）"""
    print("\n=== 删除数据示例 ===")
    
    manager = get_db_manager()
    
    # 软删除（标记为已删除）
    result = manager.execute_update(
        "UPDATE user_cards SET is_deleted = 1, is_active = 0 WHERE display_name LIKE '%演示%'",
        ()
    )
    
    print(f"软删除演示卡片: 影响 {result} 行")
    
    return True

def example_custom_config():
    """自定义配置示例"""
    print("\n=== 自定义配置示例 ===")
    
    # 创建自定义数据库配置
    custom_db_path = Path(__file__).parent / "custom_demo.db"
    custom_config = DatabaseConfig(custom_db_path)
    custom_manager = DatabaseManager(custom_config)
    
    print(f"自定义数据库路径: {custom_config.db_path}")
    
    # 在自定义数据库中执行操作
    try:
        # 创建表（简化版）
        custom_manager.execute_update("""
            CREATE TABLE IF NOT EXISTS demo_table (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 插入数据
        custom_manager.execute_update(
            "INSERT INTO demo_table (name) VALUES (?)",
            ("演示数据",)
        )
        
        # 查询数据
        results = custom_manager.execute_query("SELECT * FROM demo_table")
        print(f"自定义数据库数据: {results}")
        
        # 清理
        if custom_config.db_path.exists():
            custom_config.db_path.unlink()
            print("已清理自定义数据库文件")
        
    except Exception as e:
        print(f"自定义数据库操作失败: {e}")
    
    return True

def example_transaction():
    """事务处理示例"""
    print("\n=== 事务处理示例 ===")
    
    manager = get_db_manager()
    
    try:
        # 手动管理事务（使用上下文管理器）
        with manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 开始事务
            cursor.execute("BEGIN TRANSACTION")
            
            # 执行多个操作
            cursor.execute(
                "INSERT INTO users (id, phone, nick_name, status, is_active) VALUES (?, ?, ?, ?, ?)",
                ("trans_user_001", "13800138111", "事务用户", "active", 1)
            )
            
            cursor.execute(
                "INSERT INTO user_cards (id, user_id, role_type, scene_type, display_name, is_active) VALUES (?, ?, ?, ?, ?, ?)",
                ("trans_card_001", "trans_user_001", "trans_provider", "trans", "事务卡片", 1)
            )
            
            # 提交事务
            conn.commit()
            print("事务提交成功")
            
    except Exception as e:
        print(f"事务处理失败: {e}")
        # 事务会自动回滚
    
    return True

def main():
    """主函数"""
    print("数据库使用示例开始...")
    print("=" * 50)
    
    try:
        # 运行所有示例
        example_basic_usage()
        example_query_data()
        example_insert_data()
        example_update_data()
        example_delete_data()
        example_custom_config()
        example_transaction()
        
        print("\n" + "=" * 50)
        print("✅ 所有示例执行完成！")
        
    except Exception as e:
        print(f"\n❌ 示例执行失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)