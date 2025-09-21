import pytest
import sys
import os
from unittest.mock import Mock, MagicMock
from datetime import datetime
import uuid

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def mock_db():
    """创建模拟数据库会话"""
    from sqlalchemy.orm import Session
    mock_session = Mock(spec=Session)
    return mock_session

@pytest.fixture
def sample_user_data():
    """示例用户数据"""
    return {
        "id": str(uuid.uuid4()),
        "phone": "13800138000",
        "nick_name": "测试用户",
        "avatar_url": "https://example.com/avatar.jpg",
        "gender": 1,
        "is_active": True,
        "status": "active",
        "register_at": datetime.now()
    }

@pytest.fixture
def sample_match_data():
    """示例匹配数据"""
    return {
        "id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "match_type": "dating",
        "status": "active",
        "score": 85.5,
        "created_at": datetime.now()
    }

@pytest.fixture
def sample_chat_message_data():
    """示例聊天消息数据"""
    return {
        "id": str(uuid.uuid4()),
        "match_id": str(uuid.uuid4()),
        "sender_id": str(uuid.uuid4()),
        "receiver_id": str(uuid.uuid4()),
        "content": "你好，很高兴认识你！",
        "message_type": "text",
        "is_read": False,
        "status": "sent"
    }