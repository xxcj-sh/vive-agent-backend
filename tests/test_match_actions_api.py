"""
匹配操作API单元测试
针对 /api/v1/matches/actions 接口的全面测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from datetime import datetime
import json
import uuid

from app.main import app
from app.models.match_action import MatchAction, MatchActionType
from app.models.user import User
from app.database import get_db


class TestMatchActionsAPI:
    """匹配操作API测试类"""
    
    def setup_method(self):
        """测试前置设置"""
        self.client = TestClient(app)
        self.test_user_id = "test_user_001"
        self.target_user_id = "target_user_002"
        self.card_id = f"{self.target_user_id}_card_001"
        self.auth_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.test_user_id}"
        }
        
        # 有效的请求数据
        self.valid_action_data = {
            "cardId": self.card_id,
            "action": "like",
            "sceneType": "dating",
            "sceneContext": "测试场景上下文"
        }

    def test_submit_match_action_success(self):
        """测试成功提交匹配操作"""
        response = self.client.post(
            "/api/v1/matches/actions",
            json=self.valid_action_data,
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["message"] == "success"
        assert data["data"] is not None
        assert "action_id" in data["data"]
        assert "is_match" in data["data"]
        assert "match_id" in data["data"]

    def test_submit_match_action_invalid_action_type(self):
        """测试无效的操作类型"""
        invalid_data = self.valid_action_data.copy()
        invalid_data["action"] = "invalid_action"
        
        response = self.client.post(
            "/api/v1/matches/actions",
            json=invalid_data,
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 400
        assert "无效的操作类型" in data["message"]

    def test_submit_match_action_missing_required_fields(self):
        """测试缺少必要字段"""
        invalid_data = {
            "cardId": self.card_id,
            "action": "like"
            # 缺少 sceneType
        }
        
        response = self.client.post(
            "/api/v1/matches/actions",
            json=invalid_data,
            headers=self.auth_headers
        )
        
        assert response.status_code == 422  # FastAPI验证错误

    def test_submit_match_action_invalid_card_id_format(self):
        """测试无效的卡片ID格式"""
        invalid_data = self.valid_action_data.copy()
        invalid_data["cardId"] = "invalid_card_id"
        
        response = self.client.post(
            "/api/v1/matches/actions",
            json=invalid_data,
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 400
        assert "无法从cardId" in data["message"]

    def test_submit_match_action_duplicate_action(self):
        """测试重复操作同一张卡片"""
        # 第一次操作
        response1 = self.client.post(
            "/api/v1/matches/actions",
            json=self.valid_action_data,
            headers=self.auth_headers
        )
        assert response1.status_code == 200
        
        # 第二次操作同一张卡片
        response2 = self.client.post(
            "/api/v1/matches/actions",
            json=self.valid_action_data,
            headers=self.auth_headers
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["code"] == 0
        assert "已经对该用户执行过操作" in data2["data"]["message"]

    def test_submit_match_action_different_scene_types(self):
        """测试不同的场景类型"""
        scene_types = ["dating", "housing", "activity"]
        
        for scene_type in scene_types:
            data = self.valid_action_data.copy()
            data["sceneType"] = scene_type
            data["cardId"] = f"{self.target_user_id}_card_{scene_type}"
            
            response = self.client.post(
                "/api/v1/matches/actions",
                json=data,
                headers=self.auth_headers
            )
            
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["code"] == 0

    def test_submit_match_action_different_action_types(self):
        """测试不同的操作类型"""
        action_types = ["like", "dislike", "super_like", "pass"]
        
        for i, action_type in enumerate(action_types):
            data = self.valid_action_data.copy()
            data["action"] = action_type
            data["cardId"] = f"{self.target_user_id}_card_{i}"
            
            response = self.client.post(
                "/api/v1/matches/actions",
                json=data,
                headers=self.auth_headers
            )
            
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["code"] == 0

    def test_submit_match_action_with_scene_context(self):
        """测试带场景上下文的匹配操作"""
        data_with_context = self.valid_action_data.copy()
        data_with_context["sceneContext"] = {
            "location": "北京",
            "time": "2024-01-01T10:00:00Z",
            "preferences": ["音乐", "电影"]
        }
        
        response = self.client.post(
            "/api/v1/matches/actions",
            json=data_with_context,
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0

    def test_submit_match_action_without_authorization(self):
        """测试未授权访问"""
        response = self.client.post(
            "/api/v1/matches/actions",
            json=self.valid_action_data
            # 不添加认证头
        )
        
        assert response.status_code == 401

    def test_submit_match_action_with_invalid_authorization(self):
        """测试无效的认证令牌"""
        invalid_headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer invalid_token"
        }
        
        response = self.client.post(
            "/api/v1/matches/actions",
            json=self.valid_action_data,
            headers=invalid_headers
        )
        
        assert response.status_code == 401

    def test_submit_match_action_mutual_match_scenario(self):
        """测试双向匹配场景"""
        # 用户A对用户B执行like操作
        response_a = self.client.post(
            "/api/v1/matches/actions",
            json=self.valid_action_data,
            headers=self.auth_headers
        )
        assert response_a.status_code == 200
        
        # 模拟用户B对用户A执行like操作（需要切换用户）
        user_b_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.target_user_id}"
        }
        
        # 为用户B创建测试卡片
        user_b_card_id = f"{self.test_user_id}_card_002"
        data_b = {
            "cardId": user_b_card_id,
            "action": "like",
            "sceneType": "dating"
        }
        
        response_b = self.client.post(
            "/api/v1/matches/actions",
            json=data_b,
            headers=user_b_headers
        )
        
        # 检查响应格式
        assert response_b.status_code == 200
        data_b = response_b.json()
        assert data_b["code"] == 0

    def test_submit_match_action_with_metadata(self):
        """测试带元数据的匹配操作"""
        data_with_metadata = self.valid_action_data.copy()
        data_with_metadata["metadata"] = {
            "device": "iPhone",
            "app_version": "1.0.0",
            "location": {"lat": 39.9042, "lng": 116.4074}
        }
        
        response = self.client.post(
            "/api/v1/matches/actions",
            json=data_with_metadata,
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0

    def test_submit_match_action_response_format(self):
        """测试响应格式的一致性"""
        response = self.client.post(
            "/api/v1/matches/actions",
            json=self.valid_action_data,
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 检查标准响应格式
        assert "code" in data
        assert "message" in data
        assert "data" in data
        
        # 检查数据字段
        if data["data"] is not None:
            assert "action_id" in data["data"]
            assert "is_match" in data["data"]
            assert "match_id" in data["data"]
            assert "message" in data["data"]
            assert "source" in data["data"]

    def test_submit_match_action_error_handling(self):
        """测试错误处理机制"""
        # 测试各种错误情况
        test_cases = [
            {
                "name": "空请求体",
                "data": {},
                "expected_status": 422
            },
            {
                "name": "null值",
                "data": {
                    "cardId": None,
                    "action": "like",
                    "sceneType": "dating"
                },
                "expected_status": 422
            },
            {
                "name": "空字符串",
                "data": {
                    "cardId": "",
                    "action": "like",
                    "sceneType": "dating"
                },
                "expected_status": 400
            }
        ]
        
        for test_case in test_cases:
            response = self.client.post(
                "/api/v1/matches/actions",
                json=test_case["data"],
                headers=self.auth_headers
            )
            assert response.status_code == test_case["expected_status"], f"测试用例失败: {test_case['name']}"


class TestMatchActionsIntegration:
    """匹配操作集成测试"""
    
    def setup_method(self):
        """测试前置设置"""
        self.client = TestClient(app)
        self.test_user_id = "integration_user_001"
        self.auth_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.test_user_id}"
        }

    def test_match_action_workflow(self):
        """测试完整的匹配操作流程"""
        target_user_id = "integration_target_001"
        card_id = f"{target_user_id}_card_001"
        
        # 步骤1: 提交like操作
        like_data = {
            "cardId": card_id,
            "action": "like",
            "sceneType": "dating"
        }
        
        response = self.client.post(
            "/api/v1/matches/actions",
            json=like_data,
            headers=self.auth_headers
        )
        
        assert response.status_code == 200
        like_result = response.json()
        assert like_result["code"] == 0
        assert like_result["data"]["is_match"] is False  # 第一次操作不会匹配
        
        # 步骤2: 获取用户匹配历史
        history_response = self.client.get(
            "/api/v1/matches/actions/history",
            headers=self.auth_headers
        )
        
        assert history_response.status_code == 200
        history_data = history_response.json()
        assert history_data["code"] == 0
        assert len(history_data["data"]["actions"]) > 0

    def test_match_action_with_different_users(self):
        """测试不同用户之间的匹配操作"""
        users = ["user_a", "user_b", "user_c"]
        results = []
        
        for i, user_id in enumerate(users):
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {user_id}"
            }
            
            target_user = users[(i + 1) % len(users)]
            card_id = f"{target_user}_card_001"
            
            data = {
                "cardId": card_id,
                "action": "like",
                "sceneType": "dating"
            }
            
            response = self.client.post(
                "/api/v1/matches/actions",
                json=data,
                headers=headers
            )
            
            assert response.status_code == 200
            results.append(response.json())
        
        # 验证所有操作都成功
        for result in results:
            assert result["code"] == 0


if __name__ == "__main__":
    pytest.main([__file__])