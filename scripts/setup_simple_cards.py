#!/usr/bin/env python3
"""
简化的用户卡片数据设置脚本
"""

import sys
import os
from datetime import datetime
import uuid
import json

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.database import DATABASE_URL

def setup_simple_cards():
    """设置简化的用户卡片数据"""
    
    # 创建数据库连接
    engine = create_engine(
        "sqlite:///./vmatch_dev.db",
        connect_args={"check_same_thread": False}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        print("开始设置用户卡片测试数据...")
        
        # 检查现有用户表结构
        print("检查现有数据库结构...")
        
        # 获取现有用户
        existing_users = db.execute(text("SELECT id, phone FROM users LIMIT 10")).fetchall()
        if existing_users:
            print(f"找到 {len(existing_users)} 个现有用户")
            for user_id, phone in existing_users:
                print(f"  用户: {user_id} - 电话: {phone}")
        
        # 确保user_cards表存在
        db.execute(text('''
            CREATE TABLE IF NOT EXISTS user_cards (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                role_type TEXT NOT NULL,
                scene_type TEXT NOT NULL,
                bio TEXT,
                profile_data TEXT,
                preferences TEXT,
                visibility TEXT DEFAULT 'public',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        '''))
        
        # 获取或创建测试用户
        test_phones = ['13800000001', '13800000002', '13800000003', '13800000004', '13800000005']
        user_ids = []
        
        for i, phone in enumerate(test_phones):
            # 检查用户是否已存在
            existing = db.execute(
                text("SELECT id FROM users WHERE phone = :phone"),
                {"phone": phone}
            ).fetchone()
            
            if not existing:
                user_id = str(uuid.uuid4())
                db.execute(
                    text('''
                        INSERT INTO users (id, phone, hashed_password, nick_name, is_active)
                        VALUES (:id, :phone, :password, :nick_name, 1)
                    '''),
                    {
                        "id": user_id,
                        "phone": phone,
                        "password": "hashed_password_123",
                        "nick_name": f"测试用户{str(i+1).zfill(3)}"
                    }
                )
                print(f"创建用户: {phone}")
            else:
                user_id = existing[0]
                print(f"用户已存在: {phone}")
            
            user_ids.append(user_id)
        
        # 4. 清理现有卡片数据
        for user_id in user_ids:
            db.execute(
                text("DELETE FROM user_cards WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
        
        # 5. 创建测试卡片数据
        cards_data = [
            # 找房者卡片
            {
                "user_id": user_ids[0],
                "role_type": "house_seeker",
                "scene_type": "housing",
                "bio": "寻找安静舒适的居住环境，希望找到志同道合的室友",
                "profile_data": {
                    "budget_range": [2000, 4000],
                    "preferred_areas": ["朝阳区", "海淀区"],
                    "room_type": "两居室",
                    "move_in_date": "2024-03-01",
                    "lease_duration": "1年",
                    "lifestyle": "安静，不抽烟",
                    "work_schedule": "朝九晚五",
                    "pets": False,
                    "smoking": False,
                    "occupation": "软件工程师",
                    "company_location": "中关村"
                },
                "preferences": {
                    "preferred_price_range": [1500, 4500],
                    "preferred_locations": ["朝阳区", "海淀区", "西城区"],
                    "room_type_preferences": ["一居室", "两居室"],
                    "lease_duration_preference": ["6个月", "1年", "2年"],
                    "pet_policy": "no_pets",
                    "smoking_policy": "no_smoking",
                    "max_distance_km": 15
                }
            },
            # 房源提供者卡片
            {
                "user_id": user_ids[1],
                "role_type": "house_provider",
                "scene_type": "housing",
                "bio": "望京精装修两居室出租，希望找到爱干净的租客",
                "profile_data": {
                    "property_type": "公寓",
                    "rooms": 2,
                    "area": 80,
                    "price": 3500,
                    "location": ["朝阳区", "望京"],
                    "amenities": ["wifi", "空调", "洗衣机", "冰箱"],
                    "lease_terms": "押一付三，最少租期6个月",
                    "available_from": "2024-02-15",
                    "description": "精装修两居室，采光好，交通便利"
                },
                "preferences": {
                    "preferred_tenant_type": ["上班族", "学生"],
                    "preferred_gender": ["不限"],
                    "preferred_age_range": [20, 35],
                    "preferred_occupation": ["IT", "金融", "教育"],
                    "smoking_policy": "prefer_no_smoking",
                    "pet_policy": "small_pets_allowed",
                    "max_tenants": 2
                }
            },
            # 交友卡片
            {
                "user_id": user_ids[2],
                "role_type": "dating_user",
                "scene_type": "dating",
                "bio": "寻找真诚交往的另一半，希望三观一致，有共同话题",
                "profile_data": {
                    "age": 28,
                    "height": 175,
                    "education": "本科",
                    "occupation": "产品经理",
                    "income_range": "15k-20k",
                    "relationship_status": "单身",
                    "looking_for": "认真交往",
                    "hobbies": ["阅读", "旅行", "摄影", "健身"],
                    "personality": ["开朗", "有责任心", "幽默"],
                    "lifestyle": {"drinking": "偶尔", "smoking": "不抽烟", "exercise": "每周3次"}
                },
                "preferences": {
                    "preferred_age_range": [25, 32],
                    "preferred_height_range": [160, 175],
                    "preferred_education_levels": ["本科", "硕士"],
                    "preferred_occupations": ["IT", "金融", "教育", "医疗"],
                    "preferred_relationship_status": ["单身"],
                    "looking_for_match": ["认真交往", "结婚"],
                    "shared_interests_weight": 0.7,
                    "personality_compatibility": ["开朗", "温柔", "有责任心"],
                    "max_distance_km": 20
                }
            },
            # 活动组织者卡片
            {
                "user_id": user_ids[3],
                "role_type": "activity_organizer",
                "scene_type": "activity",
                "bio": "喜欢组织各种有趣的活动，希望认识更多志同道合的朋友",
                "profile_data": {
                    "activity_types": ["户外徒步", "读书会", "桌游"],
                    "preferred_locations": ["朝阳区", "海淀区"],
                    "group_size": "5-10人",
                    "activity_frequency": "每周2-3次",
                    "experience_level": "经验丰富",
                    "interests": ["阅读", "运动", "社交"]
                },
                "preferences": {
                    "preferred_participant_count": [3, 8],
                    "preferred_locations": ["朝阳区", "海淀区", "西城区"],
                    "participant_age_range": [20, 40],
                    "participant_gender_preference": "不限",
                    "shared_interests_weight": 0.6,
                    "activity_type_preferences": ["户外徒步", "读书会", "桌游", "运动"]
                }
            },
            # 活动参与者卡片
            {
                "user_id": user_ids[4],
                "role_type": "activity_participant",
                "scene_type": "activity",
                "bio": "喜欢参加各种有趣的活动，希望认识新朋友",
                "profile_data": {
                    "preferred_activities": ["户外徒步", "摄影", "美食探店"],
                    "availability": "周末和晚上",
                    "experience_level": "初学者",
                    "interests": ["摄影", "美食", "旅行"],
                    "preferred_group_size": "3-8人",
                    "location_preference": ["朝阳区", "东城区"]
                },
                "preferences": {
                    "preferred_activities": ["户外徒步", "摄影", "美食探店", "桌游"],
                    "preferred_locations": ["朝阳区", "东城区", "西城区"],
                    "organizer_experience_preference": ["初学者", "有经验", "经验丰富"],
                    "group_size_preference": [2, 10],
                    "shared_interests_weight": 0.8,
                    "activity_frequency_preference": ["每周1次", "每周2-3次"]
                }
            }
        ]
        
        # 插入卡片数据
        for card_data in cards_data:
            card_id = str(uuid.uuid4())
            db.execute(
                text('''
                    INSERT INTO user_cards 
                    (id, user_id, role_type, scene_type, bio, profile_data, preferences, is_active)
                    VALUES (:id, :user_id, :role_type, :scene_type, :bio, :profile_data, :preferences, 1)
                '''),
                {
                    "id": card_id,
                    "user_id": card_data["user_id"],
                    "role_type": card_data["role_type"],
                    "scene_type": card_data["scene_type"],
                    "bio": card_data["bio"],
                    "profile_data": json.dumps(card_data["profile_data"], ensure_ascii=False),
                    "preferences": json.dumps(card_data["preferences"], ensure_ascii=False)
                }
            )
            print(f"创建卡片: {card_data['role_type']} - {card_data['scene_type']}")
        
        db.commit()
        
        # 6. 验证数据
        user_count = db.execute(text("SELECT COUNT(*) FROM users")).fetchone()[0]
        card_count = db.execute(text("SELECT COUNT(*) FROM user_cards")).fetchone()[0]
        
        print(f"\n✅ 数据设置完成!")
        print(f"用户总数: {user_count}")
        print(f"卡片总数: {card_count}")
        
        # 显示前几条记录
        cards = db.execute(text("""
            SELECT u.phone, uc.role_type, uc.scene_type, uc.bio 
            FROM user_cards uc 
            JOIN users u ON uc.user_id = u.id 
            LIMIT 5
        """)).fetchall()
        
        print("\n创建的卡片:")
        for phone, role_type, scene_type, bio in cards:
            print(f"  {phone}: {role_type} - {scene_type} - {bio[:50]}...")
        
    except Exception as e:
        print(f"❌ 设置数据时出错: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    setup_simple_cards()