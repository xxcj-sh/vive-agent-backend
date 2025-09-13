#!/usr/bin/env python3
"""
手动应用 match_actions 表结构更新

这个脚本会检查并更新 match_actions 和 match_results 表结构，
添加新字段和索引以支持 AI 推荐功能。
"""

import sqlite3
import os
import sys
from pathlib import Path

# 添加到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_and_update_match_actions():
    """检查并更新 match_actions 表结构"""
    db_path = project_root / "vmatch_dev.db"
    
    if not db_path.exists():
        print(f"数据库文件不存在: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查现有列
        cursor.execute("PRAGMA table_info(match_actions)")
        existing_columns = {row[1]: row for row in cursor.fetchall()}
        
        print("=== 当前 match_actions 表结构 ===")
        for col_name in sorted(existing_columns.keys()):
            print(f"- {col_name}")
        
        # 重命名 match_type 为 scene_type
        if "match_type" in existing_columns and "scene_type" not in existing_columns:
            print("重命名 match_type 为 scene_type...")
            cursor.execute("ALTER TABLE match_actions RENAME COLUMN match_type TO scene_type")
        elif "scene_type" in existing_columns:
            print("scene_type 字段已存在")
        
        # 检查 match_results 表的字段
        cursor.execute("PRAGMA table_info(match_results)")
        match_result_columns = {row[1]: row for row in cursor.fetchall()}
        
        if "match_type" in match_result_columns and "scene_type" not in match_result_columns:
            print("在 match_results 重命名 match_type 为 scene_type...")
            cursor.execute("ALTER TABLE match_results RENAME COLUMN match_type TO scene_type")
        elif "scene_type" in match_result_columns:
            print("match_results 中 scene_type 字段已存在")
        
        # 重命名 metadata 为 extra（只在 match_actions 表中）
        if "metadata" in existing_columns and "extra" not in existing_columns:
            print("重命名 metadata 为 extra...")
            cursor.execute("ALTER TABLE match_actions RENAME COLUMN metadata TO extra")
        elif "extra" in existing_columns and "metadata" not in existing_columns:
            print("extra 字段已存在")
        elif "metadata" in existing_columns and "extra" in existing_columns:
            # 如果两个字段都存在，删除 metadata 字段
            print("删除多余的 metadata 字段...")
            cursor.execute("ALTER TABLE match_actions DROP COLUMN metadata")
        
        # 添加缺失的新字段
        cursor.execute("PRAGMA table_info(match_actions)")
        updated_columns = {row[1] for row in cursor.fetchall()}
        
        new_columns = [
            ("source", "TEXT DEFAULT 'user'"),
            ("is_processed", "INTEGER DEFAULT 0"),
            ("processed_at", "DATETIME"),
            ("extra", "TEXT"),
        ]
        
        for col_name, col_def in new_columns:
            if col_name not in updated_columns:
                print(f"添加列: {col_name}")
                cursor.execute(f"ALTER TABLE match_actions ADD COLUMN {col_name} {col_def}")
            else:
                print(f"列已存在: {col_name}")
        
        # 更新 match_results 表的新字段
        cursor.execute("PRAGMA table_info(match_results)")
        match_result_updated_columns = {row[1] for row in cursor.fetchall()}
        
        new_match_result_columns = [
            ("first_message_at", "DATETIME"),
            ("is_blocked", "INTEGER DEFAULT 0"),
            ("expiry_date", "DATETIME"),
        ]
        
        for col_name, col_def in new_match_result_columns:
            if col_name not in match_result_updated_columns:
                print(f"在 match_results 添加列: {col_name}")
                cursor.execute(f"ALTER TABLE match_results ADD COLUMN {col_name} {col_def}")
            else:
                print(f"match_results 列已存在: {col_name}")
        
        conn.commit()
        
        # 验证更新结果
        cursor.execute("PRAGMA table_info(match_actions)")
        final_columns = {row[1] for row in cursor.fetchall()}
        print("\n=== 最终 match_actions 表结构 ===")
        for col in sorted(final_columns):
            print(f"- {col}")
            
        cursor.execute("PRAGMA table_info(match_results)")
        final_match_result_columns = {row[1] for row in cursor.fetchall()}
        print("\n=== 最终 match_results 表结构 ===")
        for col in sorted(final_match_result_columns):
            print(f"- {col}")
            
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"更新过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("开始更新 match_actions 表结构并处理字段重命名...")
    success = check_and_update_match_actions()
    if success:
        print("\n✅ 表结构更新和字段重命名成功完成！")
    else:
        print("\n❌ 表结构更新失败！")