#!/usr/bin/env python3
"""
快速清理测试数据脚本
一键清理数据库中的测试卡片数据
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

def quick_cleanup_test_cards():
    """快速清理测试卡片"""
    db_path = get_db_path()
    
    print("=== 快速清理测试卡片 ===")
    print(f"数据库路径: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"错误: 数据库文件不存在: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 查询测试卡片
        query = """
            SELECT id, display_name, bio, user_id, created_at
            FROM user_cards 
            WHERE (
                display_name LIKE '%测试%' OR
                LOWER(display_name) LIKE '%test%' OR
                bio LIKE '%测试%' OR
                LOWER(bio) LIKE '%test%' OR
                search_code LIKE '%test%' OR
                id LIKE 'card_test_%'
            ) AND is_deleted = 0
            ORDER BY created_at DESC
        """
        
        cursor.execute(query)
        test_cards = cursor.fetchall()
        
        if not test_cards:
            print("未找到测试卡片数据")
            return True
        
        print(f"找到 {len(test_cards)} 个测试卡片:")
        
        # 显示要删除的卡片
        for i, card in enumerate(test_cards[:5]):
            print(f"  {i+1}. {card[1]} (ID: {card[0]})")
            if len(card[2] or '') > 0:
                bio_preview = card[2][:30] + '...' if len(card[2]) > 30 else card[2]
                print(f"     简介: {bio_preview}")
        
        if len(test_cards) > 5:
            print(f"  ... 还有 {len(test_cards) - 5} 个")
        
        # 确认删除
        response = input(f"\n是否删除这 {len(test_cards)} 个测试卡片? (yes/no): ").strip().lower()
        if response not in ['yes', 'y']:
            print("取消删除操作")
            return True
        
        # 执行删除（软删除）
        card_ids = [card[0] for card in test_cards]
        placeholders = ",".join(["?" for _ in card_ids])
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        delete_query = f"""
            UPDATE user_cards 
            SET is_deleted = 1, updated_at = ? 
            WHERE id IN ({placeholders}) AND is_deleted = 0
        """
        
        cursor.execute(delete_query, [current_time] + card_ids)
        deleted_count = cursor.rowcount
        
        # 提交事务
        conn.commit()
        
        print(f"\n✅ 成功删除 {deleted_count} 个测试卡片")
        
        # 显示剩余统计
        cursor.execute("SELECT COUNT(*) FROM user_cards WHERE is_deleted = 0")
        remaining_cards = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM user_cards WHERE is_deleted = 1")
        total_deleted = cursor.fetchone()[0]
        
        print(f"\n剩余活跃卡片: {remaining_cards}")
        print(f"已删除卡片总数: {total_deleted}")
        
        return True
        
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
        return False
        
    except Exception as e:
        print(f"发生错误: {e}")
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

def show_current_stats():
    """显示当前数据库统计"""
    db_path = get_db_path()
    
    if not os.path.exists(db_path):
        print("数据库文件不存在")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取统计信息
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM user_cards WHERE is_deleted = 0")
        active_cards = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM user_cards WHERE is_deleted = 1")
        deleted_cards = cursor.fetchone()[0]
        
        # 检查其他表是否存在is_deleted列
        try:
            cursor.execute("SELECT COUNT(*) FROM match_results WHERE is_deleted = 0")
            match_count = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            # 如果没有is_deleted列，直接统计总数
            cursor.execute("SELECT COUNT(*) FROM match_results")
            match_count = cursor.fetchone()[0]
        
        print("\n=== 当前数据库统计 ===")
        print(f"用户数量: {user_count}")
        print(f"活跃卡片: {active_cards}")
        print(f"已删除卡片: {deleted_cards}")
        print(f"匹配记录: {match_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"获取统计信息失败: {e}")

def main():
    """主函数"""
    print("=== 快速测试数据清理工具 ===")
    
    # 显示当前统计
    show_current_stats()
    
    # 执行清理
    success = quick_cleanup_test_cards()
    
    if success:
        print("\n清理完成！")
        show_current_stats()
    else:
        print("\n清理失败！")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())