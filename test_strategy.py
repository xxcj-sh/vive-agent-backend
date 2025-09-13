#!/usr/bin/env python3
"""
直接测试匹配卡片策略
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('ENVIRONMENT', 'development')

from app.services.match_card_strategy import match_card_strategy

def test_match_card_strategy():
    """测试匹配卡片策略"""
    print("🧪 测试匹配卡片策略...")
    
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
            result = match_card_strategy.get_match_cards(
                match_type=case["match_type"],
                user_role=case["user_role"],
                page=case["page"],
                page_size=case["page_size"]
            )
            
            print(f"✅ {case['match_type']}-{case['user_role']}: 成功")
            print(f"   📊 总数: {result.get('total', 0)}")
            print(f"   📄 页数: {result.get('page', 0)}/{result.get('pageSize', 0)}")
            print(f"   🔍 策略: {result.get('strategy', 'unknown')}")
            
            if result.get('list'):
                print(f"   👤 示例: {result['list'][0].get('name', '匿名用户')}")
            else:
                print("   📭 暂无数据")
                
        except Exception as e:
            print(f"❌ {case['match_type']}-{case['user_role']}: 错误 - {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n🎉 策略测试完成！")

if __name__ == "__main__":
    test_match_card_strategy()