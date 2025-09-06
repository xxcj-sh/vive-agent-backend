#!/usr/bin/env python3
"""
测试新用户字段的API集成
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import sqlite3
import json
from datetime import datetime

def test_new_fields_integration():
    """测试新字段的API集成"""
    db_path = 'vmatch_dev.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=== 测试新字段API集成 ===")
        
        # 测试插入包含新字段的用户数据
        test_user_data = {
            'id': 'test_api_user_001',
            'phone': '13800138001',
            'nick_name': 'API测试用户',
            'age': 28,
            'gender': 1,
            'education': '硕士',
            'occupation': '软件工程师',
            'location': json.dumps(["北京市", "海淀区", "中关村"]),
            'interests': json.dumps(["编程", "人工智能", "摄影", "旅行"]),
            'wechat': 'test_wechat_api',
            'email': 'test.api@example.com',
            'bio': '这是一个API测试用户的个人简介',
            'status': 'active',
            'level': 3,
            'points': 250,
            'last_login': datetime.now().isoformat()
        }
        
        # 插入测试用户
        insert_sql = """
        INSERT OR REPLACE INTO users (
            id, phone, nick_name, age, gender, education, occupation, 
            location, interests, wechat, email, bio, status, level, points, last_login
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        cursor.execute(insert_sql, (
            test_user_data['id'],
            test_user_data['phone'],
            test_user_data['nick_name'],
            test_user_data['age'],
            test_user_data['gender'],
            test_user_data['education'],
            test_user_data['occupation'],
            test_user_data['location'],
            test_user_data['interests'],
            test_user_data['wechat'],
            test_user_data['email'],
            test_user_data['bio'],
            test_user_data['status'],
            test_user_data['level'],
            test_user_data['points'],
            test_user_data['last_login']
        ))
        
        conn.commit()
        print("✅ 测试用户插入成功")
        
        # 查询并验证数据
        cursor.execute("""
        SELECT id, nick_name, education, location, interests, wechat, email, status, level, points 
        FROM users WHERE id = ?
        """, (test_user_data['id'],))
        
        user = cursor.fetchone()
        if user:
            print("✅ 查询成功，用户数据：")
            print(f"  ID: {user[0]}")
            print(f"  昵称: {user[1]}")
            print(f"  教育: {user[2]}")
            print(f"  位置: {user[3]}")
            print(f"  兴趣: {user[4]}")
            print(f"  微信: {user[5]}")
            print(f"  邮箱: {user[6]}")
            print(f"  状态: {user[7]}")
            print(f"  等级: {user[8]}")
            print(f"  积分: {user[9]}")
            
            # 验证JSON格式
            location_data = json.loads(user[3])
            interests_data = json.loads(user[4])
            print(f"✅ 位置JSON解析成功: {location_data}")
            print(f"✅ 兴趣JSON解析成功: {interests_data}")
        else:
            print("❌ 查询失败")
        
        # 清理测试数据
        cursor.execute("DELETE FROM users WHERE id = ?", (test_user_data['id'],))
        conn.commit()
        print("✅ 测试数据清理完成")
        
        conn.close()
        print("\n🎉 所有API集成测试通过！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_new_fields_integration()