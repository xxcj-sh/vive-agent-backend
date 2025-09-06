#!/usr/bin/env python3
"""
测试场景API的独立脚本
"""
import requests
import json

def test_scenes_api():
    base_url = "http://localhost:8000"
    
    # 测试场景列表API
    print("Testing /api/v1/scenes...")
    try:
        response = requests.get(f"{base_url}/api/v1/scenes")
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success!")
            print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print("❌ Failed!")
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    # 测试单个场景API
    print("\nTesting /api/v1/scenes/housing...")
    try:
        response = requests.get(f"{base_url}/api/v1/scenes/housing")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success!")
            print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print("❌ Failed!")
            print(f"Error Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_scenes_api()