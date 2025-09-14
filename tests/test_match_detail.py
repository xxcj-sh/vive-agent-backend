import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db
from app.models.user import User
from app.models.match_result import MatchResult
from app.models.match_action import MatchAction, MatchActionType
from datetime import datetime
import uuid

# 创建测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_match_detail.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 覆盖数据库依赖
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture
def test_user():
    """创建测试用户"""
    db = TestingSessionLocal()
    user = User(
        id=str(uuid.uuid4()),
        name="测试用户",
        nick_name="测试用户",
        email="test@example.com",
        age=25,
        gender=1,
        location="北京",
        occupation="工程师",
        bio="测试用户简介"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user

@pytest.fixture
def test_target_user():
    """创建目标测试用户"""
    db = TestingSessionLocal()
    user = User(
        id=str(uuid.uuid4()),
        name="目标用户",
        nick_name="目标用户",
        email="target@example.com",
        age=23,
        gender=2,
        location="上海",
        occupation="设计师",
        bio="目标用户简介"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user

@pytest.fixture
def test_match(test_user, test_target_user):
    """创建测试匹配"""
    db = TestingSessionLocal()
    match = MatchResult(
        id=str(uuid.uuid4()),
        user1_id=test_user.id,
        user2_id=test_target_user.id,
        match_type="dating",
        status="matched",
        matched_at=datetime.utcnow()
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    db.close()
    return match

@pytest.fixture
def auth_headers(test_user):
    """创建认证头"""
    return {"Authorization": f"Bearer test_token_{test_user.id}"}

class TestMatchDetailAPI:
    """测试匹配详情API"""
    
    def test_get_match_detail_success(self, test_match, auth_headers):
        """测试成功获取匹配详情"""
        response = client.get(f"/api/v1/matches/{test_match.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["data"]["id"] == test_match.id
        assert "user" in data["data"]
        assert "matchedAt" in data["data"]
    
    def test_get_match_detail_not_found(self, auth_headers):
        """测试获取不存在的匹配详情"""
        fake_match_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/matches/{fake_match_id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 404
        assert "匹配记录不存在" in data["message"]
    
    def test_get_match_detail_unauthorized(self, test_match):
        """测试无权限获取匹配详情"""
        # 使用不相关的用户token
        fake_auth_headers = {"Authorization": "Bearer test_token_fake_user"}
        response = client.get(f"/api/v1/matches/{test_match.id}", headers=fake_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 404  # 应该返回404，因为用户无权查看此匹配
    
    def test_get_match_detail_invalid_id(self, auth_headers):
        """测试获取无效的匹配ID"""
        response = client.get("/api/v1/matches/invalid-id", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 404

if __name__ == "__main__":
    pytest.main([__file__, "-v"])