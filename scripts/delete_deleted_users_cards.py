#!/usr/bin/env python3
"""
删除已注销用户的卡片脚本

这个脚本用于删除数据库中已注销用户（status = 'deleted'）的所有卡片。
执行软删除操作，将卡片的 is_deleted 字段设置为 1。

使用方法:
    python scripts/delete_deleted_users_cards.py [--dry-run] [--verbose]

参数:
    --dry-run:  干运行模式，只显示将要删除的卡片，不实际执行删除操作
    --verbose:  显示详细信息
    --help:     显示帮助信息

注意事项:
    - 执行前建议备份数据库
    - 此操作不可逆，请谨慎执行
    - 生产环境使用前请在测试环境验证
"""

import os
import sys
import sqlite3
from datetime import datetime
from typing import List, Tuple, Optional
import argparse

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_db_path() -> str:
    """获取数据库文件路径"""
    # 检查常见位置
    possible_paths = [
        'vmatch_dev.db',  # 开发环境
        'vmatch.db',      # 生产环境
        os.path.join('app', 'data', 'vmatch.db'),  # 其他可能位置
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # 如果都不存在，返回默认路径
    return 'vmatch_dev.db'

def get_deleted_users(conn: sqlite3.Connection) -> List[Tuple]:
    """获取所有已注销的用户"""
    cursor = conn.cursor()
    
    query = """
        SELECT id, phone, nick_name, status, created_at, updated_at
        FROM users 
        WHERE status = 'deleted'
        ORDER BY updated_at DESC
    """
    
    cursor.execute(query)
    return cursor.fetchall()

def get_user_cards(conn: sqlite3.Connection, user_id: str) -> List[Tuple]:
    """获取指定用户的所有卡片"""
    cursor = conn.cursor()
    
    query = """
        SELECT uc.id, uc.display_name, uc.scene_type, uc.role_type, 
               uc.bio, uc.is_active, uc.is_deleted, uc.created_at, uc.updated_at,
               u.nick_name as user_nick_name, u.phone as user_phone
        FROM user_cards uc
        JOIN users u ON uc.user_id = u.id
        WHERE uc.user_id = ? AND uc.is_deleted = 0
        ORDER BY uc.created_at DESC
    """
    
    cursor.execute(query, (user_id,))
    return cursor.fetchall()

def soft_delete_cards(conn: sqlite3.Connection, card_ids: List[str]) -> int:
    """软删除指定的卡片"""
    if not card_ids:
        return 0
    
    cursor = conn.cursor()
    
    # 使用参数化查询防止SQL注入
    placeholders = ",".join(["?" for _ in card_ids])
    
    # 执行软删除（将is_deleted设置为1）
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    query = f"""
        UPDATE user_cards 
        SET is_deleted = 1, updated_at = ? 
        WHERE id IN ({placeholders}) AND is_deleted = 0
    """
    
    cursor.execute(query, [current_time] + card_ids)
    return cursor.rowcount

def show_deletion_summary(conn: sqlite3.Connection, deleted_count: int, affected_users: int):
    """显示删除摘要"""
    cursor = conn.cursor()
    
    # 获取当前统计信息
    cursor.execute("SELECT COUNT(*) FROM users WHERE status = 'deleted'")
    deleted_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM user_cards WHERE is_deleted = 0")
    active_cards = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM user_cards WHERE is_deleted = 1")
    total_deleted = cursor.fetchone()[0]
    
    print(f"\n=== 删除摘要 ===")
    print(f"已注销用户总数: {deleted_users}")
    print(f"本次删除的卡片数量: {deleted_count}")
    print(f"受影响的用户数量: {affected_users}")
    print(f"剩余活跃卡片: {active_cards}")
    print(f"已删除卡片总数: {total_deleted}")

def confirm_deletion(cards_to_delete: List[Tuple], deleted_users: List[Tuple]) -> bool:
    """确认是否删除卡片"""
    if not cards_to_delete:
        print("未找到需要删除的卡片")
        return False
    
    print(f"\n找到 {len(cards_to_delete)} 个属于已注销用户的卡片:")
    print("=" * 100)
    
    # 按用户分组显示卡片
    user_cards_map = {}
    for card in cards_to_delete:
        user_nick_name = card[9]  # 用户昵称
        user_phone = card[10]     # 用户手机号
        user_key = f"{user_nick_name} ({user_phone})"
        
        if user_key not in user_cards_map:
            user_cards_map[user_key] = []
        user_cards_map[user_key].append(card)
    
    # 显示每个用户的卡片
    for user_key, user_cards in user_cards_map.items():
        print(f"\n用户: {user_key}")
        print(f"卡片数量: {len(user_cards)}")
        print("-" * 80)
        
        # 显示前3个卡片的信息
        for i, card in enumerate(user_cards[:3]):
            card_id, display_name, scene_type, role_type, bio, is_active, is_deleted, created_at, updated_at, user_nick_name, user_phone = card
            print(f"  {i+1}. 卡片ID: {card_id}")
            print(f"     显示名称: {display_name}")
            print(f"     场景类型: {scene_type}")
            print(f"     角色类型: {role_type}")
            if bio:
                print(f"     简介: {bio[:50]}{'...' if len(bio) > 50 else ''}")
            print(f"     状态: {'活跃' if is_active else '非活跃'}")
            print(f"     创建时间: {created_at}")
            print()
        
        if len(user_cards) > 3:
            print(f"     ... 还有 {len(user_cards) - 3} 个卡片未显示")
    
    # 确认删除
    while True:
        response = input(f"\n是否删除这 {len(cards_to_delete)} 个卡片? (yes/no): ").strip().lower()
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        else:
            print("请输入 'yes' 或 'no'")

def main():
    """主函数"""
    print("=== 删除已注销用户的卡片脚本 ===")
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='删除已注销用户的卡片')
    parser.add_argument('--dry-run', action='store_true', help='干运行模式，只显示不删除')
    parser.add_argument('--verbose', action='store_true', help='显示详细信息')
    args = parser.parse_args()
    
    try:
        # 获取数据库路径
        db_path = get_db_path()
        print(f"数据库路径: {db_path}")
        
        # 检查数据库文件是否存在
        if not os.path.exists(db_path):
            print(f"错误: 数据库文件不存在: {db_path}")
            return False
        
        # 连接数据库
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # 使查询结果可以通过列名访问
        
        print("正在查找已注销的用户...")
        
        # 获取已注销的用户
        deleted_users = get_deleted_users(conn)
        
        if not deleted_users:
            print("未找到已注销的用户")
            return True
        
        print(f"找到 {len(deleted_users)} 个已注销的用户")
        
        if args.verbose:
            print("\n已注销用户列表:")
            for i, user in enumerate(deleted_users):
                print(f"  {i+1}. ID: {user[0]}, 手机号: {user[1]}, 昵称: {user[2] or 'N/A'}")
        
        # 收集所有需要删除的卡片
        all_cards_to_delete = []
        affected_users_count = 0
        
        for user in deleted_users:
            user_id = user[0]
            user_cards = get_user_cards(conn, user_id)
            
            if user_cards:
                affected_users_count += 1
                all_cards_to_delete.extend(user_cards)
                
                if args.verbose:
                    print(f"用户 {user[1]} 有 {len(user_cards)} 个卡片需要删除")
        
        if not all_cards_to_delete:
            print("未找到需要删除的卡片")
            return True
        
        print(f"\n总共找到 {len(all_cards_to_delete)} 个属于已注销用户的卡片")
        
        # 干运行模式
        if args.dry_run:
            print("\n=== 干运行模式 ===")
            print("以下卡片将被删除（实际未执行删除操作）:")
            for i, card in enumerate(all_cards_to_delete[:10]):  # 只显示前10个
                card_id, display_name, scene_type, role_type, bio, is_active, is_deleted, created_at, updated_at, user_nick_name, user_phone = card
                print(f"  {i+1}. 卡片ID: {card_id}, 名称: {display_name}, 用户: {user_nick_name}")
            
            if len(all_cards_to_delete) > 10:
                print(f"  ... 还有 {len(all_cards_to_delete) - 10} 个卡片")
            
            print(f"\n干运行完成，共 {len(all_cards_to_delete)} 个卡片将被删除")
            return True
        
        # 确认删除
        if not confirm_deletion(all_cards_to_delete, deleted_users):
            print("取消删除操作")
            return True
        
        # 提取卡片ID
        card_ids = [card[0] for card in all_cards_to_delete]
        
        print(f"\n正在删除 {len(card_ids)} 个卡片...")
        
        # 执行删除
        deleted_count = soft_delete_cards(conn, card_ids)
        
        # 提交事务
        conn.commit()
        
        print(f"成功删除 {deleted_count} 个卡片")
        
        # 显示删除摘要
        show_deletion_summary(conn, deleted_count, affected_users_count)
        
        return True
        
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
        
    except Exception as e:
        print(f"发生错误: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)