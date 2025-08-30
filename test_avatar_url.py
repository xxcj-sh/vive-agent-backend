#!/usr/bin/env python3
"""
测试avatar_url字段的脚本
"""
import requests
import json

# 测试数据
test_cases = [
    {
        "name": "avatar_url_underscore",
        "data": {"avatar_url": "/uploads/test_user_001/b27faa58-825c-426d-b140-1bbaddedf4cc.png"}
    },
    {
        "name": "avatarUrl_camelCase", 
        "data": {"avatarUrl": "/uploads/test_user_001/b27faa58-825c-426d-b140-1bbaddedf4cc.png"}
    },
    {
        "name": "both_formats",
        "data": {
            "avatar_url": "/uploads/test_user_001/underscore.png",
            "avatarUrl": "/uploads/test_user_001/camelcase.png"
        }
    },
    {
        "name": "mixed_fields",
        "data": {
            "avatar_url": "/uploads/test_user_001/b27faa58-825c-426d-b140-1bbaddedf4cc.png",
            "nick_name": "测试用户",
            "age": 25
        }
    }
]

# API配置
base_url = "http://192.168.71.103:8000/api/v1"
headers = {
    "Content-Type": "application/json",
    "X-Test-Mode": "true"
}

def run_test_case(test_case):
    """测试单个用例"""
    url = f"{base_url}/users/me"
    
    print(f"\n{'='*60}")
    print(f"测试用例: {test_case['name']}")
    print(f"数据: {json.dumps(test_case['data'], ensure_ascii=False)}")
    print("-" * 60)
    
    try:
        response = requests.put(url, json=test_case['data'], headers=headers)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 成功!")
            try:
                result = response.json()
                # 只显示相关字段
                relevant_fields = ['avatarUrl', 'nickName', 'age']
                filtered_result = {k: v for k, v in result.items() if k in relevant_fields}
                print(f"相关响应字段: {json.dumps(filtered_result, indent=2, ensure_ascii=False)}")
            except:
                print(f"响应文本: {response.text}")
        else:
            print("❌ 失败!")
            print(f"响应文本: {response.text}")
            
            # 尝试解析错误详情
            try:
                error_data = response.json()
                print(f"错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                pass
                
    except Exception as e:
        print(f"❌ 请求异常: {e}")

def main():
    print("开始测试avatar_url字段...")
    
    for test_case in test_cases:
        run_test_case(test_case)
        
    print(f"\n{'='*60}")
    print("测试完成")

if __name__ == "__main__":
    main()