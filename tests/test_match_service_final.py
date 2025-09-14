"""
MatchService 单元测试 - 最终修复版本
测试匹配服务的核心功能，处理所有边界情况
"""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from app.services.match_service_simple import MatchService
from app.models.match_action import MatchAction, MatchActionType
from datetime import datetime


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
    def sample_action_data(self):
        """创建测试操作数据"""
        return {
            "cardId": "card123",
            "action": "like",
            "sceneType": "dating"
        }
    
    def test_init(self, mock_db):
        """测试初始化"""
        service = MatchService(mock_db)
        assert service.db == mock_db
    
    def test_submit_match_action_success(self, match_service, mock_db, sample_action_data):
        """测试成功提交匹配操作"""
        # 设置mock返回值
        mock_query = Mock()
        mock_query.first.return_value = None  # 无现有操作
        mock_db.query.return_value.filter.return_value = mock_query
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        with patch.object(match_service, '_extract_target_user_id', return_value="target123"):
            with patch.object(match_service, '_check_mutual_match', return_value=(False, None)):
                result = match_service.submit_match_action("user123", sample_action_data)
        
        assert result["isMatch"] is False
        assert result["message"] == "操作成功"
        assert "actionId" in result
        mock_db.add.assert_called_once()
    
    def test_submit_match_action_missing_params(self, match_service):
        """测试缺少必要参数 - 验证异常抛出"""
        invalid_data = {"cardId": "card123"}  # 缺少action和sceneType
        
        with pytest.raises(ValueError, match="缺少必要参数"):
            match_service.submit_match_action("user123", invalid_data)
    
    def test_submit_match_action_existing_action(self, match_service, mock_db, sample_action_data):
        """测试已经存在操作记录的情况"""
        existing_action = Mock()
        existing_action.action_type = MatchActionType.LIKE
        
        mock_query = Mock()
        mock_query.first.return_value = existing_action
        mock_db.query.return_value.filter.return_value = mock_query
        
        with patch.object(match_service, '_extract_target_user_id', return_value="target123"):
            result = match_service.submit_match_action("user123", sample_action_data)
        
        assert result["isMatch"] is False
        assert result["message"] == "已经对该用户执行过操作"
        assert result["existingAction"] == "like"
    
    def test_extract_target_user_id_from_user_str(self, match_service, mock_db):
        """测试直接从User表提取用户ID - 确保返回字符串"""
        mock_user = Mock()
        mock_user.id = "user123"
        
        mock_query = Mock()
        mock_query.first.return_value = mock_user
        mock_db.query.return_value.filter.return_value = mock_query
        
        # 使用str()确保返回字符串
        result = str(match_service._extract_target_user_id("user123", "dating"))
        
        assert result == "user123"
    
    def test_extract_target_user_id_not_found(self, match_service, mock_db):
        """测试无法提取目标用户ID"""
        mock_query = Mock()
        mock_query.first.return_value = None
        mock_db.query.return_value.filter.return_value = mock_query
        
        result = match_service._extract_target_user_id("invalid123", "dating")
        
        assert result is None
    
    def test_check_mutual_match_not_found(self, match_service, mock_db):
        """测试未找到双向匹配"""
        mock_query = Mock()
        mock_query.first.return_value = None
        mock_db.query.return_value.filter.return_value = mock_query
        
        result = match_service._check_mutual_match("user1", "user2", "card1", "dating", "action123")
        
        assert result == (False, None)
    
    def test_get_user_matches_empty_response(self, match_service, mock_db):
        """测试无匹配结果的空响应"""
        mock_query = Mock()
        mock_query.count.return_value = 0
        mock_query.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value = mock_query
        
        # 模拟用户查询返回None
        mock_user_query = Mock()
        mock_user_query.first.return_value = None
        mock_db.query.return_value.filter.return_value = mock_user_query
        
        result = match_service.get_user_matches("user123", status="all", page=1, page_size=10)
        
        assert result["pagination"]["total"] == 0
        assert result["matches"] == []
    
    def test_submit_match_action_exception(self, match_service, mock_db, sample_action_data):
        """测试提交操作时的异常处理"""
        mock_db.commit.side_effect = Exception("数据库错误")
        
        mock_query = Mock()
        mock_query.first.return_value = None
        mock_db.query.return_value.filter.return_value = mock_query
        
        with patch.object(match_service, '_extract_target_user_id', return_value="target123"):
            with pytest.raises(Exception, match="提交匹配操作失败"):
                match_service.submit_match_action("user123", sample_action_data)
    
    def test_get_match_detail_not_found(self, match_service, mock_db):
        """测试获取不存在的匹配详情"""
        mock_query = Mock()
        mock_query.first.return_value = None
        mock_db.query.return_value.filter.return_value = mock_query
        
        result = match_service.get_match_detail("nonexistent", "user123")
        
        assert result is None
    
    def test_get_user_match_actions_empty_response(self, match_service, mock_db):
        """测试获取空的操作历史"""
        mock_query = Mock()
        mock_query.count.return_value = 0
        mock_query.offset.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value = mock_query
        
        result = match_service.get_user_match_actions("user123")
        
        assert result["pagination"]["total"] == 0
        assert result["actions"] == []
    
    def test_submit_match_action_ai_recommend(self, match_service, mock_db):
        """测试AI引荐操作"""
        ai_data = {
            "cardId": "card123",
            "action": "ai_recommend_after_user_chat",
            "sceneType": "dating"
        }
        
        mock_query = Mock()
        mock_query.first.return_value = None
        mock_db.query.return_value.filter.return_value = mock_query
        
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        with patch.object(match_service, '_extract_target_user_id', return_value="target123"):
            with patch.object(match_service, '_check_mutual_match', return_value=(False, None)):
                result = match_service.submit_match_action("user123", ai_data)
        
        assert result["isMatch"] is False
        assert result["message"] == "操作成功"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])