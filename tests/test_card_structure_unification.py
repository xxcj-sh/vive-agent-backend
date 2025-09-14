"""
测试卡片数据结构统一化
验证get_match_cards和get_match_recommendation_cards返回的卡片数据结构一致性
"""

import pytest
import json
from datetime import datetime
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.models.user_card_db import UserCard as UserCardModel
from app.services.match_service.card_strategy import MatchCardStrategy


class TestCardStructureUnification:
    """测试卡片数据结构统一化"""

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)

    @pytest.fixture
    def mock_current_user(self):
        """模拟当前用户"""
        return {
            "id": "test_user_001",
            "username": "test_user",
            "nick_name": "测试用户"
        }

    @pytest.fixture
    def mock_db_users(self):
        """模拟数据库用户"""
        users = []
        for i in range(1, 6):
            user = MagicMock()
            user.id = f"user_{i:03d}"
            user.username = f"user_{i}"
            user.nick_name = f"用户{i}"
            user.age = 25 + i
            user.occupation = f"职业{i}"
            user.location = f"城市{i}"
            user.bio = f"这是用户{i}的个人简介"
            user.interests = ["运动", "阅读", "音乐"]
            user.gender = "male" if i % 2 == 0 else "female"
            user.education = "本科"
            user.height = 170 + i
            user.relationship_status = "单身"
            user.dating_purpose = "交友"
            user.created_at = datetime.now()
            users.append(user)
        return users

    @pytest.fixture
    def mock_user_cards(self):
        """模拟用户卡片数据"""
        cards = []
        for i in range(1, 6):
            card = MagicMock()
            card.user_id = f"user_{i:03d}"
            card.scene_type = "housing" if i % 3 == 0 else ("dating" if i % 3 == 1 else "activity")
            card.role_type = "seeker" if i % 2 == 0 else "provider"
            card.title = f"{card.scene_type}卡片{i}"
            card.price = 1000 + i * 100
            card.location = f"城市{i}"
            card.description = f"这是{card.scene_type}卡片的描述"
            card.house_type = "公寓"
            card.area = 80 + i * 10
            card.available_from = "2024-01-01"
            card.available_to = "2024-12-31"
            card.activity_time = "2024-02-01 14:00"
            card.activity_type = "户外运动"
            cards.append(card)
        return cards

    def test_get_match_cards_structure(self, client, mock_current_user, mock_db_users, mock_user_cards):
        """测试get_match_cards返回的卡片数据结构"""
        
        with patch('app.routers.matches.get_current_user', return_value=mock_current_user):
            with patch('app.routers.matches.get_db') as mock_db:
                # 模拟数据库会话
                db_session = MagicMock()
                mock_db.return_value = db_session
                
                # 模拟MatchCardStrategy.get_match_cards返回数据
                mock_strategy = MagicMock()
                mock_strategy.get_match_cards.return_value = {
                    "total": 5,
                    "list": [
                        {
                            "id": f"card_{i:03d}",
                            "userId": user.id,
                            "sceneType": card.scene_type,
                            "userRole": card.role_type,
                            "name": user.nick_name,
                            "avatar": "",
                            "age": user.age,
                            "occupation": user.occupation,
                            "location": user.location,
                            "bio": user.bio,
                            "interests": user.interests,
                            "createdAt": user.created_at.isoformat(),
                            "matchScore": 75 + i,
                            # 场景特定字段
                            "houseTitle": card.title if card.scene_type == "housing" else None,
                            "housePrice": card.price if card.scene_type == "housing" else None,
                            "houseLocation": card.location if card.scene_type == "housing" else None,
                            "houseType": card.house_type if card.scene_type == "housing" else None,
                            "houseArea": card.area if card.scene_type == "housing" else None,
                            "gender": user.gender if card.scene_type == "dating" else None,
                            "education": user.education if card.scene_type == "dating" else None,
                            "height": user.height if card.scene_type == "dating" else None,
                            "activityName": card.title if card.scene_type == "activity" else None,
                            "activityTime": card.activity_time if card.scene_type == "activity" else None,
                            "activityLocation": card.location if card.scene_type == "activity" else None,
                            "activityPrice": card.price if card.scene_type == "activity" else None
                        }
                        for i, (user, card) in enumerate(zip(mock_db_users, mock_user_cards), 1)
                    ],
                    "page": 1,
                    "pageSize": 10,
                    "strategy": "housing_strategy"
                }
                
                with patch('app.services.match_card_strategy.MatchCardStrategy', return_value=mock_strategy):
                    # 调用get_match_cards接口
                    response = client.get("/api/v1/matches/cards", params={
                        "sceneType": "housing",
                        "userRole": "seeker",
                        "page": 1,
                        "pageSize": 10
                    })
                    
                    assert response.status_code == 200
                    data = response.json()
                    
                    # 验证数据结构
                    assert "data" in data
                    assert "cards" in data["data"]
                    assert "pagination" in data["data"]
                    
                    cards = data["data"]["cards"]
                    assert len(cards) == 5
                    
                    # 验证统一的数据结构
                    for card in cards:
                        self._validate_unified_card_structure(card)

    def test_get_match_recommendation_cards_structure(self, client, mock_current_user, mock_db_users, mock_user_cards):
        """测试get_match_recommendation_cards返回的卡片数据结构"""
        
        with patch('app.routers.matches.get_current_user', return_value=mock_current_user):
            with patch('app.routers.matches.get_db') as mock_db:
                # 模拟数据库会话
                db_session = MagicMock()
                mock_db.return_value = db_session
                
                # 模拟没有AI推荐，使用普通推荐
                db_session.query.return_value.filter.return_value.count.return_value = 0
                
                # 模拟MatchService.get_recommendation_cards返回数据
                mock_match_service = MagicMock()
                mock_match_service.get_recommendation_cards.return_value = {
                    "total": 5,
                    "cards": [
                        {
                            "id": f"card_{i:03d}",
                            "userId": user.id,
                            "sceneType": card.scene_type,
                            "userRole": card.role_type,
                            "name": user.nick_name,
                            "avatar": "",
                            "age": user.age,
                            "occupation": user.occupation,
                            "location": user.location,
                            "bio": user.bio,
                            "interests": user.interests,
                            "createdAt": user.created_at.isoformat(),
                            "matchScore": 75 + i,
                            # 场景特定字段
                            "houseTitle": card.title if card.scene_type == "housing" else None,
                            "housePrice": card.price if card.scene_type == "housing" else None,
                            "houseLocation": card.location if card.scene_type == "housing" else None,
                            "houseType": card.house_type if card.scene_type == "housing" else None,
                            "houseArea": card.area if card.scene_type == "housing" else None,
                            "gender": user.gender if card.scene_type == "dating" else None,
                            "education": user.education if card.scene_type == "dating" else None,
                            "height": user.height if card.scene_type == "dating" else None,
                            "activityName": card.title if card.scene_type == "activity" else None,
                            "activityTime": card.activity_time if card.scene_type == "activity" else None,
                            "activityLocation": card.location if card.scene_type == "activity" else None,
                            "activityPrice": card.price if card.scene_type == "activity" else None
                        }
                        for i, (user, card) in enumerate(zip(mock_db_users, mock_user_cards), 1)
                    ]
                }
                
                with patch('app.services.match_service.MatchService', return_value=mock_match_service):
                    # 调用get_match_recommendation_cards接口
                    response = client.get("/api/v1/matches/recommendation-cards", params={
                        "sceneType": "housing",
                        "roleType": "seeker",
                        "page": 1,
                        "pageSize": 10
                    })
                    
                    assert response.status_code == 200
                    data = response.json()
                    
                    # 验证数据结构
                    assert "data" in data
                    assert "cards" in data["data"]
                    assert "pagination" in data["data"]
                    
                    cards = data["data"]["cards"]
                    assert len(cards) == 5
                    
                    # 验证统一的数据结构
                    for card in cards:
                        self._validate_unified_card_structure(card)

    def test_ai_recommendation_cards_structure(self, client, mock_current_user, mock_db_users, mock_user_cards):
        """测试AI推荐卡片数据结构"""
        
        with patch('app.routers.matches.get_current_user', return_value=mock_current_user):
            with patch('app.routers.matches.get_db') as mock_db:
                # 模拟数据库会话
                db_session = MagicMock()
                mock_db.return_value = db_session
                
                # 模拟有AI推荐
                db_session.query.return_value.filter.return_value.count.return_value = 1
                
                # 模拟AI推荐数据
                mock_ai_action = MagicMock()
                mock_ai_action.id = "ai_action_001"
                mock_ai_action.user_id = "user_001"
                mock_ai_action.target_user_id = "test_user_001"
                mock_ai_action.action_type = "ai_recommend_after_user_chat"
                mock_ai_action.target_card_id = "card_001"
                mock_ai_action.created_at = datetime.now()
                mock_ai_action.scene_context = json.dumps({
                    "aiAnalysis": {
                        "matchScore": 92,
                        "preferenceJudgement": "基于聊天内容智能推荐"
                    }
                })
                
                db_session.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_ai_action]
                
                # 模拟目标用户
                target_user = mock_db_users[0]
                db_session.query.return_value.filter.return_value.first.return_value = target_user
                
                # 模拟目标卡片
                target_card = mock_user_cards[0]
                db_session.query.return_value.filter.return_value.first.return_value = target_card
                
                # 调用get_match_recommendation_cards接口
                response = client.get("/api/v1/matches/recommendation-cards", params={
                    "sceneType": "dating",
                    "roleType": "seeker",
                    "page": 1,
                    "pageSize": 10
                })
                
                assert response.status_code == 200
                data = response.json()
                
                # 验证数据结构
                assert "data" in data
                assert "cards" in data["data"]
                assert "pagination" in data["data"]
                
                cards = data["data"]["cards"]
                assert len(cards) > 0
                
                # 验证统一的数据结构
                for card in cards:
                    self._validate_unified_card_structure(card)

    def _validate_unified_card_structure(self, card):
        """验证统一的卡片数据结构"""
        # 基础字段验证
        required_fields = [
            "id", "userId", "sceneType", "userRole", "name", "avatar",
            "age", "occupation", "location", "bio", "interests",
            "createdAt", "matchScore"
        ]
        
        for field in required_fields:
            assert field in card, f"缺少必要字段: {field}"
        
        # 验证字段类型和格式
        assert isinstance(card["id"], str)
        assert isinstance(card["userId"], str)
        assert isinstance(card["sceneType"], str)
        assert isinstance(card["userRole"], str)
        assert isinstance(card["name"], str)
        assert isinstance(card["avatar"], str)
        assert isinstance(card["age"], int)
        assert isinstance(card["occupation"], str)
        assert isinstance(card["location"], str)
        assert isinstance(card["bio"], str)
        assert isinstance(card["interests"], list)
        assert isinstance(card["createdAt"], str)
        assert isinstance(card["matchScore"], int)
        
        # 验证时间格式
        try:
            datetime.fromisoformat(card["createdAt"])
        except ValueError:
            pytest.fail(f"时间格式不正确: {card['createdAt']}")

    def test_card_structure_consistency(self):
        """测试不同接口返回的卡片数据结构一致性"""
        
        # 模拟一个示例卡片
        sample_card = {
            "id": "test_card_001",
            "userId": "user_001",
            "sceneType": "housing",
            "userRole": "seeker",
            "name": "测试用户",
            "avatar": "",
            "age": 28,
            "occupation": "工程师",
            "location": "北京",
            "bio": "测试简介",
            "interests": ["编程", "阅读"],
            "createdAt": "2024-01-01T00:00:00",
            "matchScore": 85,
            "houseTitle": "温馨公寓",
            "housePrice": 2500,
            "houseLocation": "朝阳区",
            "houseType": "公寓",
            "houseArea": 80,
            "houseImages": [],
            "rentStartDate": "2024-02-01",
            "rentEndDate": "2024-12-31",
            "houseDescription": "精装修公寓"
        }
        
        # 验证这个示例卡片符合统一结构
        self._validate_unified_card_structure(sample_card)

    def test_scene_specific_fields(self):
        """测试场景特定字段的正确性"""
        
        # 测试房源场景
        housing_card = {
            "id": "housing_001",
            "userId": "user_001",
            "sceneType": "housing",
            "userRole": "seeker",
            "name": "房东",
            "houseTitle": "温馨公寓",
            "housePrice": 2500,
            "houseLocation": "朝阳区",
            "houseType": "公寓"
        }
        
        # 测试交友场景
        dating_card = {
            "id": "dating_001",
            "userId": "user_002",
            "sceneType": "dating",
            "userRole": "seeker",
            "name": "交友用户",
            "gender": "female",
            "education": "硕士",
            "height": 165
        }
        
        # 测试活动场景
        activity_card = {
            "id": "activity_001",
            "userId": "user_003",
            "sceneType": "activity",
            "userRole": "provider",
            "name": "活动组织者",
            "activityName": "周末徒步",
            "activityTime": "2024-02-03 09:00",
            "activityLocation": "香山",
            "activityPrice": 50
        }
        
        # 验证所有卡片都符合统一结构
        for card in [housing_card, dating_card, activity_card]:
            self._validate_unified_card_structure(card)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])