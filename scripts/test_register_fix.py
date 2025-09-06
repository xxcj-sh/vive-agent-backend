#!/usr/bin/env python3
"""
测试注册修复：验证location数组转换为JSON字符串
"""

import sqlite3
import json
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_location_json_conversion():
    """测试location字段的JSON转换"""
    
    # 连接到测试数据库
    db_path = 'vmatch_dev.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 创建测试用户
        test_user_id = 'test_user_001'
        cursor.execute("""
            INSERT OR REPLACE INTO users (id, phone, nick_name, location, interests) 
            VALUES (?, ?, ?, ?, ?)
        """, (test_user_id, '13800138000', '测试用户', '[]', '[]'))
        conn.commit()
        
        # 模拟前端传来的location数组
        location_array = ['上海市', '上海市', '黄浦区']
        interests_array = ['音乐', '电影', '旅行']
        
        # 转换为JSON字符串
        location_json = json.dumps(location_array, ensure_ascii=False)
        interests_json = json.dumps(interests_array, ensure_ascii=False)
        
        print(f"原始location数组: {location_array}")
        print(f"转换后的JSON字符串: {location_json}")
        print(f"原始interests数组: {interests_array}")
        print(f"转换后的JSON字符串: {interests_json}")
        
        # 更新用户数据
        cursor.execute("""
            UPDATE users 
            SET location = ?, interests = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (location_json, interests_json, test_user_id))
        conn.commit()
        
        # 验证数据是否正确存储
        cursor.execute("SELECT location, interests FROM users WHERE id = ?", (test_user_id,))
        result = cursor.fetchone()
        
        if result:
            stored_location, stored_interests = result
            print(f"数据库存储的location: {stored_location}")
            print(f"数据库存储的interests: {stored_interests}")
            
            # 验证JSON可以正确解析回数组
            parsed_location = json.loads(stored_location)
            parsed_interests = json.loads(stored_interests)
            
            print(f"解析回的location数组: {parsed_location}")
            print(f"解析回的interests数组: {parsed_interests}")
            
            # 验证数据一致性
            if parsed_location == location_array and parsed_interests == interests_array:
                print("✅ JSON转换测试通过！数据一致性验证成功")
                return True
            else:
                print("❌ JSON转换测试失败！数据不一致")
                return False
        else:
            print("❌ 未找到测试用户")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {str(e)}")
        return False
    finally:
        # 清理测试数据
        cursor.execute("DELETE FROM users WHERE id = ?", (test_user_id,))
        conn.commit()
        conn.close()

def test_direct_array_insert():
    """测试直接插入数组是否会失败"""
    
    db_path = 'vmatch_dev.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 尝试直接插入数组（应该失败）
        test_user_id = 'test_user_002'
        location_array = ['上海市', '上海市', '黄浦区']
        
        try:
            cursor.execute("""
                INSERT INTO users (id, phone, nick_name, location) 
                VALUES (?, ?, ?, ?)
            """, (test_user_id, '13800138001', '测试用户2', location_array))
            conn.commit()
            print("❌ 直接插入数组未触发错误，这不正常")
            return False
        except sqlite3.InterfaceError as e:
            print(f"✅ 直接插入数组触发预期错误: {str(e)}")
            return True
            
    except Exception as e:
        print(f"❌ 测试过程中出现意外错误: {str(e)}")
        return False
    finally:
        # 清理测试数据
        cursor.execute("DELETE FROM users WHERE id = ?", (test_user_id,))
        conn.commit()
        conn.close()

if __name__ == "__main__":
    print("=== 测试注册修复方案 ===")
    print()
    
    print("1. 测试JSON转换功能...")
    success1 = test_location_json_conversion()
    print()
    
    print("2. 测试直接数组插入错误...")
    success2 = test_direct_array_insert()
    print()
    
    if success1 and success2:
        print("🎉 所有测试通过！修复方案有效")
    else:
        print("⚠️  部分测试失败，需要进一步检查")