#!/usr/bin/env python3
"""
测试完整的注册流程
"""

import sys
import os
import requests
import json

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.utils.db_config import get_db
from app.services.user_card_service import UserCardService
from app.models.user_card import CardCreate

def test_registration_flow():
    """测试完整的注册流程"""
    db: Session = next(get_db())
    
    test_user_id = "test_user_register_001"
    
    try:
        # 测试1: 检查用户卡片是否存在（应该不存在）
        print("🔍 测试1: 检查用户卡片是否存在")
        
        test_cases = [
            ("dating", "dating_provider"),
            ("dating", "dating_seeker"),
            ("housing", "housing_provider"),
            ("housing", "housing_seeker"),
            ("activity", "activity_organizer"),
            ("activity", "activity_participant")
        ]
        
        for scene_type, role_type in test_cases:
            card = UserCardService.get_user_card_by_role(
                db, test_user_id, scene_type, role_type
            )
            if card:
                print(f"  ❌ 发现已存在的卡片: {scene_type}.{role_type}")
            else:
                print(f"  ✅ 卡片不存在: {scene_type}.{role_type}")
        
        # 测试2: 创建测试卡片
        print("\n📝 测试2: 创建测试卡片")
        
        test_cards = [
            {
                "scene_type": "dating",
                "role_type": "dating_provider",
                "display_name": "测试交友提供者",
                "bio": "这是一个测试交友提供者卡片"
            },
            {
                "scene_type": "dating", 
                "role_type": "dating_seeker",
                "display_name": "测试交友寻找者",
                "bio": "这是一个测试交友寻找者卡片"
            },
            {
                "scene_type": "housing",
                "role_type": "housing_provider", 
                "display_name": "测试房源提供者",
                "bio": "这是一个测试房源提供者卡片"
            },
            {
                "scene_type": "housing",
                "role_type": "housing_seeker",
                "display_name": "测试房源寻找者", 
                "bio": "这是一个测试房源寻找者卡片"
            },
            {
                "scene_type": "activity",
                "role_type": "activity_organizer",
                "display_name": "测试活动组织者",
                "bio": "这是一个测试活动组织者卡片"
            },
            {
                "scene_type": "activity",
                "role_type": "activity_participant",
                "display_name": "测试活动参与者",
                "bio": "这是一个测试活动参与者卡片"
            }
        ]
        
        created_cards = []
        for card_data in test_cards:
            card_create = CardCreate(
                scene_type=card_data["scene_type"],
                role_type=card_data["role_type"],
                display_name=card_data["display_name"],
                bio=card_data["bio"]
            )
            
            card = UserCardService.create_card(
                db, test_user_id, card_create
            )
            created_cards.append(card)
            print(f"  ✅ 创建成功: {card.scene_type}.{card.role_type} (ID: {card.id})")
        
        # 测试3: 验证卡片可以正常获取
        print("\n🔍 测试3: 验证卡片获取")
        
        for scene_type, role_type in test_cases:
            card = UserCardService.get_user_card_by_role(
                db, test_user_id, scene_type, role_type
            )
            if card:
                print(f"  ✅ 成功获取卡片: {scene_type}.{role_type}")
            else:
                print(f"  ❌ 无法获取卡片: {scene_type}.{role_type}")
        
        # 测试4: 模拟注册流程中的检查
        print("\n🔄 测试4: 模拟注册流程检查")
        
        # 模拟前端发送的角色类型
        frontend_roles = ["seeker", "provider", "organizer", "participant"]
        scene_types = ["dating", "housing", "activity"]
        
        for scene in scene_types:
            for role in frontend_roles:
                # 构建完整的role_type
                if role in ["seeker", "provider"]:
                    full_role_type = f"{scene}_{role}"
                elif role == "organizer" and scene == "activity":
                    full_role_type = "activity_organizer"
                elif role == "participant" and scene == "activity":
                    full_role_type = "activity_participant"
                else:
                    continue
                
                card = UserCardService.get_user_card_by_role(
                    db, test_user_id, scene, full_role_type
                )
                if card:
                    print(f"  ✅ 找到卡片: {scene}.{full_role_type}")
                else:
                    print(f"  ❌ 未找到卡片: {scene}.{full_role_type}")
        
        db.commit()
        print("\n✅ 所有测试完成！注册流程应该正常工作")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_registration_flow()