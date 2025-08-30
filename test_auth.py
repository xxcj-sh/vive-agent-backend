#!/usr/bin/env python3
"""
测试认证的脚本
"""
import requests
import json

# API配置
base_url = "http://192.168.71.103:8000/api/v1"
headers = {
    "Content-Type": "application/json",
    "X-Test-Mode": "true"
}

def test_get_user():
    """测试获取用户信息"""
    url = f"{base_url}/users/me"
    
    print("测试GET /users/me...")
    
    try:
        response = requests.get(url, headers=headers)
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            print("✅ GET请求成功!")
            return True
        else:
            print("❌ GET请求失败!")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def test_put_user():
    """测试更新用户信息"""
    url = f"{base_url}/users/me"
    data = {"age": 30}
    
    print("\n测试PUT /users/me...")
    print(f"数据: {json.dumps(data)}")
    
    try:
        response = requests.put(url, json=data, headers=headers)
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            print("✅ PUT请求成功!")
            return True
        else:
            print("❌ PUT请求失败!")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return False

def main():
    print("开始测试认证...")
    
    # 先测试GET请求
    get_success = test_get_user()
    
    if get_success:
        # 如果GET成功，再测试PUT请求
        test_put_user()
    else:
        print("GET请求失败，跳过PUT测试")

if __name__ == "__main__":
    main()