#!/usr/bin/env python3
"""
检查用户表结构
"""

import sqlite3
import os

def check_table_structure():
    """检查用户表结构"""
    db_path = 'vmatch.db'
    if not os.path.exists(db_path):
        print(f"数据库文件 {db_path} 不存在")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=== 用户表结构 ===")
        
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
        
        # 获取创建表的SQL
        cursor.execute("SELECT sql FROM sqlite_master WHERE name='users'")
        create_sql = cursor.fetchone()
        if create_sql:
            print(f"\n创建SQL:\n{create_sql[0]}")
        
        # 获取索引
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='users'")
        indexes = cursor.fetchall()
        
        print(f"\n索引数: {len(indexes)}")
        for idx in indexes:
            print(f"  {idx[0]}")
        
        conn.close()
        
    except Exception as e:
        print(f"检查失败: {e}")

if __name__ == "__main__":
    check_table_structure()