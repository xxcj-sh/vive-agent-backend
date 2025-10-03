#!/usr/bin/env python3
"""
用户画像功能测试脚本
测试用户画像的创建、查询、更新和分析功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user_profile import UserProfileCreate, UserProfileUpdate
from app.services.user_profile_service import UserProfileService
from app.models.user import User
import uuid
from datetime import datetime

def test_user_profile_service():
    """测试用户画像服务"""
    
    # 创建测试数据库连接
    engine = create_engine("sqlite:///./test_user_profile.db")
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # 创建表
    from app.utils.db_config import Base
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # 创建测试用户
        test_user_id = str(uuid.uuid4())
        test_user = User(
            id=test_user_id,
            phone="13800138000",
            nick_name="测试用户",
            avatar_url="https://example.com/avatar.jpg"
        )
        db.add(test_user)
        db.commit()
        
        print("✅ 测试用户创建成功")
        
        # 创建用户画像服务
        service = UserProfileService(db)
        
        # 测试1: 创建用户画像
        print("\n📝 测试1: 创建用户画像")
        profile_data = UserProfileCreate(
            user_id=test_user_id,
            preferences={
                "housing": {"budget": 5000, "location": "市中心"},
                "dating": {"age_range": [25, 35], "gender": "异性"}
            },
            personality_traits={
                "openness": 8,
                "conscientiousness": 7,
                "extraversion": 6,
                "agreeableness": 9,
                "neuroticism": 3
            },
            mood_state={
                "current_mood": "happy",
                "mood_intensity": 8,
                "mood_stability": 7
            },
            behavior_patterns={
                "activity_level": "high",
                "social_frequency": "weekly",
                "preferred_time": "evening"
            },
            interest_tags=["旅游", "美食", "电影", "健身"],
            social_preferences={
                "group_size": "small",
                "meeting_format": "casual",
                "communication_style": "direct"
            },
            match_preferences={
                "compatibility_threshold": 0.7,
                "preferred_scenes": ["dating", "activity"]
            },
            data_source="llm_analysis",
            confidence_score=85,
            update_reason="初始创建"
        )
        
        profile = service.create_user_profile(profile_data)
        print(f"✅ 用户画像创建成功，ID: {profile.id}")
        
        # 测试2: 获取激活画像
        print("\n🔍 测试2: 获取激活画像")
        active_profile = service.get_active_user_profile(test_user_id)
        if active_profile:
            print(f"✅ 激活画像获取成功，ID: {active_profile.id}")
        else:
            print("❌ 激活画像获取失败")
            return False
        
        # 测试3: 更新用户画像
        print("\n✏️ 测试3: 更新用户画像")
        update_data = UserProfileUpdate(
            mood_state={
                "current_mood": "excited",
                "mood_intensity": 9,
                "mood_stability": 8
            },
            update_reason="心情更新"
        )
        
        updated_profile = service.update_user_profile(profile.id, update_data)
        if updated_profile:
            print(f"✅ 画像更新成功，更新原因: {updated_profile.update_reason}")
        else:
            print("❌ 画像更新失败")
            return False
        
        # 测试4: 分析用户偏好
        print("\n📊 测试4: 分析用户偏好")
        preference_analysis = service.analyze_user_preferences(test_user_id)
        if "error" not in preference_analysis:
            print(f"✅ 偏好分析成功，置信度: {preference_analysis['confidence_score']}")
        else:
            print("❌ 偏好分析失败")
            return False
        
        # 测试5: 分析用户个性
        print("\n🧠 测试5: 分析用户个性")
        personality_analysis = service.analyze_user_personality(test_user_id)
        if "error" not in personality_analysis:
            print(f"✅ 个性分析成功，置信度: {personality_analysis['confidence_score']}")
        else:
            print("❌ 个性分析失败")
            return False
        
        # 测试6: 分析用户心情
        print("\n😊 测试6: 分析用户心情")
        mood_analysis = service.analyze_user_mood(test_user_id)
        if "error" not in mood_analysis:
            print(f"✅ 心情分析成功，当前心情: {mood_analysis['mood_state']['current_mood']}")
        else:
            print("❌ 心情分析失败")
            return False
        
        # 测试7: 获取统计信息
        print("\n📈 测试7: 获取统计信息")
        statistics = service.get_profile_statistics(test_user_id)
        print(f"✅ 统计信息获取成功，总画像数: {statistics['total_profiles']}")
        
        # 测试8: 创建第二个画像并测试激活切换
        print("\n🔄 测试8: 创建第二个画像并测试激活切换")
        profile_data2 = UserProfileCreate(
            user_id=test_user_id,
            preferences={
                "housing": {"budget": 6000, "location": "郊区"},
                "dating": {"age_range": [28, 40], "gender": "不限"}
            },
            data_source="user_update",
            confidence_score=90,
            update_reason="用户手动更新"
        )
        
        profile2 = service.create_user_profile(profile_data2)
        print(f"✅ 第二个画像创建成功，ID: {profile2.id}")
        
        # 检查第一个画像是否被停用
        original_profile = service.get_user_profile(profile.id)
        if original_profile.is_active == 0:
            print("✅ 第一个画像已正确停用")
        else:
            print("❌ 第一个画像停用失败")
            return False
        
        # 检查第二个画像是否激活
        new_active_profile = service.get_active_user_profile(test_user_id)
        if new_active_profile and new_active_profile.id == profile2.id:
            print("✅ 第二个画像已正确激活")
        else:
            print("❌ 第二个画像激活失败")
            return False
        
        # 测试9: 手动激活第一个画像
        print("\n🔄 测试9: 手动激活第一个画像")
        success = service.activate_user_profile(profile.id)
        if success:
            reactivated_profile = service.get_active_user_profile(test_user_id)
            if reactivated_profile and reactivated_profile.id == profile.id:
                print("✅ 第一个画像重新激活成功")
            else:
                print("❌ 第一个画像重新激活失败")
                return False
        else:
            print("❌ 激活操作失败")
            return False
        
        # 测试10: 获取所有画像
        print("\n📋 测试10: 获取所有画像")
        all_profiles = service.get_user_profiles(test_user_id, include_inactive=True)
        print(f"✅ 获取所有画像成功，总数: {len(all_profiles)}")
        
        print("\n🎉 所有测试通过！用户画像功能正常运行")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()
        # 清理测试数据库
        if os.path.exists("./test_user_profile.db"):
            os.remove("./test_user_profile.db")

if __name__ == "__main__":
    success = test_user_profile_service()
    sys.exit(0 if success else 1)