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
    hashed_password = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # 扩展用户字段以支持更多信息
    nick_name = Column(String, nullable=True)  # 昵称
    avatar_url = Column(String, nullable=True)  # 头像URL
    gender = Column(Integer, nullable=True)  # 性别 1-男 2-女
    age = Column(Integer, nullable=True)  # 年龄
    bio = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    matches = relationship("Match", back_populates="user")
    profiles = relationship("UserProfile", back_populates="user")

# Pydantic 模型用于API
class UserBase(BaseModel):
    phone: Optional[str] = None
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    gender: Optional[int] = None

class UserCreate(UserBase):
    phone: str
    username: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    phone: Optional[str] = None
    username: Optional[str] = None
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
