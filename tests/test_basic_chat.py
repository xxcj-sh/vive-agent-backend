#!/usr/bin/env python3
"""
基础聊天功能测试 - 直接操作数据库
"""
import sys
sys.path.insert(0, '.')

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.user import User
from app.models.match import Match, MatchType, MatchStatus
from app.models.chat_message import ChatMessage, ChatConversation, MessageType, MessageStatus
import uuid
import random

def test_basic_chat():
    """测试基础聊天功能"""
    db = SessionLocal()
    try:
        print("🚀 开始基础聊天功能测试...")
        
        # 1. 创建测试用户
        user1 = User(
            id=str(uuid.uuid4()),
            phone=f"13800{random.randint(10000, 99999)}",
            nick_name="测试用户1"
        )
        user2 = User(
            id=str(uuid.uuid4()),
            phone=f"13800{random.randint(10000, 99999)}",
            nick_name="测试用户2"
        )
        
        db.add(user1)
        db.add(user2)
        db.flush()
        
        print(f"✅ 用户创建成功:")
        print(f"  用户1: {user1.nick_name} ({user1.id})")
        print(f"  用户2: {user2.nick_name} ({user2.id})")
        
        # 2. 创建匹配记录
        match = Match(
            id=str(uuid.uuid4()),
            user_id=user1.id,
            match_type=MatchType.DATING,
            status=MatchStatus.ACCEPTED,
            score=85.5
        )
        
        db.add(match)
        db.flush()
        
        print(f"✅ 匹配创建成功: {match.id}")
        
        # 3. 创建会话
        conversation = ChatConversation(
            id=str(uuid.uuid4()),
            match_id=match.id,
            user1_id=user1.id,
            user2_id=user2.id
        )
        
        db.add(conversation)
        db.flush()
        
        print(f"✅ 会话创建成功: {conversation.id}")
        
        # 4. 发送消息
        message1 = ChatMessage(
            id=str(uuid.uuid4()),
            match_id=match.id,
            sender_id=user1.id,
            receiver_id=user2.id,
            content="你好，很高兴认识你！",
            message_type=MessageType.TEXT,
            status=MessageStatus.SENT
        )
        
        message2 = ChatMessage(
            id=str(uuid.uuid4()),
            match_id=match.id,
            sender_id=user2.id,
            receiver_id=user1.id,
            content="我也很高兴认识你！",
            message_type=MessageType.TEXT,
            status=MessageStatus.SENT
        )
        
        db.add(message1)
        db.add(message2)
        db.flush()
        
        print(f"✅ 消息发送成功:")
        print(f"  消息1: {message1.content} (来自 {user1.nick_name})")
        print(f"  消息2: {message2.content} (来自 {user2.nick_name})")
        
        # 5. 查询聊天记录
        messages = db.query(ChatMessage).filter(
            ChatMessage.match_id == match.id,
            ChatMessage.is_deleted == False
        ).order_by(ChatMessage.created_at).all()
        
        print(f"\n📱 聊天记录 ({len(messages)} 条):")
        for msg in messages:
            sender = db.query(User).filter(User.id == msg.sender_id).first()
            print(f"  {sender.nick_name}: {msg.content} ({msg.created_at})")
        
        # 6. 标记消息已读
        message1.is_read = True
        message1.read_at = message1.created_at
        message1.status = MessageStatus.READ
        
        db.commit()
        
        print(f"✅ 消息已标记为已读")
        
        # 7. 统计未读消息
        unread_count = db.query(ChatMessage).filter(
            ChatMessage.receiver_id == user2.id,
            ChatMessage.is_read == False,
            ChatMessage.is_deleted == False
        ).count()
        
        print(f"📊 用户2的未读消息数: {unread_count}")
        
        print("\n🎉 基础聊天功能测试完成！")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    test_basic_chat()