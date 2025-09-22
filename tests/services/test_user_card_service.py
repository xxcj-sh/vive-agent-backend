import pytest
import uuid
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.user_card_service import UserCardService
from app.models.user_card import CardCreate
from app.models.user_card_db import UserCard


class TestUserCardService:
    """用户卡片服务测试类"""
    
    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def sample_card_data(self):
        """示例卡片数据"""
        return CardCreate(
            role_type="participant",
            scene_type="dating",
            display_name="测试用户",
            avatar_url="https://example.com/avatar.jpg",
            bio="这是一个测试用户",
            trigger_and_output=[{"trigger": "打招呼", "output": "你好"}],
            profile_data={"age": 25, "gender": "male"},
            preferences={"interests": ["运动", "音乐"]},
            visibility="public",
            search_code="test123"
        )
    
    @pytest.fixture
    def sample_user_card(self):
        """示例用户卡片"""
        card = Mock(spec=UserCard)
        card.id = f"card_dating_participant_{uuid.uuid4().hex[:8]}"
        card.user_id = str(uuid.uuid4())
        card.role_type = "participant"
        card.scene_type = "dating"
        card.display_name = "测试用户"
        card.avatar_url = "https://example.com/avatar.jpg"
        card.bio = "这是一个测试用户"
        card.trigger_and_output = json.dumps([{"trigger": "打招呼", "output": "你好"}])
        card.profile_data = json.dumps({"age": 25, "gender": "male"})
        card.preferences = json.dumps({"interests": ["运动", "音乐"]})
        card.visibility = "public"
        card.search_code = "test123"
        card.is_active = 1
        card.is_deleted = 0
        card.created_at = datetime.now()
        card.updated_at = datetime.now()
        return card
    
    def test_create_card_success(self, mock_db, sample_card_data):
        """测试创建卡片成功"""
        # 设置模拟数据库行为
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # 创建卡片
        result = UserCardService.create_card(mock_db, "user_123", sample_card_data)
        
        # 验证数据库操作被调用
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        
        # 验证创建的卡片属性
        assert result.user_id == "user_123"
        assert result.role_type == "participant"
        assert result.scene_type == "dating"
        assert result.display_name == "测试用户"
    
    def test_create_card_with_json_serialization(self, mock_db):
        """测试创建卡片时JSON字段的序列化"""
        # 测试各种JSON数据类型
        card_data = CardCreate(
            role_type="organizer",
            scene_type="friends",
            display_name="JSON测试",
            bio="测试JSON序列化",
            trigger_and_output={"complex": {"nested": [1, 2, 3]}},
            profile_data={"nested": {"data": True}},
            preferences=[1, 2, 3, 4, 5]
        )
        
        result = UserCardService.create_card(mock_db, "user_456", card_data)
        
        # 验证JSON字段被正确序列化
        assert isinstance(result.trigger_and_output, str)
        assert isinstance(result.profile_data, str)
        assert isinstance(result.preferences, str)
        
        # 验证可以反序列化
        assert json.loads(result.trigger_and_output) == {"complex": {"nested": [1, 2, 3]}}
        assert json.loads(result.profile_data) == {"nested": {"data": True}}
        assert json.loads(result.preferences) == [1, 2, 3, 4, 5]
    
    def test_get_user_cards_success(self, mock_db, sample_user_card):
        """测试获取用户卡片成功"""
        # 设置查询结果
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [sample_user_card]
        
        mock_db.query.return_value = mock_query
        
        # 获取用户卡片
        result = UserCardService.get_user_cards(mock_db, "user_123")
        
        # 验证结果
        assert len(result) == 1
        assert result[0] == sample_user_card
        mock_db.query.assert_called_once_with(UserCard)
    
    def test_get_user_cards_active_only(self, mock_db, sample_user_card):
        """测试只获取活跃的用户卡片"""
        # 设置查询链
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query  # 第二次filter调用
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [sample_user_card]
        
        mock_db.query.return_value = mock_query
        
        # 获取活跃卡片
        result = UserCardService.get_user_cards(mock_db, "user_123", active_only=True)
        
        # 验证调用了两次filter（用户ID和活跃状态）
        assert mock_query.filter.call_count == 2
        assert len(result) == 1
    
    def test_get_card_by_id_success(self, mock_db, sample_user_card):
        """测试根据ID获取卡片成功"""
        # 设置查询结果
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_user_card
        
        mock_db.query.return_value = mock_query
        
        # 获取卡片
        result = UserCardService.get_card_by_id(mock_db, "card_123")
        
        # 验证结果
        assert result == sample_user_card
        mock_db.query.assert_called_once_with(UserCard)
    
    def test_get_card_by_id_not_found(self, mock_db):
        """测试根据ID获取卡片不存在"""
        # 设置查询返回None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        mock_db.query.return_value = mock_query
        
        # 获取不存在的卡片
        result = UserCardService.get_card_by_id(mock_db, "non_existent_card")
        
        # 验证返回None
        assert result is None
    
    def test_get_user_card_by_role_success(self, mock_db, sample_user_card):
        """测试获取用户在特定场景和角色下的卡片成功"""
        # 设置用户卡片查询
        mock_card_query = Mock()
        mock_card_query.filter.return_value = mock_card_query
        mock_card_query.filter.return_value = mock_card_query
        mock_card_query.first.return_value = sample_user_card
        
        # 设置用户查询
        from app.models.user import User
        mock_user = Mock()
        mock_user.nick_name = "测试昵称"
        mock_user.age = 25
        mock_user.gender = 1
        mock_user.phone = "13800138000"
        mock_user.occupation = "工程师"
        mock_user.location = "北京"
        mock_user.education = "本科"
        mock_user.interests = ["运动", "音乐"]
        
        mock_user_query = Mock()
        mock_user_query.filter.return_value = mock_user_query
        mock_user_query.first.return_value = mock_user
        
        # 设置数据库查询链
        mock_db.query.side_effect = [mock_card_query, mock_user_query]
        
        # 获取用户卡片
        result = UserCardService.get_user_card_by_role(
            mock_db, "user_123", "dating", "participant"
        )
        
        # 验证结果
        assert result is not None
        assert result["id"] == sample_user_card.id
        assert result["user_id"] == sample_user_card.user_id
        assert result["role_type"] == "participant"
        assert result["scene_type"] == "dating"
        assert result["username"] == "测试昵称"
        assert result["age"] == 25
        assert result["gender"] == 1
    
    def test_get_user_card_by_role_card_not_found(self, mock_db):
        """测试获取用户卡片不存在"""
        # 设置卡片查询返回None
        mock_card_query = Mock()
        mock_card_query.filter.return_value = mock_card_query
        mock_card_query.filter.return_value = mock_card_query
        mock_card_query.first.return_value = None
        
        mock_db.query.return_value = mock_card_query
        
        # 获取不存在的卡片
        result = UserCardService.get_user_card_by_role(
            mock_db, "user_123", "dating", "participant"
        )
        
        # 验证返回None
        assert result is None
    
    def test_get_cards_by_scene_success(self, mock_db, sample_user_card):
        """测试获取用户在特定场景下的所有卡片"""
        # 设置查询链
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [sample_user_card]
        
        mock_db.query.return_value = mock_query
        
        # 获取场景卡片
        result = UserCardService.get_cards_by_scene(mock_db, "user_123", "dating")
        
        # 验证结果
        assert len(result) == 1
        assert result[0] == sample_user_card
        # 验证调用了两次filter（用户ID和场景类型）
        assert mock_query.filter.call_count == 2
    
    def test_update_card_success(self, mock_db, sample_user_card):
        """测试更新卡片成功"""
        # 设置查询返回要更新的卡片
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_user_card
        
        mock_db.query.return_value = mock_query
        
        # 更新数据
        update_data = {
            "bio": "更新后的简介",
            "trigger_and_output": [{"trigger": "新触发", "output": "新输出"}],
            "visibility": "private"
        }
        
        # 更新卡片
        result = UserCardService.update_card(mock_db, "card_123", update_data)
        
        # 验证结果
        assert result == sample_user_card
        assert sample_user_card.bio == "更新后的简介"
        assert sample_user_card.visibility == "private"
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_update_card_json_fields(self, mock_db, sample_user_card):
        """测试更新卡片的JSON字段"""
        # 设置查询返回要更新的卡片
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_user_card
        
        mock_db.query.return_value = mock_query
        
        # 更新JSON数据
        new_trigger_data = [{"trigger": "测试", "output": "响应"}]
        new_profile_data = {"age": 30, "location": "上海"}
        new_preferences = {"interests": ["读书", "旅行"]}
        
        update_data = {
            "trigger_and_output": new_trigger_data,
            "profile_data": new_profile_data,
            "preferences": new_preferences
        }
        
        # 更新卡片
        result = UserCardService.update_card(mock_db, "card_123", update_data)
        
        # 验证JSON字段被序列化
        assert isinstance(sample_user_card.trigger_and_output, str)
        assert isinstance(sample_user_card.profile_data, str)
        assert isinstance(sample_user_card.preferences, str)
        
        # 验证可以反序列化
        assert json.loads(sample_user_card.trigger_and_output) == new_trigger_data
        assert json.loads(sample_user_card.profile_data) == new_profile_data
        assert json.loads(sample_user_card.preferences) == new_preferences
    
    def test_update_card_not_found(self, mock_db):
        """测试更新不存在的卡片"""
        # 设置查询返回None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        
        mock_db.query.return_value = mock_query
        
        # 尝试更新不存在的卡片
        result = UserCardService.update_card(mock_db, "non_existent_card", {"bio": "新简介"})
        
        # 验证返回None
        assert result is None
    
    def test_update_card_invalid_json_data(self, mock_db, sample_user_card):
        """测试更新卡片时处理无效的JSON数据"""
        # 设置查询返回要更新的卡片
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_user_card
        
        mock_db.query.return_value = mock_query
        
        # 使用非预期的数据类型
        update_data = {
            "trigger_and_output": "invalid_string",
            "profile_data": 123,  # 数字而不是字典
            "preferences": None
        }
        
        # 更新卡片
        result = UserCardService.update_card(mock_db, "card_123", update_data)
        
        # 验证结果被转换为JSON字符串
        assert isinstance(sample_user_card.trigger_and_output, str)
        assert isinstance(sample_user_card.profile_data, str)
        assert isinstance(sample_user_card.preferences, str)
        
        # 验证默认值被使用
        assert json.loads(sample_user_card.trigger_and_output) == []
        assert json.loads(sample_user_card.profile_data) == {}
        assert json.loads(sample_user_card.preferences) == {}
    
    def test_card_id_generation_format(self, mock_db, sample_card_data):
        """测试卡片ID生成格式"""
        # 设置模拟数据库行为
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        # 创建卡片
        result = UserCardService.create_card(mock_db, "user_123", sample_card_data)
        
        # 验证ID格式
        assert result.id.startswith(f"card_{sample_card_data.scene_type}_{sample_card_data.role_type}_")
        assert len(result.id.split("_")[-1]) == 8  # UUID部分长度
    
    @patch('app.services.user_card_service.datetime')
    def test_update_card_timestamp(self, mock_datetime, mock_db, sample_user_card):
        """测试更新卡片时时间戳更新"""
        # 设置模拟时间
        mock_now = datetime(2024, 1, 1, 12, 0, 0)
        mock_datetime.now.return_value = mock_now
        
        # 设置查询返回要更新的卡片
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_user_card
        
        mock_db.query.return_value = mock_query
        
        # 更新卡片
        UserCardService.update_card(mock_db, "card_123", {"bio": "更新时间"})
        
        # 验证时间戳被更新
        assert sample_user_card.updated_at == mock_now