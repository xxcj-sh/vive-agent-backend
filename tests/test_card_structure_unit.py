"""
单元测试：验证卡片数据结构统一化
测试MatchCardStrategy和MatchService返回的卡片数据结构一致性
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from app.services.match_service.card_strategy import MatchCardStrategy
from app.services.match_service import MatchService
from app.models.user import User


class TestCardStructureUnit:
    """单元测试：卡片数据结构统一化"""

    @pytest.fixture
    def mock_user(self):
        """模拟用户对象"""
        user = MagicMock(spec=User)
        user.id = "test_user_001"
        user.username = "test_user"
        user.nick_name = "测试用户"
        user.age = 28
        user.occupation = "工程师"
        user.location = "北京"
        user.bio = "测试简介"
        user.interests = ["编程", "阅读"]
        user.gender = "male"
        user.education = "本科"
        user.height = 175
        user.relationship_status = "单身"
        user.dating_purpose = "交友"
        user.created_at = datetime.now()
        return user

    @pytest.fixture
    def mock_user_card(self):
        """模拟用户卡片数据"""
        card = MagicMock()
        card.user_id = "test_user_001"
        card.scene_type = "housing"
        card.role_type = "seeker"
        card.title = "温馨公寓"
        card.price = 2500
        card.location = "朝阳区"
        card.description = "精装修公寓"
        card.house_type = "公寓"
        card.area = 80
        card.available_from = "2024-02-01"
        card.available_to = "2024-12-31"
        card.activity_time = "2024-02-03 09:00"
        card.activity_type = "户外运动"
        return card

    def test_housing_card_structure(self, mock_user, mock_user_card):
        """测试房源卡片数据结构"""
        strategy = MatchCardStrategy()
        
        with patch('app.services.match_card_strategy.get_db') as mock_db:
            # 模拟数据库查询
            mock_session = MagicMock()
            mock_db.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = mock_user_card
            
            # 调用转换方法
            result = strategy._convert_user_to_housing_card_for_seeker(mock_user)
            
            # 验证统一的数据结构
            expected_fields = [
                "id", "userId", "sceneType", "userRole", "name", "avatar",
                "age", "occupation", "location", "bio", "interests",
                "houseTitle", "housePrice", "houseArea", "houseLocation", "houseImages",
                "orientation", "floor", "hasElevator", "decoration", "deposit", "community",
                "createdAt", "matchScore", "recommendReason"
            ]
            
            for field in expected_fields:
                assert field in result, f"房源卡片缺少字段: {field}"
            
            # 验证字段值
            assert result["sceneType"] == "housing"
            assert result["userRole"] == "seeker"
            assert result["name"] == "测试用户"
            assert "温馨公寓" in result["houseTitle"] or "未知小区" in result["houseTitle"]
            assert result["housePrice"] == 5000

    def test_dating_card_structure(self, mock_user, mock_user_card):
        """测试交友卡片数据结构"""
        strategy = MatchCardStrategy()
        
        with patch('app.services.match_card_strategy.get_db') as mock_db:
            # 模拟数据库查询
            mock_session = MagicMock()
            mock_db.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = mock_user_card
            
            # 调用转换方法
            result = strategy._convert_user_to_dating_card(mock_user)
            
            # 验证统一的数据结构
            expected_fields = [
                "id", "userId", "sceneType", "userRole", "name", "avatar",
                "age", "occupation", "location", "bio", "interests",
                "education", "height", "income", "lookingFor",
                "createdAt", "matchScore", "recommendReason"
            ]
            
            for field in expected_fields:
                assert field in result, f"交友卡片缺少字段: {field}"
            
            # 验证字段值
            assert result["sceneType"] == "dating"
            assert result["userRole"] == "user"
            assert result["name"] == "测试用户"

    def test_activity_card_structure(self, mock_user, mock_user_card):
        """测试活动卡片数据结构"""
        strategy = MatchCardStrategy()
        
        with patch('app.services.match_card_strategy.get_db') as mock_db:
            # 模拟数据库查询
            mock_session = MagicMock()
            mock_db.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = mock_user_card
            
            # 调用转换方法
            result = strategy._convert_user_to_activity_card_for_seeker(mock_user)
            
            # 验证统一的数据结构
            expected_fields = [
                "id", "userId", "sceneType", "userRole", "name", "avatar",
                "age", "occupation", "location", "bio", "interests",
                "activityName", "activityType", "activityTime", "activityLocation", "activityPrice",
                "activityDuration", "activityMaxParticipants", "activityDifficulty",
                "createdAt", "matchScore", "recommendReason"
            ]
            
            for field in expected_fields:
                assert field in result, f"活动卡片缺少字段: {field}"
            
            # 验证字段值
            assert result["sceneType"] == "activity"
            assert result["userRole"] == "seeker"
            assert result["name"] == "测试用户"

    def test_tenant_card_structure(self, mock_user, mock_user_card):
        """测试租客卡片数据结构"""
        strategy = MatchCardStrategy()
        
        with patch('app.services.match_card_strategy.get_db') as mock_db:
            # 模拟数据库查询
            mock_session = MagicMock()
            mock_db.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = mock_user_card
            
            # 调用转换方法
            result = strategy._convert_user_to_tenant_card_for_provider(mock_user)
            
            # 验证统一的数据结构
            expected_fields = [
                "id", "userId", "sceneType", "userRole", "name", "avatar",
                "age", "occupation", "location", "bio", "interests",
                "budget", "budgetRange", "leaseDuration", "moveInDate", "availability",
                "createdAt", "matchScore", "recommendReason"
            ]
            
            for field in expected_fields:
                assert field in result, f"租客卡片缺少字段: {field}"
            
            # 验证字段值
            assert result["sceneType"] == "housing"
            assert result["userRole"] == "provider"
            assert result["name"] == "测试用户"

    def test_participant_card_structure(self, mock_user, mock_user_card):
        """测试参与者卡片数据结构"""
        strategy = MatchCardStrategy()
        
        with patch('app.services.match_card_strategy.get_db') as mock_db:
            # 模拟数据库查询
            mock_session = MagicMock()
            mock_db.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = mock_user_card
            
            # 调用转换方法
            result = strategy._convert_user_to_participant_card_for_organizer(mock_user)
            
            # 验证统一的数据结构
            expected_fields = [
                "id", "userId", "sceneType", "userRole", "name", "avatar",
                "age", "occupation", "location", "bio", "interests",
                "preferredActivity", "budgetRange", "preferredTime", "preferredLocation",
                "createdAt", "matchScore", "recommendReason"
            ]
            
            for field in expected_fields:
                assert field in result, f"参与者卡片缺少字段: {field}"
            
            # 验证字段值
            assert result["sceneType"] == "activity"
            assert result["userRole"] == "provider"
            assert result["name"] == "测试用户"

    def test_field_consistency(self):
        """测试字段命名一致性"""
        
        # 定义统一的字段映射
        field_mapping = {
            "userId": "userId",  # 统一使用userId而不是id
            "sceneType": "sceneType",  # 统一使用sceneType而不是matchType
            "userRole": "userRole",  # 统一使用userRole而不是userRole
            "name": "name",
            "avatar": "avatar",
            "age": "age",
            "occupation": "occupation",
            "location": "location",
            "bio": "bio",
            "interests": "interests",
            "createdAt": "createdAt",
            "matchScore": "matchScore"
        }
        
        # 验证所有转换方法都使用统一的字段命名
        strategy = MatchCardStrategy()
        
        # 检查每个转换方法的返回字段
        with patch('app.services.match_card_strategy.get_db') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = MagicMock()
            
            # 创建模拟用户
            user = MagicMock()
            user.id = "test_user"
            user.nick_name = "测试用户"
            user.age = 25
            user.occupation = "测试职业"
            user.location = "测试城市"
            user.bio = "测试简介"
            user.created_at = datetime.now()
            
            # 测试每个转换方法
            methods = [
                strategy._convert_user_to_housing_card_for_seeker,
                strategy._convert_user_to_tenant_card_for_provider,
                strategy._convert_user_to_dating_card,
                strategy._convert_user_to_activity_card_for_seeker,
                strategy._convert_user_to_participant_card_for_organizer
            ]
            
            for method in methods:
                result = method(user)
                
                # 验证基础字段存在且命名一致
                for unified_name in field_mapping.values():
                    assert unified_name in result, f"方法 {method.__name__} 缺少统一字段: {unified_name}"

    def test_flat_structure(self):
        """测试扁平化数据结构"""
        
        strategy = MatchCardStrategy()
        
        with patch('app.services.match_card_strategy.get_db') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = MagicMock()
            
            # 创建模拟用户
            user = MagicMock()
            user.id = "test_user"
            user.nick_name = "测试用户"
            user.age = 25
            user.occupation = "测试职业"
            user.location = "测试城市"
            user.bio = "测试简介"
            user.created_at = datetime.now()
            
            # 测试所有转换方法返回的都是扁平结构
            methods = [
                strategy._convert_user_to_housing_card_for_seeker,
                strategy._convert_user_to_tenant_card_for_provider,
                strategy._convert_user_to_dating_card,
                strategy._convert_user_to_activity_card_for_seeker,
                strategy._convert_user_to_participant_card_for_organizer
            ]
            
            for method in methods:
                result = method(user)
                
                # 验证没有嵌套对象
                for key, value in result.items():
                    if isinstance(value, dict):
                        pytest.fail(f"方法 {method.__name__} 返回了嵌套对象: {key}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])