#!/usr/bin/env python3
"""
删除测试卡片数据脚本
用于清理数据库中的测试用卡片数据
"""

import sys
import os
from pathlib import Path
import sqlite3
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def get_db_path():
    """获取数据库路径"""
    # 默认使用项目根目录下的数据库文件
    default_db = os.path.join(Path(__file__).parent.parent, "vmatch_dev.db")
    
    # 检查环境变量
    db_url = os.getenv("DATABASE_URL", "")
    if db_url and "sqlite" in db_url:
        # 从URL中提取路径
        db_path = db_url.replace("sqlite:///", "")
        # 处理相对路径
        if not os.path.isabs(db_path):
            db_path = os.path.join(Path(__file__).parent.parent, db_path)
        return db_path
    
    return default_db

def identify_test_cards(conn):
    """识别测试卡片数据"""
    cursor = conn.cursor()
    
    # 定义测试数据的识别条件
    test_conditions = [
        # 条件1: 显示名称包含测试字样
        "display_name LIKE '%测试%'",
        # 条件2: 显示名称包含 test 字样（不区分大小写）
        "LOWER(display_name) LIKE '%test%'",
        # 条件3: 卡片ID格式符合测试模式
        "id LIKE 'card_test_%'",
        # 条件4: 简介中包含测试字样
        "bio LIKE '%测试%'",
        # 条件5: 简介中包含 test 字样（不区分大小写）
        "LOWER(bio) LIKE '%test%'",
        # 条件6: 搜索代码包含测试字样
        "search_code LIKE '%test%'",
        # 条件7: 用户ID可能是测试用户（包含test或测试）
        "user_id IN (SELECT id FROM users WHERE nick_name LIKE '%测试%' OR LOWER(nick_name) LIKE '%test%')"
    ]
    
    # 构建查询语句
    where_clause = " OR ".join(test_conditions)
    query = f"""
        SELECT id, user_id, display_name, scene_type, role_type, bio, search_code, created_at
        FROM user_cards 
        WHERE ({where_clause}) AND is_deleted = 0
        ORDER BY created_at DESC
    """
    
    cursor.execute(query)
    return cursor.fetchall()

def delete_cards_by_ids(conn, card_ids):
    """根据ID列表删除卡片（软删除）"""
    if not card_ids:
        return 0
    
    cursor = conn.cursor()
    
    # 使用参数化查询防止SQL注入
    placeholders = ",".join(["?" for _ in card_ids])
    
    # 执行软删除（将is_deleted设置为1）
    query = f"UPDATE user_cards SET is_deleted = 1, updated_at = ? WHERE id IN ({placeholders})"
    
    # 获取当前时间
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute(query, [current_time] + card_ids)
    
    return cursor.rowcount

def show_deletion_summary(conn, deleted_count):
    """显示删除摘要"""
    cursor = conn.cursor()
    
    # 获取当前统计信息
    cursor.execute("SELECT COUNT(*) FROM user_cards WHERE is_deleted = 0")
    active_cards = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM user_cards WHERE is_deleted = 1")
    deleted_cards = cursor.fetchone()[0]
    
    print(f"\n=== 删除摘要 ===")
    print(f"本次删除的卡片数量: {deleted_count}")
    print(f"剩余活跃卡片数量: {active_cards}")
    print(f"已删除卡片总数: {deleted_cards}")

def confirm_deletion(test_cards):
    """确认是否删除测试卡片"""
    if not test_cards:
        print("未找到测试卡片数据")
        return False
    
    print(f"\n找到 {len(test_cards)} 个可能是测试的卡片:")
    print("-" * 80)
    
    # 显示前10个卡片的信息
    for i, card in enumerate(test_cards[:10]):
        card_id, user_id, display_name, scene_type, role_type, bio, search_code, created_at = card
        print(f"{i+1:2d}. ID: {card_id}")
        print(f"    用户ID: {user_id}")
        print(f"    显示名称: {display_name}")
        print(f"    场景类型: {scene_type}, 角色类型: {role_type}")
        if bio:
            print(f"    简介: {bio[:50]}{'...' if len(bio) > 50 else ''}")
        if search_code:
            print(f"    搜索代码: {search_code}")
        print(f"    创建时间: {created_at}")
        print()
    
    if len(test_cards) > 10:
        print(f"... 还有 {len(test_cards) - 10} 个卡片未显示")
    
    # 确认删除
    while True:
        response = input(f"是否删除这 {len(test_cards)} 个卡片? (yes/no): ").strip().lower()
        if response in ['yes', 'y']:
            return True
        elif response in ['no', 'n']:
            return False
        else:
            print("请输入 'yes' 或 'no'")

def main():
    """主函数"""
    print("=== 删除测试卡片数据脚本 ===")
    
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
        
        print("正在识别测试卡片数据...")
        
        # 识别测试卡片
        test_cards = identify_test_cards(conn)
        
        if not test_cards:
            print("未找到测试卡片数据")
            return True
        
        # 确认删除
        if not confirm_deletion(test_cards):
            print("取消删除操作")
            return True
        
        # 提取卡片ID
        card_ids = [card[0] for card in test_cards]
        
        print(f"\n正在删除 {len(card_ids)} 个测试卡片...")
        
        # 执行删除
        deleted_count = delete_cards_by_ids(conn, card_ids)
        
        # 提交事务
        conn.commit()
        
        print(f"成功删除 {deleted_count} 个测试卡片")
        
        # 显示删除摘要
        show_deletion_summary(conn, deleted_count)
        
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