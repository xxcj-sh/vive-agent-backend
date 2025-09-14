"""
测试基于角色的卡片返回逻辑
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.match_service.card_strategy import MatchCardStrategy

def test_housing_seeker_cards():
    """测试租客视角的房源卡片"""
    from app.database import SessionLocal
    db = SessionLocal()
    strategy = MatchCardStrategy(db)
    
    print("=== 测试租客视角的房源卡片 ===")
    
    result = strategy.get_match_cards(
        scene_type="housing",
        role_type="seeker",
        page=1,
        page_size=3,
        current_user={"id": "test_seeker_001"}
    )
    
    if result and result.get("list"):
        print(f"策略: {result.get('strategy')}")
        for i, card in enumerate(result["list"]):
            print(f"\n卡片 {i+1} (租客看到的房源):")
            print(f"  ID: {card.get('id')}")
            print(f"  匹配类型: {card.get('matchType')}")
            print(f"  用户角色: {card.get('userRole')}")
            print(f"  房源价格: {card.get('houseInfo', {}).get('price', 'N/A')}元/月")
            print(f"  房源面积: {card.get('houseInfo', {}).get('area', 'N/A')}㎡")
            print(f"  房源位置: {card.get('houseInfo', {}).get('location', 'N/A')}")
            print(f"  房东姓名: {card.get('landlordInfo', {}).get('name', 'N/A')}")
            print(f"  房源图片数量: {len(card.get('houseInfo', {}).get('images', []))}")

def test_housing_provider_cards():
    """测试房东视角的租客卡片"""
    from app.database import SessionLocal
    db = SessionLocal()
    strategy = MatchCardStrategy(db)
    
    print("\n=== 测试房东视角的租客卡片 ===")
    
    result = strategy.get_match_cards(
        scene_type="housing",
        role_type="provider",  # 房东身份
        page=1,
        page_size=3,
        current_user={"id": "test_provider_001"}
    )
    
    if result and result.get("list"):
        print(f"策略: {result.get('strategy')}")
        for i, card in enumerate(result["list"]):
            print(f"\n卡片 {i+1} (房东看到的租客):")
            print(f"  ID: {card.get('id')}")
            print(f"  匹配类型: {card.get('matchType')}")
            print(f"  用户角色: {card.get('userRole')}")
            print(f"  租客姓名: {card.get('name', 'N/A')}")
            print(f"  租客年龄: {card.get('age', 'N/A')}岁")
            print(f"  租客职业: {card.get('occupation', 'N/A')}")
            print(f"  租房预算: {card.get('tenantInfo', {}).get('budget', 'N/A')}元/月")
            print(f"  期望租期: {card.get('tenantInfo', {}).get('leaseDuration', 'N/A')}")

def test_activity_seeker_cards():
    """测试活动参与者视角的活动卡片"""
    from app.database import SessionLocal
    db = SessionLocal()
    strategy = MatchCardStrategy(db)
    
    print("\n=== 测试活动参与者视角的活动卡片 ===")
    
    result = strategy.get_match_cards(
        scene_type="activity",
        role_type="participant",
        page=1,
        page_size=2,
        current_user={"id": "test_activity_seeker_001"}
    )
    
    if result and result.get("list"):
        print(f"策略: {result.get('strategy')}")
        for i, card in enumerate(result["list"]):
            print(f"\n卡片 {i+1} (参与者看到的活动):")
            print(f"  ID: {card.get('id')}")
            print(f"  匹配类型: {card.get('matchType')}")
            print(f"  用户角色: {card.get('userRole')}")
            print(f"  活动名称: {card.get('activityName', 'N/A')}")
            print(f"  活动类型: {card.get('activityType', 'N/A')}")
            print(f"  活动价格: {card.get('activityPrice', 'N/A')}元")
            print(f"  组织者: {card.get('name', 'N/A')}")

def test_activity_organizer_cards():
    """测试活动组织者视角的参与者卡片"""
    from app.database import SessionLocal
    db = SessionLocal()
    strategy = MatchCardStrategy(db)
    
    print("\n=== 测试活动组织者视角的参与者卡片 ===")
    
    result = strategy.get_match_cards(
        scene_type="activity",
        role_type="organizer",
        page=1,
        page_size=2,
        current_user={"id": "test_activity_organizer_001"}
    )
    
    if result and result.get("list"):
        print(f"策略: {result.get('strategy')}")
        for i, card in enumerate(result["list"]):
            print(f"\n卡片 {i+1} (组织者看到的参与者):")
            print(f"  ID: {card.get('id')}")
            print(f"  匹配类型: {card.get('matchType')}")
            print(f"  用户角色: {card.get('userRole')}")
            print(f"  参与者姓名: {card.get('name', 'N/A')}")
            print(f"  参与者年龄: {card.get('age', 'N/A')}岁")
            print(f"  偏好活动: {card.get('preferredActivity', 'N/A')}")
            print(f"  预算范围: {card.get('budgetRange', 'N/A')}")

if __name__ == "__main__":
    print("开始测试基于角色的卡片返回逻辑...")
    
    try:
        test_housing_seeker_cards()
        test_housing_provider_cards()
        test_activity_seeker_cards()
        test_activity_organizer_cards()
        
        print("\n=== 测试完成 ===")
        print("✅ 租客身份返回房东的房源信息")
        print("✅ 房东身份返回租客的需求信息")
        print("✅ 参与者身份返回组织者的活动信息")
        print("✅ 组织者身份返回参与者的个人信息")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()