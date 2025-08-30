#!/usr/bin/env python3
"""
测试图片URL前缀处理
"""
import requests
import json

# API配置
base_url = "http://192.168.71.103:8000/api/v1"
headers = {
    "Content-Type": "application/json",
    "X-Test-Mode": "true"
}

def test_image_url_prefix():
    """测试图片URL前缀处理"""
    url = f"{base_url}/users/me"
    
    print("=== 测试图片URL前缀处理 ===")
    
    # 测试用例1：相对路径
    print("\n1. 测试相对路径...")
    update_data = {"avatar_url": "/uploads/test_user_001/avatar.jpg"}
    put_response = requests.put(url, json=update_data, headers=headers)
    
    if put_response.status_code == 200:
        result = put_response.json()
        avatar_url = result.get('avatarUrl', 'NOT_FOUND')
        print(f"更新后的avatarUrl: {avatar_url}")
        
        if avatar_url.startswith('http://'):
            print("✅ 相对路径已正确添加HTTP前缀")
        else:
            print("❌ 相对路径未添加HTTP前缀")
    else:
        print(f"❌ 更新失败: {put_response.status_code}")
    
    # 测试用例2：完整URL
    print("\n2. 测试完整URL...")
    update_data = {"avatar_url": "https://example.com/avatar.jpg"}
    put_response = requests.put(url, json=update_data, headers=headers)
    
    if put_response.status_code == 200:
        result = put_response.json()
        avatar_url = result.get('avatarUrl', 'NOT_FOUND')
        print(f"更新后的avatarUrl: {avatar_url}")
        
        if avatar_url == "https://example.com/avatar.jpg":
            print("✅ 完整URL保持不变")
        else:
            print("❌ 完整URL被错误修改")
    else:
        print(f"❌ 更新失败: {put_response.status_code}")
    
    # 测试用例3：无前缀路径
    print("\n3. 测试无前缀路径...")
    update_data = {"avatar_url": "uploads/test_user_001/no_prefix.jpg"}
    put_response = requests.put(url, json=update_data, headers=headers)
    
    if put_response.status_code == 200:
        result = put_response.json()
        avatar_url = result.get('avatarUrl', 'NOT_FOUND')
        print(f"更新后的avatarUrl: {avatar_url}")
        
        if avatar_url.startswith('http://') and 'uploads/test_user_001/no_prefix.jpg' in avatar_url:
            print("✅ 无前缀路径已正确添加HTTP前缀和斜杠")
        else:
            print("❌ 无前缀路径处理错误")
    else:
        print(f"❌ 更新失败: {put_response.status_code}")
    
    # 测试用例4：验证GET请求也返回正确的URL
    print("\n4. 验证GET请求返回正确的URL...")
    get_response = requests.get(url, headers=headers)
    
    if get_response.status_code == 200:
        result = get_response.json()
        avatar_url = result.get('avatarUrl', 'NOT_FOUND')
        print(f"GET请求返回的avatarUrl: {avatar_url}")
        
        if avatar_url.startswith('http://'):
            print("✅ GET请求返回的URL包含HTTP前缀")
        else:
            print("❌ GET请求返回的URL缺少HTTP前缀")
    else:
        print(f"❌ GET请求失败: {get_response.status_code}")

if __name__ == "__main__":
    test_image_url_prefix()