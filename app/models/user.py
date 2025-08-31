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
    username = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=True)
    hashed_password = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # 扩展用户字段以支持更多信息
    nick_name = Column(String, nullable=True)  # 昵称
    avatar_url = Column(String, nullable=True)  # 头像URL
    gender = Column(Integer, nullable=True)  # 性别 1-男 2-女
    age = Column(Integer, nullable=True)  # 年龄
    occupation = Column(String, nullable=True)  # 职业
    location = Column(JSON, nullable=True)  # 位置信息
    bio = Column(Text, nullable=True)  # 个人简介
    match_type = Column(String, nullable=True)  # 匹配类型
    user_role = Column(String, nullable=True)  # 用户角色
    interests = Column(JSON, nullable=True)  # 兴趣爱好
    preferences = Column(JSON, nullable=True)  # 偏好设置
    phone = Column(String, unique=True, nullable=True, index=True)  # 电话，添加唯一约束和索引
    education = Column(String, nullable=True)  # 教育背景
    join_date = Column(Integer, nullable=True)  # 加入时间戳
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    matches = relationship("Match", back_populates="user")
    profiles = relationship("UserProfile", back_populates="user")

# Pydantic 模型用于API
class UserBase(BaseModel):
    phone: Optional[str] = None
    nick_name: Optional[str] = None
    avatar_url: Optional[str] = None
    gender: Optional[int] = None

class UserCreate(UserBase):
    phone: str
    nick_name: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    phone: Optional[str] = None
    nick_name: Optional[str] = None
    avatar_url: Optional[str] = None
    gender: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    phone: str
    verification_code: str

class RegisterRequest(BaseModel):
    phone: str
    verification_code: str
    nick_name: Optional[str] = None
