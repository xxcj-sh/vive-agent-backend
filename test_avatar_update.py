#!/usr/bin/env python3
"""
测试头像更新是否真的保存到数据库
"""
import requests
import json

# API配置
base_url = "http://192.168.71.103:8000/api/v1"
headers = {
    "Content-Type": "application/json",
    "X-Test-Mode": "true"
}

def test_avatar_update():
    """测试头像更新流程"""
    url = f"{base_url}/users/me"
    
    print("=== 头像更新测试 ===")
    
    # 1. 获取当前用户信息
    print("1. 获取当前用户信息...")
    get_response = requests.get(url, headers=headers)
    if get_response.status_code == 200:
        current_user = get_response.json()
        current_avatar = current_user.get('avatarUrl', 'NOT_FOUND')
        print(f"当前头像: {current_avatar}")
    else:
        print("❌ 获取用户信息失败")
        return
    
    # 2. 更新头像
    new_avatar = "http://192.168.71.103:8000/uploads/test_user_001/b11b8ec9-ce22-4335-b6e9-2ca38159a8d4.jpg"
    update_data = {"avatar_url": new_avatar}
    
    print(f"\n2. 更新头像为: {new_avatar}")
    put_response = requests.put(url, json=update_data, headers=headers)
    
    if put_response.status_code == 200:
        updated_user = put_response.json()
        updated_avatar = updated_user.get('avatarUrl', 'NOT_FOUND')
        print(f"✅ 更新请求成功")
        print(f"响应中的头像: {updated_avatar}")
        
        # 检查是否真的更新了
        if updated_avatar == new_avatar:
            print("✅ 响应中头像已更新")
        else:
            print("❌ 响应中头像未更新")
    else:
        print("❌ 更新请求失败")
        print(f"状态码: {put_response.status_code}")
        print(f"响应: {put_response.text}")
        return
    
    # 3. 重新获取用户信息验证
    print(f"\n3. 重新获取用户信息验证...")
    verify_response = requests.get(url, headers=headers)
    
    if verify_response.status_code == 200:
        verify_user = verify_response.json()
        verify_avatar = verify_user.get('avatarUrl', 'NOT_FOUND')
        print(f"验证获取的头像: {verify_avatar}")
        
        if verify_avatar == new_avatar:
            print("✅ 数据库中头像已更新！")
        else:
            print("❌ 数据库中头像未更新！")
            print(f"期望: {new_avatar}")
            print(f"实际: {verify_avatar}")
    else:
        print("❌ 验证请求失败")

if __name__ == "__main__":
    test_avatar_update()