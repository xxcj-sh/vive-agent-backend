#!/usr/bin/env python3
"""
检查开发数据库用户表结构
"""

import sqlite3
import os

def check_dev_db_structure():
    """检查开发数据库用户表结构"""
    db_path = 'vmatch_dev.db'
    if not os.path.exists(db_path):
        print(f"数据库文件 {db_path} 不存在")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=== 开发数据库用户表结构 ===")
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("用户表不存在")
            conn.close()
            return
        
        # 获取所有字段
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        print(f"总字段数: {len(columns)}")
        print("字段详情：")
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            nullable = "可空" if col[3] == 0 else "非空"
            default = f"默认值: {col[4]}" if col[4] is not None else "无默认值"
            print(f"  {col_name}: {col_type} ({nullable}, {default})")
        
        # 获取索引
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='users'")
        indexes = cursor.fetchall()
        
        print(f"\n索引数: {len(indexes)}")
        for idx in indexes:
            print(f"  {idx[0]}")
        
        conn.close()
        
    except Exception as e:
        print(f"检查失败: {e}")

if __name__ == "__main__":
    check_dev_db_structure()