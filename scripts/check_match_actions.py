#!/usr/bin/env python3
"""
检查 MatchAction 表中的数据
"""

import sqlite3
import os
import json
from datetime import datetime

def check_match_actions():
    """检查 MatchAction 表中的数据"""
    db_path = 'vmatch.db'
    if not os.path.exists(db_path):
        print(f"主数据库文件 {db_path} 不存在，尝试检查开发数据库...")
        db_path = 'vmatch_dev.db'
        if not os.path.exists(db_path):
            print(f"开发数据库文件 {db_path} 也不存在")
            return
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # 使查询结果可以按列名访问
        cursor = conn.cursor()
        
        print(f"=== 检查数据库: {db_path} ===")
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='match_actions'")
        if not cursor.fetchone():
            print("match_actions 表不存在")
            return
        
        print("✓ match_actions 表存在")
        
        # 获取总记录数
        cursor.execute("SELECT COUNT(*) as count FROM match_actions")
        total_count = cursor.fetchone()['count']
        print(f"总记录数: {total_count}")
        
        if total_count == 0:
            print("表中没有数据")
            return
        
        # 按操作类型统计
        print("\n=== 按操作类型统计 ===")
        cursor.execute("""
            SELECT action_type, COUNT(*) as count 
            FROM match_actions 
            GROUP BY action_type 
            ORDER BY count DESC
        """)
        action_stats = cursor.fetchall()
        for row in action_stats:
            print(f"  {row['action_type']}: {row['count']}")
        
        # 按场景类型统计
        print("\n=== 按场景类型统计 ===")
        cursor.execute("""
            SELECT scene_type, COUNT(*) as count 
            FROM match_actions 
            GROUP BY scene_type 
            ORDER BY count DESC
        """)
        scene_stats = cursor.fetchall()
        for row in scene_stats:
            print(f"  {row['scene_type']}: {row['count']}")
        
        # 按来源统计
        print("\n=== 按来源统计 ===")
        cursor.execute("""
            SELECT source, COUNT(*) as count 
            FROM match_actions 
            GROUP BY source 
            ORDER BY count DESC
        """)
        source_stats = cursor.fetchall()
        for row in source_stats:
            print(f"  {row['source']}: {row['count']}")
        
        # 按处理状态统计
        print("\n=== 按处理状态统计 ===")
        cursor.execute("""
            SELECT is_processed, COUNT(*) as count 
            FROM match_actions 
            GROUP BY is_processed
        """)
        processed_stats = cursor.fetchall()
        for row in processed_stats:
            status = "已处理" if row['is_processed'] else "未处理"
            print(f"  {status}: {row['count']}")
        
        # 最新10条记录详情
        print("\n=== 最新10条记录详情 ===")
        cursor.execute("""
            SELECT 
                id, user_id, target_user_id, target_card_id,
                action_type, scene_type, source, is_processed,
                created_at, updated_at, scene_context, extra
            FROM match_actions
            ORDER BY created_at DESC
            LIMIT 10
        """)
        latest_records = cursor.fetchall()
        
        for i, row in enumerate(latest_records, 1):
            print(f"\n记录 {i}:")
            print(f"  ID: {row['id']}")
            print(f"  用户ID: {row['user_id']}")
            print(f"  目标用户ID: {row['target_user_id']}")
            print(f"  目标卡片ID: {row['target_card_id']}")
            print(f"  操作类型: {row['action_type']}")
            print(f"  场景类型: {row['scene_type']}")
            print(f"  来源: {row['source']}")
            print(f"  处理状态: {'已处理' if row['is_processed'] else '未处理'}")
            print(f"  创建时间: {row['created_at']}")
            if row['updated_at'] and row['updated_at'] != row['created_at']:
                print(f"  更新时间: {row['updated_at']}")
            if row['scene_context']:
                try:
                    context = json.loads(row['scene_context'])
                    print(f"  场景上下文: {json.dumps(context, ensure_ascii=False, indent=2)}")
                except:
                    print(f"  场景上下文: {row['scene_context']}")
            if row['extra']:
                try:
                    extra = json.loads(row['extra'])
                    print(f"  额外数据: {json.dumps(extra, ensure_ascii=False, indent=2)}")
                except:
                    print(f"  额外数据: {row['extra']}")
        
        # 检查表结构
        print("\n=== 表结构详情 ===")
        cursor.execute("PRAGMA table_info(match_actions)")
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
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='match_actions'")
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
    check_match_actions()