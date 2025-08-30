#!/usr/bin/env python3
"""
测试用户更新API的脚本
"""
import requests
import json

# 测试数据
test_data = {
    "age": 30,
    "bio": "这是一个测试账号，用于开发和测试微信小程序",
    "interests": ["编程", "测试", "开发"],
    "location": "上海市 上海市 徐汇区",
    "occupation": "软件工程师",
    "preferences": {
        "ageRange": [25, 35],
        "distance": 20
    }
}

# API配置
base_url = "http://192.168.71.103:8000/api/v1"
headers = {
    "Content-Type": "application/json",
    "X-Test-Mode": "true"  # 使用测试模式
}

def test_user_update():
    """测试用户更新API"""
    url = f"{base_url}/users/me"
    
    print("测试数据:")
    print(json.dumps(test_data, indent=2, ensure_ascii=False))
    print("\n" + "="*50)
    
    try:
        response = requests.put(url, json=test_data, headers=headers)
        
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ 更新成功!")
            result = response.json()
            print("响应数据:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print("❌ 更新失败!")
            print(f"错误信息: {response.text}")
            
            # 尝试解析错误响应
            try:
                error_data = response.json()
                print("错误详情:")
                print(json.dumps(error_data, indent=2, ensure_ascii=False))
            except:
                pass
                
    except Exception as e:
        print(f"❌ 请求异常: {e}")

if __name__ == "__main__":
    test_user_update()