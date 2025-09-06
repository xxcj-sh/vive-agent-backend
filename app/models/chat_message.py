from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.utils.db_config import Base
import uuid
from enum import Enum as PyEnum

class MessageType(PyEnum):
    """消息类型枚举"""
    TEXT = "text"
    IMAGE = "image"
    VOICE = "voice"
    VIDEO = "video"
    FILE = "file"
    SYSTEM = "system"

class MessageStatus(PyEnum):
    """消息状态枚举"""
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    DELETED = "deleted"

class ChatMessage(Base):
    """聊天消息数据模型"""
    __tablename__ = "chat_messages"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    match_id = Column(String, ForeignKey("matches.id"), nullable=False, index=True)
    sender_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    receiver_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    # 消息内容
    content = Column(Text, nullable=False)
    message_type = Column(Enum(MessageType), default=MessageType.TEXT)
    
    # 媒体文件URL（图片、语音、视频等）
    media_url = Column(String, nullable=True)
    media_size = Column(Integer, nullable=True)  # 文件大小（字节）
    media_duration = Column(Integer, nullable=True)  # 语音/视频时长（秒）
    
    # 消息状态
    status = Column(Enum(MessageStatus), default=MessageStatus.SENT)
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # 回复消息
    reply_to_id = Column(String, ForeignKey("chat_messages.id"), nullable=True)
    
    # 系统消息相关
    system_type = Column(String, nullable=True)  # 系统消息类型
    system_data = Column(String, nullable=True)  # 系统消息数据(JSON字符串)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 软删除
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(String, nullable=True)
    
    # 关系
    match = relationship("Match", back_populates="chat_messages")
    sender = relationship("User", foreign_keys=[sender_id], back_populates="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")
    reply_to = relationship("ChatMessage", remote_side=[id])
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "match_id": self.match_id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "content": self.content,
            "message_type": self.message_type.value,
            "media_url": self.media_url,
            "media_size": self.media_size,
            "media_duration": self.media_duration,
            "status": self.status.value,
            "is_read": self.is_read,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "reply_to_id": self.reply_to_id,
            "system_type": self.system_type,
            "system_data": self.system_data,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class ChatConversation(Base):
    """聊天会话模型，用于存储每个匹配的最新聊天状态"""
    __tablename__ = "chat_conversations"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    match_id = Column(String, ForeignKey("matches.id"), nullable=False, unique=True, index=True)
    user1_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    user2_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    # 最新消息
    last_message_id = Column(String, ForeignKey("chat_messages.id"), nullable=True)
    last_message_content = Column(Text, nullable=True)
    last_message_time = Column(DateTime(timezone=True), nullable=True)
    
    # 未读消息计数
    user1_unread_count = Column(Integer, default=0)
    user2_unread_count = Column(Integer, default=0)
    
    # 会话状态
    is_active = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)
    blocked_by = Column(String, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    match = relationship("Match", back_populates="chat_conversation")
    user1 = relationship("User", foreign_keys=[user1_id])
    user2 = relationship("User", foreign_keys=[user2_id])
    last_message = relationship("ChatMessage")
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "match_id": self.match_id,
            "user1_id": self.user1_id,
            "user2_id": self.user2_id,
            "last_message_id": self.last_message_id,
            "last_message_content": self.last_message_content,
            "last_message_time": self.last_message_time.isoformat() if self.last_message_time else None,
            "user1_unread_count": self.user1_unread_count,
            "user2_unread_count": self.user2_unread_count,
            "is_active": self.is_active,
            "is_blocked": self.is_blocked,
            "blocked_by": self.blocked_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }