import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.utils.db_config import SessionLocal
from app.models.user import User

client = TestClient(app)

class TestNewUserScenario:
    """测试新用户场景"""
    
    def setup_method(self):
        """测试前置设置"""
        self.test_headers = {"Content-Type": "application/json"}
        
        # 确保测试用户不存在
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.phone == "18900189000").first()
            if user:
                db.delete(user)
                db.commit()
        finally:
            db.close()
    
    def test_new_user_login_returns_is_new_user_true(self):
        """测试新用户登录时 isNewUser 为 true"""
        payload = {"phone": "18900189000", "code": "123456"}
        response = client.post("/api/v1/auth/sessions/phone",
                             json=payload,
                             headers=self.test_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == 0
        assert "token" in data["data"]
        assert "isNewUser" in data["data"]
        assert data["data"]["isNewUser"] is True
        print(f"✅ 新用户登录测试通过，isNewUser: {data['data']['isNewUser']}")
    
    def test_existing_user_login_returns_is_new_user_false(self):
        """测试现有用户登录时 isNewUser 为 false"""
        payload = {"phone": "13800138000", "code": "123456"}  # 测试数据中的现有用户
        response = client.post("/api/v1/auth/sessions/phone",
                             json=payload,
                             headers=self.test_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["code"] == 0
        assert "token" in data["data"]
        assert "isNewUser" in data["data"]
        assert data["data"]["isNewUser"] is False
        print(f"✅ 现有用户登录测试通过，isNewUser: {data['data']['isNewUser']}")