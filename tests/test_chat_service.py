#!/usr/bin/env python3
"""
聊天服务测试脚本
测试新的聊天数据模型和服务功能
"""

import os
import sys
import uuid
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, get_db
from app.models.chat_message import ChatMessage, ChatConversation, MessageType, MessageStatus
from app.models.user import User
from app.models.match import Match
from app.services.chat_service import ChatService
from app.models.schemas import SendMessageRequest

def setup_test_data(session):
    """设置测试数据"""
    print("设置测试数据...")
    
    # 创建测试用户
    user1 = User(
        id=str(uuid.uuid4()),
        phone="13800138001",
        hashed_password="hashed_password_1",
        nick_name="测试用户1",
        avatar_url="https://example.com/avatar1.jpg"
    )
    
    user2 = User(
        id=str(uuid.uuid4()),
        phone="13800138002",
        hashed_password="hashed_password_2",
        nick_name="测试用户2",
        avatar_url="https://example.com/avatar2.jpg"
    )
    
    session.add_all([user1, user2])
    session.commit()
    
    # 创建测试匹配
    match = Match(
        id=str(uuid.uuid4()),
        user_id=user1.id,
        type="mutual",
        status="active"
    )
    
    session.add(match)
    session.commit()
    
    return user1, user2, match

def test_send_message(session, chat_service, user1, user2, match):
    """测试发送消息"""
    print("测试发送消息...")
    
    request = SendMessageRequest(
        match_id=match.id,
        content="你好，这是一条测试消息",
        type="text"
    )
    
    result = chat_service.send_message(request, user1.id)
    
    assert "id" in result
    assert "timestamp" in result
    assert "status" in result
    
    print(f"✅ 消息发送成功: {result}")
    
    # 验证消息已保存到数据库
    message = session.query(ChatMessage).filter(ChatMessage.id == result["id"]).first()
    assert message is not None
    assert message.content == "你好，这是一条测试消息"
    assert message.sender_id == user1.id
    assert message.receiver_id != user1.id
    
    print("✅ 消息已保存到数据库")
    
    return result["id"]

def test_get_chat_history(session, chat_service, user1, user2, match):
    """测试获取聊天记录"""
    print("测试获取聊天记录...")
    
    # 先发送几条测试消息
    messages = []
    for i in range(3):
        request = SendMessageRequest(
            match_id=match.id,
            content=f"测试消息 {i+1}",
            type="text"
        )
        result = chat_service.send_message(request, user1.id)
        messages.append(result["id"])
    
    # 获取聊天记录
    history = chat_service.get_chat_history(match.id, user1.id, page=1, limit=10)
    
    assert len(history.list) >= 3
    assert history.pagination["total"] >= 3
    
    print(f"✅ 获取聊天记录成功，共 {len(history.list)} 条消息")
    
    return history

def test_mark_messages_as_read(session, chat_service, user1, user2, match):
    """测试标记消息为已读"""
    print("测试标记消息为已读...")
    
    # 发送一条消息给user2
    request = SendMessageRequest(
        match_id=match.id,
        content="这条消息需要被标记为已读",
        type="text"
    )
    result = chat_service.send_message(request, user1.id)
    
    # 标记为已读
    success = chat_service.mark_messages_as_read(
        match_id=match.id,
        message_ids=[result["id"]],
        user_id=user2.id  # 用接收者身份标记已读
    )
    
    assert success is True
    
    # 验证消息状态已更新
    message = session.query(ChatMessage).filter(ChatMessage.id == result["id"]).first()
    assert message.is_read is True
    assert message.read_at is not None
    
    print("✅ 消息已标记为已读")

def test_get_unread_count(session, chat_service, user1, user2, match):
    """测试获取未读消息数量"""
    print("测试获取未读消息数量...")
    
    # 发送一条未读消息
    request = SendMessageRequest(
        match_id=match.id,
        content="这是一条未读消息",
        type="text"
    )
    chat_service.send_message(request, user1.id)
    
    # 获取未读计数
    unread_count = chat_service.get_unread_count(match.id, user2.id)
    
    assert unread_count.unread_count >= 1
    
    print(f"✅ 未读消息数量: {unread_count.unread_count}")

def test_get_conversation_list(session, chat_service, user1, user2, match):
    """测试获取会话列表"""
    print("测试获取会话列表...")
    
    # 发送消息以创建会话
    request = SendMessageRequest(
        match_id=match.id,
        content="创建会话的消息",
        type="text"
    )
    chat_service.send_message(request, user1.id)
    
    # 获取会话列表
    conversations = chat_service.get_conversation_list(user1.id, page=1, limit=10)
    
    assert len(conversations.list) >= 1
    assert conversations.pagination["total"] >= 1
    
    print(f"✅ 获取会话列表成功，共 {len(conversations.list)} 个会话")

def test_delete_message(session, chat_service, user1, match):
    """测试删除消息"""
    print("测试删除消息...")
    
    # 发送一条消息
    request = SendMessageRequest(
        match_id=match.id,
        content="这条消息将被删除",
        type="text"
    )
    result = chat_service.send_message(request, user1.id)
    
    # 删除消息
    count = chat_service.delete_messages([result["id"]], user1.id)
    
    assert count == 1
    
    # 验证消息已被软删除
    message = session.query(ChatMessage).filter(ChatMessage.id == result["id"]).first()
    assert message.is_deleted is True
    
    print("✅ 消息删除成功")

def main():
    """主测试函数"""
    print("=" * 50)
    print("开始测试聊天服务...")
    print("=" * 50)
    
    # 创建测试数据库
    test_db_path = "test_chat.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    
    engine = create_engine(f"sqlite:///{test_db_path}")
    SessionLocal = sessionmaker(bind=engine)
    
    # 创建表
    Base.metadata.create_all(bind=engine)
    
    # 创建会话
    session = SessionLocal()
    
    try:
        # 设置测试数据
        user1, user2, match = setup_test_data(session)
        chat_service = ChatService(session)
        
        # 运行测试
        test_send_message(session, chat_service, user1, user2, match)
        test_get_chat_history(session, chat_service, user1, user2, match)
        test_mark_messages_as_read(session, chat_service, user1, user2, match)
        test_get_unread_count(session, chat_service, user1, user2, match)
        test_get_conversation_list(session, chat_service, user1, user2, match)
        test_delete_message(session, chat_service, user1, match)
        
        print("=" * 50)
        print("所有测试通过！")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()
        
    # 清理测试数据库
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

if __name__ == "__main__":
    main()