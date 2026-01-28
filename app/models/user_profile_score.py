"""
用户画像评分数据模型
用于存储用户画像的评分、历史记录和技能解锁状态
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import enum


class ScoreType(str, enum.Enum):
    """评分类型枚举"""
    COMPLETENESS = "completeness"  # 完整度评分
    ACCURACY = "accuracy"  # 准确度评分
    ACTIVITY = "activity"  # 活跃度评分
    CREDIBILITY = "credibility"  # 可信度评分
    OVERALL = "overall"  # 总体评分


class SkillLevel(str, enum.Enum):
    """技能等级枚举"""
    LOCKED = "locked"  # 未解锁
    UNLOCKED = "unlocked"  # 已解锁
    ACTIVE = "active"  # 已激活


class UserProfileScore(Base):
    """
    用户画像评分表
    存储用户当前的画像评分信息
    """
    __tablename__ = "user_profile_scores"
    
    id = Column(String(64), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(64), nullable=False, index=True, unique=True, comment="用户ID")
    
    # 各维度评分 (0-100)
    completeness_score = Column(Integer, default=0, comment="完整度评分(0-100)")  # 画像完整性
    accuracy_score = Column(Integer, default=0, comment="准确度评分(0-100)")  # 用户确认的准确度
    activity_score = Column(Integer, default=0, comment="活跃度评分(0-100)")  # 用户参与度
    credibility_score = Column(Integer, default=0, comment="可信度评分(0-100)")  # 可信度评分
    
    # 总体评分
    overall_score = Column(Integer, default=0, comment="总体评分(0-100)")  # 综合得分
    
    # 评分组成部分详情
    score_components = Column(JSON, default=dict, comment="评分组成部分详情")  # 记录各部分得分详情
    
    # 上次更新时间
    last_score_update = Column(DateTime(timezone=True), onupdate=func.now(), comment="评分更新时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # 关联关系
    history = relationship("UserProfileScoreHistory", back_populates="current_score", 
                          cascade="all, delete-orphan", lazy="selectin")
    skills = relationship("UserProfileSkill", back_populates="user_score", 
                         cascade="all, delete-orphan", lazy="selectin")


class UserProfileScoreHistory(Base):
    """
    用户画像评分历史记录表
    记录用户评分的变化历史
    """
    __tablename__ = "user_profile_score_history"
    
    id = Column(String(64), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    score_id = Column(String(64), ForeignKey("user_profile_scores.id"), nullable=False, index=True, comment="评分ID")
    user_id = Column(String(64), nullable=False, index=True, comment="用户ID")
    
    # 评分变化记录
    completeness_score = Column(Integer, nullable=False, comment="完整度评分")
    accuracy_score = Column(Integer, nullable=False, comment="准确度评分")
    activity_score = Column(Integer, nullable=False, comment="活跃度评分")
    credibility_score = Column(Integer, nullable=False, comment="可信度评分")
    overall_score = Column(Integer, nullable=False, comment="总体评分")
    
    # 变化原因和触发事件
    change_reason = Column(String(255), nullable=True, comment="评分变化原因")
    trigger_event = Column(String(100), nullable=True, comment="触发事件")
    
    # 记录时间
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), comment="记录时间")
    
    # 关联关系
    current_score = relationship("UserProfileScore", back_populates="history")


class UserProfileSkill(Base):
    """
    用户画像技能解锁表
    记录用户已解锁的AI技能
    """
    __tablename__ = "user_profile_skills"
    
    id = Column(String(64), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    score_id = Column(String(64), ForeignKey("user_profile_scores.id"), nullable=False, index=True, comment="评分ID")
    user_id = Column(String(64), nullable=False, index=True, comment="用户ID")
    
    # 技能信息
    skill_code = Column(String(50), nullable=False, index=True, comment="技能代码")
    skill_name = Column(String(100), nullable=False, comment="技能名称")
    skill_description = Column(String(500), nullable=True, comment="技能描述")
    
    # 技能状态
    skill_level = Column(Enum(SkillLevel), default=SkillLevel.LOCKED, nullable=False, comment="技能状态")
    unlock_threshold = Column(Integer, nullable=False, default=0, comment="解锁所需分数")
    
    # 解锁信息
    unlocked_at = Column(DateTime(timezone=True), nullable=True, comment="解锁时间")
    activated_at = Column(DateTime(timezone=True), nullable=True, comment="激活时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    
    # 关联关系
    user_score = relationship("UserProfileScore", back_populates="skills")


# Pydantic 模型用于API

class UserProfileScoreBase(BaseModel):
    """用户画像评分基础模型"""
    user_id: str = Field(..., description="用户ID")
    completeness_score: Optional[int] = Field(0, description="完整度评分(0-100)")
    accuracy_score: Optional[int] = Field(0, description="准确度评分(0-100)")
    activity_score: Optional[int] = Field(0, description="活跃度评分(0-100)")
    credibility_score: Optional[int] = Field(0, description="可信度评分(0-100)")
    overall_score: Optional[int] = Field(0, description="总体评分(0-100)")
    score_components: Optional[Dict[str, Any]] = Field(default_factory=dict, description="评分组成部分详情")


class UserProfileScoreCreate(UserProfileScoreBase):
    """创建用户画像评分模型"""
    pass


class UserProfileScoreUpdate(BaseModel):
    """更新用户画像评分模型"""
    completeness_score: Optional[int] = Field(None, ge=0, le=100, description="完整度评分(0-100)")
    accuracy_score: Optional[int] = Field(None, ge=0, le=100, description="准确度评分(0-100)")
    activity_score: Optional[int] = Field(None, ge=0, le=100, description="活跃度评分(0-100)")
    credibility_score: Optional[int] = Field(None, ge=0, le=100, description="可信度评分(0-100)")
    overall_score: Optional[int] = Field(None, ge=0, le=100, description="总体评分(0-100)")
    score_components: Optional[Dict[str, Any]] = Field(None, description="评分组成部分详情")
    change_reason: Optional[str] = Field(None, description="评分变化原因")
    trigger_event: Optional[str] = Field(None, description="触发事件")


class UserProfileScoreResponse(UserProfileScoreBase):
    """用户画像评分响应模型"""
    id: str = Field(..., description="评分ID")
    last_score_update: Optional[datetime] = Field(None, description="评分更新时间")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True


class UserProfileScoreHistoryResponse(BaseModel):
    """用户画像评分历史响应模型"""
    id: str = Field(..., description="历史记录ID")
    score_id: str = Field(..., description="评分ID")
    user_id: str = Field(..., description="用户ID")
    completeness_score: int = Field(..., description="完整度评分")
    accuracy_score: int = Field(..., description="准确度评分")
    activity_score: int = Field(..., description="活跃度评分")
    credibility_score: int = Field(..., description="可信度评分")
    overall_score: int = Field(..., description="总体评分")
    change_reason: Optional[str] = Field(None, description="评分变化原因")
    trigger_event: Optional[str] = Field(None, description="触发事件")
    recorded_at: datetime = Field(..., description="记录时间")
    
    class Config:
        from_attributes = True


class UserProfileSkillBase(BaseModel):
    """用户画像技能基础模型"""
    skill_code: str = Field(..., description="技能代码")
    skill_name: str = Field(..., description="技能名称")
    skill_description: Optional[str] = Field(None, description="技能描述")
    unlock_threshold: int = Field(..., ge=0, le=100, description="解锁所需分数")


class UserProfileSkillCreate(UserProfileSkillBase):
    """创建用户画像技能模型"""
    user_id: str = Field(..., description="用户ID")


class UserProfileSkillUpdate(BaseModel):
    """更新用户画像技能模型"""
    skill_level: Optional[SkillLevel] = Field(None, description="技能状态")


class UserProfileSkillResponse(UserProfileSkillBase):
    """用户画像技能响应模型"""
    id: str = Field(..., description="技能ID")
    user_id: str = Field(..., description="用户ID")
    skill_level: SkillLevel = Field(..., description="技能状态")
    unlocked_at: Optional[datetime] = Field(None, description="解锁时间")
    activated_at: Optional[datetime] = Field(None, description="激活时间")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True


class UserProfileScoreOverview(BaseModel):
    """用户画像评分概览模型"""
    user_id: str = Field(..., description="用户ID")
    current_scores: UserProfileScoreResponse = Field(..., description="当前评分")
    recent_history: List[UserProfileScoreHistoryResponse] = Field(default_factory=list, description="近期评分历史")
    unlocked_skills: List[UserProfileSkillResponse] = Field(default_factory=list, description="已解锁技能")
    locked_skills: List[UserProfileSkillResponse] = Field(default_factory=list, description="未解锁技能")
    
    class Config:
        from_attributes = True


class ScoreCalculationRequest(BaseModel):
    """评分计算请求模型"""
    user_id: str = Field(..., description="用户ID")
    profile_data: Optional[Dict[str, Any]] = Field(None, description="用户画像数据")
    force_recalculation: bool = Field(False, description="是否强制重新计算")


class ScoreCalculationResponse(BaseModel):
    """评分计算响应模型"""
    user_id: str = Field(..., description="用户ID")
    new_scores: UserProfileScoreResponse = Field(..., description="计算后的新评分")
    score_changes: Dict[str, int] = Field(default_factory=dict, description="评分变化")
    newly_unlocked_skills: List[UserProfileSkillResponse] = Field(default_factory=list, description="新解锁的技能")