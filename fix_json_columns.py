"""
修复数据库中JSON列的数据格式问题
"""

import sqlite3
import json

def fix_json_columns():
    """修复JSON列中的数据格式"""
    conn = sqlite3.connect('vmatch_dev.db')
    cursor = conn.cursor()
    
    try:
        # 修复 location 列
        cursor.execute('SELECT id, location FROM users WHERE location IS NOT NULL')
        users_with_location = cursor.fetchall()
        
        for user_id, location in users_with_location:
            if location and location.strip():
                try:
                    # 尝试解析现有的location值
                    json.loads(location)
                    print(f"✅ 用户 {user_id} 的location已经是有效JSON: {location}")
                except json.JSONDecodeError:
                    # 如果不是有效JSON，将其转换为JSON数组格式
                    fixed_location = json.dumps([location.strip()], ensure_ascii=False)
                    cursor.execute('UPDATE users SET location = ? WHERE id = ?', (fixed_location, user_id))
                    print(f"🔧 修复用户 {user_id} 的location: {location} -> {fixed_location}")
        
        # 修复 interests 列
        cursor.execute('SELECT id, interests FROM users WHERE interests IS NOT NULL')
        users_with_interests = cursor.fetchall()
        
        for user_id, interests in users_with_interests:
            if interests and interests.strip():
                try:
                    # 尝试解析现有的interests值
                    json.loads(interests)
                    print(f"✅ 用户 {user_id} 的interests已经是有效JSON: {interests}")
                except json.JSONDecodeError:
                    # 如果不是有效JSON，将其转换为JSON数组格式
                    fixed_interests = json.dumps([interests.strip()], ensure_ascii=False)
                    cursor.execute('UPDATE users SET interests = ? WHERE id = ?', (fixed_interests, user_id))
                    print(f"🔧 修复用户 {user_id} 的interests: {interests} -> {fixed_interests}")
        
        # 提交更改
        conn.commit()
        print("✅ JSON列数据修复完成")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ 修复失败: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_json_columns()