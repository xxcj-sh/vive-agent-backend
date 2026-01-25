#!/usr/bin/env python3
"""
Database migration script: Add birthday column to users table
执行前请确保已激活虚拟环境: .\venv\Scripts\activate
"""

import pymysql

# 数据库连接配置 - 使用阿里云 RDS
DB_CONFIG = {
    'host': 'rm-cn-w7k4hvvlx0003bbo.rwlb.rds.aliyuncs.com',
    'port': 3306,
    'user': 'user_test',
    'password': 'Test2025',
    'database': 'vmatch_dev',
    'charset': 'utf8mb4'
}

def add_birthday_column():
    """添加 birthday 列到 users 表"""
    
    connection = pymysql.connect(**DB_CONFIG)
    try:
        with connection.cursor() as cursor:
            # 检查列是否已存在
            cursor.execute("""
                SELECT COUNT(*)
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = 'users'
                AND TABLE_SCHEMA = 'vmatch_dev'
                AND COLUMN_NAME = 'birthday'
            """)
            
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                print("✅ 列 'birthday' 已存在于 users 表中，无需重复添加")
            else:
                # 添加 birthday 列
                cursor.execute("""
                    ALTER TABLE users 
                    ADD COLUMN birthday VARCHAR(20) DEFAULT NULL 
                    COMMENT '用户出生日期'
                """)
                connection.commit()
                print("✅ 成功添加 'birthday' 列到 users 表")
                
                # 验证添加成功
                cursor.execute("""
                    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_COMMENT
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = 'users'
                    AND TABLE_SCHEMA = 'vmatch_dev'
                    AND COLUMN_NAME = 'birthday'
                """)
                result = cursor.fetchone()
                print(f"   列信息: {result}")
                
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        connection.rollback()
        raise
    finally:
        connection.close()

if __name__ == '__main__':
    print("开始执行数据库迁移...")
    add_birthday_column()
    print("迁移完成！")
