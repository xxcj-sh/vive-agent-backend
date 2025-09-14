"""
MatchService 单元测试
测试匹配服务的核心功能
"""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from app.services.match_service_simple import MatchService
from app.models.match_action import MatchAction, MatchResult, MatchActionType, MatchResultStatus
from app.models.user import User
from datetime import datetime
import uuid


class TestMatchService:
    """MatchService 测试类"""
    
    @pytest.fixture
    def mock_db(self):
        """创建mock数据库会话"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def match_service(self, mock_db):
        """创建MatchService实例"""
        return MatchService(mock_db)
    
    @pytest.fixture
    def sample_user(self):
        """创建测试用户"""
        user = Mock(spec=User)
        user.id = "user123"
        return user
    
    @pytest.fixture
    def sample_action_data(self):
        """创建测试操作数据"""
        return {
            "cardId": "card123",
            "action": "like",
            "sceneType": "dating",
            "sceneContext": {"message": "你好"}
        }
    
    def test_init(self, mock_db):
        """测试初始化"""
        service = MatchService(mock_db)
        assert service.db == mock_db
    
    def test_submit_match_action_success(self, match_service, mock_db, sample_action_data):
        """测试成功提交匹配操作"""
        # 设置mock返回值
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        with patch.object(match_service, '_extract_target_user_id', return_value="target123"):
            with patch.object(match_service, '_check_mutual_match', return_value=(False, None)):
                result = match_service.submit_match_action("user123", sample_action_data)
        
        assert result["isMatch"] is False
        assert result["message"] == "操作成功"
        assert "actionId" in result
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_submit_match_action_missing_params(self, match_service):
        """测试缺少必要参数"""
        invalid_data = {"cardId": "card123"}  # 缺少action和sceneType
        
        with pytest.raises(ValueError) as exc_info:
            match_service.submit_match_action("user123", invalid_data)
        
        assert "缺少必要参数" in str(exc_info.value)
        assert "action" in str(exc_info.value)
        assert "sceneType" in str(exc_info.value)
    
    def test_submit_match_action_existing_action(self, match_service, mock_db, sample_action_data):
        """测试已经存在操作记录的情况"""
        existing_action = Mock()
        existing_action.action_type = MatchActionType.LIKE
        
        mock_db.query.return_value.filter.return_value.first.return_value = existing_action
        
        with patch.object(match_service, '_extract_target_user_id', return_value="target123"):
            result = match_service.submit_match_action("user123", sample_action_data)
        
        assert result["isMatch"] is False
        assert result["message"] == "已经对该用户执行过操作"
        assert result["existingAction"] == "like"
        mock_db.add.assert_not_called()
    
    def test_extract_target_user_id_from_user_card(self, match_service, mock_db):
        """测试从UserCard提取目标用户ID"""
        with patch('app.models.user_card_db.UserCard') as mock_user_card:
            mock_card = Mock()
            mock_card.user_id = "target123"
            mock_db.query.return_value.filter.return_value.first.return_value = mock_card
            
            result = match_service._extract_target_user_id("card123", "dating")
            
            assert result == "target123"
    
    def test_extract_target_user_id_from_user(self, match_service, mock_db):
        """测试直接从User表提取用户ID"""
        mock_user = Mock()
        mock_user.id = "user123"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = match_service._extract_target_user_id("user123", "dating")
        
        assert result == "user123"
    
    def test_extract_target_user_id_not_found(self, match_service, mock_db):
        """测试无法提取目标用户ID"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = match_service._extract_target_user_id("invalid123", "dating")
        
        assert result is None
    
    def test_check_mutual_match_found(self, match_service, mock_db):
        """测试发现双向匹配"""
        target_action = Mock()
        target_action.id = "action456"
        target_action.target_card_id = "card456"
        
        mock_db.query.return_value.filter.return_value.first.return_value = target_action
        mock_db.query.return_value.filter.return_value.first.side_effect = [target_action, None]  # 先找到action，再检查无现有匹配
        
        with patch('uuid.uuid4', return_value="match789"):
            result = match_service._check_mutual_match("user1", "user2", "card1", "dating", "action123")
        
        assert result == (True, "match789")
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_check_mutual_match_not_found(self, match_service, mock_db):
        """测试未找到双向匹配"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        result = match_service._check_mutual_match("user1", "user2", "card1", "dating", "action123")
        
        assert result == (False, None)
    
    def test_check_mutual_match_existing(self, match_service, mock_db):
        """测试已存在匹配结果"""
        target_action = Mock()
        target_action.id = "action456"
        target_action.target_card_id = "card456"
        
        existing_match = Mock()
        existing_match.id = "existing_match123"
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [target_action, existing_match]
        
        result = match_service._check_mutual_match("user1", "user2", "card1", "dating", "action123")
        
        assert result == (True, "existing_match123")
        mock_db.add.assert_not_called()  # 不应该创建新匹配
    
    def test_get_user_matches_all_status(self, match_service, mock_db):
        """测试获取所有状态的匹配"""
        mock_matches = [Mock(), Mock()]
        mock_query = Mock()
        mock_query.offset.return_value.limit.return_value.all.return_value = mock_matches
        mock_query.count.return_value = 2
        
        mock_db.query.return_value.filter.return_value = mock_query
        
        result = match_service.get_user_matches("user123", status="all", page=1, page_size=10)
        
        assert result["total"] == 2
        assert result["list"] == mock_matches
        assert result["page"] == 1
        assert result["pageSize"] == 10
    
    def test_get_user_matches_new_status(self, match_service, mock_db):
        """测试获取新匹配"""
        mock_matches = [Mock()]
        mock_query = Mock()
        mock_query.offset.return_value.limit.return_value.all.return_value = mock_matches
        mock_query.count.return_value = 1
        
        mock_db.query.return_value.filter.return_value = mock_query
        
        result = match_service.get_user_matches("user123", status="new", page=1, page_size=10)
        
        assert result["total"] == 1
        assert result["list"] == mock_matches
    
    def test_get_user_matches_contacted_status(self, match_service, mock_db):
        """测试获取已联系匹配"""
        mock_matches = [Mock()]
        mock_query = Mock()
        mock_query.offset.return_value.limit.return_value.all.return_value = mock_matches
        mock_query.count.return_value = 1
        
        mock_db.query.return_value.filter.return_value = mock_query
        
        result = match_service.get_user_matches("user123", status="contacted", page=1, page_size=10)
        
        assert result["total"] == 1
        assert result["list"] == mock_matches
    
    def test_get_user_matches_empty(self, match_service, mock_db):
        """测试无匹配结果"""
        mock_query = Mock()
        mock_query.offset.return_value.limit.return_value.all.return_value = []
        mock_query.count.return_value = 0
        
        mock_db.query.return_value.filter.return_value = mock_query
        
        result = match_service.get_user_matches("user123", status="all", page=1, page_size=10)
        
        assert result["total"] == 0
        assert result["list"] == []
    
    def test_submit_match_action_exception(self, match_service, mock_db, sample_action_data):
        """测试提交操作时的异常处理"""
        mock_db.commit.side_effect = Exception("数据库错误")
        
        with patch.object(match_service, '_extract_target_user_id', return_value="target123"):
            with pytest.raises(Exception) as exc_info:
                match_service.submit_match_action("user123", sample_action_data)
        
        assert "提交匹配操作失败" in str(exc_info.value)
        mock_db.rollback.assert_called_once()
    
    def test_check_mutual_match_exception(self, match_service, mock_db):
        """测试检查双向匹配时的异常处理"""
        mock_db.query.side_effect = Exception("查询错误")
        
        result = match_service._check_mutual_match("user1", "user2", "card1", "dating", "action123")
        
        assert result == (False, None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])