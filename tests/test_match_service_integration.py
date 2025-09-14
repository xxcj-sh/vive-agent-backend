"""
整合后的match_service模块单元测试
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.match_action import MatchAction, MatchActionType
from app.models.user import User
from app.services.match_service import MatchService, MatchCardStrategy
from app.services.match_service.models import MatchResult, MatchActionType as ServiceActionType


@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    engine = create_engine('sqlite:///:memory:')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # 创建测试表
    from app.models.base import Base
    Base.metadata.create_all(engine)
    
    yield session
    session.close()


@pytest.fixture
def match_service(db_session):
    """创建MatchService实例"""
    return MatchService(db_session)


@pytest.fixture
def match_card_strategy(db_session):
    """创建MatchCardStrategy实例"""
    return MatchCardStrategy(db_session)


@pytest.fixture
def test_users(db_session):
    """创建测试用户"""
    user1 = User(
        id=str(uuid.uuid4()),
        nick_name="测试用户1",
        email="test1@example.com",
        gender=1,
        age=25,
        location="北京",
        occupation="工程师",
        interests=["阅读", "电影"]
    )
    
    user2 = User(
        id=str(uuid.uuid4()),
        nick_name="测试用户2",
        email="test2@example.com",
        gender=2,
        age=23,
        location="上海",
        occupation="设计师",
        interests=["旅行", "摄影"]
    )
    
    db_session.add_all([user1, user2])
    db_session.commit()
    
    return [user1, user2]


class TestMatchService:
    """测试MatchService核心功能"""
    
    def test_submit_match_action_success(self, match_service, test_users):
        """测试成功提交匹配操作"""
        user1, user2 = test_users
        
        action_data = {
            "cardId": f"{user2.id}_123456",
            "action": "like",
            "matchType": "dating"
        }
        
        result = match_service.submit_match_action(user1.id, action_data)
        
        assert isinstance(result, MatchResult)
        assert result.is_match is False  # 首次操作不会立即匹配
        assert result.action_id is not None
        assert result.message == "操作成功"
    
    def test_submit_match_action_duplicate(self, match_service, test_users):
        """测试重复提交匹配操作"""
        user1, user2 = test_users
        
        action_data = {
            "cardId": f"{user2.id}_123456",
            "action": "like",
            "matchType": "dating"
        }
        
        # 第一次提交
        match_service.submit_match_action(user1.id, action_data)
        
        # 第二次提交
        result = match_service.submit_match_action(user1.id, action_data)
        
        assert result.is_match is False
        assert result.existing_action == "like"
        assert "已经对该用户执行过操作" in result.message
    
    def test_submit_match_action_invalid_params(self, match_service, test_users):
        """测试提交无效参数的匹配操作"""
        user1, user2 = test_users
        
        action_data = {
            "cardId": f"{user2.id}_123456",
            # 缺少 action 参数
            "matchType": "dating"
        }
        
        with pytest.raises(ValueError, match="缺少必要参数"):
            match_service.submit_match_action(user1.id, action_data)
    
    def test_submit_match_action_invalid_action_type(self, match_service, test_users):
        """测试提交无效的action类型"""
        user1, user2 = test_users
        
        action_data = {
            "cardId": f"{user2.id}_123456",
            "action": "invalid_action",
            "matchType": "dating"
        }
        
        with pytest.raises(ValueError, match="无效的操作类型"):
            match_service.submit_match_action(user1.id, action_data)
    
    def test_mutual_match(self, match_service, test_users, db_session):
        """测试双向匹配"""
        user1, user2 = test_users
        
        # 用户1喜欢用户2
        action_data1 = {
            "cardId": f"{user2.id}_123456",
            "action": "like",
            "matchType": "dating"
        }
        result1 = match_service.submit_match_action(user1.id, action_data1)
        
        # 用户2喜欢用户1
        action_data2 = {
            "cardId": f"{user1.id}_654321",
            "action": "like",
            "matchType": "dating"
        }
        result2 = match_service.submit_match_action(user2.id, action_data2)
        
        # 验证双向匹配
        assert result2.is_match is True
        assert result2.match_id is not None
        
        # 验证数据库状态
        match_action1 = db_session.query(MatchAction).filter(
            MatchAction.user_id == user1.id,
            MatchAction.target_user_id == user2.id
        ).first()
        
        match_action2 = db_session.query(MatchAction).filter(
            MatchAction.user_id == user2.id,
            MatchAction.target_user_id == user1.id
        ).first()
        
        assert match_action1.action_type == MatchActionType.MUTUAL_MATCH
        assert match_action2.action_type == MatchActionType.MUTUAL_MATCH
        assert match_action1.match_id == match_action2.match_id
    
    def test_get_user_matches(self, match_service, test_users, db_session):
        """测试获取用户匹配列表"""
        user1, user2 = test_users
        
        # 创建一些匹配记录
        match_action = MatchAction(
            id=str(uuid.uuid4()),
            user_id=user1.id,
            target_user_id=user2.id,
            target_card_id=f"{user2.id}_123456",
            action_type=MatchActionType.LIKE,
            match_type="dating"
        )
        
        db_session.add(match_action)
        db_session.commit()
        
        result = match_service.get_user_matches(user1.id)
        
        assert "matches" in result
        assert "total" in result
        assert isinstance(result["matches"], list)
        assert result["total"] >= 1
        assert len(result["matches"]) >= 1
        assert result["matches"][0]["targetUserId"] == user2.id
    
    def test_get_match_statistics(self, match_service, test_users, db_session):
        """测试获取匹配统计"""
        user1, user2 = test_users
        
        # 创建一些匹配记录
        actions = [
            MatchAction(
                id=str(uuid.uuid4()),
                user_id=user1.id,
                target_user_id=user2.id,
                target_card_id=f"{user2.id}_{i}",
                action_type=MatchActionType.LIKE,
                match_type="dating"
            )
            for i in range(3)
        ]
        
        db_session.add_all(actions)
        db_session.commit()
        
        stats = match_service.get_match_statistics(user1.id, days=30)
        
        assert stats.total_actions >= 3
        assert "like" in stats.action_breakdown
        assert isinstance(stats.ai_recommendations, int)
        assert stats.period == "30 days"


class TestMatchCardStrategy:
    """测试MatchCardStrategy功能"""
    
    def test_get_recommendation_cards_housing(self, match_card_strategy, test_users):
        """测试获取房源推荐卡片"""
        user1, user2 = test_users
        
        result = match_card_strategy.get_recommendation_cards(
            user_id=user1.id,
            scene_type="housing",
            user_role="seeker",
            page=1,
            page_size=10
        )
        
        assert "cards" in result
        assert "total" in result
        assert isinstance(result["cards"], list)
        assert isinstance(result["total"], int)
    
    def test_get_recommendation_cards_dating(self, match_card_strategy, test_users):
        """测试获取交友推荐卡片"""
        user1, user2 = test_users
        
        result = match_card_strategy.get_recommendation_cards(
            user_id=user1.id,
            scene_type="dating",
            user_role="seeker",
            page=1,
            page_size=10
        )
        
        assert "cards" in result
        assert "total" in result
        assert isinstance(result["cards"], list)
        assert isinstance(result["total"], int)
    
    def test_get_recommendation_cards_activity(self, match_card_strategy, test_users):
        """测试获取活动推荐卡片"""
        user1, user2 = test_users
        
        result = match_card_strategy.get_recommendation_cards(
            user_id=user1.id,
            scene_type="activity",
            user_role="seeker",
            page=1,
            page_size=10
        )
        
        assert "cards" in result
        assert "total" in result
        assert isinstance(result["cards"], list)
        assert isinstance(result["total"], int)
    
    def test_calculate_match_score(self, match_card_strategy):
        """测试匹配分数计算"""
        current_user = {
            "location": "北京",
            "interests": ["阅读", "电影"],
            "age": 25
        }
        
        mock_user = Mock()
        mock_user.location = "北京"
        mock_user.interests = ["阅读", "摄影"]
        mock_user.age = 26
        
        score = match_card_strategy._calculate_match_score(current_user, mock_user)
        
        assert isinstance(score, int)
        assert 50 <= score <= 100


class TestAIRecommendations:
    """测试AI推荐功能"""
    
    def test_get_ai_recommendations_empty(self, match_service, test_users):
        """测试获取空AI推荐列表"""
        user1, user2 = test_users
        
        recommendations = match_service.get_ai_recommendations(user1.id, "dating")
        
        assert isinstance(recommendations, list)
        assert len(recommendations) == 0
    
    def test_update_ai_recommendation_status(self, match_service, test_users, db_session):
        """测试更新AI推荐状态"""
        user1, user2 = test_users
        
        # 创建AI推荐记录
        ai_action = MatchAction(
            id=str(uuid.uuid4()),
            user_id=user1.id,
            target_user_id=user2.id,
            target_card_id=f"{user2.id}_ai_123",
            action_type=MatchActionType.AI_RECOMMEND_BY_SYSTEM,
            match_type="dating",
            is_processed=False
        )
        
        db_session.add(ai_action)
        db_session.commit()
        
        # 更新状态
        success = match_service.update_ai_recommendation_status(ai_action.id, True)
        
        assert success is True
        
        # 验证数据库更新
        updated_action = db_session.query(MatchAction).filter(
            MatchAction.id == ai_action.id
        ).first()
        
        assert updated_action.is_processed is True
        assert updated_action.processed_at is not None


class TestCompatibility:
    """测试兼容性"""
    
    def test_legacy_import_compatibility(self, db_session):
        """测试原有导入方式兼容性"""
        # 测试可以按原有方式导入
        from app.services.match_service.legacy_compat import MatchService as LegacyMatchService
        from app.services.match_service.legacy_compat import MatchServiceSimple as LegacySimpleService
        from app.services.match_service.legacy_compat import MatchCardStrategyCompat
        
        # 确保可以实例化
        legacy_service = LegacyMatchService(db_session)
        legacy_simple = LegacySimpleService(db_session)
        legacy_strategy = MatchCardStrategyCompat(db_session)
        
        assert legacy_service is not None
        assert legacy_simple is not None
        assert legacy_strategy is not None


if __name__ == "__main__":
    pytest.main([__file__])