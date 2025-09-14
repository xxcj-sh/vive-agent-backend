"""
MatchService单元测试 - 更细粒度的测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import uuid

from app.services.match_service.models import MatchResult, MatchActionType
from app.services.match_service.core import MatchService
from app.services.match_service.card_strategy import MatchCardStrategy


class TestMatchServiceUnit:
    """MatchService单元测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.mock_db = Mock()
        self.service = MatchService(self.mock_db)
    
    def test_validate_action_data_valid(self):
        """测试验证有效的action数据"""
        valid_data = {
            "cardId": "user123_card456",
            "action": "like",
            "matchType": "dating"
        }
        
        result = self.service._validate_action_data(valid_data)
        
        assert result is True
    
    def test_validate_action_data_missing_fields(self):
        """测试验证缺少字段的action数据"""
        invalid_data = {
            "cardId": "user123_card456",
            # 缺少 action
            "matchType": "dating"
        }
        
        with pytest.raises(ValueError, match="缺少必要参数"):
            self.service._validate_action_data(invalid_data)
    
    def test_validate_action_data_invalid_action_type(self):
        """测试验证无效的action类型"""
        invalid_data = {
            "cardId": "user123_card456",
            "action": "invalid_action",
            "matchType": "dating"
        }
        
        with pytest.raises(ValueError, match="无效的操作类型"):
            self.service._validate_action_data(invalid_data)
    
    def test_validate_action_data_invalid_match_type(self):
        """测试验证无效的match类型"""
        invalid_data = {
            "cardId": "user123_card456",
            "action": "like",
            "matchType": "invalid_type"
        }
        
        with pytest.raises(ValueError, match="无效的匹配类型"):
            self.service._validate_action_data(invalid_data)
    
    def test_parse_card_id_valid(self):
        """测试解析有效的card ID"""
        card_id = "user123_card456"
        
        user_id, card_suffix = self.service._parse_card_id(card_id)
        
        assert user_id == "user123"
        assert card_suffix == "card456"
    
    def test_parse_card_id_invalid_format(self):
        """测试解析无效的card ID格式"""
        card_id = "invalid_card_id"
        
        with pytest.raises(ValueError, match="无效的卡片ID格式"):
            self.service._parse_card_id(card_id)
    
    def test_check_existing_action_found(self):
        """测试检查已存在的action"""
        mock_query = Mock()
        mock_existing = Mock()
        mock_existing.action_type = "like"
        mock_existing.id = "action123"
        mock_query.filter.return_value.first.return_value = mock_existing
        
        self.mock_db.query.return_value = mock_query
        
        result = self.service._check_existing_action("user1", "user2", "dating")
        
        assert result == mock_existing
    
    def test_check_existing_action_not_found(self):
        """测试检查不存在的action"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        
        self.mock_db.query.return_value = mock_query
        
        result = self.service._check_existing_action("user1", "user2", "dating")
        
        assert result is None
    
    def test_check_mutual_match_found(self):
        """测试检查存在的双向匹配"""
        mock_query = Mock()
        mock_existing = Mock()
        mock_existing.action_type = "like"
        mock_existing.id = "action123"
        mock_query.filter.return_value.first.return_value = mock_existing
        
        self.mock_db.query.return_value = mock_query
        
        result = self.service._check_mutual_match("user1", "user2", "dating")
        
        assert result == mock_existing
    
    def test_check_mutual_match_not_found(self):
        """测试检查不存在的双向匹配"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        
        self.mock_db.query.return_value = mock_query
        
        result = self.service._check_mutual_match("user1", "user2", "dating")
        
        assert result is None
    
    def test_create_match_action_new(self):
        """测试创建新的匹配action"""
        action_data = {
            "cardId": "user123_card456",
            "action": "like",
            "matchType": "dating"
        }
        
        self.mock_db.add = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.flush = Mock()
        
        result = self.service._create_match_action(
            user_id="user1",
            target_user_id="user123",
            action_data=action_data,
            existing_action=None
        )
        
        assert result is not None
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
    
    def test_create_match_action_update(self):
        """测试更新已存在的匹配action"""
        action_data = {
            "cardId": "user123_card456",
            "action": "like",
            "matchType": "dating"
        }
        
        existing_action = Mock()
        existing_action.action_type = "skip"
        existing_action.id = "action123"
        
        self.mock_db.commit = Mock()
        
        result = self.service._create_match_action(
            user_id="user1",
            target_user_id="user123",
            action_data=action_data,
            existing_action=existing_action
        )
        
        assert result == existing_action
        assert existing_action.action_type == "like"
        self.mock_db.commit.assert_called_once()
    
    def test_create_match_record(self):
        """测试创建匹配记录"""
        user1_id = "user1"
        user2_id = "user2"
        action1_id = "action1"
        action2_id = "action2"
        
        self.mock_db.add = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.flush = Mock()
        
        match_id = self.service._create_match_record(
            user1_id, user2_id, action1_id, action2_id
        )
        
        assert match_id is not None
        assert len(match_id) == 36  # UUID格式
        self.mock_db.add.assert_called()
        self.mock_db.commit.assert_called_once()
    
    def test_format_match_response_new_action(self):
        """测试格式化新action的响应"""
        action = Mock()
        action.id = "action123"
        action.action_type = "like"
        action.created_at = datetime.now()
        
        result = self.service._format_match_response(action, is_match=False, match_id=None)
        
        assert isinstance(result, MatchResult)
        assert result.action_id == "action123"
        assert result.is_match is False
        assert result.match_id is None
        assert result.message == "操作成功"
    
    def test_format_match_response_mutual_match(self):
        """测试格式化双向匹配的响应"""
        action = Mock()
        action.id = "action123"
        action.action_type = "like"
        action.created_at = datetime.now()
        
        result = self.service._format_match_response(
            action, is_match=True, match_id="match123"
        )
        
        assert isinstance(result, MatchResult)
        assert result.action_id == "action123"
        assert result.is_match is True
        assert result.match_id == "match123"
        assert "匹配成功" in result.message
    
    @patch('app.services.match_service.core.datetime')
    def test_get_match_statistics(self, mock_datetime):
        """测试获取匹配统计"""
        # 设置固定时间
        fixed_date = datetime(2024, 1, 15)
        mock_datetime.now.return_value = fixed_date
        mock_datetime.timedelta = datetime.timedelta
        
        # 模拟查询结果
        mock_result = Mock()
        mock_result.total = 5
        mock_result.like = 3
        mock_result.skip = 2
        mock_result.ai_recommendations = 1
        
        mock_query = Mock()
        mock_query.scalar.return_value = mock_result
        self.mock_db.query.return_value = mock_query
        
        stats = self.service.get_match_statistics("user1", days=30)
        
        assert stats.total_actions == 5
        assert stats.action_breakdown["like"] == 3
        assert stats.action_breakdown["skip"] == 2
        assert stats.ai_recommendations == 1
        assert stats.period == "30 days"
    
    def test_get_ai_recommendations_empty(self):
        """测试获取空AI推荐列表"""
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = []
        self.mock_db.query.return_value = mock_query
        
        recommendations = self.service.get_ai_recommendations("user1", "dating")
        
        assert recommendations == []
    
    def test_get_ai_recommendations_with_data(self):
        """测试获取有数据的AI推荐列表"""
        mock_action = Mock()
        mock_action.id = "ai123"
        mock_action.target_user_id = "user2"
        mock_action.target_card_id = "user2_card123"
        mock_action.created_at = datetime.now()
        
        mock_target_user = Mock()
        mock_target_user.nick_name = "推荐用户"
        mock_target_user.age = 25
        mock_target_user.location = "北京"
        
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = [mock_action]
        self.mock_db.query.return_value = mock_query
        
        with patch.object(self.service, '_get_user_by_id', return_value=mock_target_user):
            recommendations = self.service.get_ai_recommendations("user1", "dating")
        
        assert len(recommendations) == 1
        assert recommendations[0]["id"] == "ai123"
        assert recommendations[0]["targetUserId"] == "user2"
    
    def test_update_ai_recommendation_status_success(self):
        """测试成功更新AI推荐状态"""
        mock_action = Mock()
        mock_action.id = "ai123"
        mock_action.is_processed = False
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_action
        self.mock_db.query.return_value = mock_query
        
        result = self.service.update_ai_recommendation_status("ai123", True)
        
        assert result is True
        assert mock_action.is_processed is True
        self.mock_db.commit.assert_called_once()
    
    def test_update_ai_recommendation_status_not_found(self):
        """测试更新不存在的AI推荐状态"""
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
        result = self.service.update_ai_recommendation_status("ai123", True)
        
        assert result is False
        self.mock_db.commit.assert_not_called()


class TestMatchCardStrategyUnit:
    """MatchCardStrategy单元测试"""
    
    def setup_method(self):
        """测试前设置"""
        self.mock_db = Mock()
        self.strategy = MatchCardStrategy(self.mock_db)
    
    def test_calculate_match_score_identical(self):
        """测试完全相同用户的匹配分数"""
        current_user = {
            "location": "北京",
            "interests": ["阅读", "电影"],
            "age": 25
        }
        
        target_user = Mock()
        target_user.location = "北京"
        target_user.interests = ["阅读", "电影"]
        target_user.age = 25
        
        score = self.strategy._calculate_match_score(current_user, target_user)
        
        assert score == 100
    
    def test_calculate_match_score_partial_match(self):
        """测试部分匹配的匹配分数"""
        current_user = {
            "location": "北京",
            "interests": ["阅读", "电影"],
            "age": 25
        }
        
        target_user = Mock()
        target_user.location = "上海"  # 不同位置
        target_user.interests = ["阅读", "摄影"]  # 部分相同
        target_user.age = 30  # 年龄差异
        
        score = self.strategy._calculate_match_score(current_user, target_user)
        
        assert 50 <= score < 100
    
    def test_calculate_match_score_no_match(self):
        """测试完全不匹配的匹配分数"""
        current_user = {
            "location": "北京",
            "interests": ["阅读", "电影"],
            "age": 25
        }
        
        target_user = Mock()
        target_user.location = "广州"
        target_user.interests = ["运动", "游戏"]
        target_user.age = 40
        
        score = self.strategy._calculate_match_score(current_user, target_user)
        
        assert 50 <= score < 70
    
    def test_convert_user_to_dating_card(self):
        """测试转换用户为交友卡片"""
        mock_user = Mock()
        mock_user.id = "user123"
        mock_user.nick_name = "测试用户"
        mock_user.age = 25
        mock_user.location = "北京"
        mock_user.occupation = "工程师"
        mock_user.interests = ["阅读", "电影"]
        mock_user.avatar_url = "http://example.com/avatar.jpg"
        
        card = self.strategy._convert_user_to_dating_card(mock_user, 85)
        
        assert card["type"] == "user"
        assert card["id"] == "user123_dating"
        assert card["title"] == "测试用户"
        assert card["subtitle"] == "25岁 · 北京 · 工程师"
        assert card["tags"] == ["阅读", "电影"]
        assert card["score"] == 85
    
    def test_convert_user_to_activity_card_for_seeker(self):
        """测试转换用户为活动卡片（寻求者视角）"""
        mock_user = Mock()
        mock_user.id = "user123"
        mock_user.nick_name = "活动组织者"
        mock_user.age = 30
        mock_user.location = "上海"
        mock_user.occupation = "活动策划"
        mock_user.interests = ["旅行", "摄影"]
        mock_user.avatar_url = "http://example.com/avatar.jpg"
        
        card = self.strategy._convert_user_to_activity_card_for_seeker(mock_user, 90)
        
        assert card["type"] == "activity"
        assert card["id"] == "user123_activity"
        assert card["title"] == "活动组织者"
        assert card["subtitle"] == "30岁 · 上海"
        assert card["tags"] == ["旅行", "摄影"]
        assert card["score"] == 90
    
    def test_convert_user_to_activity_card_for_organizer(self):
        """测试转换用户为活动卡片（组织者视角）"""
        mock_user = Mock()
        mock_user.id = "user123"
        mock_user.nick_name = "参与者"
        mock_user.age = 28
        mock_user.location = "广州"
        mock_user.occupation = "设计师"
        mock_user.interests = ["艺术", "音乐"]
        mock_user.avatar_url = "http://example.com/avatar.jpg"
        
        card = self.strategy._convert_user_to_activity_card_for_organizer(mock_user, 75)
        
        assert card["type"] == "participant"
        assert card["id"] == "user123_activity_participant"
        assert card["title"] == "参与者"
        assert card["subtitle"] == "28岁 · 广州"
        assert card["tags"] == ["艺术", "音乐"]
        assert card["score"] == 75
    
    def test_convert_user_to_housing_card_for_seeker(self):
        """测试转换用户为房源卡片（寻求者视角）"""
        mock_user = Mock()
        mock_user.id = "user123"
        mock_user.nick_name = "房东"
        mock_user.age = 35
        mock_user.location = "深圳"
        mock_user.occupation = "软件工程师"
        mock_user.interests = ["阅读", "投资"]
        mock_user.avatar_url = "http://example.com/avatar.jpg"
        
        card = self.strategy._convert_user_to_housing_card_for_seeker(mock_user, 95)
        
        assert card["type"] == "housing"
        assert card["id"] == "user123_housing"
        assert card["title"] == "房东"
        assert card["subtitle"] == "35岁 · 深圳"
        assert card["tags"] == ["阅读", "投资"]
        assert card["score"] == 95
    
    def test_convert_user_to_housing_card_for_lister(self):
        """测试转换用户为房源卡片（发布者视角）"""
        mock_user = Mock()
        mock_user.id = "user123"
        mock_user.nick_name = "求租者"
        mock_user.age = 27
        mock_user.location = "杭州"
        mock_user.occupation = "产品经理"
        mock_user.interests = ["旅行", "美食"]
        mock_user.avatar_url = "http://example.com/avatar.jpg"
        
        card = self.strategy._convert_user_to_housing_card_for_lister(mock_user, 80)
        
        assert card["type"] == "tenant"
        assert card["id"] == "user123_housing_tenant"
        assert card["title"] == "求租者"
        assert card["subtitle"] == "27岁 · 杭州"
        assert card["tags"] == ["旅行", "美食"]
        assert card["score"] == 80


if __name__ == "__main__":
    pytest.main([__file__])