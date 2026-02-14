"""
修改 user_cards 表的 preferences 列从 JSON 改为 VARCHAR
"""

import pymysql

def migrate_preferences_column():
    """将 preferences 列从 JSON 改为 VARCHAR"""
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='your_password',  # 请修改为实际密码
        database='vive_agent',
        charset='utf8mb4'
    )
    
    try:
        with connection.cursor() as cursor:
            # 1. 添加临时 VARCHAR 列
            print("1. 添加临时 VARCHAR 列...")
            cursor.execute("""
                ALTER TABLE user_cards
                ADD COLUMN preferences_temp VARCHAR(500) NULL
            """)
            
            # 2. 将现有 JSON 数据转换为字符串并复制到临时列
            print("2. 转换现有数据...")
            cursor.execute("""
                UPDATE user_cards
                SET preferences_temp = JSON_UNQUOTE(preferences)
                WHERE preferences IS NOT NULL
            """)
            
            # 3. 删除原有的 JSON 列
            print("3. 删除原有 JSON 列...")
            cursor.execute("""
                ALTER TABLE user_cards
                DROP COLUMN preferences
            """)
            
            # 4. 将临时列重命名为 preferences
            print("4. 重命名列...")
            cursor.execute("""
                ALTER TABLE user_cards
                CHANGE COLUMN preferences_temp preferences VARCHAR(500) NULL
            """)
            
        connection.commit()
        print("✅ 迁移完成！preferences 列已成功从 JSON 改为 VARCHAR")
        
    except Exception as e:
        connection.rollback()
        print(f"❌ 迁移失败: {str(e)}")
        raise
    finally:
        connection.close()

if __name__ == "__main__":
    migrate_preferences_column()
