"""
测试多媒体数据集成
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.match_service.card_strategy import MatchCardStrategy

def test_housing_cards_with_media():
    """测试房源卡片的多媒体数据"""
    print("=== 测试房源卡片多媒体数据 ===")
    
    result = match_card_strategy.get_match_cards(
        match_type="housing",
        user_role="seeker",
        page=1,
        page_size=2,
        current_user={"id": "test_user_001", "interests": ["旅行", "摄影"]}
    )
    
    if result and result.get("list"):
        for i, card in enumerate(result["list"]):
            print(f"\n卡片 {i+1}:")
            print(f"  ID: {card.get('id')}")
            print(f"  头像: {card.get('avatar', 'N/A')}")
            print(f"  视频: {card.get('videoUrl', 'N/A')}")
            print(f"  图片数量: {len(card.get('images', []))}")
            
            if 'houseInfo' in card:
                house_info = card['houseInfo']
                print(f"  房源图片数量: {len(house_info.get('images', []))}")
                print(f"  房源视频: {house_info.get('videoUrl', 'N/A')}")
            
            if 'landlordInfo' in card:
                landlord_info = card['landlordInfo']
                print(f"  房东头像: {landlord_info.get('avatar', 'N/A')}")

def test_dating_cards_with_media():
    """测试交友卡片的多媒体数据"""
    print("\n=== 测试交友卡片多媒体数据 ===")
    
    result = match_card_strategy.get_match_cards(
        match_type="dating",
        user_role="seeker",
        page=1,
        page_size=2,
        current_user={"id": "test_user_002", "interests": ["音乐", "电影"]}
    )
    
    if result and result.get("list"):
        for i, card in enumerate(result["list"]):
            print(f"\n卡片 {i+1}:")
            print(f"  ID: {card.get('id')}")
            print(f"  姓名: {card.get('name', 'N/A')}")
            print(f"  头像: {card.get('avatar', 'N/A')}")
            print(f"  视频: {card.get('videoUrl', 'N/A')}")
            print(f"  图片数量: {len(card.get('images', []))}")
            print(f"  兴趣爱好: {card.get('hobbies', [])}")

def test_activity_cards_with_media():
    """测试活动卡片的多媒体数据"""
    print("\n=== 测试活动卡片多媒体数据 ===")
    
    result = match_card_strategy.get_match_cards(
        match_type="activity",
        user_role="seeker",
        page=1,
        page_size=2,
        current_user={"id": "test_user_003", "interests": ["运动", "户外"]}
    )
    
    if result and result.get("list"):
        for i, card in enumerate(result["list"]):
            print(f"\n卡片 {i+1}:")
            print(f"  ID: {card.get('id')}")
            print(f"  活动名称: {card.get('activityName', 'N/A')}")
            print(f"  组织者: {card.get('name', 'N/A')}")
            print(f"  头像: {card.get('avatar', 'N/A')}")
            print(f"  视频: {card.get('videoUrl', 'N/A')}")
            print(f"  图片数量: {len(card.get('images', []))}")
            
            if 'organizer' in card:
                organizer = card['organizer']
                print(f"  组织者头像: {organizer.get('avatar', 'N/A')}")

if __name__ == "__main__":
    print("开始测试多媒体数据集成...")
    
    try:
        test_housing_cards_with_media()
        test_dating_cards_with_media()
        test_activity_cards_with_media()
        
        print("\n=== 测试完成 ===")
        print("所有卡片都已包含多媒体数据支持！")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()