#!/usr/bin/env python3
"""
详细调试脚本
"""
import requests
import json

# 测试数据
test_data = {
    "avatar_url": "/uploads/test_user_001/b27faa58-825c-426d-b140-1bbaddedf4cc.png"
}

# API配置
base_url = "http://192.168.71.103:8000/api/v1"
headers = {
    "Content-Type": "application/json",
    "X-Test-Mode": "true"
}

def test_with_debug():
    """带调试信息的测试"""
    url = f"{base_url}/users/me"
    
    print("详细调试测试:")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Data: {json.dumps(test_data, ensure_ascii=False)}")
    print("="*60)
    
    try:
        # 先测试GET请求确认认证正常
        print("1. 测试GET请求...")
        get_response = requests.get(url, headers=headers)
        print(f"GET状态码: {get_response.status_code}")
        
        if get_response.status_code != 200:
            print("❌ GET请求失败，认证可能有问题")
            print(f"GET响应: {get_response.text}")
            return
        
        print("✅ GET请求成功，认证正常")
        
        # 测试PUT请求
        print("\n2. 测试PUT请求...")
        put_response = requests.put(url, json=test_data, headers=headers)
        print(f"PUT状态码: {put_response.status_code}")
        print(f"PUT响应头: {dict(put_response.headers)}")
        
        if put_response.status_code == 200:
            print("✅ PUT请求成功!")
            result = put_response.json()
            print(f"avatarUrl字段: {result.get('avatarUrl', 'NOT_FOUND')}")
        else:
            print("❌ PUT请求失败!")
            print(f"响应内容: {put_response.text}")
            
            # 尝试解析JSON错误
            try:
                error_json = put_response.json()
                print(f"错误JSON: {json.dumps(error_json, indent=2, ensure_ascii=False)}")
            except:
                print("无法解析为JSON")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        import traceback
        print(f"异常详情: {traceback.format_exc()}")

if __name__ == "__main__":
    test_with_debug()