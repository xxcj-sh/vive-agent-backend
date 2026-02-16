"""
聊天消息数据模型
"""

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.sql import func
import uuid
from app.database import Base

class ChatMessage(Base):
    """聊天消息记录表"""
    __tablename__ = "chat_messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), index=True)
    card_id = Column(String(32), ForeignKey('user_cards.id'), index=True)
    session_id = Column(String(36), nullable=True, index=True)  # 会话ID（可选）
    content = Column(Text, nullable=False)  # 消息内容
    message_type = Column(String(20), default='text')  # 消息类型: text, image, audio, video
    sender_type = Column(String(20), nullable=False)  # 发送者类型: user, ai, system, card_creator
    is_anonymous = Column(Boolean, default=False, index=True)  # 是否为匿名消息
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, user_id={self.user_id}, sender_type={self.sender_type})>"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'card_id': self.card_id,
            'content': self.content,
            'message_type': self.message_type,
            'sender_type': self.sender_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_anonymous': self.is_anonymous,
            'session_id': self.session_id
        }


class ChatSummary(Base):
    """聊天总结记录表"""
    __tablename__ = "chat_summaries"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), index=True)
    card_id = Column(String(32), ForeignKey('user_cards.id'), index=True)
    session_id = Column(String(36), nullable=True, index=True)  # 会话ID（可选）
    summary_type = Column(String(20), default='chat')  # 总结类型: chat, opinion, analysis
    summary_content = Column(Text, nullable=False)  # 总结内容
    chat_messages_count = Column(String(10), nullable=True)  # 聊天消息数量
    summary_language = Column(String(10), default='zh')  # 总结语言: zh, en
    is_read = Column(Boolean, default=False, index=True)  # 是否已读
    read_at = Column(DateTime, nullable=True)  # 阅读时间
    created_at = Column(DateTime, server_default=func.now(), index=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<ChatSummary(id={self.id}, user_id={self.user_id}, summary_type={self.summary_type})>"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'card_id': self.card_id,
            'session_id': self.session_id,
            'summary_type': self.summary_type,
            'summary_content': self.summary_content,
            'chat_messages_count': self.chat_messages_count,
            'summary_language': self.summary_language,
            'is_read': self.is_read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }