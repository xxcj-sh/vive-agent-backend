#!/usr/bin/env python3
"""
调试422错误的脚本
"""
import requests
import json

# 测试不同的数据格式
test_cases = [
    # 测试1：最简单的数据
    {
        "name": "simple_age",
        "data": {"age": 30}
    },
    # 测试2：字符串字段
    {
        "name": "simple_string",
        "data": {"bio": "test bio"}
    },
    # 测试3：数组字段
    {
        "name": "simple_array",
        "data": {"interests": ["test"]}
    },
    # 测试4：对象字段
    {
        "name": "simple_object",
        "data": {"preferences": {"test": "value"}}
    },
    # 测试5：location字符串
    {
        "name": "location_string",
        "data": {"location": "上海市 上海市 徐汇区"}
    },
    # 测试6：完整数据
    {
        "name": "full_data",
        "data": {
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
                print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
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
    print("开始调试422错误...")
    
    for test_case in test_cases:
        run_test_case(test_case)
        
    print(f"\n{'='*60}")
    print("调试完成")

if __name__ == "__main__":
    main()