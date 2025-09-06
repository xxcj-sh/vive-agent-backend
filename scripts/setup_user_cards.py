#!/usr/bin/env python3
"""
基于新数据模型设置用户卡片测试数据
使用新的卡片模型结构
"""

import sys
import os
from datetime import datetime
import uuid
import json

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db, engine, Base
from app.models.user import User
from app.models.user_card_db import UserCard
from app.models.card_profiles import (
    HouseSeekerProfile, HouseProfile, DatingProfile,
    ActivityOrganizerProfile, ActivityParticipantProfile
)
from app.models.card_preferences import (
    HouseSeekerPreferences, HousePreferences, DatingPreferences,
    ActivityOrganizerPreferences, ActivityParticipantPreferences
)

def setup_user_cards():
    """设置用户卡片测试数据"""
    
    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        print("数据库表已创建/验证")
        
        # 获取数据库会话
        db = next(get_db())
        
        print("开始设置用户卡片测试数据...")
        
        # 1. 创建测试用户（如果不存在）
        test_users_data = [
            ('test_user_001', 'test_user_001@test.com', '13800000001', '测试用户001'),
            ('test_user_002', 'test_user_002@test.com', '13800000002', '测试用户002'),
            ('test_user_003', 'test_user_003@test.com', '13800000003', '测试用户003'),
            ('test_user_004', 'test_user_004@test.com', '13800000004', '测试用户004'),
            ('test_user_005', 'test_user_005@test.com', '13800000005', '测试用户005'),
        ]
        
        users = {}
        for username, email, phone, nickname in test_users_data:
            # 检查用户是否已存在
            existing_user = db.query(User).filter(User.username == username).first()
            if existing_user:
                users[username] = existing_user
                print(f"用户 {username} 已存在")
            else:
                user = User(
                    id=str(uuid.uuid4()),
                    username=username,
                    email=email,
                    phone=phone,
                    nickname=nickname,
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(user)
                db.flush()  # 获取ID
                users[username] = user
                print(f"创建用户 {username}")
        
        print(f"准备了 {len(users)} 个测试用户")
        
        # 2. 清理现有用户卡片数据
        for username in test_users_data:
            user = users[username[0]]
            existing_cards = db.query(UserCard).filter(UserCard.user_id == user.id).all()
            for card in existing_cards:
                db.delete(card)
        
        print("清理了现有用户卡片数据")
        
        # 3. 为每个用户创建不同角色的卡片
        user_cards = []
        
        # 用户1：找房者卡片
        house_seeker_profile = HouseSeekerProfile(
            budget_range=[2000, 4000],
            preferred_areas=["朝阳区", "海淀区"],
            room_type="两居室",
            move_in_date="2024-03-01",
            lease_duration="1年",
            lifestyle="安静，不抽烟",
            work_schedule="朝九晚五",
            pets=False,
            smoking=False,
            occupation="软件工程师",
            company_location="中关村"
        )
        
        house_seeker_preferences = HouseSeekerPreferences(
            preferred_price_range=[1500, 4500],
            preferred_locations=["朝阳区", "海淀区", "西城区"],
            room_type_preferences=["一居室", "两居室"],
            lease_duration_preference=["6个月", "1年", "2年"],
            pet_policy="no_pets",
            smoking_policy="no_smoking",
            max_distance_km=15
        )
        
        card1 = UserCard(
            id=str(uuid.uuid4()),
            user_id=users['test_user_001'].id,
            role_type="house_seeker",
            scene_type="housing",
            bio="寻找安静舒适的居住环境，希望找到志同道合的室友",
            profile_data=house_seeker_profile.dict(),
            preferences=house_seeker_preferences.dict(),
            visibility="public",
            is_active=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(card1)
        user_cards.append(card1)
        
        # 用户2：房源提供者卡片
        house_profile = HouseProfile(
            property_type="公寓",
            rooms=2,
            area=80,
            price=3500,
            location=["朝阳区", "望京"],
            amenities=["wifi", "空调", "洗衣机", "冰箱"],
            lease_terms="押一付三，最少租期6个月",
            available_from="2024-02-15",
            description="精装修两居室，采光好，交通便利"
        )
        
        house_preferences = HousePreferences(
            preferred_tenant_type=["上班族", "学生"],
            preferred_gender=["不限"],
            preferred_age_range=[20, 35],
            preferred_occupation=["IT", "金融", "教育"],
            smoking_policy="prefer_no_smoking",
            pet_policy="small_pets_allowed",
            max_tenants=2
        )
        
        card2 = UserCard(
            id=str(uuid.uuid4()),
            user_id=users['test_user_002'].id,
            role_type="house_provider",
            scene_type="housing",
            bio="望京精装修两居室出租，希望找到爱干净的租客",
            profile_data=house_profile.dict(),
            preferences=house_preferences.dict(),
            visibility="public",
            is_active=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(card2)
        user_cards.append(card2)
        
        # 用户3：交友卡片
        dating_profile = DatingProfile(
            age=28,
            height=175,
            education="本科",
            occupation="产品经理",
            income_range="15k-20k",
            relationship_status="单身",
            looking_for="认真交往",
            hobbies=["阅读", "旅行", "摄影", "健身"],
            personality=["开朗", "有责任心", "幽默"],
            lifestyle={"drinking": "偶尔", "smoking": "不抽烟", "exercise": "每周3次"}
        )
        
        dating_preferences = DatingPreferences(
            preferred_age_range=[25, 32],
            preferred_height_range=[160, 175],
            preferred_education_levels=["本科", "硕士"],
            preferred_occupations=["IT", "金融", "教育", "医疗"],
            preferred_relationship_status=["单身"],
            looking_for_match=["认真交往", "结婚"],
            shared_interests_weight=0.7,
            personality_compatibility=["开朗", "温柔", "有责任心"],
            max_distance_km=20
        )
        
        card3 = UserCard(
            id=str(uuid.uuid4()),
            user_id=users['test_user_003'].id,
            role_type="dating_user",
            scene_type="dating",
            bio="寻找真诚交往的另一半，希望三观一致，有共同话题",
            profile_data=dating_profile.dict(),
            preferences=dating_preferences.dict(),
            visibility="public",
            is_active=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(card3)
        user_cards.append(card3)
        
        # 用户4：活动组织者卡片
        organizer_profile = ActivityOrganizerProfile(
            activity_types=["户外徒步", "读书会", "桌游"],
            preferred_locations=["朝阳区", "海淀区"],
            group_size="5-10人",
            activity_frequency="每周2-3次",
            experience_level="经验丰富",
            interests=["阅读", "运动", "社交"]
        )
        
        organizer_preferences = ActivityOrganizerPreferences(
            preferred_participant_count=[3, 8],
            preferred_locations=["朝阳区", "海淀区", "西城区"],
            participant_age_range=[20, 40],
            participant_gender_preference="不限",
            shared_interests_weight=0.6,
            activity_type_preferences=["户外徒步", "读书会", "桌游", "运动"]
        )
        
        card4 = UserCard(
            id=str(uuid.uuid4()),
            user_id=users['test_user_004'].id,
            role_type="activity_organizer",
            scene_type="activity",
            bio="喜欢组织各种有趣的活动，希望认识更多志同道合的朋友",
            profile_data=organizer_profile.dict(),
            preferences=organizer_preferences.dict(),
            visibility="public",
            is_active=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(card4)
        user_cards.append(card4)
        
        # 用户5：活动参与者卡片
        participant_profile = ActivityParticipantProfile(
            preferred_activities=["户外徒步", "摄影", "美食探店"],
            availability="周末和晚上",
            experience_level="初学者",
            interests=["摄影", "美食", "旅行"],
            preferred_group_size="3-8人",
            location_preference=["朝阳区", "东城区"]
        )
        
        participant_preferences = ActivityParticipantPreferences(
            preferred_activities=["户外徒步", "摄影", "美食探店", "桌游"],
            preferred_locations=["朝阳区", "东城区", "西城区"],
            organizer_experience_preference=["初学者", "有经验", "经验丰富"],
            group_size_preference=[2, 10],
            shared_interests_weight=0.8,
            activity_frequency_preference=["每周1次", "每周2-3次"]
        )
        
        card5 = UserCard(
            id=str(uuid.uuid4()),
            user_id=users['test_user_005'].id,
            role_type="activity_participant",
            scene_type="activity",
            bio="喜欢参加各种有趣的活动，希望认识新朋友",
            profile_data=participant_profile.dict(),
            preferences=participant_preferences.dict(),
            visibility="public",
            is_active=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(card5)
        user_cards.append(card5)
        
        # 提交所有更改
        db.commit()
        
        # 4. 验证数据
        print(f"\n✅ 创建了 {len(user_cards)} 个用户卡片")
        
        # 显示创建的卡片
        for card in user_cards:
            print(f"Card: {card.id}")
            print(f"  User: {card.user_id}")
            print(f"  Role: {card.role_type}")
            print(f"  Scene: {card.scene_type}")
            print(f"  Bio: {card.bio}")
            print(f"  Profile keys: {list(card.profile_data.keys()) if card.profile_data else 'None'}")
            print(f"  Preferences keys: {list(card.preferences.keys()) if card.preferences else 'None'}")
            print()
        
        print("✅ 用户卡片测试数据设置完成！")
        
    except Exception as e:
        print(f"❌ 设置用户卡片数据时出错: {str(e)}")
        if 'db' in locals():
            db.rollback()
        raise
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    setup_user_cards()