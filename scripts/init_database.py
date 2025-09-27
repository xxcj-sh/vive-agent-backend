#!/usr/bin/env python3
"""
SQLite数据库初始化脚本
用于创建和初始化数据库表结构
"""

import sqlite3
import os
import sys
from pathlib import Path

def init_database(db_path=None, sql_script_path=None):
    """
    初始化SQLite数据库
    
    Args:
        db_path: 数据库文件路径，默认为项目根目录下的vmatch.db
        sql_script_path: SQL脚本文件路径，默认为当前目录下的init_sqlite_db.sql
    """
    
    # 设置默认路径
    if db_path is None:
        db_path = Path(__file__).parent.parent / "vmatch.db"
    
    if sql_script_path is None:
        sql_script_path = Path(__file__).parent / "init_sqlite_db.sql"
    
    print(f"数据库文件路径: {db_path}")
    print(f"SQL脚本路径: {sql_script_path}")
    
    # 检查SQL脚本文件是否存在
    if not os.path.exists(sql_script_path):
        print(f"错误: SQL脚本文件不存在: {sql_script_path}")
        return False
    
    try:
        # 读取SQL脚本
        with open(sql_script_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # 创建数据库连接
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("正在创建数据库表结构...")
        
        # 执行SQL脚本
        cursor.executescript(sql_script)
        
        # 提交事务
        conn.commit()
        
        print("数据库初始化完成！")
        
        # 显示创建的表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = cursor.fetchall()
        
        print(f"\n成功创建 {len(tables)} 个表:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # 显示创建的索引
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index';")
        indexes = cursor.fetchall()
        
        print(f"\n成功创建 {len(indexes)} 个索引:")
        for index in indexes:
            print(f"  - {index[0]}")
        
        # 显示创建的视图
        cursor.execute("SELECT name FROM sqlite_master WHERE type='view';")
        views = cursor.fetchall()
        
        print(f"\n成功创建 {len(views)} 个视图:")
        for view in views:
            print(f"  - {view[0]}")
        
        # 显示用户数据
        cursor.execute("SELECT COUNT(*) FROM users;")
        user_count = cursor.fetchone()[0]
        print(f"\n用户数据: {user_count} 条记录")
        
        # 显示卡片数据
        cursor.execute("SELECT COUNT(*) FROM user_cards;")
        card_count = cursor.fetchone()[0]
        print(f"卡片数据: {card_count} 条记录")
        
        # 关闭连接
        conn.close()
        
        return True
        
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
        return False
    except Exception as e:
        print(f"初始化失败: {e}")
        return False

def reset_database(db_path=None):
    """
    重置数据库（删除现有数据库文件）
    
    Args:
        db_path: 数据库文件路径
    """
    if db_path is None:
        db_path = Path(__file__).parent.parent / "vmatch.db"
    
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
            print(f"已删除现有数据库文件: {db_path}")
            return True
        except Exception as e:
            print(f"删除数据库文件失败: {e}")
            return False
    else:
        print("数据库文件不存在，无需删除")
        return True

def main():
    """
    主函数
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='初始化SQLite数据库')
    parser.add_argument('--db-path', type=str, help='数据库文件路径')
    parser.add_argument('--sql-script', type=str, help='SQL脚本文件路径')
    parser.add_argument('--reset', action='store_true', help='重置数据库（删除现有数据库）')
    parser.add_argument('--force', action='store_true', help='强制重置（不询问确认）')
    
    args = parser.parse_args()
    
    # 如果指定了重置选项
    if args.reset:
        if not args.force:
            response = input("确定要删除现有数据库吗？(y/N): ")
            if response.lower() != 'y':
                print("操作已取消")
                return
        
        if reset_database(args.db_path):
            print("数据库重置完成")
        else:
            print("数据库重置失败")
            return
    
    # 初始化数据库
    success = init_database(args.db_path, args.sql_script)
    
    if success:
        print("\n✅ 数据库初始化成功！")
    else:
        print("\n❌ 数据库初始化失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()