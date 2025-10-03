#!/usr/bin/env python3
"""
MySQL数据库初始化脚本
用于创建和初始化MySQL数据库表结构
"""

import mysql.connector
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings

def init_mysql_database(sql_script_path=None):
    """
    初始化MySQL数据库
    
    Args:
        sql_script_path: SQL脚本文件路径，默认为当前目录下的init_mysql_db.sql
    """
    
    # 设置默认路径
    if sql_script_path is None:
        sql_script_path = Path(__file__).parent / "init_mysql_db.sql"
    
    print(f"MySQL主机: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}")
    print(f"数据库名: {settings.MYSQL_DATABASE}")
    print(f"用户名: {settings.MYSQL_USERNAME}")
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
        conn = mysql.connector.connect(
            host=settings.MYSQL_HOST,
            port=int(settings.MYSQL_PORT),
            user=settings.MYSQL_USERNAME,
            password=settings.MYSQL_PASSWORD,
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        
        print("正在创建数据库和表结构...")
        
        # 执行SQL脚本
        # 分割SQL语句（MySQL连接器不支持executescript）
        sql_statements = sql_script.split(';')
        
        for statement in sql_statements:
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                try:
                    cursor.execute(statement)
                except mysql.connector.Error as e:
                    # 忽略一些预期的错误（如表已存在）
                    if "already exists" not in str(e) and "Unknown database" not in str(e):
                        print(f"警告: 执行SQL语句时出错: {e}")
        
        # 提交事务
        conn.commit()
        
        print("MySQL数据库初始化完成！")
        
        # 显示创建的表
        cursor.execute(f"USE {settings.MYSQL_DATABASE}")
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"创建的表数量: {len(tables)}")
        for table in tables:
            print(f"  - {table[0]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except mysql.connector.Error as e:
        print(f"MySQL数据库连接错误: {e}")
        return False
    except Exception as e:
        print(f"初始化过程中出错: {e}")
        return False

def test_mysql_connection():
    """测试MySQL数据库连接"""
    try:
        conn = mysql.connector.connect(
            host=settings.MYSQL_HOST,
            port=int(settings.MYSQL_PORT),
            user=settings.MYSQL_USERNAME,
            password=settings.MYSQL_PASSWORD,
            database=settings.MYSQL_DATABASE
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        print("✅ MySQL数据库连接测试成功")
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ MySQL数据库连接测试失败: {e}")
        return False

def reset_mysql_database():
    """重置MySQL数据库（删除所有表）"""
    try:
        conn = mysql.connector.connect(
            host=settings.MYSQL_HOST,
            port=int(settings.MYSQL_PORT),
            user=settings.MYSQL_USERNAME,
            password=settings.MYSQL_PASSWORD,
            charset='utf8mb4'
        )
        
        cursor = conn.cursor()
        
        # 删除数据库
        cursor.execute(f"DROP DATABASE IF EXISTS {settings.MYSQL_DATABASE}")
        
        # 重新创建数据库
        cursor.execute(f"CREATE DATABASE {settings.MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ MySQL数据库重置完成")
        return True
        
    except mysql.connector.Error as e:
        print(f"❌ MySQL数据库重置失败: {e}")
        return False

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='初始化MySQL数据库')
    parser.add_argument('--sql-script', type=str, help='SQL脚本文件路径')
    parser.add_argument('--test', action='store_true', help='测试数据库连接')
    parser.add_argument('--reset', action='store_true', help='重置数据库（删除所有表）')
    parser.add_argument('--force', action='store_true', help='强制重置（不询问确认）')
    
    args = parser.parse_args()
    
    # 测试数据库连接
    if args.test:
        test_mysql_connection()
        return
    
    # 重置数据库
    if args.reset:
        if not args.force:
            response = input("确定要重置MySQL数据库吗？这将删除所有数据！(y/N): ")
            if response.lower() != 'y':
                print("操作已取消")
                return
        
        if reset_mysql_database():
            print("数据库重置完成")
        else:
            print("数据库重置失败")
            return
    
    # 初始化数据库
    success = init_mysql_database(args.sql_script)
    
    if success:
        print("\n✅ MySQL数据库初始化成功！")
    else:
        print("\n❌ MySQL数据库初始化失败！")
        sys.exit(1)

if __name__ == "__main__":
    main()