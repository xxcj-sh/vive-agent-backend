import pytest
import uuid
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta

from app.services.user_stats_service import UserStatsService
from app.models.match_action import MatchAction, MatchActionType
from app.models.match_action import MatchResult, MatchResultStatus
from app.models.user import User
from app.models.user_card_db import UserCard


class TestUserStatsService:
    """用户统计服务测试类"""
    
    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return Mock()
    
    @pytest.fixture
    def sample_user_id(self):
        """示例用户ID"""
        return str(uuid.uuid4())
    
    def test_get_user_stats_success(self, mock_db, sample_user_id):
        """测试获取用户统计数据成功"""
        # 创建服务实例
        service = UserStatsService(mock_db)
        
        # 模拟卡片统计
        mock_card_query = Mock()
        mock_card_query.filter.return_value = mock_card_query
        mock_card_query.count.side_effect = [5, 3, 8, 2]  # total_cards, active_cards, total_created, recent_cards
        
        # 模拟收藏统计
        mock_favorite_query = Mock()
        mock_favorite_query.filter.return_value = mock_favorite_query
        mock_favorite_query.count.return_value = 10
        
        # 设置数据库查询
        mock_db.query.side_effect = [mock_card_query, mock_favorite_query]
        
        # 获取统计数据
        result = service.get_user_stats(sample_user_id)
        
        # 验证结果
        assert result["cardCount"] == 5
        assert result["activeCardCount"] == 3
        assert result["favoriteCardCount"] == 10
        assert result["totalCardsCreated"] == 8
        assert result["recentCards"] == 2
    
    def test_get_user_stats_with_exception(self, mock_db, sample_user_id):
        """测试获取用户统计数据时发生异常"""
        # 创建服务实例
        service = UserStatsService(mock_db)
        
        # 模拟数据库查询抛出异常
        mock_db.query.side_effect = Exception("数据库连接失败")
        
        # 获取统计数据
        result = service.get_user_stats(sample_user_id)
        
        # 验证返回默认值
        assert result["cardCount"] == 0
        assert result["activeCardCount"] == 0
        assert result["favoriteCardCount"] == 0
        assert result["totalCardsCreated"] == 0
        assert result["recentCards"] == 0
    
    def test_get_match_stats_success(self, mock_db, sample_user_id):
        """测试获取匹配统计成功"""
        # 创建服务实例
        service = UserStatsService(mock_db)
        
        # 模拟匹配查询
        mock_match_query = Mock()
        mock_match_query.filter.return_value = mock_match_query
        mock_match_query.count.side_effect = [15, 8, 3]  # total_matches, active_matches, new_matches
        
        mock_db.query.return_value = mock_match_query
        
        # 调用私有方法（通过名称访问）
        result = service._get_match_stats(sample_user_id)
        
        # 验证结果
        assert result["total_matches"] == 15
        assert result["active_matches"] == 8
        assert result["new_matches"] == 3
    

    
    def test_get_card_stats_success(self, mock_db, sample_user_id):
        """测试获取卡片统计成功"""
        # 创建服务实例
        service = UserStatsService(mock_db)
        
        # 模拟卡片查询
        mock_card_query = Mock()
        mock_card_query.filter.return_value = mock_card_query
        mock_card_query.count.side_effect = [7, 4, 10, 1]  # 各种统计
        
        mock_db.query.return_value = mock_card_query
        
        # 调用私有方法
        result = service._get_card_stats(sample_user_id)
        
        # 验证结果
        assert result["total_cards"] == 7
        assert result["active_cards"] == 4
        assert result["total_created"] == 10
        assert result["recent_cards"] == 1
    
    def test_get_favorite_stats_success(self, mock_db, sample_user_id):
        """测试获取收藏统计成功"""
        # 创建服务实例
        service = UserStatsService(mock_db)
        
        # 模拟收藏查询
        mock_favorite_query = Mock()
        mock_favorite_query.filter.return_value = mock_favorite_query
        mock_favorite_query.count.return_value = 25
        
        mock_db.query.return_value = mock_favorite_query
        
        # 调用私有方法
        result = service._get_favorite_stats(sample_user_id)
        
        # 验证结果
        assert result["favorite_cards"] == 25
    
    def test_get_detailed_stats_success(self, mock_db, sample_user_id):
        """测试获取详细统计成功"""
        # 创建服务实例
        service = UserStatsService(mock_db)
        
        # 模拟基础统计
        mock_card_query = Mock()
        mock_card_query.filter.return_value = mock_card_query
        mock_card_query.count.side_effect = [5, 3, 8, 2]
        
        mock_favorite_query = Mock()
        mock_favorite_query.filter.return_value = mock_favorite_query
        mock_favorite_query.count.return_value = 10
        
        # 模拟用户查询
        mock_user = Mock()
        mock_user.created_at = datetime.now() - timedelta(days=30)
        
        mock_user_query = Mock()
        mock_user_query.filter.return_value = mock_user_query
        mock_user_query.first.return_value = mock_user
        
        # 设置数据库查询
        mock_db.query.side_effect = [mock_card_query, mock_favorite_query, mock_user_query]
        
        # 获取详细统计
        result = service.get_detailed_stats(sample_user_id)
        
        # 验证结果包含基础统计
        assert "cardCount" in result
        assert result["cardCount"] == 5
        assert "accountAgeDays" in result
        assert result["accountAgeDays"] == 30
    
    def test_get_detailed_stats_no_user(self, mock_db, sample_user_id):
        """测试获取详细统计时用户不存在"""
        # 创建服务实例
        service = UserStatsService(mock_db)
        
        # 模拟基础统计
        mock_card_query = Mock()
        mock_card_query.filter.return_value = mock_card_query
        mock_card_query.count.side_effect = [5, 3, 8, 2]
        
        mock_favorite_query = Mock()
        mock_favorite_query.filter.return_value = mock_favorite_query
        mock_favorite_query.count.return_value = 10
        
        # 模拟用户不存在
        mock_user_query = Mock()
        mock_user_query.filter.return_value = mock_user_query
        mock_user_query.first.return_value = None
        
        # 设置数据库查询
        mock_db.query.side_effect = [mock_card_query, mock_favorite_query, mock_user_query]
        
        # 获取详细统计
        result = service.get_detailed_stats(sample_user_id)
        
        # 验证结果包含基础统计但没有账户年龄
        assert "cardCount" in result
        assert result["cardCount"] == 5
        assert "accountAgeDays" not in result
    
    def test_get_collect_stats_success(self, mock_db, sample_user_id):
        """测试获取收藏统计（替代方法）"""
        # 创建服务实例
        service = UserStatsService(mock_db)
        
        # 模拟收藏查询
        mock_collect_query = Mock()
        mock_collect_query.filter.return_value = mock_collect_query
        mock_collect_query.count.return_value = 30
        
        mock_db.query.return_value = mock_collect_query
        
        # 调用私有方法
        result = service._get_collect_stats(sample_user_id)
        
        # 验证结果
        assert result["total_favorites"] == 30
    
    def test_complex_query_conditions(self, mock_db, sample_user_id):
        """测试复杂的查询条件"""
        # 创建服务实例
        service = UserStatsService(mock_db)
        
        # 模拟匹配统计中的OR条件
        mock_match_query = Mock()
        mock_match_query.filter.return_value = mock_match_query
        mock_match_query.count.return_value = 20
        
        mock_db.query.return_value = mock_match_query
        
        # 调用方法验证OR条件
        result = service._get_match_stats(sample_user_id)
        
        # 验证查询被调用
        mock_db.query.assert_called()
        assert result["total_matches"] == 20
    
    def test_time_range_queries(self, mock_db, sample_user_id):
        """测试时间范围查询"""
        # 创建服务实例
        service = UserStatsService(mock_db)
        
        # 模拟最近7天的查询
        mock_card_query = Mock()
        mock_card_query.filter.return_value = mock_card_query
        mock_card_query.filter.return_value = mock_card_query
        mock_card_query.count.return_value = 3
        
        mock_db.query.return_value = mock_card_query
        
        # 调用方法
        result = service._get_card_stats(sample_user_id)
        
        # 验证结果
        assert result["recent_cards"] == 3
        # 验证时间条件被使用
        assert mock_card_query.filter.call_count == 2
    
    def test_empty_stats_handling(self, mock_db, sample_user_id):
        """测试空统计数据的处理"""
        # 创建服务实例
        service = UserStatsService(mock_db)
        
        # 模拟所有查询都返回0
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        
        mock_db.query.return_value = mock_query
        
        # 获取各种统计
        match_stats = service._get_match_stats(sample_user_id)
        card_stats = service._get_card_stats(sample_user_id)
        
        # 验证所有统计都为0
        assert all(value == 0 for value in match_stats.values())
        assert all(value == 0 for value in card_stats.values())