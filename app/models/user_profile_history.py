"""
用户画像历史记录模型
用于存储用户画像的变更历史，支持版本回溯和变更追踪
"""

from sqlalchemy import Column, String, Text, DateTime, JSON, Integer, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid


class UserProfileHistory(Base):
    """用户画像历史记录表"""
    __tablename__ = "user_profile_history"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String(36), ForeignKey("user_profiles.id"), nullable=False, index=True, comment="画像ID")
    user_id = Column(String(36), nullable=False, index=True, comment="用户ID")
    
    # 历史记录版本信息
    version = Column(Integer, nullable=False, comment="版本号")
    change_type = Column(String(50), nullable=False, comment="变更类型: create, update, manual_update, auto_update, review_update")
    
    # 变更前的数据快照
    previous_preferences = Column(JSON, nullable=True, comment="变更前的用户偏好")
    previous_personality_traits = Column(JSON, nullable=True, comment="变更前的个性特征")
    previous_mood_state = Column(JSON, nullable=True, comment="变更前的心情状态")
    previous_behavior_patterns = Column(JSON, nullable=True, comment="变更前的行为模式")
    previous_interest_tags = Column(JSON, nullable=True, comment="变更前的兴趣标签")
    previous_social_preferences = Column(JSON, nullable=True, comment="变更前的社交偏好")
    previous_match_preferences = Column(JSON, nullable=True, comment="变更前的匹配偏好")
    
    # 变更后的数据快照
    current_preferences = Column(JSON, nullable=True, comment="变更后的用户偏好")
    current_personality_traits = Column(JSON, nullable=True, comment="变更后的个性特征")
    current_mood_state = Column(JSON, nullable=True, comment="变更后的心情状态")
    current_behavior_patterns = Column(JSON, nullable=True, comment="变更后的行为模式")
    current_interest_tags = Column(JSON, nullable=True, comment="变更后的兴趣标签")
    current_social_preferences = Column(JSON, nullable=True, comment="变更后的社交偏好")
    current_match_preferences = Column(JSON, nullable=True, comment="变更后的匹配偏好")

    # 用户评价
    accuracy_rating = Column(String(20), nullable=True, comment="准确率评价(accurate, partial, inaccurate)")
    adjustment_text = Column(Text, nullable=True, comment="调整建议")

    # 变更元数据
    change_reason = Column(String(255), nullable=True, comment="变更原因")
    change_source = Column(String(100), nullable=False, comment="变更来源: user, system, admin, llm")
    confidence_score_before = Column(Integer, nullable=True, comment="变更前的置信度评分")
    confidence_score_after = Column(Integer, nullable=True, comment="变更后的置信度评分")
    
    # 变更详情
    changed_fields = Column(JSON, nullable=True, comment="变更的字段列表")
    change_summary = Column(Text, nullable=True, comment="变更摘要")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # 关联关系
    profile = relationship("UserProfile", back_populates="history")


# Pydantic 模型用于API
class UserProfileHistoryBase(BaseModel):
    """用户画像历史记录基础模型"""
    profile_id: str = Field(..., description="画像ID")
    user_id: str = Field(..., description="用户ID")
    version: int = Field(..., description="版本号")
    change_type: str = Field(..., description="变更类型")
    change_reason: Optional[str] = Field(None, description="变更原因")
    change_source: str = Field(..., description="变更来源")
    confidence_score_before: Optional[int] = Field(None, description="变更前的置信度评分")
    confidence_score_after: Optional[int] = Field(None, description="变更后的置信度评分")
    changed_fields: Optional[List[str]] = Field(None, description="变更的字段列表")
    change_summary: Optional[str] = Field(None, description="变更摘要")
    accuracy_rating: Optional[str] = Field(None, description="准确率评价(accurate, partial, inaccurate)")
    adjustment_text: Optional[str] = Field(None, description="调整建议")


class UserProfileHistoryCreate(UserProfileHistoryBase):
    """创建用户画像历史记录模型"""
    # 变更前的数据
    previous_preferences: Optional[Dict[str, Any]] = Field(None, description="变更前的用户偏好")
    previous_personality_traits: Optional[Dict[str, Any]] = Field(None, description="变更前的个性特征")
    previous_mood_state: Optional[Dict[str, Any]] = Field(None, description="变更前的心情状态")
    previous_behavior_patterns: Optional[Dict[str, Any]] = Field(None, description="变更前的行为模式")
    previous_interest_tags: Optional[List[str]] = Field(None, description="变更前的兴趣标签")
    previous_social_preferences: Optional[Dict[str, Any]] = Field(None, description="变更前的社交偏好")
    previous_match_preferences: Optional[Dict[str, Any]] = Field(None, description="变更前的匹配偏好")
    
    # 变更后的数据
    current_preferences: Optional[Dict[str, Any]] = Field(None, description="变更后的用户偏好")
    current_personality_traits: Optional[Dict[str, Any]] = Field(None, description="变更后的个性特征")
    current_mood_state: Optional[Dict[str, Any]] = Field(None, description="变更后的心情状态")
    current_behavior_patterns: Optional[Dict[str, Any]] = Field(None, description="变更后的行为模式")
    current_interest_tags: Optional[List[str]] = Field(None, description="变更后的兴趣标签")
    current_social_preferences: Optional[Dict[str, Any]] = Field(None, description="变更后的社交偏好")
    current_match_preferences: Optional[Dict[str, Any]] = Field(None, description="变更后的匹配偏好")
    
    # 用户评价数据（新增）
    previous_accuracy_rating: Optional[str] = Field(None, description="变更前的准确率评价")
    previous_adjustment_text: Optional[str] = Field(None, description="变更前的调整建议")
    current_accuracy_rating: Optional[str] = Field(None, description="变更后的准确率评价")
    current_adjustment_text: Optional[str] = Field(None, description="变更后的调整建议")


class UserProfileHistoryResponse(UserProfileHistoryBase):
    """用户画像历史记录响应模型"""
    id: str = Field(..., description="历史记录ID")
    created_at: datetime = Field(..., description="创建时间")
    
    # 变更前的数据
    previous_preferences: Optional[Dict[str, Any]] = Field(None, description="变更前的用户偏好")
    previous_personality_traits: Optional[Dict[str, Any]] = Field(None, description="变更前的个性特征")
    previous_mood_state: Optional[Dict[str, Any]] = Field(None, description="变更前的心情状态")
    previous_behavior_patterns: Optional[Dict[str, Any]] = Field(None, description="变更前的行为模式")
    previous_interest_tags: Optional[List[str]] = Field(None, description="变更前的兴趣标签")
    previous_social_preferences: Optional[Dict[str, Any]] = Field(None, description="变更前的社交偏好")
    previous_match_preferences: Optional[Dict[str, Any]] = Field(None, description="变更前的匹配偏好")
    
    # 变更后的数据
    current_preferences: Optional[Dict[str, Any]] = Field(None, description="变更后的用户偏好")
    current_personality_traits: Optional[Dict[str, Any]] = Field(None, description="变更后的个性特征")
    current_mood_state: Optional[Dict[str, Any]] = Field(None, description="变更后的心情状态")
    current_behavior_patterns: Optional[Dict[str, Any]] = Field(None, description="变更后的行为模式")
    current_interest_tags: Optional[List[str]] = Field(None, description="变更后的兴趣标签")
    current_social_preferences: Optional[Dict[str, Any]] = Field(None, description="变更后的社交偏好")
    current_match_preferences: Optional[Dict[str, Any]] = Field(None, description="变更后的匹配偏好")
    
    # 用户评价数据（新增）
    previous_accuracy_rating: Optional[str] = Field(None, description="变更前的准确率评价")
    previous_adjustment_text: Optional[str] = Field(None, description="变更前的调整建议")
    current_accuracy_rating: Optional[str] = Field(None, description="变更后的准确率评价")
    current_adjustment_text: Optional[str] = Field(None, description="变更后的调整建议")
    
    class Config:
        from_attributes = True


class UserProfileHistoryListResponse(BaseModel):
    """用户画像历史记录列表响应模型"""
    history: List[UserProfileHistoryResponse] = Field(..., description="历史记录列表")
    total_count: int = Field(..., description="总数量")
    user_id: str = Field(..., description="用户ID")


class UserProfileComparisonRequest(BaseModel):
    """用户画像对比请求模型"""
    profile_id: str = Field(..., description="画像ID")
    version1: int = Field(..., description="版本1")
    version2: int = Field(..., description="版本2")


class UserProfileComparisonResponse(BaseModel):
    """用户画像对比响应模型"""
    profile_id: str = Field(..., description="画像ID")
    user_id: str = Field(..., description="用户ID")
    version1: int = Field(..., description="版本1")
    version2: int = Field(..., description="版本2")
    version1_data: Dict[str, Any] = Field(..., description="版本1数据")
    version2_data: Dict[str, Any] = Field(..., description="版本2数据")
    differences: Dict[str, Any] = Field(..., description="差异分析")
    change_summary: str = Field(..., description="变更摘要")