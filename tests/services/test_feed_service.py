"""
FeedService 测试用例
"""
import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.services.feed_service import FeedService
from app.models.user import User
from app.models.topic_card_db import TopicCard
from app.models.vote_card_db import VoteCard
from app.models.user_card_db import UserCard
from tests.test_utils import (
    create_mock_user, create_mock_topic_card, create_mock_vote_card,
    create_mock_user_card, setup_mock_query, assert_pagination_result,
    assert_card_structure, MockQueryBuilder
)


class TestFeedService:
    """FeedService 测试类"""
    
    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def feed_service(self, mock_db):
        """创建 FeedService 实例"""
        return FeedService(mock_db)
    
    @pytest.fixture
    def mock_user(self):
        """创建模拟用户"""
        return create_mock_user(
            user_id="test_user_123",
            nick_name="测试用户",
            avatar_url="http://example.com/avatar.jpg",
            is_public=True
        )
    
    @pytest.fixture
    def mock_topic_card(self):
        """创建模拟话题卡片"""
        return create_mock_topic_card(
            card_id="test_topic_123",
            user_id="test_user_123",
            title="测试话题",
            description="这是一个测试话题描述",
            cover_image="http://example.com/cover.jpg",
            category="测试分类",
            tags=["测试", "话题"],
            visibility="public",
            is_anonymous=False
        )
    
    @pytest.fixture
    def mock_vote_card(self):
        """创建模拟投票卡片"""
        return create_mock_vote_card(
            card_id="test_vote_123",
            user_id="test_user_123",
            title="测试投票",
            vote_type="single",
            is_anonymous=False,
            is_realtime_result=True,
            is_active=True
        )
    
    @pytest.fixture
    def mock_user_card(self):
        """创建模拟用户卡片"""
        return create_mock_user_card(
            card_id="test_user_card_123",
            user_id="test_user_123",
            nick_name="测试用户",
            avatar_url="http://example.com/avatar.jpg",
            bio="这是一个测试用户的简介",
            is_public=True
        )


class TestFeedServiceMediaUrlProcessing:
    """测试媒体URL处理功能"""
    
    def test_process_media_url_with_full_url(self):
        """测试处理完整URL的情况"""
        url = "https://example.com/image.jpg"
        result = FeedService._process_media_url(url)
        assert result == url
    
    def test_process_media_url_with_relative_path(self):
        """测试处理相对路径的情况"""
        url = "/uploads/image.jpg"
        result = FeedService._process_media_url(url)
        assert result == "http://47.117.95.151:8000/uploads/image.jpg"
    
    def test_process_media_url_with_empty_string(self):
        """测试处理空字符串的情况"""
        url = ""
        result = FeedService._process_media_url(url)
        assert result == ""
    
    def test_process_media_url_with_none(self):
        """测试处理None的情况"""
        url = None
        result = FeedService._process_media_url(url)
        assert result is None


class TestFeedServiceRandomPublicUserCards:
    """测试获取随机公开用户卡片功能"""
    
    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def feed_service(self, mock_db):
        """创建 FeedService 实例"""
        return FeedService(mock_db)
    
    @pytest.fixture
    def mock_user(self):
        """创建模拟用户"""
        return create_mock_user(
            user_id="test_user_123",
            nick_name="测试用户",
            avatar_url="http://example.com/avatar.jpg",
            is_public=True
        )
    
    def test_get_random_public_user_cards_success(self, feed_service, mock_db):
        """测试成功获取随机公开用户卡片"""
        # 创建模拟用户卡片列表
        mock_user_cards = []
        for i in range(5):
            user_card = Mock()
            user_card.id = f"user_card_{i}"
            user_card.user_id = f"user_{i}"
            user_card.display_name = f"用户{i}"
            user_card.avatar_url = f"http://example.com/avatar_{i}.jpg"
            user_card.location = f"城市{i}"
            user_card.bio = f"这是用户{i}的简介"
            user_card.visibility = "public"
            user_card.is_active = 1
            user_card.is_deleted = 0
            mock_user_cards.append(user_card)
        
        # 创建对应的模拟用户
        mock_users = []
        for i in range(5):
            user = Mock()
            user.id = f"user_{i}"
            user.nick_name = f"用户{i}"
            user.avatar_url = f"http://example.com/avatar_{i}.jpg"
            user.age = 25 + i
            user.occupation = f"职业{i}"
            user.interests = [f"兴趣{i}", f"爱好{i}"]
            user.is_active = 1
            mock_users.append(user)
        
        # 设置数据库查询返回结果
        # 第一次查询返回用户卡片
        mock_user_card_query = Mock()
        mock_user_card_query.filter.return_value = mock_user_card_query
        mock_user_card_query.order_by.return_value = mock_user_card_query
        mock_user_card_query.limit.return_value = mock_user_card_query
        mock_user_card_query.all.return_value = mock_user_cards
        
        # 用户查询 - 每次都返回对应的用户
        def create_user_query():
            user_query = Mock()
            user_query.filter.return_value = user_query
            user_query.first.side_effect = mock_users  # 按顺序返回用户
            return user_query
        
        # 设置查询的side_effect
        query_count = 0
        def query_side_effect(model):
            nonlocal query_count
            if model.__name__ == 'UserCard':
                return mock_user_card_query
            elif model.__name__ == 'User':
                query_count += 1
                return create_user_query()
            return Mock()
        
        mock_db.query.side_effect = query_side_effect
        
        # 调用方法
        result = feed_service.get_random_public_user_cards(limit=5)
        
        # 验证结果
        assert len(result) == 5
        assert result[0]["cardType"] == "social"
        assert result[0]["userId"] == "user_0"
        assert result[0]["name"] == "用户0"
        assert "avatar" in result[0]
        assert "bio" in result[0]
    
    def test_get_random_public_user_cards_empty_result(self, feed_service, mock_db):
        """测试没有公开用户的情况"""
        # 设置数据库查询返回空结果
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        
        # 调用方法
        result = feed_service.get_random_public_user_cards(limit=5)
        
        # 验证结果
        assert result == []
    
    def test_get_random_public_user_cards_with_limit(self, feed_service, mock_db):
        """测试指定数量限制的情况"""
        # 创建模拟用户卡片
        mock_user_card = Mock()
        mock_user_card.id = "user_card_123"
        mock_user_card.user_id = "user_123"
        mock_user_card.display_name = "测试用户"
        mock_user_card.avatar_url = "http://example.com/avatar.jpg"
        mock_user_card.location = "测试城市"
        mock_user_card.bio = "这是测试用户的简介"
        mock_user_card.visibility = "public"
        mock_user_card.is_active = 1
        mock_user_card.is_deleted = 0
        
        # 创建对应的模拟用户
        mock_user = Mock()
        mock_user.id = "user_123"
        mock_user.nick_name = "测试用户"
        mock_user.avatar_url = "http://example.com/avatar.jpg"
        mock_user.age = 25
        mock_user.occupation = "测试职业"
        mock_user.interests = ["测试兴趣"]
        mock_user.is_active = 1
        
        # 设置数据库查询返回结果
        mock_db.query.side_effect = [
            # 第一次查询 - 用户卡片
            Mock(filter=Mock(return_value=Mock(
                order_by=Mock(return_value=Mock(
                    limit=Mock(return_value=Mock(
                        all=Mock(return_value=[mock_user_card])
                    ))
                ))
            ))),
            # 后续查询 - 用户
            Mock(filter=Mock(return_value=Mock(
                first=Mock(return_value=mock_user)
            )))
        ]
        
        # 调用方法
        result = feed_service.get_random_public_user_cards(limit=1)
        
        # 验证结果
        assert len(result) == 1
        assert result[0]["userId"] == "user_123"


class TestFeedServiceRecommendationUserCards:
    """测试获取推荐用户卡片功能"""
    
    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def feed_service(self, mock_db):
        """创建 FeedService 实例"""
        return FeedService(mock_db)
    
    @pytest.fixture
    def mock_user(self):
        """创建模拟用户"""
        return create_mock_user(
            user_id="test_user_123",
            nick_name="测试用户",
            avatar_url="http://example.com/avatar.jpg",
            is_public=True
        )
    
    def test_get_feed_user_cards_success(self, feed_service, mock_db, mock_user, monkeypatch):
        """测试成功获取推荐用户卡片"""
        # 创建模拟推荐用户数据（这是 UserConnectionService.get_recommended_users 的返回格式）
        mock_recommended_users = []
        for i in range(10):
            user_data = {
                "id": f"user_{i}",
                "nick_name": f"用户{i}",
                "avatar_url": f"http://example.com/avatar_{i}.jpg",
                "gender": "male",
                "age": 25 + i,
                "occupation": f"职业{i}",
                "location": f"城市{i}",
                "bio": f"这是用户{i}的简介",
                "last_visit_time": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "connection_info": {"has_visited": True}
            }
            mock_recommended_users.append(user_data)
        
        # 创建模拟用户卡片
        mock_user_cards = []
        for i in range(10):
            card = Mock()
            card.id = f"user_card_{i}"
            card.user_id = f"user_{i}"
            card.display_name = f"用户{i}"
            card.avatar_url = f"http://example.com/avatar_{i}.jpg"
            card.location = f"城市{i}"
            card.bio = f"这是用户{i}的简介"
            card.visibility = "public"
            card.is_active = 1
            card.is_deleted = 0
            mock_user_cards.append(card)
        
        # 模拟 UserConnectionService.get_recommended_users 方法
        def mock_get_recommended_users(db, current_user_id, limit):
            return mock_recommended_users[:limit]
        
        # 使用 monkeypatch 替换实际的 UserConnectionService.get_recommended_users
        import app.services.feed_service as feed_module
        monkeypatch.setattr(feed_module.UserConnectionService, 'get_recommended_users', mock_get_recommended_users)
        
        # 设置数据库查询返回结果（用于查询用户卡片）
        mock_card_query = Mock()
        mock_card_query.filter.return_value = mock_card_query
        mock_card_query.count.return_value = len(mock_user_cards)
        mock_card_query.all.return_value = mock_user_cards
        
        mock_db.query.return_value = mock_card_query
        
        # 调用方法
        result = feed_service.get_feed_user_cards(
            user_id="current_user_123",
            page=1,
            page_size=10
        )
        
        # 验证结果
        assert "cards" in result
        assert "pagination" in result
        assert "source" in result
        assert len(result["cards"]) == 10
        assert result["pagination"]["page"] == 1
        assert result["pagination"]["pageSize"] == 10
        assert result["pagination"]["total"] == 10
        assert result["pagination"]["totalPages"] == 1
        assert result["source"] == "recommendation_with_visit_logic"
    
    def test_get_feed_user_cards_empty_result(self, feed_service, mock_db, monkeypatch):
        """测试没有推荐用户的情况"""
        # 模拟 UserConnectionService.get_recommended_users 返回空列表
        def mock_get_recommended_users(db, current_user_id, limit):
            return []
        
        # 使用 monkeypatch 替换实际的 UserConnectionService.get_recommended_users
        import app.services.feed_service as feed_module
        monkeypatch.setattr(feed_module.UserConnectionService, 'get_recommended_users', mock_get_recommended_users)
        
        # 调用方法
        result = feed_service.get_feed_user_cards(
            user_id="current_user_123",
            page=1,
            page_size=10
        )
        
        # 验证结果
        assert len(result["cards"]) == 0
        assert result["pagination"]["total"] == 0
        assert result["pagination"]["totalPages"] == 0
        assert result["source"] == "recommendation_with_visit_logic"
    
    def test_get_feed_user_cards_pagination(self, feed_service, mock_db, mock_user, monkeypatch):
        """测试分页功能"""
        # 创建模拟推荐用户数据（15个用户）
        mock_recommended_users = []
        for i in range(15):
            user_data = {
                "id": f"user_{i}",
                "nick_name": f"用户{i}",
                "avatar_url": f"http://example.com/avatar_{i}.jpg",
                "gender": "male",
                "age": 25 + i,
                "occupation": f"职业{i}",
                "location": f"城市{i}",
                "bio": f"这是用户{i}的简介",
                "last_visit_time": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "connection_info": {"has_visited": True}
            }
            mock_recommended_users.append(user_data)
        
        # 创建模拟用户卡片（15个）
        mock_user_cards = []
        for i in range(15):
            card = Mock()
            card.id = f"user_card_{i}"
            card.user_id = f"user_{i}"
            card.display_name = f"用户{i}"
            card.avatar_url = f"http://example.com/avatar_{i}.jpg"
            card.location = f"城市{i}"
            card.bio = f"这是用户{i}的简介"
            card.visibility = "public"
            card.is_active = 1
            card.is_deleted = 0
            mock_user_cards.append(card)
        
        # 模拟 UserConnectionService.get_recommended_users 方法
        def mock_get_recommended_users(db, current_user_id, limit):
            return mock_recommended_users[:limit]
        
        # 使用 monkeypatch 替换实际的 UserConnectionService.get_recommended_users
        import app.services.feed_service as feed_module
        monkeypatch.setattr(feed_module.UserConnectionService, 'get_recommended_users', mock_get_recommended_users)
        
        # 设置数据库查询返回结果（用于查询用户卡片）
        mock_card_query = Mock()
        mock_card_query.filter.return_value = mock_card_query
        mock_card_query.count.return_value = 15
        mock_card_query.all.return_value = mock_user_cards
        
        mock_db.query.return_value = mock_card_query
        
        # 调用方法（第二页）
        result = feed_service.get_feed_user_cards(
            user_id="current_user_123",
            page=2,
            page_size=10
        )
        
        # 验证分页参数
        assert result["pagination"]["page"] == 2
        assert result["pagination"]["pageSize"] == 10
        assert result["pagination"]["total"] == 15
        assert result["pagination"]["totalPages"] == 2


class TestFeedServiceGetFeedCards:
    """测试获取卡片流功能"""
    
    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def feed_service(self, mock_db):
        """创建 FeedService 实例"""
        return FeedService(mock_db)
    
    @pytest.fixture
    def mock_user(self):
        """创建模拟用户"""
        return create_mock_user(
            user_id="test_user_123",
            nick_name="测试用户",
            avatar_url="http://example.com/avatar.jpg",
            is_public=True
        )
    
    @pytest.fixture
    def mock_topic_card(self):
        """创建模拟话题卡片"""
        return create_mock_topic_card(
            card_id="test_topic_123",
            user_id="test_user_123",
            title="测试话题",
            description="这是一个测试话题描述",
            cover_image="http://example.com/cover.jpg",
            category="测试分类",
            tags=["测试", "话题"],
            visibility="public",
            is_anonymous=False
        )
    
    @pytest.fixture
    def mock_vote_card(self):
        """创建模拟投票卡片"""
        return create_mock_vote_card(
            card_id="test_vote_123",
            user_id="test_user_123",
            title="测试投票",
            vote_type="single",
            is_anonymous=False,
            is_realtime_result=True,
            is_active=True
        )
    
    def test_get_feed_item_cards_with_user_authenticated(self, feed_service, mock_db, mock_user, mock_topic_card, mock_vote_card, monkeypatch):
        """测试用户已认证的情况"""
        # 创建模拟话题卡片响应（这是 TopicCardService.get_topic_cards 的返回格式）
        mock_topic_cards = [
            Mock(
                id="topic_1",
                title="测试话题1",
                description="测试话题描述1",
                category="测试分类",
                tags=["测试"],
                cover_image="http://example.com/cover1.jpg",
                visibility="public",
                is_anonymous=False,
                view_count=10,
                like_count=5,
                discussion_count=3,
                created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
                creator_nickname="用户1",
                creator_avatar="http://example.com/avatar1.jpg"
            ),
            Mock(
                id="topic_2",
                title="测试话题2",
                description="测试话题描述2",
                category="测试分类",
                tags=["测试"],
                cover_image="http://example.com/cover2.jpg",
                visibility="public",
                is_anonymous=False,
                view_count=20,
                like_count=10,
                discussion_count=6,
                created_at=datetime(2024, 1, 2, tzinfo=timezone.utc),
                creator_nickname="用户2",
                creator_avatar="http://example.com/avatar2.jpg"
            )
        ]
        
        # 创建模拟投票卡片响应（匹配 VoteCard 模型结构）
        mock_vote_cards = [
            Mock(
                id="vote_1",
                user_id="user_3",
                title="测试投票1",
                description="测试投票描述1",
                category="测试分类",
                tags=["测试"],
                cover_image="http://example.com/cover1.jpg",
                vote_type="single",
                is_anonymous=False,
                is_realtime_result=True,
                visibility="public",
                total_votes=100,
                view_count=50,
                discussion_count=5,
                created_at=datetime(2024, 1, 3, tzinfo=timezone.utc),
                updated_at=datetime(2024, 1, 3, tzinfo=timezone.utc),
                end_time=datetime(2024, 2, 1, tzinfo=timezone.utc),
                start_time=None
            ),
            Mock(
                id="vote_2",
                user_id="user_4",
                title="测试投票2",
                description="测试投票描述2",
                category="测试分类",
                tags=["测试"],
                cover_image="http://example.com/cover2.jpg",
                vote_type="multiple",
                is_anonymous=True,
                is_realtime_result=False,
                visibility="public",
                total_votes=50,
                view_count=30,
                discussion_count=3,
                created_at=datetime(2024, 1, 4, tzinfo=timezone.utc),
                updated_at=datetime(2024, 1, 4, tzinfo=timezone.utc),
                end_time=datetime(2024, 2, 2, tzinfo=timezone.utc),
                start_time=None
            )
        ]
        
        # 模拟 TopicCardService.get_topic_cards 方法
        def mock_get_topic_cards(db, user_id, page, page_size, category=None):
            return {
                "items": mock_topic_cards,
                "total": len(mock_topic_cards),
                "page": page,
                "page_size": page_size,
                "total_pages": 1
            }
        
        # 模拟 VoteService.get_recall_vote_cards 方法
        def mock_get_recall_vote_cards(db, limit=10, user_id=None):
            return mock_vote_cards
        
        # 模拟 VoteService.get_vote_results 方法
        def mock_get_vote_results(self, vote_card_id, user_id=None):
            return {
                "has_voted": False,
                "user_votes": [],
                "options": []
            }
        
        # 使用 monkeypatch 替换实际的服务方法
        import app.services.feed_service as feed_module
        monkeypatch.setattr(feed_module.TopicCardService, 'get_topic_cards', mock_get_topic_cards)
        monkeypatch.setattr(feed_module.VoteService, 'get_recall_vote_cards', mock_get_recall_vote_cards)
        monkeypatch.setattr(feed_module.VoteService, 'get_vote_results', mock_get_vote_results)
        
        # 调用方法
        result = feed_service.get_feed_item_cards(
            user_id="test_user_123",
            page=1,
            page_size=10
        )
        
        # 验证结果
        assert "items" in result
        assert "page" in result
        assert "page_size" in result
        assert "total" in result
        assert len(result["items"]) == 4
        assert result["page"] == 1
        assert result["page_size"] == 10
        assert result["total"] == 4
    
    def test_get_feed_item_cards_anonymous_user(self, feed_service, mock_db, mock_topic_card, mock_vote_card, monkeypatch):
        """测试匿名用户的情况"""
        # 创建模拟话题卡片响应
        mock_topic_cards = [
            Mock(
                id="topic_1",
                title="测试话题1",
                description="测试话题描述1",
                category="测试分类",
                tags=["测试"],
                cover_image="http://example.com/cover1.jpg",
                visibility="public",
                is_anonymous=False,
                view_count=10,
                like_count=5,
                discussion_count=3,
                created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
                creator_nickname="用户1",
                creator_avatar="http://example.com/avatar1.jpg"
            )
        ]
        
        # 创建模拟投票卡片响应（匹配 VoteCard 模型结构）
        mock_vote_cards = [
            Mock(
                id="vote_1",
                user_id="user_3",
                title="测试投票1",
                description="测试投票描述1",
                category="测试分类",
                tags=["测试"],
                cover_image="http://example.com/cover1.jpg",
                vote_type="single",
                is_anonymous=False,
                is_realtime_result=True,
                visibility="public",
                total_votes=100,
                view_count=50,
                discussion_count=5,
                created_at=datetime(2024, 1, 3, tzinfo=timezone.utc),
                updated_at=datetime(2024, 1, 3, tzinfo=timezone.utc),
                end_time=datetime(2024, 2, 1, tzinfo=timezone.utc),
                start_time=None
            )
        ]
        
        # 模拟 TopicCardService.get_topic_cards 方法
        def mock_get_topic_cards(db, user_id, page, page_size, category=None):
            return {
                "items": mock_topic_cards,
                "total": len(mock_topic_cards),
                "page": page,
                "page_size": page_size,
                "total_pages": 1
            }
        
        # 模拟 VoteService.get_recall_vote_cards 方法
        def mock_get_recall_vote_cards(db, limit=10, user_id=None):
            return mock_vote_cards
        
        # 模拟 VoteService.get_vote_results 方法
        def mock_get_vote_results(self, vote_card_id, user_id=None):
            return {
                "has_voted": False,
                "user_votes": [],
                "options": []
            }
        
        # 模拟用户查询
        mock_user = Mock()
        mock_user.avatar_url = "http://example.com/avatar3.jpg"
        mock_user.nick_name = "用户3"
        mock_user.is_active = True
        mock_user.status = "active"
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        # 使用 monkeypatch 替换实际的服务方法
        import app.services.feed_service as feed_module
        monkeypatch.setattr(feed_module.TopicCardService, 'get_topic_cards', mock_get_topic_cards)
        monkeypatch.setattr(feed_module.VoteService, 'get_recall_vote_cards', mock_get_recall_vote_cards)
        monkeypatch.setattr(feed_module.VoteService, 'get_vote_results', mock_get_vote_results)
        
        # 调用方法
        result = feed_service.get_feed_item_cards(
            user_id=None,
            page=1,
            page_size=10
        )
        
        # 验证结果
        assert len(result["items"]) == 2
    
    def test_get_feed_item_cards_with_card_type_filter(self, feed_service, mock_db, mock_topic_card, monkeypatch):
        """测试按卡片类型筛选"""
        # 创建模拟话题卡片响应
        mock_topic_cards = [
            Mock(
                id="topic_1",
                title="测试话题1",
                description="测试话题描述1",
                category="测试分类",
                tags=["测试"],
                cover_image="http://example.com/cover1.jpg",
                visibility="public",
                is_anonymous=False,
                view_count=10,
                like_count=5,
                discussion_count=3,
                created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
                creator_nickname="用户1",
                creator_avatar="http://example.com/avatar1.jpg"
            )
        ]
        
        # 模拟 TopicCardService.get_topic_cards 方法
        def mock_get_topic_cards(db, user_id, page, page_size, category=None):
            return {
                "items": mock_topic_cards,
                "total": len(mock_topic_cards),
                "page": page,
                "page_size": page_size,
                "total_pages": 1
            }
        
        # 模拟 VoteService.get_recall_vote_cards 方法返回空结果（避免干扰测试）
        def mock_get_recall_vote_cards(db, limit=10, user_id=None):
            return []
        
        # 使用 monkeypatch 替换实际的服务方法
        import app.services.feed_service as feed_module
        monkeypatch.setattr(feed_module.TopicCardService, 'get_topic_cards', mock_get_topic_cards)
        monkeypatch.setattr(feed_module.VoteService, 'get_recall_vote_cards', mock_get_recall_vote_cards)
        
        # 调用方法（只获取话题卡片）
        result = feed_service.get_feed_item_cards(
            user_id="test_user_123",
            page=1,
            page_size=10,
            card_type="topic"
        )
        
        # 验证结果
        assert len(result["items"]) == 1
        assert result["items"][0]["type"] == "topic"
    
    def test_get_feed_item_cards_with_category_filter(self, feed_service, mock_db, mock_topic_card, monkeypatch):
        """测试按分类筛选"""
        # 创建模拟话题卡片响应
        mock_topic_cards = [
            Mock(
                id="topic_1",
                title="测试话题1",
                description="测试话题描述1",
                category="科技",
                tags=["测试"],
                cover_image="http://example.com/cover1.jpg",
                visibility="public",
                is_anonymous=False,
                view_count=10,
                like_count=5,
                discussion_count=3,
                created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
                creator_nickname="用户1",
                creator_avatar="http://example.com/avatar1.jpg"
            )
        ]
        
        # 模拟 TopicCardService.get_topic_cards 方法
        def mock_get_topic_cards(db, user_id, page, page_size, category=None):
            return {
                "items": mock_topic_cards,
                "total": len(mock_topic_cards),
                "page": page,
                "page_size": page_size,
                "total_pages": 1
            }
        
        # 模拟 VoteService.get_recall_vote_cards 方法返回空结果（避免干扰测试）
        def mock_get_recall_vote_cards(db, limit=10, user_id=None):
            return []
        
        # 使用 monkeypatch 替换实际的服务方法
        import app.services.feed_service as feed_module
        monkeypatch.setattr(feed_module.TopicCardService, 'get_topic_cards', mock_get_topic_cards)
        monkeypatch.setattr(feed_module.VoteService, 'get_recall_vote_cards', mock_get_recall_vote_cards)
        
        # 调用方法（按分类筛选）
        result = feed_service.get_feed_item_cards(
            user_id="test_user_123",
            page=1,
            page_size=10,
            category="科技"
        )
        
        # 验证结果
        assert len(result["items"]) == 1
        assert result["items"][0]["category"] == "科技"
    
    def test_get_feed_item_cards_empty_result(self, feed_service, mock_db, monkeypatch):
        """测试没有卡片的情况"""
        # 模拟 TopicCardService.get_topic_cards 方法返回空结果
        def mock_get_topic_cards(db, user_id, page, page_size, category=None):
            return {
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0
            }
        
        # 模拟 VoteService.get_recall_vote_cards 方法返回空结果
        def mock_get_recall_vote_cards(db, limit=10, user_id=None):
            return []
        
        # 使用 monkeypatch 替换实际的服务方法
        import app.services.feed_service as feed_module
        monkeypatch.setattr(feed_module.TopicCardService, 'get_topic_cards', mock_get_topic_cards)
        monkeypatch.setattr(feed_module.VoteService, 'get_recall_vote_cards', mock_get_recall_vote_cards)
        
        # 调用方法
        result = feed_service.get_feed_item_cards(
            user_id="test_user_123",
            page=1,
            page_size=10
        )
        
        # 验证结果
        assert len(result["items"]) == 0
        assert result["total"] == 0
        assert result["total_pages"] == 0
    
    def test_get_feed_item_cards_pagination(self, feed_service, mock_db, mock_topic_card, monkeypatch):
        """测试分页功能"""
        # 创建15个模拟话题卡片
        mock_topic_cards = []
        for i in range(15):
            mock_topic_cards.append(
                Mock(
                    id=f"topic_{i+1}",
                    title=f"测试话题{i+1}",
                    description=f"测试话题描述{i+1}",
                    category="测试分类",
                    tags=["测试"],
                    cover_image="http://example.com/cover1.jpg",
                    visibility="public",
                    is_anonymous=False,
                    view_count=10,
                    like_count=5,
                    discussion_count=3,
                    created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
                    creator_nickname="用户1",
                    creator_avatar="http://example.com/avatar1.jpg"
                )
            )
        
        # 模拟 TopicCardService.get_topic_cards 方法
        def mock_get_topic_cards(db, user_id, page, page_size, category=None):
            return {
                "items": mock_topic_cards,
                "total": len(mock_topic_cards),
                "page": page,
                "page_size": page_size,
                "total_pages": 2
            }
        
        # 模拟 VoteService.get_recall_vote_cards 方法返回空结果（避免干扰测试）
        def mock_get_recall_vote_cards(db, limit=10, user_id=None):
            return []
        
        # 使用 monkeypatch 替换实际的服务方法
        import app.services.feed_service as feed_module
        monkeypatch.setattr(feed_module.TopicCardService, 'get_topic_cards', mock_get_topic_cards)
        monkeypatch.setattr(feed_module.VoteService, 'get_recall_vote_cards', mock_get_recall_vote_cards)
        
        # 调用方法（第二页）
        result = feed_service.get_feed_item_cards(
            user_id="test_user_123",
            page=2,
            page_size=10
        )
        
        # 验证分页参数
        assert result["page"] == 2
        assert result["page_size"] == 10
        assert result["total"] == 15
        assert result["total_pages"] == 2