#!/usr/bin/env python3
"""
匹配服务测试脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.user import User
from app.models.user_card_db import UserCard
from app.models.match_action import MatchAction, MatchResult, MatchActionType
from app.services.match_service import MatchService
from app.utils.db_config import Base
import uuid

# 测试数据库配置
TEST_DATABASE_URL = "sqlite:///./test_match.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def setup_test_db():
    """设置测试数据库"""
    Base.metadata.create_all(bind=engine)

def teardown_test_db():
    """清理测试数据库"""
    Base.metadata.drop_all(bind=engine)

def create_test_users(db):
    """创建测试用户"""
    user1 = User(
        id="test_user_001",
        nick_name="测试用户1",
        avatar_url="https://example.com/avatar1.jpg",
        gender=1,
        age=25,
        occupation="软件工程师"
    )
    
    user2 = User(
        id="test_user_002", 
        nick_name="测试用户2",
        avatar_url="https://example.com/avatar2.jpg",
        gender=2,
        age=23,
        occupation="设计师"
    )
    
    db.add(user1)
    db.add(user2)
    db.commit()
    
    # 创建用户资料
    from datetime import datetime
    profile1 = UserProfile(
        id="profile_001",
        user_id="test_user_001",
        role_type="housing_seeker",
        scene_type="housing",
        display_name="小李找房",
        bio="寻找合适的合租房源",
        avatar_url=None,
        profile_data=None,
        preferences=None,
        tags=None,
        visibility="public",
        is_active=1,
        created_at=datetime.now(),
        updated_at=None
    )
    
    profile2 = UserProfile(
        id="profile_002",
        user_id="test_user_002",
        role_type="housing_provider", 
        scene_type="housing",
        display_name="小王出租",
        bio="出租精装两居室",
        avatar_url=None,
        profile_data=None,
        preferences=None,
        tags=None,
        visibility="public",
        is_active=1,
        created_at=datetime.now(),
        updated_at=None
    )
    
    db.add(profile1)
    db.add(profile2)
    db.commit()
    
    return user1, user2, profile1, profile2

def test_single_match_action():
    """测试单个匹配操作"""
    setup_test_db()
    db = TestingSessionLocal()
    
    try:
        # 创建测试用户
        user1, user2, profile1, profile2 = create_test_users(db)
        
        # 创建匹配服务
        match_service = MatchService(db)
        
        # 用户1对用户2执行喜欢操作
        action_data = {
            "cardId": "profile_002",
            "action": "like",
            "matchType": "housing"
        }
        
        result = match_service.submit_match_action("test_user_001", action_data)
        
        # 验证结果
        assert result["isMatch"] == False  # 单向操作，不应该匹配
        assert result["actionId"] is not None
        assert result["message"] == "操作成功"
        
        # 验证数据库中的记录
        action = db.query(MatchAction).filter(MatchAction.id == result["actionId"]).first()
        assert action is not None
        assert action.user_id == "test_user_001"
        assert action.target_user_id == "test_user_002"
        assert action.action_type == MatchActionType.LIKE
        
        print("✅ 单个匹配操作测试通过")
        
    finally:
        db.close()
        teardown_test_db()

def test_mutual_match():
    """测试双向匹配"""
    setup_test_db()
    db = TestingSessionLocal()
    
    try:
        # 创建测试用户
        user1, user2, profile1, profile2 = create_test_users(db)
        
        # 创建匹配服务
        match_service = MatchService(db)
        
        # 用户1对用户2执行喜欢操作
        action_data1 = {
            "cardId": "profile_002",
            "action": "like",
            "matchType": "housing"
        }
        result1 = match_service.submit_match_action("test_user_001", action_data1)
        assert result1["isMatch"] == False
        
        # 用户2对用户1执行喜欢操作
        action_data2 = {
            "cardId": "profile_001", 
            "action": "like",
            "matchType": "housing"
        }
        result2 = match_service.submit_match_action("test_user_002", action_data2)
        
        # 验证双向匹配成功
        assert result2["isMatch"] == True
        assert result2["matchId"] is not None
        
        # 验证匹配结果记录
        match_result = db.query(MatchResult).filter(MatchResult.id == result2["matchId"]).first()
        assert match_result is not None
        assert {match_result.user1_id, match_result.user2_id} == {"test_user_001", "test_user_002"}
        assert match_result.match_type == "housing"
        
        print("✅ 双向匹配测试通过")
        
    finally:
        db.close()
        teardown_test_db()

def test_duplicate_action():
    """测试重复操作"""
    setup_test_db()
    db = TestingSessionLocal()
    
    try:
        # 创建测试用户
        user1, user2, profile1, profile2 = create_test_users(db)
        
        # 创建匹配服务
        match_service = MatchService(db)
        
        # 第一次操作
        action_data = {
            "cardId": "profile_002",
            "action": "like", 
            "matchType": "housing"
        }
        result1 = match_service.submit_match_action("test_user_001", action_data)
        assert result1["message"] == "操作成功"
        
        # 重复操作
        result2 = match_service.submit_match_action("test_user_001", action_data)
        assert result2["isMatch"] == False
        assert "已经对该用户执行过操作" in result2["message"]
        
        print("✅ 重复操作测试通过")
        
    finally:
        db.close()
        teardown_test_db()

def test_get_matches():
    """测试获取匹配列表"""
    setup_test_db()
    db = TestingSessionLocal()
    
    try:
        # 创建测试用户
        user1, user2, profile1, profile2 = create_test_users(db)
        
        # 创建匹配服务
        match_service = MatchService(db)
        
        # 创建双向匹配
        action_data1 = {"cardId": "profile_002", "action": "like", "matchType": "housing"}
        match_service.submit_match_action("test_user_001", action_data1)
        
        action_data2 = {"cardId": "profile_001", "action": "like", "matchType": "housing"}
        result = match_service.submit_match_action("test_user_002", action_data2)
        
        # 获取用户1的匹配列表
        matches = match_service.get_user_matches("test_user_001")
        
        assert len(matches["matches"]) == 1
        assert matches["matches"][0]["user"]["id"] == "test_user_002"
        assert matches["matches"][0]["matchType"] == "housing"
        
        print("✅ 获取匹配列表测试通过")
        
    finally:
        db.close()
        teardown_test_db()

def run_all_tests():
    """运行所有测试"""
    print("🧪 开始运行匹配服务测试...")
    
    try:
        test_single_match_action()
        test_mutual_match()
        test_duplicate_action()
        test_get_matches()
        
        print("\n✅ 所有测试通过！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()