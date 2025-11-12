"""
聊天消息数据模型
"""

from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class ChatMessage(Base):
    """聊天消息记录表"""
    __tablename__ = "chat_messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=True, index=True)  # 用户ID（移除外键约束，允许为NULL，支持匿名聊天）
    card_id = Column(String(36), ForeignKey('user_cards.id'), nullable=True, index=True)  # 卡片ID（可选）
    content = Column(Text, nullable=False)  # 消息内容
    message_type = Column(String(20), default='text')  # 消息类型: text, image, audio, video
    sender_type = Column(String(20), nullable=False)  # 发送者类型: user, ai, system
    session_id = Column(String(36), nullable=True, index=True)  # 会话ID（可选）
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
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }