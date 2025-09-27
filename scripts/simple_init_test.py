#!/usr/bin/env python3
"""
简单的数据库初始化测试
"""

import sqlite3
import os
from pathlib import Path

def main():
    # 设置路径
    db_path = Path(__file__).parent.parent / 'vmatch.db'
    sql_path = Path(__file__).parent / 'init_sqlite_db.sql'
    
    print(f'数据库路径: {db_path}')
    print(f'SQL路径: {sql_path}')
    
    # 检查SQL文件是否存在
    if not sql_path.exists():
        print(f'错误: SQL文件不存在: {sql_path}')
        return False
    
    try:
        # 读取SQL文件
        with open(sql_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        print(f'SQL文件大小: {len(sql_content)} 字符')
        
        # 如果数据库已存在，先删除
        if db_path.exists():
            os.remove(db_path)
            print('已删除现有数据库文件')
        
        # 创建数据库连接
        print('创建数据库连接...')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print('执行SQL脚本...')
        # 执行SQL脚本
        cursor.executescript(sql_content)
        conn.commit()
        
        print('检查创建的表...')
        # 检查创建的表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = cursor.fetchall()
        print(f'创建表数量: {len(tables)}')
        for table in tables:
            print(f'  - {table[0]}')
        
        print('检查数据...')
        # 检查用户数据
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f'用户数据: {user_count} 条记录')
        
        # 检查卡片数据
        cursor.execute("SELECT COUNT(*) FROM user_cards")
        card_count = cursor.fetchone()[0]
        print(f'卡片数据: {card_count} 条记录')
        
        # 显示一些用户数据
        if user_count > 0:
            cursor.execute("SELECT id, nick_name, phone FROM users LIMIT 3")
            users = cursor.fetchall()
            print('\n前3个用户:')
            for user in users:
                print(f'  - {user[1]} ({user[0]}): {user[2]}')
        
        conn.close()
        print('\n✅ 数据库初始化成功！')
        return True
        
    except Exception as e:
        print(f'\n❌ 数据库初始化失败: {e}')
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)