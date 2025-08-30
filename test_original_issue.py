#!/usr/bin/env python3
"""
测试原始问题的脚本
"""
import requests
import json

# 原始问题数据
original_data = {
    "avatar_url": "/uploads/test_user_001/b27faa58-825c-426d-b140-1bbaddedf4cc.png"
}

# API配置
base_url = "http://192.168.71.103:8000/api/v1"
headers = {
    "Content-Type": "application/json",
    "X-Test-Mode": "true"
}

def test_original_issue():
    """测试原始问题"""
    url = f"{base_url}/users/me"
    
    print("测试原始问题数据:")
    print(f"数据: {json.dumps(original_data, ensure_ascii=False)}")
    print("="*50)
    
    try:
        response = requests.put(url, json=original_data, headers=headers)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 修复成功!")
            result = response.json()
            print(f"avatarUrl字段: {result.get('avatarUrl', 'NOT_FOUND')}")
        else:
            print("❌ 仍然失败!")
            print(f"响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")

if __name__ == "__main__":
    test_original_issue()