#!/usr/bin/env python3
"""
测试卡片API的新增接口
测试 POST, PUT, DELETE 方法
"""

import requests
import json
from typing import Dict, Any

# 测试配置
BASE_URL = "http://localhost:8000/api/v1/cards"
TEST_TOKEN = "test_token_001"
HEADERS = {
    "Authorization": f"Bearer {TEST_TOKEN}",
    "Content-Type": "application/json"
}

def test_create_card():
    """测试创建卡片"""
    print("🧪 测试创建卡片...")
    
    card_data = {
        "role_type": "housing_seeker",
        "scene_type": "housing",
        "display_name": "测试找房者",
        "bio": "寻找一个舒适的家",
        "visibility": "public",
        "profile_data": {
            "budget_range": [2000, 4000],
            "preferred_areas": ["朝阳区", "海淀区"],
            "room_type": "整租",
            "move_in_date": "2024-12-01",
            "lease_duration": "1年",
            "lifestyle": "安静",
            "work_schedule": "朝九晚五",
            "pets": False,
            "smoking": False,
            "occupation": "程序员",
            "company_location": "中关村"
        },
        "preferences": {
            "roommate_gender": "any",
            "roommate_age_range": [20, 35],
            "shared_facilities": ["厨房", "洗衣机"],
            "transportation": ["地铁", "公交"],
            "nearby_facilities": ["超市", "餐厅", "健身房"]
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/cards/",
            json=card_data,
            headers=HEADERS
        )
        
        if response.status_code == 201 or response.status_code == 200:
            result = response.json()
            print(f"✅ 创建成功: {result}")
            return result.get("data", {}).get("id")
        else:
            print(f"❌ 创建失败: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 创建请求异常: {e}")
        return None

def test_update_card(card_id: str):
    """测试更新卡片"""
    print(f"🧪 测试更新卡片 {card_id}...")
    
    update_data = {
        "display_name": "更新后的找房者",
        "bio": "更新后的简介：寻找温馨小窝",
        "visibility": "private",
        "profile_data": {
            "budget_range": [2500, 4500],
            "preferred_areas": ["朝阳区", "海淀区", "西城区"]
        }
    }
    
    try:
        response = requests.put(
            f"{BASE_URL}/cards/{card_id}",
            json=update_data,
            headers=HEADERS
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 更新成功: {result}")
            return True
        else:
            print(f"❌ 更新失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 更新请求异常: {e}")
        return False

def test_delete_card(card_id: str):
    """测试删除卡片"""
    print(f"🧪 测试删除卡片 {card_id}...")
    
    try:
        response = requests.delete(
            f"{BASE_URL}/cards/{card_id}",
            headers=HEADERS
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 删除成功: {result}")
            return True
        else:
            print(f"❌ 删除失败: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 删除请求异常: {e}")
        return False

def test_get_card(card_id: str):
    """测试获取卡片详情"""
    print(f"🧪 测试获取卡片 {card_id}...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/cards/{card_id}",
            headers=HEADERS
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 获取成功: {result}")
            return result
        else:
            print(f"❌ 获取失败: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 获取请求异常: {e}")
        return None

def main():
    """主测试函数"""
    print("🚀 开始测试卡片API...")
    print(f"基础URL: {BASE_URL}")
    
    # 测试创建卡片
    card_id = test_create_card()
    
    if card_id:
        # 测试获取卡片
        test_get_card(card_id)
        
        # 测试更新卡片
        test_update_card(card_id)
        
        # 再次获取验证更新
        test_get_card(card_id)
        
        # 测试删除卡片
        test_delete_card(card_id)
        
        # 验证删除后无法获取
        test_get_card(card_id)
    
    print("🏁 测试完成！")

if __name__ == "__main__":
    main()