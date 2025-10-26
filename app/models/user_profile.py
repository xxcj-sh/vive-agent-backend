"""
用户画像数据模型
用于存储模型预测得到的用户偏好、个性、心情等数据
"""

from sqlalchemy import Column, String, Text, DateTime, JSON, Integer, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid


class UserProfile(Base):
    """用户画像数据表"""
    __tablename__ = "user_profiles"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True, comment="用户ID")
    
    # 用户偏好数据
    preferences = Column(JSON, nullable=True, comment="用户偏好设置")
    
    # 用户个性特征
    personality_traits = Column(JSON, nullable=True, comment="个性特征分析")
    
    # 用户心情状态
    mood_state = Column(JSON, nullable=True, comment="心情状态分析")
    
    # 行为模式分析
    behavior_patterns = Column(JSON, nullable=True, comment="行为模式分析")
    
    # 兴趣标签
    interest_tags = Column(JSON, nullable=True, comment="兴趣标签")
    
    # 社交偏好
    social_preferences = Column(JSON, nullable=True, comment="社交偏好")
    
    # 匹配偏好
    match_preferences = Column(JSON, nullable=True, comment="匹配偏好")
    
    # 数据来源和置信度
    data_source = Column(String(100), nullable=True, comment="数据来源")
    confidence_score = Column(Integer, nullable=True, comment="置信度评分(0-100)")
    
    # 更新时间信息
    update_reason = Column(String(255), nullable=True, comment="更新原因")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # 用户评价
    accuracy_rating = Column(String(20), nullable=True, comment="准确率评价(accurate, partial, inaccurate)")
    adjustment_text = Column(Text, nullable=True, comment="调整建议")
    
    # 关联关系 - 用户画像历史记录
    history = relationship("UserProfileHistory", back_populates="profile", cascade="all, delete-orphan")
    


# Pydantic 模型用于API
class UserProfileBase(BaseModel):
    """用户画像基础模型"""
    user_id: str = Field(..., description="用户ID")
    basic_info: Optional[Dict[str, Any]] = Field(None, description="基本信息")
    preferences: Optional[Dict[str, Any]] = Field(None, description="用户偏好")
    mood_state: Optional[Dict[str, Any]] = Field(None, description="心情状态分析")
    behavior_patterns: Optional[Dict[str, Any]] = Field(None, description="聊天中体现的行为模式分析")
    personality_traits: Optional[Dict[str, Any]] = Field(None, description="个性特征分析")
    interest_tags: Optional[List[str]] = Field(None, description="兴趣标签")
    social_preferences: Optional[Dict[str, Any]] = Field(None, description="沟通偏好")
    match_preferences: Optional[Dict[str, Any]] = Field(None, description="匹配偏好")
    data_source: Optional[str] = Field(None, description="数据来源")
    confidence_score: Optional[int] = Field(None, description="置信度评分(0-100)")
    update_reason: Optional[str] = Field(None, description="更新原因")
    accuracy_rating: Optional[str] = Field(None, description="准确率评价(accurate, partial, inaccurate)")
    adjustment_text: Optional[str] = Field(None, description="调整建议")


class UserProfileCreate(UserProfileBase):
    """创建用户画像模型"""
    pass


class UserProfileUpdate(BaseModel):
    """更新用户画像模型"""
    preferences: Optional[Dict[str, Any]] = Field(None, description="用户偏好设置")
    personality_traits: Optional[Dict[str, Any]] = Field(None, description="个性特征分析")
    mood_state: Optional[Dict[str, Any]] = Field(None, description="心情状态分析")
    behavior_patterns: Optional[Dict[str, Any]] = Field(None, description="行为模式分析")
    interest_tags: Optional[List[str]] = Field(None, description="兴趣标签")
    social_preferences: Optional[Dict[str, Any]] = Field(None, description="社交偏好")
    match_preferences: Optional[Dict[str, Any]] = Field(None, description="匹配偏好")
    data_source: Optional[str] = Field(None, description="数据来源")
    confidence_score: Optional[int] = Field(None, description="置信度评分(0-100)")
    update_reason: Optional[str] = Field(None, description="更新原因")
    accuracy_rating: Optional[str] = Field(None, description="准确率评价(accurate, partial, inaccurate)")
    adjustment_text: Optional[str] = Field(None, description="调整建议")


class UserProfileResponse(UserProfileBase):
    """用户画像响应模型"""
    id: str = Field(..., description="画像ID")
    version: int = Field(..., description="数据版本")
    is_active: int = Field(..., description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    
    class Config:
        from_attributes = True


class UserProfileListResponse(BaseModel):
    """用户画像列表响应模型"""
    profiles: List[UserProfileResponse] = Field(..., description="用户画像列表")
    total_count: int = Field(..., description="总数量")
    active_count: int = Field(..., description="激活数量")


class UserProfileAnalysisRequest(BaseModel):
    """用户画像分析请求模型"""
    user_id: str = Field(..., description="用户ID")
    analysis_type: str = Field(..., description="分析类型: preferences, personality, mood, behavior")
    context_data: Optional[Dict[str, Any]] = Field(None, description="上下文数据")


class UserProfileAnalysisResponse(BaseModel):
    """用户画像分析响应模型"""
    user_id: str = Field(..., description="用户ID")
    analysis_type: str = Field(..., description="分析类型")
    results: Dict[str, Any] = Field(..., description="分析结果")
    confidence_score: int = Field(..., description="置信度评分")
    data_source: str = Field(..., description="数据来源")
    generated_at: datetime = Field(..., description="生成时间")