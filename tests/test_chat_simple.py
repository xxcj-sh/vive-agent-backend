#!/usr/bin/env python3
"""
简单的聊天功能测试脚本
"""
import sys
sys.path.insert(0, '.')

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.user import User
from app.models.match import Match, MatchType, MatchStatus
from app.models.chat_message import ChatMessage, ChatConversation
from app.services.chat_service import ChatService
from datetime import datetime
import uuid

def create_test_data():
    """创建测试数据"""
    db = SessionLocal()
    try:
        # 创建测试用户
        import random
        user1 = User(
            id=str(uuid.uuid4()),
            nick_name="测试用户1",
            phone=f"13800{random.randint(10000, 99999)}"
        )
        user2 = User(
            id=str(uuid.uuid4()),
            nick_name="测试用户2", 
            phone=f"13800{random.randint(10000, 99999)}"
        )
        
        db.add(user1)
        db.add(user2)
        db.flush()  # 获取用户ID
        
        # 创建匹配记录
        match = Match(
            id=str(uuid.uuid4()),
            user_id=user1.id,
            match_type=MatchType.DATING,
            status=MatchStatus.ACCEPTED,
            score=85.5
        )
        
        db.add(match)
        db.flush()
        
        # 创建会话
        conversation = ChatConversation(
            id=str(uuid.uuid4()),
            match_id=match.id,
            user1_id=user1.id,
            user2_id=user2.id
        )
        
        db.add(conversation)
        db.commit()
        
        print(f"✅ 测试数据创建成功")
        print(f"用户1 ID: {user1.id}")
        print(f"用户2 ID: {user2.id}")
        print(f"匹配ID: {match.id}")
        print(f"会话ID: {conversation.id}")
        
        return user1.id, user2.id, match.id, conversation.id
        
    except Exception as e:
        db.rollback()
        print(f"❌ 创建测试数据失败: {e}")
        return None, None, None, None
    finally:
        db.close()

def test_send_message():
    """测试发送消息"""
    user1_id, user2_id, match_id, conversation_id = create_test_data()
    if not user1_id:
        return
        
    db = SessionLocal()
    try:
        from app.models.schemas import SendMessageRequest
        
        chat_service = ChatService(db)
        
        # 测试发送消息
        request = SendMessageRequest(
            match_id=match_id,
            content="你好，很高兴认识你！",
            type="TEXT"
        )
        
        response = chat_service.send_message(
            request=request,
            sender_id=user1_id
        )
        
        print(f"✅ 消息发送成功")
        print(f"消息ID: {response['id']}")
        
        # 测试获取聊天记录
        history = chat_service.get_chat_history(
            match_id=match_id,
            user_id=user1_id,
            limit=10
        )
        
        print(f"\n📱 聊天记录:")
        for msg in history.list:
            print(f"{msg.sender_name}: {msg.content}")
            
        # 测试获取未读消息数
        unread_count = chat_service.get_unread_count(
            user_id=user2_id
        )
        
        print(f"\n📊 用户2未读消息数: {unread_count['unreadCount']}")
        
        # 测试标记已读
        marked = chat_service.mark_messages_as_read(
            match_id=match_id,
            message_ids=[response['id']],
            user_id=user2_id
        )
        
        print(f"✅ 标记已读: {marked}")
        
        # 再次检查未读消息数
        unread_count = chat_service.get_unread_count(
            user_id=user2_id
        )
        
        print(f"📊 标记后未读消息数: {unread_count['unreadCount']}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 开始测试聊天功能...")
    test_send_message()
    print("✅ 测试完成")