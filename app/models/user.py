from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.utils.db_config import Base
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))  # 改为String类型支持字符串ID
    phone = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # 扩展用户字段以支持更多信息
    nick_name = Column(String(100), nullable=True)  # 昵称
    avatar_url = Column(String, nullable=True)  # 头像URL
    gender = Column(Integer, nullable=True)  # 性别 1-男 2-女
    age = Column(Integer, nullable=True)  # 年龄
    bio = Column(Text, nullable=True)  # 个人简介
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    occupation = Column(String(100), nullable=True)  # 职业
    location = Column(Text, nullable=True)  # 位置（JSON格式存储数组）
    education = Column(String(100), nullable=True)  # 教育
    
    # 新增字段
    interests = Column(Text, nullable=True)  # 兴趣爱好（JSON格式存储数组）
    wechat = Column(String(100), nullable=True)  # 微信号
    email = Column(String(255), nullable=True)  # 邮箱
    status = Column(String(20), default='active')  # 用户状态
    last_login = Column(DateTime(timezone=True), nullable=True)  # 最后登录时间
    level = Column(Integer, default=1)  # 用户等级
    points = Column(Integer, default=0)  # 积分
        
    # 关系
    matches = relationship("Match", back_populates="user")
    sent_messages = relationship("ChatMessage", foreign_keys="ChatMessage.sender_id", back_populates="sender")
    received_messages = relationship("ChatMessage", foreign_keys="ChatMessage.receiver_id", back_populates="receiver")
    cards = relationship("UserCard", back_populates="user")

# Pydantic 模型用于API
class UserBase(BaseModel):
    phone: Optional[str] = None
    nick_name: Optional[str] = None
    avatar_url: Optional[str] = None
    gender: Optional[int] = None
    age: Optional[int] = None
    bio: Optional[str] = None
    occupation: Optional[str] = None
    location: Optional[str] = None  # JSON字符串
    education: Optional[str] = None
    interests: Optional[str] = None  # JSON字符串
    wechat: Optional[str] = None
    email: Optional[str] = None

class UserCreate(UserBase):
    phone: str
    nick_name: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    phone: Optional[str] = None
    nick_name: Optional[str] = None
    avatar_url: Optional[str] = None
    gender: Optional[int] = None
    age: Optional[int] = None
    bio: Optional[str] = None
    occupation: Optional[str] = None
    location: Optional[str] = None
    education: Optional[str] = None
    interests: Optional[str] = None
    wechat: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = None
    level: Optional[int] = None
    points: Optional[int] = None
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    phone: str
    verification_code: str

class RegisterRequest(BaseModel):
    phone: str
    verification_code: str
    nick_name: Optional[str] = None

class UserProfileUpdate(BaseModel):
    nick_name: Optional[str] = None
    avatar_url: Optional[str] = None
    gender: Optional[int] = None
    age: Optional[int] = None
    bio: Optional[str] = None
    occupation: Optional[str] = None
    location: Optional[str] = None  # JSON字符串
    education: Optional[str] = None
    interests: Optional[str] = None  # JSON字符串
    wechat: Optional[str] = None
    email: Optional[str] = None
