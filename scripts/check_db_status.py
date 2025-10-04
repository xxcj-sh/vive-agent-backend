#!/usr/bin/env python3
"""
数据库状态检查脚本
用于检查数据库连接和表结构状态

使用方法:
    python check_db_status.py [--detailed]
    
参数:
    --detailed: 显示详细的表结构信息
"""

import os
import sys
import argparse
import pymysql
from typing import Dict, List
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 数据库配置
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
MYSQL_USERNAME = os.getenv('MYSQL_USERNAME', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'vmatch_dev')

def get_connection():
    """获取数据库连接"""
    try:
        return pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USERNAME,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        return None

def check_connection() -> bool:
    """检查数据库连接"""
    conn = get_connection()
    if conn:
        conn.close()
        return True
    return False

def get_database_info() -> Dict:
    """获取数据库信息"""
    conn = get_connection()
    if not conn:
        return {}
    
    try:
        with conn.cursor() as cursor:
            # 获取数据库大小
            cursor.execute(f"SELECT SUM(data_length + index_length) as size FROM information_schema.tables WHERE table_schema = '{MYSQL_DATABASE}'")
            db_size = cursor.fetchone()['size'] or 0
            
            # 获取表数量
            cursor.execute(f"SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = '{MYSQL_DATABASE}'")
            table_count = cursor.fetchone()['table_count']
            
            # 获取数据库字符集
            cursor.execute(f"SELECT default_character_set_name FROM information_schema.schemata WHERE schema_name = '{MYSQL_DATABASE}'")
            result = cursor.fetchone()
            charset = result['default_character_set_name'] if result and 'default_character_set_name' in result else 'utf8mb4'
            
            return {
                'size': db_size,
                'table_count': table_count,
                'charset': charset,
                'name': MYSQL_DATABASE
            }
    finally:
        conn.close()

def get_table_info(detailed: bool = False) -> List[Dict]:
    """获取表信息"""
    conn = get_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cursor:
            # 获取所有表
            cursor.execute(f"""
                SELECT 
                    table_name as TABLE_NAME,
                    table_rows as TABLE_ROWS,
                    COALESCE(data_length, 0) as data_length,
                    COALESCE(index_length, 0) as index_length,
                    create_time as CREATE_TIME,
                    update_time as UPDATE_TIME,
                    table_comment as TABLE_COMMENT
                FROM information_schema.tables 
                WHERE table_schema = '{MYSQL_DATABASE}'
                ORDER BY table_name
            """)
            tables = cursor.fetchall()
            
            if not detailed:
                # 转换为大写键名以便后续使用
                return [{k.upper(): v for k, v in table.items()} for table in tables]
            
            # 获取详细信息
            detailed_info = []
            for table in tables:
                table_name = table['table_name']
                
                # 获取列信息
                cursor.execute(f"DESCRIBE {table_name}")
                columns = cursor.fetchall()
                
                # 获取索引信息
                cursor.execute(f"SHOW INDEX FROM {table_name}")
                indexes = cursor.fetchall()
                
                detailed_info.append({
                    'table_info': table,
                    'columns': columns,
                    'indexes': indexes
                })
            
            return detailed_info
    finally:
        conn.close()

def check_table_integrity() -> Dict:
    """检查表完整性"""
    conn = get_connection()
    if not conn:
        return {'status': 'error', 'message': '无法连接数据库'}
    
    try:
        with conn.cursor() as cursor:
            # 检查外键约束
            cursor.execute(f"""
                SELECT 
                    table_name,
                    constraint_name,
                    column_name,
                    referenced_table_name,
                    referenced_column_name
                FROM information_schema.key_column_usage 
                WHERE table_schema = '{MYSQL_DATABASE}' 
                AND referenced_table_name IS NOT NULL
            """)
            foreign_keys = cursor.fetchall()
            
            # 检查是否有孤立的记录
            issues = []
            
            # 检查用户卡片的外键
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM user_cards uc 
                LEFT JOIN users u ON uc.user_id = u.id 
                WHERE u.id IS NULL
            """)
            orphaned_cards = cursor.fetchone()['count']
            if orphaned_cards > 0:
                issues.append(f"用户卡片表中有 {orphaned_cards} 条孤立记录")
            
            # 检查匹配操作的外键
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM match_actions ma 
                LEFT JOIN users u ON ma.user_id = u.id 
                WHERE u.id IS NULL
            """)
            orphaned_actions = cursor.fetchone()['count']
            if orphaned_actions > 0:
                issues.append(f"匹配操作表中有 {orphaned_actions} 条孤立记录")
            
            return {
                'status': 'ok' if not issues else 'warning',
                'foreign_keys': len(foreign_keys),
                'issues': issues
            }
    finally:
        conn.close()

def format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes == 0:
        return "0 B"
    
    size_bytes = float(size_bytes)
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.2f} TB"

def main():
    parser = argparse.ArgumentParser(description='数据库状态检查脚本')
    parser.add_argument('--detailed', action='store_true', help='显示详细的表结构信息')
    args = parser.parse_args()
    
    print(f"🔍 检查数据库状态: {MYSQL_DATABASE}")
    print(f"📡 连接: {MYSQL_HOST}:{MYSQL_PORT}")
    print("-" * 50)
    
    # 检查连接
    print("1️⃣ 检查数据库连接...")
    if check_connection():
        print("   ✅ 数据库连接正常")
    else:
        print("   ❌ 数据库连接失败")
        sys.exit(1)
    
    # 获取数据库信息
    print("\n2️⃣ 获取数据库信息...")
    db_info = get_database_info()
    if db_info:
        print(f"   📊 数据库: {db_info['name']}")
        print(f"   📏 大小: {format_size(db_info['size'])}")
        print(f"   📋 表数量: {db_info['table_count']}")
        print(f"   🔤 字符集: {db_info['charset']}")
    
    # 获取表信息
    print("\n3️⃣ 检查表结构...")
    tables = get_table_info(args.detailed)
    
    if not tables:
        print("   ⚠️  数据库中没有表")
    else:
        print(f"   📋 发现 {len(tables)} 个表:")
        
        if not args.detailed:
            for table in tables:
                size = format_size(table['DATA_LENGTH'] + table['INDEX_LENGTH'])
                print(f"      - {table['TABLE_NAME']}: {table['TABLE_ROWS']} 行, {size}")
        else:
            for table_info in tables:
                table = table_info['table_info'] if isinstance(table_info, dict) and 'table_info' in table_info else table_info
                size = format_size(table['DATA_LENGTH'] + table['INDEX_LENGTH'])
                print(f"\n   📄 {table['TABLE_NAME']}:")
                print(f"      行数: {table['TABLE_ROWS']}")
                print(f"      大小: {size}")
                if isinstance(table_info, dict) and 'columns' in table_info:
                    print(f"      列数: {len(table_info['columns'])}")
                    print(f"      索引数: {len(table_info['indexes'])}")
                    
                    # 显示列信息
                    print("      列:")
                    for col in table_info['columns']:
                        nullable = "NULL" if col['Null'] == 'YES' else "NOT NULL"
                        print(f"        - {col['Field']}: {col['Type']} {nullable} {col['Default'] or ''}")
    
    # 检查完整性
    print("\n4️⃣ 检查数据完整性...")
    integrity = check_table_integrity()
    
    if integrity['status'] == 'ok':
        print("   ✅ 数据完整性检查通过")
        print(f"   🔗 外键约束: {integrity['foreign_keys']} 个")
    elif integrity['status'] == 'warning':
        print("   ⚠️  发现数据完整性问题:")
        for issue in integrity['issues']:
            print(f"      - {issue}")
    else:
        print(f"   ❌ {integrity['message']}")
    
    print("\n" + "=" * 50)
    print("✅ 数据库状态检查完成")

if __name__ == '__main__':
    main()