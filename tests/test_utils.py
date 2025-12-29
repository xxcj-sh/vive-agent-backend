"""
测试工具模块
提供测试中常用的工具函数和辅助类
"""
from datetime import datetime, timezone
from unittest.mock import Mock
from typing import List, Optional, Dict, Any


def create_mock_user(user_id: str = "test_user_123", 
                    nick_name: str = "测试用户",
                    avatar_url: str = "http://example.com/avatar.jpg",
                    is_public: bool = True) -> Mock:
    """
    创建模拟用户对象
    
    Args:
        user_id: 用户ID
        nick_name: 用户昵称
        avatar_url: 头像URL
        is_public: 是否公开
    
    Returns:
        Mock: 模拟用户对象
    """
    user = Mock()
    user.id = user_id
    user.nick_name = nick_name
    user.avatar_url = avatar_url
    user.is_public = is_public
    user.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    user.updated_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return user


def create_mock_topic_card(card_id: str = "test_topic_123",
                          user_id: str = "test_user_123",
                          title: str = "测试话题",
                          description: str = "这是一个测试话题描述",
                          cover_image: str = "http://example.com/cover.jpg",
                          category: str = "测试分类",
                          tags: Optional[List[str]] = None,
                          visibility: str = "public",
                          is_anonymous: bool = False) -> Mock:
    """
    创建模拟话题卡片对象
    
    Args:
        card_id: 卡片ID
        user_id: 用户ID
        title: 话题标题
        description: 话题描述
        cover_image: 封面图片URL
        category: 分类
        tags: 标签列表
        visibility: 可见性
        is_anonymous: 是否匿名
    
    Returns:
        Mock: 模拟话题卡片对象
    """
    if tags is None:
        tags = ["测试", "话题"]
    
    card = Mock()
    card.id = card_id
    card.user_id = user_id
    card.title = title
    card.description = description
    card.cover_image = cover_image
    card.category = category
    card.tags = tags
    card.visibility = visibility
    card.is_anonymous = is_anonymous
    card.view_count = 10
    card.like_count = 5
    card.comment_count = 3
    card.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    card.updated_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return card


def create_mock_vote_card(card_id: str = "test_vote_123",
                         user_id: str = "test_user_123",
                         title: str = "测试投票",
                         vote_type: str = "single",
                         is_anonymous: bool = False,
                         is_realtime_result: bool = True,
                         is_active: bool = True) -> Mock:
    """
    创建模拟投票卡片对象
    
    Args:
        card_id: 卡片ID
        user_id: 用户ID
        title: 投票标题
        vote_type: 投票类型 (single/multiple)
        is_anonymous: 是否匿名
        is_realtime_result: 是否实时显示结果
        is_active: 是否激活
    
    Returns:
        Mock: 模拟投票卡片对象
    """
    card = Mock()
    card.id = card_id
    card.user_id = user_id
    card.title = title
    card.vote_type = vote_type
    card.is_anonymous = is_anonymous
    card.is_realtime_result = is_realtime_result
    card.is_active = is_active
    card.is_deleted = False
    card.total_votes = 15
    card.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    card.updated_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return card


def create_mock_user_card(card_id: str = "test_user_card_123",
                         user_id: str = "test_user_123",
                         nick_name: str = "测试用户",
                         avatar_url: str = "http://example.com/avatar.jpg",
                         bio: str = "这是一个测试用户的简介",
                         is_public: bool = True) -> Mock:
    """
    创建模拟用户卡片对象
    
    Args:
        card_id: 卡片ID
        user_id: 用户ID
        nick_name: 用户昵称
        avatar_url: 头像URL
        bio: 个人简介
        is_public: 是否公开
    
    Returns:
        Mock: 模拟用户卡片对象
    """
    card = Mock()
    card.id = card_id
    card.user_id = user_id
    card.nick_name = nick_name
    card.avatar_url = avatar_url
    card.bio = bio
    card.is_public = is_public
    card.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    card.updated_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return card


def setup_mock_query(mock_db, return_values: List[Any], total_count: int = None):
    """
    设置模拟数据库查询
    
    Args:
        mock_db: 模拟数据库会话
        return_values: 查询返回值列表
        total_count: 总记录数（用于分页）
    
    Returns:
        Mock: 配置好的模拟查询对象
    """
    mock_query = Mock()
    mock_query.filter.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    mock_query.offset.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.all.return_value = return_values
    
    if total_count is not None:
        mock_query.count.return_value = total_count
    
    mock_db.query.return_value = mock_query
    return mock_query


def assert_pagination_result(result: Dict[str, Any], 
                           expected_page: int,
                           expected_page_size: int,
                           expected_total: int,
                           expected_total_pages: int):
    """
    验证分页结果
    
    Args:
        result: 测试结果字典
        expected_page: 期望的页码
        expected_page_size: 期望的每页大小
        expected_total: 期望的总记录数
        expected_total_pages: 期望的总页数
    """
    assert "pagination" in result
    pagination = result["pagination"]
    
    assert pagination["page"] == expected_page
    assert pagination["page_size"] == expected_page_size
    assert pagination["total"] == expected_total
    assert pagination["total_pages"] == expected_total_pages


def assert_card_structure(card: Dict[str, Any], expected_type: str):
    """
    验证卡片结构
    
    Args:
        card: 卡片字典
        expected_type: 期望的卡片类型
    """
    assert "type" in card
    assert card["type"] == expected_type
    
    # 验证通用字段
    assert "id" in card
    assert "created_at" in card
    assert "updated_at" in card
    
    # 根据类型验证特定字段
    if expected_type == "topic_card":
        assert "title" in card
        assert "description" in card
        assert "category" in card
        assert "tags" in card
    elif expected_type == "vote_card":
        assert "title" in card
        assert "vote_type" in card
        assert "total_votes" in card
    elif expected_type == "user_card":
        assert "user_id" in card
        assert "nick_name" in card
        assert "avatar_url" in card


class MockQueryBuilder:
    """模拟查询构建器，用于简化复杂的查询模拟"""
    
    def __init__(self, mock_db):
        self.mock_db = mock_db
        self.query_chain = []
        self.return_values = []
        self.total_count = 0
    
    def filter(self, *conditions):
        """添加过滤条件"""
        self.query_chain.append(("filter", conditions))
        return self
    
    def order_by(self, *conditions):
        """添加排序条件"""
        self.query_chain.append(("order_by", conditions))
        return self
    
    def offset(self, offset_value):
        """添加偏移量"""
        self.query_chain.append(("offset", offset_value))
        return self
    
    def limit(self, limit_value):
        """添加限制数量"""
        self.query_chain.append(("limit", limit_value))
        return self
    
    def with_return_values(self, values: List[Any]):
        """设置返回值"""
        self.return_values = values
        return self
    
    def with_total_count(self, count: int):
        """设置总记录数"""
        self.total_count = count
        return self
    
    def build(self):
        """构建模拟查询"""
        mock_query = Mock()
        
        # 设置链式调用
        current_mock = mock_query
        for method_name, _ in self.query_chain:
            getattr(current_mock, method_name).return_value = current_mock
        
        # 设置最终返回值
        current_mock.all.return_value = self.return_values
        current_mock.count.return_value = self.total_count
        
        # 设置到数据库会话
        self.mock_db.query.return_value = mock_query
        
        return mock_query