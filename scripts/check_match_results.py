#!/usr/bin/env python3
"""
检查 MatchResult 表中的数据
"""

import sqlite3
import os
import json
from datetime import datetime

def check_match_results():
    """检查 MatchResult 表中的数据"""
    db_path = 'vmatch_dev.db'
    if not os.path.exists(db_path):
        print(f"开发数据库文件 {db_path} 不存在")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # 使查询结果可以按列名访问
        cursor = conn.cursor()
        
        print(f"=== 检查数据库: {db_path} ===")
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='match_results'")
        if not cursor.fetchone():
            print("match_results 表不存在")
            return
        
        print("✓ match_results 表存在")
        
        # 获取总记录数
        cursor.execute("SELECT COUNT(*) as count FROM match_results")
        total_count = cursor.fetchone()['count']
        print(f"总记录数: {total_count}")
        
        if total_count == 0:
            print("表中没有数据")
            return
        
        # 按匹配状态统计
        print("\n=== 按匹配状态统计 ===")
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM match_results 
            GROUP BY status 
            ORDER BY count DESC
        """)
        status_stats = cursor.fetchall()
        for row in status_stats:
            print(f"  {row['status']}: {row['count']}")
        
        # 按场景类型统计
        print("\n=== 按场景类型统计 ===")
        cursor.execute("""
            SELECT scene_type, COUNT(*) as count 
            FROM match_results 
            GROUP BY scene_type 
            ORDER BY count DESC
        """)
        scene_stats = cursor.fetchall()
        for row in scene_stats:
            print(f"  {row['scene_type']}: {row['count']}")
        
        # 按活跃状态统计
        print("\n=== 按活跃状态统计 ===")
        cursor.execute("""
            SELECT is_active, COUNT(*) as count 
            FROM match_results 
            GROUP BY is_active
        """)
        active_stats = cursor.fetchall()
        for row in active_stats:
            status = "活跃" if row['is_active'] else "不活跃"
            print(f"  {status}: {row['count']}")
        
        # 最新5条记录详情
        print("\n=== 最新5条记录详情 ===")
        cursor.execute("""
            SELECT 
                id, user1_id, user2_id, user1_card_id, user2_card_id,
                scene_type, status, is_active, matched_at, last_activity_at
            FROM match_results
            ORDER BY matched_at DESC
            LIMIT 5
        """)
        latest_records = cursor.fetchall()
        
        for i, row in enumerate(latest_records, 1):
            print(f"\n记录 {i}:")
            print(f"  ID: {row['id']}")
            print(f"  用户1ID: {row['user1_id']}")
            print(f"  用户2ID: {row['user2_id']}")
            print(f"  用户1卡片ID: {row['user1_card_id']}")
            print(f"  用户2卡片ID: {row['user2_card_id']}")
            print(f"  场景类型: {row['scene_type']}")
            print(f"  状态: {row['status']}")
            print(f"  活跃状态: {'活跃' if row['is_active'] else '不活跃'}")
            print(f"  匹配时间: {row['matched_at']}")
            if row['last_activity_at']:
                print(f"  最后活动时间: {row['last_activity_at']}")
        
        # 检查表结构
        print("\n=== 表结构详情 ===")
        cursor.execute("PRAGMA table_info(match_results)")
        columns = cursor.fetchall()
        
        print(f"总字段数: {len(columns)}")
        print("字段详情：")
        for col in columns:
            col_name = col['name']
            col_type = col['type']
            nullable = "可空" if col['notnull'] == 0 else "非空"
            default = f"默认值: {col['dflt_value']}" if col['dflt_value'] is not None else "无默认值"
            print(f"  {col_name}: {col_type} ({nullable}, {default})")
        
        # 获取索引
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='match_results'")
        indexes = cursor.fetchall()
        
        print(f"\n索引数: {len(indexes)}")
        for idx in indexes:
            if idx['sql']:
                print(f"  {idx['name']}: {idx['sql']}")
            else:
                print(f"  {idx['name']}")
        
        conn.close()
        
    except Exception as e:
        print(f"检查失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_match_results()