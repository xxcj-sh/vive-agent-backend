#!/usr/bin/env python3
"""
测试卡片创建流程，验证角色映射是否正确
"""

import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.utils.db_config import get_db
from app.services.user_card_service import UserCardService
from app.models.user_card import CardCreate

def test_card_creation():
    """测试卡片创建流程"""
    print("=== 测试卡片创建流程 ===")
    
    # 获取数据库会话
    db = next(get_db())
    
    # 测试用户ID
    test_user_id = "test_user_001"
    
    # 测试不同的角色组合
    test_cases = [
        ("dating", "dating_seeker"),
        ("dating", "dating_provider"),
        ("housing", "housing_seeker"),
        ("housing", "housing_provider"),
        ("activity", "activity_organizer"),
        ("activity", "activity_participant")
    ]
    
    for scene_type, role_type in test_cases:
        print(f"\n测试场景: {scene_type}, 角色: {role_type}")
        
        try:
            # 检查是否已存在卡片
            existing_card = UserCardService.get_user_card_by_role(
                db, test_user_id, scene_type, role_type
            )
            
            if existing_card:
                print(f"  ✅ 已存在卡片: {existing_card.get('id')}")
            else:
                print("  📝 卡片不存在，可以创建")
                
                # 创建测试卡片数据
                card_data = CardCreate(
                    role_type=role_type,
                    scene_type=scene_type,
                    display_name=f"测试用户_{role_type}",
                    bio=f"这是一个{scene_type}场景的{role_type}测试卡片",
                    profile_data={
                        "age": 25,
                        "gender": "male",
                        "location": "上海市",
                        "birthday": "1998-01-01"
                    },
                    preferences={
                        "age_range": [18, 35],
                        "location": "上海市"
                    },
                    tags=["测试", "开发"],
                    visibility="public"
                )
                
                # 创建卡片
                new_card = UserCardService.create_card(db, test_user_id, card_data)
                print(f"  ✅ 创建成功: {new_card.id}")
                
        except Exception as e:
            print(f"  ❌ 错误: {str(e)}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_card_creation()