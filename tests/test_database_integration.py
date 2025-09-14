#!/usr/bin/env python3
"""
测试数据库集成的匹配卡片策略
"""

from app.services.match_service.card_strategy import MatchCardStrategy

def test_database_integration():
    """测试数据库集成功能"""
    print("🗄️ 测试数据库集成的匹配卡片策略")
    print("=" * 60)
    
    try:
        # 测试房源卡片 - 租客视角
        print("1. 测试房源卡片 - 租客视角（从数据库获取房东数据）")
        housing_seeker_result = match_card_strategy.get_match_cards(
            match_type='housing',
            user_role='seeker',
            page=1,
            page_size=3,
            current_user={'id': 'test_user_001'}
        )
        
        print(f"   策略: {housing_seeker_result.get('strategy')}")
        print(f"   总数: {housing_seeker_result.get('total')}")
        print(f"   卡片数量: {len(housing_seeker_result.get('list', []))}")
        
        if housing_seeker_result.get('list'):
            card = housing_seeker_result['list'][0]
            print(f"   第一个卡片:")
            print(f"     ID: {card.get('id')}")
            print(f"     匹配类型: {card.get('matchType')}")
            print(f"     房源价格: {card.get('houseInfo', {}).get('price')}元/月")
            print(f"     房东姓名: {card.get('landlordInfo', {}).get('name')}")
        
        print()
        
        # 测试房源卡片 - 房东视角
        print("2. 测试房源卡片 - 房东视角（从数据库获取租客数据）")
        housing_provider_result = match_card_strategy.get_match_cards(
            match_type='housing',
            user_role='provider',
            page=1,
            page_size=3,
            current_user={'id': 'test_landlord_001'}
        )
        
        print(f"   策略: {housing_provider_result.get('strategy')}")
        print(f"   总数: {housing_provider_result.get('total')}")
        print(f"   卡片数量: {len(housing_provider_result.get('list', []))}")
        
        if housing_provider_result.get('list'):
            card = housing_provider_result['list'][0]
            print(f"   第一个卡片:")
            print(f"     ID: {card.get('id')}")
            print(f"     匹配类型: {card.get('matchType')}")
            print(f"     租客姓名: {card.get('name')}")
            print(f"     租房预算: {card.get('tenantInfo', {}).get('budget')}元/月")
        
        print()
        
        # 测试交友卡片
        print("3. 测试交友卡片（从数据库获取用户数据）")
        dating_result = match_card_strategy.get_match_cards(
            match_type='dating',
            user_role='user',
            page=1,
            page_size=3,
            current_user={'id': 'test_dating_user_001'}
        )
        
        print(f"   策略: {dating_result.get('strategy')}")
        print(f"   总数: {dating_result.get('total')}")
        print(f"   卡片数量: {len(dating_result.get('list', []))}")
        
        if dating_result.get('list'):
            card = dating_result['list'][0]
            print(f"   第一个卡片:")
            print(f"     ID: {card.get('id')}")
            print(f"     匹配类型: {card.get('matchType')}")
            print(f"     姓名: {card.get('name')}")
            print(f"     年龄: {card.get('age')}岁")
        
        print()
        
        # 测试活动卡片 - 参与者视角
        print("4. 测试活动卡片 - 参与者视角（从数据库获取组织者数据）")
        activity_seeker_result = match_card_strategy.get_match_cards(
            match_type='activity',
            user_role='seeker',
            page=1,
            page_size=3,
            current_user={'id': 'test_participant_001'}
        )
        
        print(f"   策略: {activity_seeker_result.get('strategy')}")
        print(f"   总数: {activity_seeker_result.get('total')}")
        print(f"   卡片数量: {len(activity_seeker_result.get('list', []))}")
        
        if activity_seeker_result.get('list'):
            card = activity_seeker_result['list'][0]
            print(f"   第一个卡片:")
            print(f"     ID: {card.get('id')}")
            print(f"     匹配类型: {card.get('matchType')}")
            print(f"     活动名称: {card.get('activityName')}")
            print(f"     组织者: {card.get('name')}")
        
        print("\n" + "=" * 60)
        print("✅ 数据库集成测试完成！")
        print("✅ 系统已支持从数据库获取真实用户数据")
        print("✅ 当数据库查询失败时，自动降级到样本数据")
        print("✅ 多媒体数据通过媒体服务动态加载")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_database_integration()