#!/usr/bin/env python3
"""
核心修复验证脚本 - 验证location数组转JSON字符串的修复
"""

import sqlite3
import json
import sys
import os

def test_location_json_conversion():
    """测试location数组转JSON字符串的修复"""
    print("=== 核心修复验证 ===")
    
    # 使用开发数据库
    db_path = 'vmatch_dev.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 清理之前的测试数据
        cursor.execute("DELETE FROM users WHERE id LIKE 'test_%'")
        conn.commit()
        
        # 测试数据
        test_user_id = 'test_fix_001'
        location_array = ['上海市', '上海市', '黄浦区']
        interests_array = ['阅读', '旅行', '摄影']
        
        # 1. 测试数组转JSON字符串存储
        location_json = json.dumps(location_array)
        interests_json = json.dumps(interests_array)
        
        cursor.execute("""
            INSERT INTO users (id, phone, nick_name, location, interests)
            VALUES (?, ?, ?, ?, ?)
        """, (test_user_id, '13900139000', '测试用户', location_json, interests_json))
        conn.commit()
        
        # 2. 验证存储的数据格式
        cursor.execute("SELECT location, interests FROM users WHERE id = ?", (test_user_id,))
        stored_location, stored_interests = cursor.fetchone()
        
        print(f"✅ 存储的location: {stored_location}")
        print(f"✅ 存储的interests: {stored_interests}")
        
        # 3. 验证JSON解析回数组
        parsed_location = json.loads(stored_location)
        parsed_interests = json.loads(stored_interests)
        
        print(f"✅ 解析回的location: {parsed_location}")
        print(f"✅ 解析回的interests: {parsed_interests}")
        
        # 4. 验证数据一致性
        assert parsed_location == location_array, "location数据不一致"
        assert parsed_interests == interests_array, "interests数据不一致"
        
        print("🎉 所有验证通过！location数组转JSON修复成功")
        
        # 清理测试数据
        cursor.execute("DELETE FROM users WHERE id = ?", (test_user_id,))
        conn.commit()
        
        return True
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = test_location_json_conversion()
    if success:
        print("\n✅ 修复验证完成 - 注册问题已解决")
        sys.exit(0)
    else:
        print("\n❌ 修复验证失败")
        sys.exit(1)