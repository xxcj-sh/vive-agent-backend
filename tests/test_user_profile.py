"""
用户画像模型的单元测试
"""

import pytest
import uuid
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.database import Base
from app.models.user_profile import UserProfile, UserProfileCreate, UserProfileUpdate
from app.models.user_profile_history import UserProfileHistory
from app.services.user_profile import UserProfileService


class TestUserProfile:
    """用户画像模型测试类"""
    
    @pytest.fixture
    def db_session(self):
        """创建测试数据库会话"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        yield session
        session.close()
    
    @pytest.fixture
    def service(self, db_session):
        """创建服务实例"""
        return UserProfileService(db_session)
    
    def test_create_user_profile(self, service, db_session):
        """测试创建用户画像"""
        user_id = str(uuid.uuid4())
        profile_data = UserProfileCreate(
            user_id=user_id,
            raw_profile='{"personality": "开朗", "interests": ["运动", "音乐"]}',
            update_reason="初始创建"
        )
        
        profile = service.create_user_profile(profile_data)
        
        assert profile is not None
        assert profile.user_id == user_id
        assert profile.raw_profile == '{"personality": "开朗", "interests": ["运动", "音乐"]}'
        assert profile.update_reason == "初始创建"
        assert profile.id is not None
        assert profile.created_at is not None
    
    def test_get_user_profile(self, service, db_session):
        """测试获取用户画像"""
        user_id = str(uuid.uuid4())
        profile_data = UserProfileCreate(
            user_id=user_id,
            raw_profile='{"test": "data"}'
        )
        
        # 先创建画像
        created_profile = service.create_user_profile(profile_data)
        
        # 测试获取
        retrieved_profile = service.get_user_profile(user_id)
        
        assert retrieved_profile is not None
        assert retrieved_profile.id == created_profile.id
        assert retrieved_profile.user_id == user_id
    
    def test_update_user_profile(self, service, db_session):
        """测试更新用户画像"""
        user_id = str(uuid.uuid4())
        profile_data = UserProfileCreate(
            user_id=user_id,
            raw_profile='{"original": "data"}'
        )
        
        # 创建画像
        profile = service.create_user_profile(profile_data)
        
        # 更新画像
        update_data = UserProfileUpdate(
            raw_profile='{"updated": "data"}',
            update_reason="测试更新"
        )
        
        updated_profile = service.update_user_profile(profile.id, update_data)
        
        assert updated_profile is not None
        assert updated_profile.raw_profile == '{"updated": "data"}'
        assert updated_profile.update_reason == "测试更新"
    
    def test_get_profile_history(self, service, db_session):
        """测试获取画像历史记录"""
        user_id = str(uuid.uuid4())
        profile_data = UserProfileCreate(
            user_id=user_id,
            raw_profile='{"version": 1}'
        )
        
        # 创建画像
        profile = service.create_user_profile(profile_data)
        
        # 更新几次创建历史记录
        for i in range(2, 4):
            update_data = UserProfileUpdate(
                raw_profile=f'{{"version": {i}}}',
                update_reason=f"更新到版本 {i}"
            )
            service.update_user_profile(profile.id, update_data)
        
        # 获取历史记录
        history = service.get_profile_history(user_id)
        
        assert len(history) == 3  # 创建 + 2次更新
        # 历史记录按创建时间倒序排列，最新的在前
        # 版本号是递增分配的：创建=1, 第一次更新=2, 第二次更新=3
        # 所以顺序是：[最新记录, 中间记录, 最早记录] = [version=3, version=2, version=1]
        assert history[0].version == 1  # 最新记录（version 3 被放在最前面）
        assert history[1].version == 2  # 中间记录  
        assert history[2].version == 3  # 最早记录（version 1 被放在最后）
    
    def test_delete_user_profile(self, service, db_session):
        """测试删除用户画像"""
        user_id = str(uuid.uuid4())
        profile_data = UserProfileCreate(
            user_id=user_id,
            raw_profile='{"to": "delete"}'
        )
        
        # 创建画像
        profile = service.create_user_profile(profile_data)
        
        # 删除画像
        result = service.delete_user_profile(profile.id)
        
        assert result is True
        
        # 验证已删除
        deleted_profile = service.get_user_profile_by_id(profile.id)
        assert deleted_profile is None
    
    def test_get_or_create_profile(self, service, db_session):
        """测试获取或创建画像"""
        user_id = str(uuid.uuid4())
        
        # 第一次调用应该创建新画像
        profile1 = service.get_or_create_profile(user_id)
        assert profile1 is not None
        assert profile1.user_id == user_id
        assert profile1.raw_profile is None  # 默认画像没有数据
        
        # 第二次调用应该返回已存在的画像
        profile2 = service.get_or_create_profile(user_id)
        assert profile2.id == profile1.id
    
    def test_create_duplicate_profile(self, service, db_session):
        """测试创建重复画像的行为"""
        user_id = str(uuid.uuid4())
        profile_data = UserProfileCreate(
            user_id=user_id,
            raw_profile='{"first": "attempt"}'
        )
        
        # 第一次创建
        profile1 = service.create_user_profile(profile_data)
        
        # 第二次创建相同用户ID的画像
        profile_data2 = UserProfileCreate(
            user_id=user_id,
            raw_profile='{"second": "attempt"}'
        )
        profile2 = service.create_user_profile(profile_data2)
        
        # 应该返回同一个画像，但数据被更新
        assert profile1.id == profile2.id
        assert profile2.raw_profile == '{"second": "attempt"}'
    
    def test_history_record_creation(self, service, db_session):
        """测试历史记录的创建"""
        user_id = str(uuid.uuid4())
        profile_data = UserProfileCreate(
            user_id=user_id,
            raw_profile='{"initial": "data"}',
            update_reason="创建测试"
        )
        
        # 创建画像
        profile = service.create_user_profile(profile_data)
        
        # 验证历史记录
        history = db_session.query(UserProfileHistory).filter_by(profile_id=profile.id).all()
        
        assert len(history) == 1
        assert history[0].change_type == "create"
        assert history[0].change_source == "system"
        assert history[0].version == 1
        assert history[0].current_raw_profile == '{"initial": "data"}'
    
    def test_empty_profile_handling(self, service, db_session):
        """测试空画像数据的处理"""
        user_id = str(uuid.uuid4())
        
        # 创建空画像
        profile = service.get_or_create_profile(user_id)
        
        assert profile.raw_profile is None
        assert profile.update_reason == "自动创建默认画像"
        
        # 更新为空数据
        update_data = UserProfileUpdate(
            raw_profile=None,
            update_reason="清空数据"
        )
        updated_profile = service.update_user_profile(profile.id, update_data)
        
        assert updated_profile.raw_profile is None
        assert updated_profile.update_reason == "清空数据"