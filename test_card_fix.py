#!/usr/bin/env python3
"""
测试用户卡片创建功能
"""

import os
import sys
import json

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.models.user_card_db import UserCard
from app.models.user_card import CardCreate
from app.services.user_card_service import UserCardService
from app.database import get_db

def test_card_creation():
    """测试卡片创建"""
    print("测试用户卡片创建...")
    
    try:
        # 获取数据库会话
        db = next(get_db())
        
        # 测试数据 - 模拟错误情况
        test_card_data = CardCreate(
            role_type="activity_organizer",
            scene_type="activity", 
            display_name="测试用户",
            avatar_url="http://example.com/avatar.jpg",
            bio="测试简介",
            trigger_and_output=[],  # 空列表，之前导致错误的参数
            profile_data={},
            preferences={
                "participant_requirements": {
                    "min_age": 18,
                    "max_age": 60,
                    "fitness_level": "",
                    "experience": ""
                },
                "activity_types": [],
                "weather_dependency": "flexible",
                "group_size_preference": ""
            }
        )
        
        # 使用测试用户ID
        test_user_id = "03f90eb6-f5de-4a25-a759-eea1a7f7120e"
        
        print(f"创建卡片数据:")
        print(f"- 角色类型: {test_card_data.role_type}")
        print(f"- 场景类型: {test_card_data.scene_type}")
        print(f"- 显示名称: {test_card_data.display_name}")
        print(f"- trigger_and_output 类型: {type(test_card_data.trigger_and_output)}")
        print(f"- trigger_and_output 值: {test_card_data.trigger_and_output}")
        print(f"- profile_data 类型: {type(test_card_data.profile_data)}")
        print(f"- profile_data 值: {test_card_data.profile_data}")
        
        # 创建卡片
        print("\n正在创建卡片...")
        new_card = UserCardService.create_card(db, test_user_id, test_card_data)
        
        print(f"✅ 卡片创建成功!")
        print(f"- 卡片ID: {new_card.id}")
        print(f"- 创建时间: {new_card.created_at}")
        print(f"- trigger_and_output 类型: {type(new_card.trigger_and_output)}")
        print(f"- trigger_and_output 值: {new_card.trigger_and_output}")
        
        # 验证数据可以正确读取
        print("\n验证数据读取...")
        retrieved_card = UserCardService.get_card_by_id(db, new_card.id)
        if retrieved_card:
            print(f"✅ 数据读取成功!")
            print(f"- trigger_and_output 类型: {type(retrieved_card.trigger_and_output)}")
            print(f"- trigger_and_output 值: {retrieved_card.trigger_and_output}")
        else:
            print("❌ 数据读取失败!")
        
        # 清理测试数据
        print("\n清理测试数据...")
        UserCardService.delete_card(db, new_card.id)
        print("✅ 测试数据已清理")
        
        db.close()
        print("\n✅ 测试完成!")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    test_card_creation()