#!/usr/bin/env python3
"""
测试完整的匹配推荐API
"""
import sys
import os
import requests
import json

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('ENVIRONMENT', 'development')

def test_recommendation_api():
    """测试匹配推荐API"""
    base_url = "http://localhost:8000"
    
    print("🧪 测试匹配推荐API...")
    
    # 测试参数
    test_cases = [
        {"match_type": "dating", "user_role": "seeker", "page": 1, "page_size": 5},
        {"match_type": "housing", "user_role": "seeker", "page": 1, "page_size": 5},
        {"match_type": "housing", "user_role": "provider", "page": 1, "page_size": 5},
        {"match_type": "activity", "user_role": "participant", "page": 1, "page_size": 5},
        {"match_type": "activity", "user_role": "organizer", "page": 1, "page_size": 5},
    ]
    
    for case in test_cases:
        try:
            url = f"{base_url}/api/v1/matches/recommendations"
            params = {
                "sceneType": case["match_type"],
                "roleType": case["user_role"],
                "page": case["page"],
                "pageSize": case["page_size"]
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {case['match_type']}-{case['user_role']}: 成功")
                print(f"   📊 总数: {data.get('total', 0)}")
                print(f"   📄 页数: {data.get('page', 0)}/{data.get('pageSize', 0)}")
                print(f"   🔍 策略: {data.get('strategy', 'unknown')}")
                if data.get('list'):
                    print(f"   👤 示例: {data['list'][0].get('name', '匿名用户')}")
            else:
                print(f"❌ {case['match_type']}-{case['user_role']}: HTTP {response.status_code}")
                print(f"   {response.text}")
                
        except Exception as e:
            print(f"❌ {case['match_type']}-{case['user_role']}: 错误 - {str(e)}")
    
    print("\n🎉 API测试完成！")

if __name__ == "__main__":
    test_recommendation_api()