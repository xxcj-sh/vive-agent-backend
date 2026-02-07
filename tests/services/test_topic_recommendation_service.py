"""
TopicRecommendationService 单元测试
测试话题/投票卡片的召回策略、排序算法、过滤逻辑等功能

测试策略：
1. 使用 Mock 对象模拟数据库查询，避免依赖真实数据库
2. 测试正常场景和异常场景
3. 测试边界条件
4. 为持续迭代优化提供基准测试

运行测试：
    pytest tests/services/test_topic_recommendation_service.py -v

运行特定测试类：
    pytest tests/services/test_topic_recommendation_service.py::TestScoreCalculation -v
"""
import pytest
from unittest.mock import Mock, MagicMock, patch, call
from datetime import datetime, timedelta
from typing import List, Set, Tuple

from app.services.topic_recommendation_service import TopicRecommendationService
from app.models.topic_card_db import TopicCard
from app.models.vote_card_db import VoteCard, VoteRecord
from app.models.tag import Tag, UserTagRel, TagType, UserTagRelStatus
from app.models.user import User
from app.models.user_connection import UserConnection, ConnectionType


class TestTopicRecommendationService:
    """TopicRecommendationService 测试基类"""
    
    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return Mock()
    
    @pytest.fixture
    def service(self, mock_db):
        """创建 TopicRecommendationService 实例"""
        return TopicRecommendationService(mock_db)
    
    @pytest.fixture
    def mock_topic_card(self):
        """创建模拟话题卡片"""
        card = Mock(spec=TopicCard)
        card.id = "topic_123"
        card.user_id = "user_456"
        card.title = "测试话题"
        card.description = "这是一个测试话题内容"
        card.category = "生活"
        card.tags = ["tag1", "tag2"]
        card.cover_image = "http://example.com/cover.jpg"
        card.discussion_count = 10
        card.like_count = 5
        card.view_count = 100
        card.is_active = 1
        card.is_deleted = 0
        card.visibility = "public"
        card.is_anonymous = 0
        card.created_at = datetime.now() - timedelta(days=1)
        card.updated_at = datetime.now()
        return card
    
    @pytest.fixture
    def mock_vote_card(self):
        """创建模拟投票卡片"""
        card = Mock(spec=VoteCard)
        card.id = "vote_123"
        card.user_id = "user_456"
        card.title = "测试投票"
        card.description = "这是一个测试投票"
        card.category = "娱乐"
        card.tags = ["tag1", "tag2"]
        card.cover_image = "http://example.com/cover.jpg"
        card.vote_type = "single"
        card.total_votes = 50
        card.view_count = 200
        card.is_active = 1
        card.is_deleted = 0
        card.visibility = "public"
        card.end_time = datetime.now() + timedelta(days=7)
        card.created_at = datetime.now() - timedelta(days=2)
        card.updated_at = datetime.now()
        return card
    
    @pytest.fixture
    def mock_topic_cards_list(self):
        """创建模拟话题卡片列表"""
        cards = []
        for i in range(5):
            card = Mock(spec=TopicCard)
            card.id = f"topic_{i}"
            card.user_id = f"user_{i}"
            card.title = f"话题{i}"
            card.description = f"内容{i}"
            card.category = "测试"
            card.tags = []
            card.cover_image = None
            card.discussion_count = i * 10
            card.like_count = i * 5
            card.view_count = i * 20
            card.is_active = 1
            card.is_deleted = 0
            card.visibility = "public"
            card.is_anonymous = 0
            card.created_at = datetime.now() - timedelta(days=i)
            card.updated_at = datetime.now()
            cards.append(card)
        return cards
    
    @pytest.fixture
    def mock_vote_cards_list(self):
        """创建模拟投票卡片列表"""
        cards = []
        for i in range(5):
            card = Mock(spec=VoteCard)
            card.id = f"vote_{i}"
            card.user_id = f"user_{i}"
            card.title = f"投票{i}"
            card.description = f"描述{i}"
            card.category = "测试"
            card.tags = []
            card.cover_image = None
            card.vote_type = "single"
            card.total_votes = i * 20
            card.view_count = i * 30
            card.is_active = 1
            card.is_deleted = 0
            card.visibility = "public"
            card.end_time = datetime.now() + timedelta(days=7)
            card.created_at = datetime.now() - timedelta(days=i)
            card.updated_at = datetime.now()
            cards.append(card)
        return cards


class TestScoreCalculation(TestTopicRecommendationService):
    """测试分数计算 - 核心算法测试"""
    
    def test_calculate_topic_card_score_creator_match(self, service, mock_topic_card):
        """测试话题卡片分数计算 - 创作者匹配（最高30分）"""
        # 创作者匹配的情况
        interested_users = {"user_456"}  # mock_topic_card.user_id
        score = service._calculate_topic_card_score(mock_topic_card, interested_users)
        
        # 验证分数包含创作者匹配分（30分）
        assert score >= 30, f"创作者匹配应至少得30分，实际得分: {score}"
    
    def test_calculate_topic_card_score_engagement_high(self, service):
        """测试话题卡片分数计算 - 高互动热度（30分）"""
        # 创建高互动卡片
        card = Mock(spec=TopicCard)
        card.user_id = "user_999"  # 不在感兴趣列表中
        card.discussion_count = 100
        card.like_count = 50
        card.created_at = datetime.now() - timedelta(days=10)
        
        interested_users = set()
        score = service._calculate_topic_card_score(card, interested_users)
        
        # 验证分数包含高互动热度分（30分）
        assert score >= 30, f"高互动应至少得30分，实际得分: {score}"
    
    def test_calculate_topic_card_score_engagement_medium(self, service):
        """测试话题卡片分数计算 - 中等互动热度（20分）"""
        card = Mock(spec=TopicCard)
        card.user_id = "user_999"
        card.discussion_count = 50
        card.like_count = 20
        card.created_at = datetime.now() - timedelta(days=10)
        
        interested_users = set()
        score = service._calculate_topic_card_score(card, interested_users)
        
        # 验证分数至少包含中等互动热度分（20分）
        assert score >= 20, f"中等互动应至少得20分，实际得分: {score}"
    
    def test_calculate_topic_card_score_freshness_high(self, service):
        """测试话题卡片分数计算 - 高新鲜度（30分）"""
        # 创建新卡片
        card = Mock(spec=TopicCard)
        card.user_id = "user_999"
        card.discussion_count = 0
        card.like_count = 0
        card.created_at = datetime.now() - timedelta(hours=1)  # 1小时前
        
        interested_users = set()
        score = service._calculate_topic_card_score(card, interested_users)
        
        # 验证分数包含高新鲜度分（30分）
        assert score >= 30, f"高新鲜度应至少得30分，实际得分: {score}"
    
    def test_calculate_topic_card_score_freshness_medium(self, service):
        """测试话题卡片分数计算 - 中等新鲜度（20分）"""
        card = Mock(spec=TopicCard)
        card.user_id = "user_999"
        card.discussion_count = 0
        card.like_count = 0
        card.created_at = datetime.now() - timedelta(days=3)  # 3天前
        
        interested_users = set()
        score = service._calculate_topic_card_score(card, interested_users)
        
        # 验证分数至少包含中等新鲜度分（20分）
        assert score >= 20, f"中等新鲜度应至少得20分，实际得分: {score}"
    
    def test_calculate_topic_card_score_random_factor(self, service, mock_topic_card):
        """测试话题卡片分数计算 - 随机因子（0-10分）"""
        interested_users = set()
        
        # 多次计算验证随机因子存在
        scores = []
        for _ in range(10):
            score = service._calculate_topic_card_score(mock_topic_card, interested_users)
            scores.append(score)
        
        # 验证分数有变化（随机因子的作用）
        assert len(set(scores)) > 1, "随机因子应导致分数有变化"
    
    def test_calculate_topic_card_score_range(self, service, mock_topic_cards_list):
        """测试话题卡片分数范围（0-100分）"""
        interested_users = {"user_0"}
        
        for card in mock_topic_cards_list:
            score = service._calculate_topic_card_score(card, interested_users)
            assert 0 <= score <= 100, f"分数应在0-100范围内，实际得分: {score}"
    
    def test_calculate_vote_card_score_creator_match(self, service, mock_vote_card):
        """测试投票卡片分数计算 - 创作者匹配（30分）"""
        # 创作者匹配的情况
        interested_users = {"user_456"}  # mock_vote_card.user_id
        score = service._calculate_vote_card_score(mock_vote_card, interested_users)
        
        # 验证分数包含创作者匹配分（30分）
        assert score >= 30, f"创作者匹配应至少得30分，实际得分: {score}"
    
    def test_calculate_vote_card_score_participation_high(self, service):
        """测试投票卡片分数计算 - 高参与度（30分）"""
        # 创建高参与度卡片
        card = Mock(spec=VoteCard)
        card.user_id = "user_999"
        card.total_votes = 100
        card.created_at = datetime.now() - timedelta(days=10)
        
        interested_users = set()
        score = service._calculate_vote_card_score(card, interested_users)
        
        # 验证分数包含高参与度分（30分）
        assert score >= 30, f"高参与度应至少得30分，实际得分: {score}"
    
    def test_calculate_vote_card_score_range(self, service, mock_vote_cards_list):
        """测试投票卡片分数范围（0-100分）"""
        interested_users = {"user_0"}
        
        for card in mock_vote_cards_list:
            score = service._calculate_vote_card_score(card, interested_users)
            assert 0 <= score <= 100, f"分数应在0-100范围内，实际得分: {score}"


class TestTitleSimilarity(TestTopicRecommendationService):
    """测试标题相似度计算"""
    
    def test_calculate_title_similarity_exact_match(self, service):
        """测试标题相似度 - 完全匹配"""
        similarity = service._calculate_title_similarity("测试标题", "测试标题")
        assert similarity == 1.0, f"完全匹配相似度应为1.0，实际: {similarity}"
    
    def test_calculate_title_similarity_completely_different(self, service):
        """测试标题相似度 - 完全不同"""
        similarity = service._calculate_title_similarity("abc", "xyz")
        assert similarity == 0.0, f"完全不同相似度应为0.0，实际: {similarity}"
    
    def test_calculate_title_similarity_partial_match(self, service):
        """测试标题相似度 - 部分匹配"""
        similarity = service._calculate_title_similarity("测试标题", "测试")
        assert 0 < similarity < 1, f"部分匹配相似度应在0-1之间，实际: {similarity}"
    
    def test_calculate_title_similarity_empty_strings(self, service):
        """测试标题相似度 - 空字符串"""
        similarity = service._calculate_title_similarity("", "测试")
        assert similarity == 0.0, f"空字符串相似度应为0.0，实际: {similarity}"
        
        similarity = service._calculate_title_similarity("测试", "")
        assert similarity == 0.0, f"空字符串相似度应为0.0，实际: {similarity}"


class TestDeduplication(TestTopicRecommendationService):
    """测试去重功能"""
    
    def test_deduplicate_cards_by_content_exact_match(self, service):
        """测试基于内容去重 - 完全匹配"""
        # 创建有相同标题的卡片
        cards = []
        for i in range(3):
            card = Mock(spec=TopicCard)
            card.id = f"topic_{i}"
            card.title = "相同标题"  # 相同标题
            cards.append(card)
        
        # 执行测试
        result = service.deduplicate_cards_by_content(cards, similarity_threshold=0.8)
        
        # 验证结果 - 应该只保留一个
        assert len(result) == 1, f"完全重复应只保留1个，实际保留: {len(result)}"
    
    def test_deduplicate_cards_by_content_similar_match(self, service):
        """测试基于内容去重 - 相似匹配"""
        # 创建有相似标题的卡片
        cards = []
        titles = ["这是一个测试标题", "这是一个测试标题！", "完全不同的标题"]
        for i, title in enumerate(titles):
            card = Mock(spec=TopicCard)
            card.id = f"topic_{i}"
            card.title = title
            cards.append(card)
        
        # 执行测试
        result = service.deduplicate_cards_by_content(cards, similarity_threshold=0.8)
        
        # 验证结果 - 前两个应该被视为重复
        assert len(result) <= 2, f"相似标题去重后应保留不超过2个，实际保留: {len(result)}"
    
    def test_deduplicate_cards_by_content_no_duplicates(self, service):
        """测试基于内容去重 - 无重复"""
        # 创建完全不同标题的卡片
        cards = []
        for i in range(3):
            card = Mock(spec=TopicCard)
            card.id = f"topic_{i}"
            card.title = f"完全不同的标题{i}"
            cards.append(card)
        
        # 执行测试
        result = service.deduplicate_cards_by_content(cards, similarity_threshold=0.8)
        
        # 验证结果 - 应该全部保留
        assert len(result) == 3, f"无重复时应保留全部3个，实际保留: {len(result)}"
    
    def test_deduplicate_cards_by_content_empty_list(self, service):
        """测试基于内容去重 - 空列表"""
        result = service.deduplicate_cards_by_content([], similarity_threshold=0.8)
        assert result == [], "空列表应返回空列表"


class TestRankingStrategies(TestTopicRecommendationService):
    """测试排序策略"""
    
    def test_rank_topic_cards_empty_list(self, service):
        """测试话题卡片排序 - 空列表"""
        result = service.rank_topic_cards("user_123", [], 10)
        assert result == [], "空列表应返回空列表"
    
    def test_rank_topic_cards_with_data(self, service, mock_topic_cards_list):
        """测试话题卡片排序 - 有数据"""
        # 模拟 _get_interested_user_ids 方法
        with patch.object(service, '_get_interested_user_ids', return_value={"user_0", "user_1"}):
            # 执行测试
            result = service.rank_topic_cards("user_123", mock_topic_cards_list, 3)
            
            # 验证结果
            assert len(result) <= 3, f"返回数量不应超过限制"
            # 验证返回的是元组列表 (card, score)
            for item in result:
                assert isinstance(item, tuple), "返回项应为元组"
                card, score = item
                assert isinstance(score, float), "分数应为浮点数"
                assert score >= 0, "分数应大于等于0"
    
    def test_rank_topic_cards_order_by_score(self, service, mock_topic_cards_list):
        """测试话题卡片排序 - 按分数降序排列"""
        # 模拟 _get_interested_user_ids 方法
        with patch.object(service, '_get_interested_user_ids', return_value={"user_0"}):
            # 执行测试
            result = service.rank_topic_cards("user_123", mock_topic_cards_list, 5)
            
            # 验证结果按分数降序排列
            if len(result) > 1:
                scores = [score for _, score in result]
                assert scores == sorted(scores, reverse=True), "应按分数降序排列"
    
    def test_rank_vote_cards_empty_list(self, service):
        """测试投票卡片排序 - 空列表"""
        result = service.rank_vote_cards("user_123", [], 10)
        assert result == [], "空列表应返回空列表"
    
    def test_rank_vote_cards_with_data(self, service, mock_vote_cards_list):
        """测试投票卡片排序 - 有数据"""
        # 模拟 _get_interested_user_ids 方法
        with patch.object(service, '_get_interested_user_ids', return_value={"user_0", "user_1"}):
            # 执行测试
            result = service.rank_vote_cards("user_123", mock_vote_cards_list, 3)
            
            # 验证结果
            assert len(result) <= 3, f"返回数量不应超过限制"
            # 验证返回的是元组列表 (card, score)
            for item in result:
                assert isinstance(item, tuple), "返回项应为元组"
                card, score = item
                assert isinstance(score, float), "分数应为浮点数"
                assert score >= 0, "分数应大于等于0"


class TestInterestedUserIds(TestTopicRecommendationService):
    """测试获取感兴趣用户ID"""
    
    def test_get_interested_user_ids_with_visits(self, service, mock_db):
        """测试获取感兴趣用户 - 有访问记录"""
        # 设置模拟数据 - 最近访问的用户 (返回元组列表)
        recent_visits = [
            ("user_1",),
            ("user_2",)
        ]
        
        # 模拟两次查询：访问记录和互动记录
        mock_db.query.return_value.filter.return_value.distinct.return_value.all.side_effect = [
            recent_visits,  # 第一次调用返回访问记录
            []              # 第二次调用返回空互动记录
        ]
        
        # 执行测试
        result = service._get_interested_user_ids("user_123")
        
        # 验证结果
        assert isinstance(result, set), "结果应为集合"
        assert "user_1" in result, "应包含访问过的用户"
        assert "user_2" in result, "应包含访问过的用户"
    
    def test_get_interested_user_ids_empty(self, service, mock_db):
        """测试获取感兴趣用户 - 无访问记录"""
        # 设置模拟数据 - 无访问记录
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        # 执行测试
        result = service._get_interested_user_ids("user_123")
        
        # 验证结果
        assert isinstance(result, set), "结果应为集合"
        assert len(result) == 0, "无访问记录时应返回空集合"


class TestCardFormatting(TestTopicRecommendationService):
    """测试卡片格式化"""
    
    def test_format_topic_card_structure(self, service, mock_topic_card):
        """测试话题卡片格式化 - 结构完整性"""
        # 模拟数据库查询
        mock_user = Mock(spec=User)
        mock_user.avatar_url = "http://example.com/avatar.jpg"
        mock_user.nick_name = "测试用户"
        service.db.query.return_value.filter.return_value.first.return_value = mock_user
        
        # 执行测试
        result = service.format_topic_card(mock_topic_card, score=85.5, is_recommendation=True)
        
        # 验证结果结构
        assert result["card_type"] == "topic", "card_type应为topic"
        assert result["id"] == "topic_123", "id应正确"
        assert result["title"] == "测试话题", "title应正确"
        assert "recommend_score" in result, "应包含recommend_score"
        assert result["isRecommendation"] is True, "isRecommendation应为True"
    
    def test_format_vote_card_structure(self, service, mock_vote_card):
        """测试投票卡片格式化 - 结构完整性"""
        # 模拟数据库查询
        mock_user = Mock(spec=User)
        mock_user.avatar_url = "http://example.com/avatar.jpg"
        mock_user.nick_name = "测试用户"
        service.db.query.return_value.filter.return_value.first.return_value = mock_user
        
        # 模拟 VoteService - 在函数内部导入，需要patch app.services.vote_service.VoteService
        with patch('app.services.vote_service.VoteService') as MockVoteService:
            mock_vote_service = Mock()
            mock_vote_service.get_vote_results.return_value = {
                "options": [],
                "has_voted": False,
                "user_votes": []
            }
            MockVoteService.return_value = mock_vote_service
            
            # 执行测试
            result = service.format_vote_card(mock_vote_card, score=90.0, is_recommendation=True, user_id="user_123")
            
            # 验证结果结构
            assert result["card_type"] == "topic", "card_type应为topic"
            assert result["id"] == "vote_123", "id应正确"
            assert result["title"] == "测试投票", "title应正确"
            assert "recommend_score" in result, "应包含recommend_score"
            assert result["isRecommendation"] is True, "isRecommendation应为True"


class TestExclusionLogic(TestTopicRecommendationService):
    """测试排除逻辑"""
    
    def test_get_excluded_topic_card_ids_own_cards(self, service, mock_db):
        """测试获取排除的话题卡片 - 自己创建的"""
        # 设置模拟数据 - 用户自己创建的卡片
        own_cards = [("topic_1",), ("topic_2",)]
        mock_db.query.return_value.filter.return_value.all.return_value = own_cards
        
        # 执行测试
        result = service.get_excluded_topic_card_ids("user_123")
        
        # 验证结果
        assert isinstance(result, set), "结果应为集合"
        assert "topic_1" in result, "应包含自己创建的卡片"
        assert "topic_2" in result, "应包含自己创建的卡片"
    
    def test_get_excluded_vote_card_ids_own_and_voted(self, service, mock_db):
        """测试获取排除的投票卡片 - 自己创建的和已投票的"""
        # 设置模拟数据 - 用户自己创建的卡片
        own_cards = [("vote_1",), ("vote_2",)]
        
        # 用户已投票的记录
        voted_records = [("vote_3",), ("vote_4",)]
        
        # 模拟两次查询 - 第一次没有distinct，第二次有distinct
        mock_db.query.return_value.filter.return_value.all.return_value = own_cards
        mock_db.query.return_value.filter.return_value.distinct.return_value.all.return_value = voted_records
        
        # 执行测试
        result = service.get_excluded_vote_card_ids("user_123")
        
        # 验证结果
        assert isinstance(result, set), "结果应为集合"
        assert "vote_1" in result, "应包含自己创建的投票"
        assert "vote_2" in result, "应包含自己创建的投票"
        assert "vote_3" in result, "应包含已投票的"
        assert "vote_4" in result, "应包含已投票的"


class TestConfigurationConstants(TestTopicRecommendationService):
    """测试配置常量"""
    
    def test_recall_limit_constant(self, service):
        """测试召回限制常量"""
        assert service.RECALL_LIMIT == 100, "RECALL_LIMIT应为100"
    
    def test_rank_limit_constant(self, service):
        """测试排序限制常量"""
        assert service.RANK_LIMIT == 50, "RANK_LIMIT应为50"
    
    def test_recent_view_days_constant(self, service):
        """测试最近浏览天数常量"""
        assert service.RECENT_VIEW_DAYS == 14, "RECENT_VIEW_DAYS应为14"
    
    def test_cold_start_user_id_constant(self, service):
        """测试冷启动用户ID常量"""
        assert service.COLD_START_USER_ID == "xiaojingling-001", "COLD_START_USER_ID应为xiaojingling-001"


class TestEdgeCases(TestTopicRecommendationService):
    """测试边界情况"""
    
    def test_calculate_score_with_none_values(self, service):
        """测试分数计算 - 处理None值"""
        card = Mock(spec=TopicCard)
        card.user_id = "user_123"
        card.discussion_count = None  # None值
        card.like_count = None
        card.created_at = None
        
        interested_users = set()
        score = service._calculate_topic_card_score(card, interested_users)
        
        # 验证能正常计算，不抛出异常
        assert isinstance(score, float), "分数应为浮点数"
        assert score >= 0, "分数应大于等于0"
    
    def test_rank_with_limit_zero(self, service, mock_topic_cards_list):
        """测试排序 - limit为0"""
        with patch.object(service, '_get_interested_user_ids', return_value=set()):
            result = service.rank_topic_cards("user_123", mock_topic_cards_list, 0)
            assert result == [], "limit为0时应返回空列表"
    
    def test_deduplicate_with_none_titles(self, service):
        """测试去重 - 处理None标题"""
        cards = []
        for i in range(2):
            card = Mock(spec=TopicCard)
            card.id = f"topic_{i}"
            card.title = None  # None标题
            cards.append(card)
        
        # 执行测试 - 不应抛出异常
        result = service.deduplicate_cards_by_content(cards, similarity_threshold=0.8)
        assert isinstance(result, list), "应返回列表"


# 用于持续迭代的基准测试
class TestBenchmarks(TestTopicRecommendationService):
    """基准测试 - 用于持续优化策略效果"""
    
    def test_topic_card_score_distribution(self, service, mock_topic_cards_list):
        """测试话题卡片分数分布 - 验证区分度"""
        interested_users = {"user_0"}
        
        scores = []
        for card in mock_topic_cards_list:
            score = service._calculate_topic_card_score(card, interested_users)
            scores.append(score)
        
        # 验证分数在合理范围内（0-100分）
        for score in scores:
            assert 0 <= score <= 100, f"分数应在0-100范围内，实际: {score}"
        
        # 验证分数有区分度（不是所有分数都相同）
        assert len(set(scores)) > 1, "分数应有区分度"
        
        # 验证最高分卡片是user_0的（创作者匹配）
        max_score_index = scores.index(max(scores))
        assert mock_topic_cards_list[max_score_index].user_id == "user_0", "最高分应为创作者匹配的卡片"
    
    def test_vote_card_score_distribution(self, service, mock_vote_cards_list):
        """测试投票卡片分数分布 - 验证区分度"""
        interested_users = {"user_0"}
        
        scores = []
        for card in mock_vote_cards_list:
            score = service._calculate_vote_card_score(card, interested_users)
            scores.append(score)
        
        # 验证分数在合理范围内（0-100分）
        for score in scores:
            assert 0 <= score <= 100, f"分数应在0-100范围内，实际: {score}"
        
        # 验证分数有区分度
        assert len(set(scores)) > 1, "分数应有区分度"
    
    def test_deduplication_effectiveness(self, service):
        """测试去重效果 - 验证准确性"""
        # 创建测试数据 - 包含重复和不同的标题
        cards = []
        titles = [
            "完全相同",
            "完全相同",
            "完全相同",
            "相似标题",
            "相似标题！",
            "完全不同1",
            "完全不同2"
        ]
        
        for i, title in enumerate(titles):
            card = Mock(spec=TopicCard)
            card.id = f"topic_{i}"
            card.title = title
            cards.append(card)
        
        # 执行去重
        result = service.deduplicate_cards_by_content(cards, similarity_threshold=0.8)
        
        # 验证去重效果 - 应该保留4个（完全相同保留1个，相似保留1个，完全不同的2个）
        assert len(result) <= 4, f"去重后应保留不超过4个，实际: {len(result)}"
        
        # 验证保留的是第一个出现的
        result_ids = [card.id for card in result]
        assert "topic_0" in result_ids, "应保留第一个完全相同标题的卡片"
