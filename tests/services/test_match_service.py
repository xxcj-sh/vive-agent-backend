import pytest
import uuid
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.services.match_service.core import MatchCore
from app.services.match_service.card_strategy import CardMatchingStrategy
from app.services.match_service.models import MatchCandidate, MatchResult

class TestMatchCore:
    """匹配核心服务测试类"""
    
    @pytest.fixture
    def match_core(self, mock_db):
        """创建匹配核心服务实例"""
        return MatchCore(mock_db)
    
    @pytest.fixture
    def sample_user_data(self):
        """示例用户数据"""
        return {
            "id": str(uuid.uuid4()),
            "nick_name": "测试用户",
            "avatar_url": "https://example.com/avatar.jpg",
            "gender": 1,
            "age": 25,
            "location": ["北京"],
            "interests": ["运动", "音乐"],
            "role": "participant"
        }
    
    @pytest.fixture
    def sample_card_data(self):
        """示例卡片数据"""
        return {
            "id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "card_type": "dating",
            "title": "测试卡片",
            "description": "这是一个测试卡片",
            "tags": ["运动", "音乐"],
            "location": ["北京"],
            "status": "active"
        }
    
    def test_find_matches_success(self, match_core, sample_user_data):
        """测试查找匹配成功"""
        user_id = sample_user_data["id"]
        match_type = "dating"
        
        # 设置模拟候选数据
        mock_candidates = [
            Mock(spec=MatchCandidate, user_id=str(uuid.uuid4()), score=85.5),
            Mock(spec=MatchCandidate, user_id=str(uuid.uuid4()), score=78.0),
            Mock(spec=MatchCandidate, user_id=str(uuid.uuid4()), score=92.0)
        ]
        
        # 模拟策略方法
        with patch.object(match_core, '_get_match_candidates', return_value=mock_candidates):
            with patch.object(match_core, '_filter_candidates', return_value=mock_candidates):
                with patch.object(match_core, '_calculate_match_scores', return_value=mock_candidates):
                    with patch.object(match_core, '_sort_candidates', return_value=mock_candidates):
                        result = match_core.find_matches(user_id, match_type)
        
        assert result is not None
        assert len(result) == 3
        assert all(candidate.score > 0 for candidate in result)
    
    def test_find_matches_no_candidates(self, match_core, sample_user_data):
        """测试查找匹配无候选"""
        user_id = sample_user_data["id"]
        match_type = "dating"
        
        # 设置空候选数据
        with patch.object(match_core, '_get_match_candidates', return_value=[]):
            result = match_core.find_matches(user_id, match_type)
        
        assert result == []
    
    def test_find_matches_with_filters(self, match_core, sample_user_data):
        """测试查找匹配带过滤条件"""
        user_id = sample_user_data["id"]
        match_type = "dating"
        filters = {"location": ["北京"], "age_range": [20, 30]}
        
        mock_candidates = [Mock(spec=MatchCandidate, user_id=str(uuid.uuid4()), score=80.0)]
        
        with patch.object(match_core, '_get_match_candidates', return_value=mock_candidates):
            with patch.object(match_core, '_filter_candidates', return_value=mock_candidates):
                with patch.object(match_core, '_calculate_match_scores', return_value=mock_candidates):
                    with patch.object(match_core, '_sort_candidates', return_value=mock_candidates):
                        result = match_core.find_matches(user_id, match_type, filters=filters)
        
        assert result is not None
        assert len(result) == 1
    
    def test_create_match_success(self, match_core, sample_user_data):
        """测试创建匹配成功"""
        user1_id = sample_user_data["id"]
        user2_id = str(uuid.uuid4())
        match_type = "dating"
        score = 85.5
        
        mock_match = Mock()
        mock_match.id = str(uuid.uuid4())
        mock_match.user1_id = user1_id
        mock_match.user2_id = user2_id
        mock_match.score = score
        
        with patch('app.services.match_service.core.create_match_result', return_value=mock_match):
            result = match_core.create_match(user1_id, user2_id, match_type, score)
        
        assert result is not None
        assert result.user1_id == user1_id
        assert result.user2_id == user2_id
        assert result.score == score
    
    def test_create_match_with_details(self, match_core, sample_user_data):
        """测试创建匹配带详情"""
        user1_id = sample_user_data["id"]
        user2_id = str(uuid.uuid4())
        match_type = "dating"
        score = 85.5
        details = {"reason": "兴趣相似", "common_tags": ["运动", "音乐"]}
        
        mock_match = Mock()
        mock_match.id = str(uuid.uuid4())
        
        with patch('app.services.match_service.core.create_match_result', return_value=mock_match):
            with patch('app.services.match_service.core.add_match_detail') as mock_add_detail:
                result = match_core.create_match(user1_id, user2_id, match_type, score, details)
        
        assert result is not None
        mock_add_detail.assert_called_once()
    
    def test_get_match_history_success(self, match_core, sample_user_data):
        """测试获取匹配历史成功"""
        user_id = sample_user_data["id"]
        match_type = "dating"
        
        mock_matches = [
            Mock(user1_id=user_id, user2_id=str(uuid.uuid4()), score=85.5),
            Mock(user1_id=str(uuid.uuid4()), user2_id=user_id, score=78.0)
        ]
        
        with patch('app.services.match_service.core.get_user_match_results', return_value=mock_matches):
            result = match_core.get_match_history(user_id, match_type)
        
        assert result is not None
        assert len(result) == 2
        assert all(hasattr(match, 'score') for match in result)
    
    def test_get_match_history_empty(self, match_core, sample_user_data):
        """测试获取匹配历史为空"""
        user_id = sample_user_data["id"]
        match_type = "dating"
        
        with patch('app.services.match_service.core.get_user_match_results', return_value=[]):
            result = match_core.get_match_history(user_id, match_type)
        
        assert result == []
    
    def test_check_mutual_match_found(self, match_core, sample_user_data):
        """测试检查相互匹配找到"""
        user1_id = sample_user_data["id"]
        user2_id = str(uuid.uuid4())
        match_type = "dating"
        
        mock_match = Mock()
        mock_match.id = str(uuid.uuid4())
        mock_match.status = "matched"
        
        with patch('app.services.match_service.core.check_mutual_match', return_value=mock_match):
            result = match_core.check_mutual_match(user1_id, user2_id, match_type)
        
        assert result is not None
        assert result.status == "matched"
    
    def test_check_mutual_match_not_found(self, match_core, sample_user_data):
        """测试检查相互匹配未找到"""
        user1_id = sample_user_data["id"]
        user2_id = str(uuid.uuid4())
        match_type = "dating"
        
        with patch('app.services.match_service.core.check_mutual_match', return_value=None):
            result = match_core.check_mutual_match(user1_id, user2_id, match_type)
        
        assert result is None
    
    def test_get_match_candidates_with_location_filter(self, match_core, sample_user_data):
        """测试获取匹配候选带位置过滤"""
        user_id = sample_user_data["id"]
        
        mock_users = [
            Mock(id=str(uuid.uuid4()), location=["北京"]),
            Mock(id=str(uuid.uuid4()), location=["上海"])
        ]
        
        # 设置数据库查询模拟
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = mock_users
        match_core.db.query.return_value = mock_query
        
        with patch.object(match_core, '_get_user_by_id', return_value=sample_user_data):
            result = match_core._get_match_candidates(user_id, location_filter=["北京"])
        
        assert result is not None
        assert len(result) > 0
    
    def test_filter_candidates_by_age_range(self, match_core, sample_user_data):
        """测试按年龄范围过滤候选"""
        user_id = sample_user_data["id"]
        
        mock_candidates = [
            Mock(user_id=str(uuid.uuid4()), age=25),
            Mock(user_id=str(uuid.uuid4()), age=35),
            Mock(user_id=str(uuid.uuid4()), age=20)
        ]
        
        filters = {"age_range": [20, 30]}
        
        with patch.object(match_core, '_get_user_info', return_value={"age": 25}):
            result = match_core._filter_candidates(user_id, mock_candidates, filters)
        
        assert result is not None
        assert all(20 <= candidate.age <= 30 for candidate in result)
    
    def test_calculate_match_scores_similarity_based(self, match_core, sample_user_data):
        """测试基于相似度计算匹配分数"""
        user_id = sample_user_data["id"]
        
        mock_candidates = [
            Mock(user_id=str(uuid.uuid4())),
            Mock(user_id=str(uuid.uuid4()))
        ]
        
        with patch.object(match_core, '_calculate_similarity_score', return_value=85.0):
            result = match_core._calculate_match_scores(user_id, mock_candidates)
        
        assert result is not None
        assert all(candidate.score == 85.0 for candidate in result)
    
    def test_sort_candidates_by_score(self, match_core):
        """测试按分数排序候选"""
        mock_candidates = [
            Mock(user_id=str(uuid.uuid4()), score=75.0),
            Mock(user_id=str(uuid.uuid4()), score=90.0),
            Mock(user_id=str(uuid.uuid4()), score=85.0)
        ]
        
        result = match_core._sort_candidates(mock_candidates)
        
        assert result is not None
        assert len(result) == 3
        assert result[0].score >= result[1].score >= result[2].score
    
    def test_sort_candidates_with_limit(self, match_core):
        """测试按分数排序候选并限制数量"""
        mock_candidates = [
            Mock(user_id=str(uuid.uuid4()), score=95.0),
            Mock(user_id=str(uuid.uuid4()), score=90.0),
            Mock(user_id=str(uuid.uuid4()), score=85.0),
            Mock(user_id=str(uuid.uuid4()), score=80.0),
            Mock(user_id=str(uuid.uuid4()), score=75.0)
        ]
        
        limit = 3
        result = match_core._sort_candidates(mock_candidates, limit=limit)
        
        assert result is not None
        assert len(result) == 3
        assert result[0].score >= result[1].score >= result[2].score
        assert result[0].score == 95.0


class TestCardMatchingStrategy:
    """卡片匹配策略测试类"""
    
    @pytest.fixture
    def card_strategy(self, mock_db):
        """创建卡片匹配策略实例"""
        return CardMatchingStrategy(mock_db)
    
    @pytest.fixture
    def sample_card_data(self):
        """示例卡片数据"""
        return {
            "id": str(uuid.uuid4()),
            "user_id": str(uuid.uuid4()),
            "card_type": "dating",
            "title": "测试卡片",
            "description": "这是一个测试卡片",
            "tags": ["运动", "音乐", "电影"],
            "location": ["北京"],
            "status": "active",
            "created_at": datetime.now()
        }
    
    def test_find_matching_cards_success(self, card_strategy, sample_card_data):
        """测试查找匹配卡片成功"""
        user_id = sample_card_data["user_id"]
        card_type = "dating"
        
        mock_cards = [
            Mock(id=str(uuid.uuid4()), user_id=str(uuid.uuid4()), tags=["运动", "音乐"]),
            Mock(id=str(uuid.uuid4()), user_id=str(uuid.uuid4()), tags=["音乐", "电影"]),
            Mock(id=str(uuid.uuid4()), user_id=str(uuid.uuid4()), tags=["运动", "电影"])
        ]
        
        with patch.object(card_strategy, '_get_available_cards', return_value=mock_cards):
            with patch.object(card_strategy, '_calculate_card_match_score', return_value=80.0):
                result = card_strategy.find_matching_cards(user_id, card_type)
        
        assert result is not None
        assert len(result) == 3
    
    def test_find_matching_cards_no_cards(self, card_strategy, sample_card_data):
        """测试查找匹配卡片无可用卡片"""
        user_id = sample_card_data["user_id"]
        card_type = "dating"
        
        with patch.object(card_strategy, '_get_available_cards', return_value=[]):
            result = card_strategy.find_matching_cards(user_id, card_type)
        
        assert result == []
    
    def test_calculate_card_match_score_tag_similarity(self, card_strategy, sample_card_data):
        """测试计算卡片匹配分数基于标签相似度"""
        user_card = sample_card_data
        target_card = Mock(
            id=str(uuid.uuid4()),
            tags=["运动", "音乐", "阅读"],
            location=["北京"]
        )
        
        with patch.object(card_strategy, '_calculate_tag_similarity', return_value=0.8):
            with patch.object(card_strategy, '_calculate_location_match', return_value=1.0):
                score = card_strategy._calculate_card_match_score(user_card, target_card)
        
        assert score > 0
        assert score <= 100
    
    def test_calculate_tag_similarity_partial_match(self, card_strategy):
        """测试计算标签相似度部分匹配"""
        user_tags = ["运动", "音乐", "电影"]
        target_tags = ["音乐", "阅读", "旅行"]
        
        similarity = card_strategy._calculate_tag_similarity(user_tags, target_tags)
        
        assert similarity > 0
        assert similarity < 1.0
    
    def test_calculate_tag_similarity_exact_match(self, card_strategy):
        """测试计算标签相似度完全匹配"""
        user_tags = ["运动", "音乐", "电影"]
        target_tags = ["运动", "音乐", "电影"]
        
        similarity = card_strategy._calculate_tag_similarity(user_tags, target_tags)
        
        assert similarity == 1.0
    
    def test_calculate_tag_similarity_no_match(self, card_strategy):
        """测试计算标签相似度无匹配"""
        user_tags = ["运动", "音乐"]
        target_tags = ["阅读", "旅行"]
        
        similarity = card_strategy._calculate_tag_similarity(user_tags, target_tags)
        
        assert similarity == 0.0
    
    def test_calculate_location_match_same_location(self, card_strategy):
        """测试计算位置匹配相同位置"""
        user_location = ["北京"]
        target_location = ["北京"]
        
        match_score = card_strategy._calculate_location_match(user_location, target_location)
        
        assert match_score == 1.0
    
    def test_calculate_location_match_different_locations(self, card_strategy):
        """测试计算位置匹配不同位置"""
        user_location = ["北京"]
        target_location = ["上海"]
        
        match_score = card_strategy._calculate_location_match(user_location, target_location)
        
        assert match_score == 0.0
    
    def test_calculate_location_match_multiple_locations(self, card_strategy):
        """测试计算位置匹配多位置"""
        user_location = ["北京", "上海"]
        target_location = ["上海", "广州"]
        
        match_score = card_strategy._calculate_location_match(user_location, target_location)
        
        assert match_score > 0
        assert match_score < 1.0
    
    def test_filter_cards_by_type(self, card_strategy):
        """测试按类型过滤卡片"""
        cards = [
            Mock(id=str(uuid.uuid4()), card_type="dating"),
            Mock(id=str(uuid.uuid4()), card_type="friendship"),
            Mock(id=str(uuid.uuid4()), card_type="dating")
        ]
        
        filtered_cards = card_strategy._filter_cards_by_type(cards, "dating")
        
        assert len(filtered_cards) == 2
        assert all(card.card_type == "dating" for card in filtered_cards)
    
    def test_filter_cards_by_status(self, card_strategy):
        """测试按状态过滤卡片"""
        cards = [
            Mock(id=str(uuid.uuid4()), status="active"),
            Mock(id=str(uuid.uuid4()), status="inactive"),
            Mock(id=str(uuid.uuid4()), status="active")
        ]
        
        filtered_cards = card_strategy._filter_cards_by_status(cards, "active")
        
        assert len(filtered_cards) == 2
        assert all(card.status == "active" for card in filtered_cards)
    
    def test_sort_cards_by_score(self, card_strategy):
        """测试按分数排序卡片"""
        cards = [
            Mock(id=str(uuid.uuid4()), score=75.0),
            Mock(id=str(uuid.uuid4()), score=90.0),
            Mock(id=str(uuid.uuid4()), score=85.0)
        ]
        
        sorted_cards = card_strategy._sort_cards_by_score(cards)
        
        assert len(sorted_cards) == 3
        assert sorted_cards[0].score >= sorted_cards[1].score >= sorted_cards[2].score
        assert sorted_cards[0].score == 90.0
    
    def test_sort_cards_with_limit(self, card_strategy):
        """测试按分数排序卡片并限制数量"""
        cards = [
            Mock(id=str(uuid.uuid4()), score=95.0),
            Mock(id=str(uuid.uuid4()), score=90.0),
            Mock(id=str(uuid.uuid4()), score=85.0),
            Mock(id=str(uuid.uuid4()), score=80.0),
            Mock(id=str(uuid.uuid4()), score=75.0)
        ]
        
        limit = 3
        sorted_cards = card_strategy._sort_cards_by_score(cards, limit=limit)
        
        assert len(sorted_cards) == 3
        assert sorted_cards[0].score >= sorted_cards[1].score >= sorted_cards[2].score
        assert sorted_cards[0].score == 95.0