from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
import os
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid

class User(Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    phone = Column(String(20), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    
    nick_name = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    gender = Column(Integer, nullable=True)
    age = Column(Integer, nullable=True)
    bio = Column(Text, nullable=True)
    birthday = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    occupation = Column(String(100), nullable=True)
    location = Column(JSON, nullable=True)
    education = Column(String(100), nullable=True)
    
    interests = Column(JSON, nullable=True)
    wechat = Column(String(100), nullable=True)
    wechat_open_id = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    
    xiaohongshu_id = Column(String(100), nullable=True)
    douyin_id = Column(String(100), nullable=True)
    wechat_official_account = Column(String(100), nullable=True)
    xiaoyuzhou_id = Column(String(100), nullable=True)
    
    status = Column(String(20), default='pending')
    last_login = Column(DateTime(timezone=True), nullable=True)
    level = Column(Integer, default=1)
    points = Column(Integer, default=0)
    register_at = Column(DateTime(timezone=True), nullable=True, server_default=func.now())
        
    cards = relationship("UserCard", back_populates="user")
    topic_cards = relationship("TopicCard", back_populates="user")
    topic_discussions_as_participant = relationship("TopicDiscussion", foreign_keys="TopicDiscussion.participant_id", back_populates="participant")
    topic_discussions_as_host = relationship("TopicDiscussion", foreign_keys="TopicDiscussion.host_id", back_populates="host")
    
    vote_cards = relationship("VoteCard", back_populates="user")
    vote_records = relationship("VoteRecord", back_populates="user")
    vote_discussions_as_participant = relationship("VoteDiscussion", foreign_keys="VoteDiscussion.participant_id", back_populates="participant")
    vote_discussions_as_host = relationship("VoteDiscussion", foreign_keys="VoteDiscussion.host_id", back_populates="host")
    vote_relations = relationship("UserCardVoteRelation", back_populates="user", cascade="all, delete-orphan")
    
    topic_opinion_summaries = relationship("TopicOpinionSummary", back_populates="user", cascade="all, delete-orphan")

class UserBase(BaseModel):
    phone: Optional[str] = None
    nick_name: Optional[str] = None
    wechat_open_id: Optional[str] = None
    avatar_url: Optional[str] = None
    gender: Optional[int] = None
    age: Optional[int] = None
    bio: Optional[str] = None
    birthday: Optional[str] = None
    occupation: Optional[str] = None
    location: Optional[str] = None
    education: Optional[str] = None
    interests: Optional[str] = None
    wechat: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = None
    register_at: Optional[datetime] = None
    xiaohongshu_id: Optional[str] = None
    douyin_id: Optional[str] = None
    wechat_official_account: Optional[str] = None
    xiaoyuzhou_id: Optional[str] = None

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
    birthday: Optional[str] = None
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
    register_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    xiaohongshu_id: Optional[str] = None
    douyin_id: Optional[str] = None
    wechat_official_account: Optional[str] = None
    xiaoyuzhou_id: Optional[str] = None
    
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
    birthday: Optional[str] = None
    occupation: Optional[str] = None
    location: Optional[str] = None
    education: Optional[str] = None
    interests: Optional[str] = None
    wechat: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = None
    register_at: Optional[datetime] = None
    xiaohongshu_id: Optional[str] = None
    douyin_id: Optional[str] = None
    wechat_official_account: Optional[str] = None
    xiaoyuzhou_id: Optional[str] = None
