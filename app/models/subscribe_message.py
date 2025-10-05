"""
订阅消息数据模型
"""

from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class SubscribeMessage(Base):
    """订阅消息记录表"""
    __tablename__ = "subscribe_messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)  # 接收消息的用户ID
    template_id = Column(String(100), nullable=False)  # 微信模板ID
    template_name = Column(String(100), nullable=False)  # 模板名称
    status = Column(String(20), nullable=False, default='pending')  # 发送状态: pending, sent, failed
    message_data = Column(Text, nullable=False)  # 消息数据(JSON格式)
    send_result = Column(Text)  # 发送结果
    error_message = Column(Text)  # 错误信息
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<SubscribeMessage(id={self.id}, user_id={self.user_id}, status={self.status})>"


class UserSubscribeSetting(Base):
    """用户订阅设置表"""
    __tablename__ = "user_subscribe_settings"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, unique=True, index=True)
    template_id = Column(String(100), nullable=False)  # 用户关注的模板ID
    is_enabled = Column(Boolean, default=True)  # 是否启用订阅
    is_subscribed = Column(Boolean, default=False)  # 是否已订阅
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<UserSubscribeSetting(user_id={self.user_id}, is_enabled={self.is_enabled})>"