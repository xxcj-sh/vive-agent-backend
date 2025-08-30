#!/usr/bin/env python3
"""
调试用户ID问题
"""
import requests
import json

# API配置
base_url = "http://192.168.71.103:8000/api/v1"
headers = {
    "Content-Type": "application/json",
    "X-Test-Mode": "true"
}

def debug_user_id():
    """调试用户ID"""
    url = f"{base_url}/users/me"
    
    print("=== 调试用户ID ===")
    
    # 获取当前用户信息
    print("1. 获取当前用户信息...")
    get_response = requests.get(url, headers=headers)
    
    if get_response.status_code == 200:
        user_data = get_response.json()
        user_id = user_data.get('id')
        print(f"用户ID: {user_id}")
        print(f"用户数据: {json.dumps(user_data, indent=2, ensure_ascii=False)}")
        
        # 测试更新
        print(f"\n2. 测试更新用户 {user_id}...")
        update_data = {"avatar_url": "http://test.com/new_avatar.jpg"}
        put_response = requests.put(url, json=update_data, headers=headers)
        
        print(f"更新状态码: {put_response.status_code}")
        if put_response.status_code == 200:
            updated_data = put_response.json()
            print(f"更新后数据: {json.dumps(updated_data, indent=2, ensure_ascii=False)}")
        else:
            print(f"更新失败: {put_response.text}")
    else:
        print(f"获取用户信息失败: {get_response.status_code}")
        print(f"响应: {get_response.text}")

if __name__ == "__main__":
    debug_user_id()