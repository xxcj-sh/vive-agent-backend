#!/usr/bin/env python3
"""
测试用户卡片JSON序列化修复
验证创建和更新操作都能正确处理JSON字段
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.services.user_card_service import UserCardService
from app.models.user_card import CardCreate
from app.models.user_card_db import UserCard
import json

def test_card_json_operations():
    """测试卡片JSON字段的创建和更新"""
    db = SessionLocal()
    
    try:
        print("=== 测试用户卡片JSON序列化修复 ===\n")
        
        # 测试数据
        test_user_id = "test_user_001"
        
        # 1. 测试创建卡片 - 包含空列表和复杂数据
        print("1. 测试创建卡片...")
        card_data = CardCreate(
            role_type="activity_organizer",
            scene_type="activity", 
            display_name="测试用户",
            avatar_url="https://example.com/avatar.jpg",
            bio="这是一个测试用户",
            trigger_and_output=[],  # 空列表
            profile_data={
                "organizing_experience": "3年",
                "specialties": ["户外运动", "团队建设"],
                "group_size_preference": "10-20人"
            },
            preferences={
                "participant_requirements": {"min_age": 18},
                "activity_types": ["徒步", "聚餐"]
            },
            visibility="public"
        )
        
        # 创建卡片
        created_card = UserCardService.create_card(db, test_user_id, card_data)
        print(f"✅ 卡片创建成功: {created_card.id}")
        
        # 验证数据库中的数据类型
        db_card = db.query(UserCard).filter(UserCard.id == created_card.id).first()
        print(f"- trigger_and_output 类型: {type(db_card.trigger_and_output)}")
        print(f"- trigger_and_output 值: {db_card.trigger_and_output}")
        print(f"- profile_data 类型: {type(db_card.profile_data)}")
        print(f"- profile_data 值: {db_card.profile_data}")
        print(f"- preferences 类型: {type(db_card.preferences)}")
        print(f"- preferences 值: {db_card.preferences}")
        
        # 2. 测试读取卡片数据（应该解析JSON字符串）
        print("\n2. 测试读取卡片数据...")
        card_data_read = UserCardService.get_user_card_by_role(db, test_user_id, "activity", "activity_organizer")
        if card_data_read:
            print("✅ 数据读取成功")
            print(f"- trigger_and_output 类型: {type(card_data_read['trigger_and_output'])}")
            print(f"- trigger_and_output 值: {card_data_read['trigger_and_output']}")
            print(f"- profile_data 类型: {type(card_data_read['profile_data'])}")
            print(f"- profile_data 值: {card_data_read['profile_data']}")
            print(f"- preferences 类型: {type(card_data_read['preferences'])}")
            print(f"- preferences 值: {card_data_read['preferences']}")
        else:
            print("❌ 数据读取失败")
        
        # 3. 测试更新卡片 - 修改JSON字段
        print("\n3. 测试更新卡片...")
        update_data = {
            "bio": "更新后的简介",
            "trigger_and_output": [
                {"trigger": "天气好", "output": "组织户外活动"},
                {"trigger": "周末", "output": "安排聚餐"}
            ],
            "profile_data": {
                "organizing_experience": "5年",
                "specialties": ["户外运动", "团队建设", "文化交流"],
                "group_size_preference": "15-30人"
            }
        }
        
        updated_card = UserCardService.update_card(db, created_card.id, update_data)
        if updated_card:
            print("✅ 卡片更新成功")
            print(f"- 更新后的bio: {updated_card.bio}")
            print(f"- 更新后的trigger_and_output: {updated_card.trigger_and_output}")
            print(f"- 更新后的profile_data: {updated_card.profile_data}")
            
            # 验证更新后的数据读取
            updated_data_read = UserCardService.get_user_card_by_role(db, test_user_id, "activity", "activity_organizer")
            if updated_data_read:
                print("✅ 更新数据读取成功")
                print(f"- 触发器和输出: {updated_data_read['trigger_and_output']}")
                print(f"- 专业领域: {updated_data_read['profile_data']['specialties']}")
        else:
            print("❌ 卡片更新失败")
        
        # 4. 测试边界情况 - 空值和无效数据
        print("\n4. 测试边界情况...")
        boundary_update = {
            "trigger_and_output": None,  # 空值
            "profile_data": {},  # 空对象
            "preferences": None  # 空值
        }
        
        boundary_card = UserCardService.update_card(db, created_card.id, boundary_update)
        if boundary_card:
            print("✅ 边界情况处理成功")
            print(f"- 空值处理后的trigger_and_output: {boundary_card.trigger_and_output}")
            print(f"- 空对象处理后的profile_data: {boundary_card.profile_data}")
            print(f"- 空值处理后的preferences: {boundary_card.preferences}")
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # 清理测试数据
        print("\n清理测试数据...")
        try:
            db.query(UserCard).filter(UserCard.user_id == test_user_id).delete()
            db.commit()
            print("✅ 测试数据已清理")
        except Exception as e:
            print(f"清理数据时出错: {e}")
        
        db.close()

if __name__ == "__main__":
    test_card_json_operations()