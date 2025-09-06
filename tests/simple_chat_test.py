#!/usr/bin/env python3
"""
简化版聊天功能测试
"""

import os
import sys
import uuid
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到路径
sys.path.insert(0, '.')

from app.database import Base
from app.models.chat_message import ChatMessage, ChatConversation, MessageType, MessageStatus
from app.models.user import User
from app.models.match import Match

def setup_test_data():
    """设置测试数据"""
    # 创建内存数据库
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 创建测试用户
        user1 = User(
            id=str(uuid.uuid4()),
            phone="13800138001",
            hashed_password="test1",
            nick_name="测试用户1",
            avatar_url="https://example.com/avatar1.jpg"
        )
        
        user2 = User(
            id=str(uuid.uuid4()),
            phone="13800138002",
            hashed_password="test2",
            nick_name="测试用户2",
            avatar_url="https://example.com/avatar2.jpg"
        )
        
        session.add_all([user1, user2])
        session.commit()
        
        # 创建测试匹配
        match = Match(
            id=str(uuid.uuid4()),
            user_id=user1.id,
            match_type="dating",
            status="accepted"
        )
        
        session.add(match)
        session.commit()
        
        print(f"✅ 创建测试数据成功")
        print(f"   用户1 ID: {user1.id}")
        print(f"   用户2 ID: {user2.id}")
        print(f"   匹配 ID: {match.id}")
        
        # 测试发送消息
        message = ChatMessage(
            id=str(uuid.uuid4()),
            match_id=match.id,
            sender_id=user1.id,
            receiver_id=user2.id,
            content="你好，这是一条测试消息",
            message_type=MessageType.TEXT
        )
        
        session.add(message)
        session.commit()
        
        print(f"✅ 发送消息成功: {message.content}")
        
        # 测试查询消息
        messages = session.query(ChatMessage).filter_by(match_id=match.id).all()
        print(f"✅ 查询消息成功，共 {len(messages)} 条消息")
        
        for msg in messages:
            print(f"   - {msg.sender.nick_name} -> {msg.receiver.nick_name}: {msg.content}")
        
        # 测试创建会话
        conversation = ChatConversation(
            id=str(uuid.uuid4()),
            match_id=match.id,
            user1_id=user1.id,
            user2_id=user2.id,
            last_message_content=message.content,
            user1_unread_count=0,
            user2_unread_count=1
        )
        
        session.add(conversation)
        session.commit()
        
        print(f"✅ 创建会话成功")
        
        # 测试查询会话
        conversations = session.query(ChatConversation).all()
        print(f"✅ 查询会话成功，共 {len(conversations)} 个会话")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        session.rollback()
        return False
    finally:
        session.close()

if __name__ == "__main__":
    print("=" * 50)
    print("开始简化版聊天功能测试...")
    print("=" * 50)
    
    success = setup_test_data()
    
    if success:
        print("=" * 50)
        print("✅ 所有测试通过！")
        print("=" * 50)
    else:
        print("=" * 50)
        print("❌ 测试失败！")
        print("=" * 50)