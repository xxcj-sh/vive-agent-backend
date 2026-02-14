"""
话题卡片服务测试 - 匿名功能测试用例
"""
import unittest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from datetime import datetime
from app.services.topic_card_service import TopicCardService
from app.models.topic_card import TopicCardCreate, TopicCardResponse
from app.models.user import User


class TestTopicCardServiceAnonymous(unittest.TestCase):
    """测试话题卡片服务的匿名功能"""

    def setUp(self):
        """设置测试环境"""
        self.db = Mock(spec=Session)
        self.user_id = "test_user_id"
        
        # 创建模拟用户
        self.mock_user = Mock(spec=User)
        self.mock_user.id = self.user_id
        self.mock_user.nick_name = "测试用户"
        self.mock_user.avatar_url = "http://example.com/avatar.jpg"
        
        # 设置用户查询结果
        self.db.query.return_value.filter.return_value.first.return_value = self.mock_user
        
        # 基础话题数据
        self.base_topic_data = TopicCardCreate(
            title="测试话题",
            description="这是一个测试话题描述",
            discussion_goal="测试讨论目标",
            category="测试",
            tags=["测试", "话题"],
            cover_image="http://example.com/cover.jpg",
            visibility="public"
        )

    def test_create_anonymous_topic_card(self):
        """测试创建匿名话题卡片"""
        # 创建匿名话题数据
        anonymous_topic_data = self.base_topic_data.copy()
        anonymous_topic_data.is_anonymous = True
        
        # 创建模拟的话题卡片对象
        mock_topic_card = Mock()
        mock_topic_card.id = "test_topic_id"
        mock_topic_card.user_id = self.user_id
        mock_topic_card.title = anonymous_topic_data.title
        mock_topic_card.description = anonymous_topic_data.description
        mock_topic_card.discussion_goal = anonymous_topic_data.discussion_goal
        mock_topic_card.category = anonymous_topic_data.category
        mock_topic_card.tags = anonymous_topic_data.tags
        mock_topic_card.cover_image = anonymous_topic_data.cover_image
        mock_topic_card.visibility = anonymous_topic_data.visibility
        mock_topic_card.is_active = 1
        mock_topic_card.is_deleted = 0
        mock_topic_card.is_anonymous = 1  # 匿名标识为1
        mock_topic_card.view_count = 0
        mock_topic_card.like_count = 0
        mock_topic_card.discussion_count = 0
        mock_topic_card.created_at = datetime.utcnow()
        mock_topic_card.updated_at = datetime.utcnow()
        
        # 模拟add, commit, refresh操作
        def side_effect_add(instance):
            pass
        
        def side_effect_refresh(instance):
            pass
        
        self.db.add.side_effect = side_effect_add
        self.db.commit.return_value = None
        self.db.refresh.side_effect = side_effect_refresh
        
        # 模拟查询结果
        self.db.query.return_value.filter.return_value.first.return_value = mock_topic_card
        
        # 为了通过Pydantic验证，我们需要确保用户对象返回的是真实字符串
        def get_user_side_effect(cls):
            query_mock = Mock()
            if cls == User:
                filter_mock = Mock()
                user_mock = Mock(spec=User)
                user_mock.nick_name = "测试用户"
                user_mock.avatar_url = "http://example.com/avatar.jpg"
                filter_mock.first.return_value = user_mock
                query_mock.filter.return_value = filter_mock
            return query_mock
        
        self.db.query.side_effect = get_user_side_effect
        
        with patch('app.services.topic_card_service.TopicCard', return_value=mock_topic_card):
            # 调用创建话题卡片方法
            result = TopicCardService.create_topic_card(self.db, self.user_id, anonymous_topic_data)
            
            # 验证结果
            self.assertIsInstance(result, TopicCardResponse)
            self.assertEqual(result.is_anonymous, 1)
            self.assertIsNone(result.creator_nickname)  # 匿名话题不应返回创建者昵称
            self.assertIsNone(result.creator_avatar)  # 匿名话题不应返回创建者头像

    def test_create_non_anonymous_topic_card(self):
        """测试创建非匿名话题卡片"""
        # 创建非匿名话题数据
        non_anonymous_topic_data = self.base_topic_data.copy()
        non_anonymous_topic_data.is_anonymous = False
        
        # 创建模拟的话题卡片对象
        mock_topic_card = Mock()
        mock_topic_card.id = "test_topic_id"
        mock_topic_card.user_id = self.user_id
        mock_topic_card.title = non_anonymous_topic_data.title
        mock_topic_card.description = non_anonymous_topic_data.description
        mock_topic_card.discussion_goal = non_anonymous_topic_data.discussion_goal
        mock_topic_card.category = non_anonymous_topic_data.category
        mock_topic_card.tags = non_anonymous_topic_data.tags
        mock_topic_card.cover_image = non_anonymous_topic_data.cover_image
        mock_topic_card.visibility = non_anonymous_topic_data.visibility
        mock_topic_card.is_active = 1
        mock_topic_card.is_deleted = 0
        mock_topic_card.is_anonymous = 0  # 非匿名标识为0
        mock_topic_card.view_count = 0
        mock_topic_card.like_count = 0
        mock_topic_card.discussion_count = 0
        mock_topic_card.created_at = datetime.utcnow()
        mock_topic_card.updated_at = datetime.utcnow()
        
        # 模拟add, commit, refresh操作
        def side_effect_add(instance):
            pass
        
        def side_effect_refresh(instance):
            pass
        
        self.db.add.side_effect = side_effect_add
        self.db.commit.return_value = None
        self.db.refresh.side_effect = side_effect_refresh
        
        # 模拟查询结果
        self.db.query.return_value.filter.return_value.first.return_value = mock_topic_card
        
        # 为了通过Pydantic验证，我们需要确保用户对象返回的是真实字符串
        def get_user_side_effect(cls):
            query_mock = Mock()
            if cls == User:
                filter_mock = Mock()
                user_mock = Mock(spec=User)
                user_mock.nick_name = "测试用户"
                user_mock.avatar_url = "http://example.com/avatar.jpg"
                filter_mock.first.return_value = user_mock
                query_mock.filter.return_value = filter_mock
            return query_mock
        
        self.db.query.side_effect = get_user_side_effect
        
        with patch('app.services.topic_card_service.TopicCard', return_value=mock_topic_card):
            # 调用创建话题卡片方法
            result = TopicCardService.create_topic_card(self.db, self.user_id, non_anonymous_topic_data)
            
            # 验证结果
            self.assertIsInstance(result, TopicCardResponse)
            self.assertEqual(result.is_anonymous, 0)
            # 非匿名话题应该返回创建者信息
            self.assertEqual(result.creator_nickname, "测试用户")
            self.assertEqual(result.creator_avatar, "http://example.com/avatar.jpg")

    def test_get_anonymous_topic_card_detail(self):
        """测试获取匿名话题卡片详情"""
        # 创建模拟的话题卡片对象
        mock_topic_card = Mock()
        mock_topic_card.id = "test_topic_id"
        mock_topic_card.user_id = self.user_id
        mock_topic_card.title = "匿名话题"
        mock_topic_card.description = "这是一个匿名话题"
        mock_topic_card.discussion_goal = "讨论目标"
        mock_topic_card.category = "测试"
        mock_topic_card.tags = ["测试", "匿名"]
        mock_topic_card.cover_image = "http://example.com/cover.jpg"
        mock_topic_card.visibility = "public"
        mock_topic_card.is_active = 1
        mock_topic_card.is_deleted = 0
        mock_topic_card.is_anonymous = 1  # 匿名标识为1
        mock_topic_card.view_count = 5
        mock_topic_card.like_count = 2
        mock_topic_card.discussion_count = 1
        mock_topic_card.created_at = datetime.utcnow()
        mock_topic_card.updated_at = datetime.utcnow()
        
        # 模拟查询结果 - 返回话题卡片和用户元组
        # 为了通过Pydantic验证，我们需要确保返回的是真实字符串而不是Mock对象
        real_user = User()
        real_user.id = self.user_id
        real_user.nick_name = "测试用户"
        real_user.avatar_url = "http://example.com/avatar.jpg"
        self.db.query.return_value.join.return_value.filter.return_value.first.return_value = (mock_topic_card, real_user)
        
        # 调用获取话题卡片详情方法
        result = TopicCardService.get_topic_card_detail(self.db, "test_topic_id", "other_user_id")
        
        # 验证结果
        self.assertIsInstance(result, TopicCardResponse)
        self.assertEqual(result.is_anonymous, 1)
        self.assertIsNone(result.creator_nickname)  # 匿名话题不应返回创建者昵称
        self.assertIsNone(result.creator_avatar)  # 匿名话题不应返回创建者头像

    def test_get_topic_cards_with_anonymous(self):
        """测试获取包含匿名话题的话题列表"""
        # 创建模拟的匿名话题卡片对象
        mock_anonymous_topic = Mock()
        mock_anonymous_topic.id = "anonymous_topic_id"
        mock_anonymous_topic.user_id = self.user_id
        mock_anonymous_topic.title = "匿名话题"
        mock_anonymous_topic.description = "这是一个匿名话题"
        mock_anonymous_topic.discussion_goal = "讨论目标"
        mock_anonymous_topic.category = "测试"
        mock_anonymous_topic.tags = ["测试", "匿名"]
        mock_anonymous_topic.cover_image = "http://example.com/cover1.jpg"
        mock_anonymous_topic.visibility = "public"
        mock_anonymous_topic.is_active = 1
        mock_anonymous_topic.is_deleted = 0
        mock_anonymous_topic.is_anonymous = 1  # 匿名标识为1
        mock_anonymous_topic.view_count = 5
        mock_anonymous_topic.like_count = 2
        mock_anonymous_topic.discussion_count = 1
        mock_anonymous_topic.created_at = datetime.utcnow()
        mock_anonymous_topic.updated_at = datetime.utcnow()
        
        # 创建模拟的非匿名话题卡片对象
        mock_non_anonymous_topic = Mock()
        mock_non_anonymous_topic.id = "non_anonymous_topic_id"
        mock_non_anonymous_topic.user_id = self.user_id
        mock_non_anonymous_topic.title = "非匿名话题"
        mock_non_anonymous_topic.description = "这是一个非匿名话题"
        mock_non_anonymous_topic.discussion_goal = "讨论目标"
        mock_non_anonymous_topic.category = "测试"
        mock_non_anonymous_topic.tags = ["测试", "非匿名"]
        mock_non_anonymous_topic.cover_image = "http://example.com/cover2.jpg"
        mock_non_anonymous_topic.visibility = "public"
        mock_non_anonymous_topic.is_active = 1
        mock_non_anonymous_topic.is_deleted = 0
        mock_non_anonymous_topic.is_anonymous = 0  # 非匿名标识为0
        mock_non_anonymous_topic.view_count = 10
        mock_non_anonymous_topic.like_count = 5
        mock_non_anonymous_topic.discussion_count = 3
        mock_non_anonymous_topic.created_at = datetime.utcnow()
        mock_non_anonymous_topic.updated_at = datetime.utcnow()
        
        # 模拟查询结果 - 返回多个(话题卡片, 用户)元组
        # 为了通过Pydantic验证，我们需要确保返回的是真实字符串而不是Mock对象
        self.db.query.return_value.join.return_value.filter.return_value.count.return_value = 2
        real_user = User()
        real_user.id = self.user_id
        real_user.nick_name = "测试用户"
        real_user.avatar_url = "http://example.com/avatar.jpg"
        self.db.query.return_value.join.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [
            (mock_anonymous_topic, real_user),
            (mock_non_anonymous_topic, real_user)
        ]
        
        # 调用获取话题卡片列表方法
        result = TopicCardService.get_topic_cards(self.db)
        
        # 验证结果
        self.assertIn('items', result)
        self.assertEqual(len(result['items']), 2)
        
        # 验证匿名话题
        self.assertEqual(result['items'][0].is_anonymous, 1)
        self.assertIsNone(result['items'][0].creator_nickname)
        self.assertIsNone(result['items'][0].creator_avatar)
        
        # 验证非匿名话题
        self.assertEqual(result['items'][1].is_anonymous, 0)
        self.assertEqual(result['items'][1].creator_nickname, self.mock_user.nick_name)
        self.assertEqual(result['items'][1].creator_avatar, self.mock_user.avatar_url)


if __name__ == '__main__':
    unittest.main()
