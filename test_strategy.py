#!/usr/bin/env python3
"""
直接测试匹配卡片策略
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('ENVIRONMENT', 'development')

from app.services.match_service.card_strategy import MatchCardStrategy

def test_match_card_strategy():
    """测试匹配卡片策略"""
    print("🧪 测试匹配卡片策略...")
    
    from app.database import SessionLocal
    db = SessionLocal()
    strategy = MatchCardStrategy(db)
    
    # 测试参数
    test_cases = [
        {"scene_type": "dating", "role_type": "seeker", "page": 1, "page_size": 5},
        {"scene_type": "housing", "role_type": "seeker", "page": 1, "page_size": 5},
        {"scene_type": "housing", "role_type": "provider", "page": 1, "page_size": 5},
        {"scene_type": "activity", "role_type": "participant", "page": 1, "page_size": 5},
        {"scene_type": "activity", "role_type": "organizer", "page": 1, "page_size": 5},
    ]
    
    for case in test_cases:
        try:
            result = strategy.get_match_cards(
                scene_type=case["scene_type"],
                role_type=case["role_type"],
                page=case["page"],
                page_size=case["page_size"],
                current_user={"id": "test_user_001"}
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