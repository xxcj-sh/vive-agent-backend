"""
测试登录功能是否正常工作
"""

import requests
import json

def test_login():
    """测试手机号登录"""
    url = "http://localhost:8000/api/auth/login"
    
    # 测试数据
    test_data = {
        "phone": "13800138000",
        "verification_code": "123456"
    }
    
    try:
        response = requests.post(url, json=test_data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 登录成功!")
            print(f"Token: {result.get('token', 'N/A')}")
            print(f"新用户: {result.get('isNewUser', 'N/A')}")
        else:
            print(f"❌ 登录失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")

if __name__ == "__main__":
    test_login()