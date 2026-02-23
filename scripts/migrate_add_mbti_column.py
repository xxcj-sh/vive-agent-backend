"""
添加 users 表缺失的 mbti 列
"""

import pymysql
import os
from dotenv import load_dotenv

load_dotenv()

def migrate_add_mbti_column():
    """添加 mbti 列到 users 表"""
    database_url = os.getenv('DATABASE_URL', '')
    
    if not database_url:
        print("错误: 未找到 DATABASE_URL 环境变量")
        return False
    
    try:
        # 解析数据库连接信息
        # 格式: mysql+pymysql://user:password@host:port/database
        db_info = database_url.replace('mysql+pymysql://', '').split('@')
        user_password = db_info[0].split(':')
        host_db = db_info[1].split('/')
        host_port = host_db[0].split(':')
        
        user = user_password[0]
        password = user_password[1]
        host = host_port[0]
        port = int(host_port[1]) if len(host_port) > 1 else 3306
        database = host_db[1]
        
        print(f"连接数据库: {host}:{port}/{database}")
        
        connection = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port,
            charset='utf8mb4'
        )
        
        try:
            with connection.cursor() as cursor:
                # 检查 mbti 列是否存在
                cursor.execute("""
                    SELECT COUNT(*) as count 
                    FROM information_schema.COLUMNS 
                    WHERE TABLE_SCHEMA = %s 
                    AND TABLE_NAME = 'users' 
                    AND COLUMN_NAME = 'mbti'
                """, (database,))
                
                result = cursor.fetchone()
                if result[0] > 0:
                    print("mbti 列已存在，无需迁移")
                    return True
                
                # 添加 mbti 列
                print("添加 mbti 列到 users 表...")
                cursor.execute("""
                    ALTER TABLE users 
                    ADD COLUMN mbti VARCHAR(10) DEFAULT NULL
                """)
                
                connection.commit()
                print("迁移成功！mbti 列已添加")
                return True
                
        finally:
            connection.close()
            
    except Exception as e:
        print(f"迁移失败: {e}")
        return False

if __name__ == '__main__':
    migrate_add_mbti_column()
