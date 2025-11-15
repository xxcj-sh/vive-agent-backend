"""
AI分身技能数据模型
用于管理AI分身可配置的技能
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class AISkill(Base):
    """AI分身技能表"""
    __tablename__ = "ai_skills"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, comment="技能名称")
    skill_type = Column(String(50), nullable=False, comment="技能类型：activity_arrangement, coffee_booking, etc.")
    description = Column(Text, nullable=True, comment="技能描述")
    icon_url = Column(String(500), nullable=True, comment="技能图标URL")
    is_active = Column(Boolean, default=True, comment="是否启用")
    sort_order = Column(Integer, default=0, comment="排序")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")


class UserCardSkill(Base):
    """用户卡片技能关联表"""
    __tablename__ = "user_card_skills"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_card_id = Column(String(36), ForeignKey("user_cards.id"), nullable=False, comment="用户卡片ID")
    skill_id = Column(String(36), ForeignKey("ai_skills.id"), nullable=False, comment="技能ID")
    is_enabled = Column(Boolean, default=True, comment="是否启用")
    skill_config = Column(Text, nullable=True, comment="技能配置JSON")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")


# Pydantic 模型用于API
class AISkillBase(BaseModel):
    """AI技能基础模型"""
    name: str = Field(..., description="技能名称")
    skill_type: str = Field(..., description="技能类型")
    description: Optional[str] = Field(None, description="技能描述")
    icon_url: Optional[str] = Field(None, description="技能图标URL")
    is_active: Optional[bool] = Field(True, description="是否启用")
    sort_order: Optional[int] = Field(0, description="排序")


class AISkillCreate(AISkillBase):
    """创建AI技能模型"""
    pass


class AISkillUpdate(BaseModel):
    """更新AI技能模型"""
    name: Optional[str] = Field(None, description="技能名称")
    description: Optional[str] = Field(None, description="技能描述")
    icon_url: Optional[str] = Field(None, description="技能图标URL")
    is_active: Optional[bool] = Field(None, description="是否启用")
    sort_order: Optional[int] = Field(None, description="排序")


class AISkillResponse(AISkillBase):
    """AI技能响应模型"""
    id: str = Field(..., description="技能ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    class Config:
        from_attributes = True


class UserCardSkillBase(BaseModel):
    """用户卡片技能关联基础模型"""
    user_card_id: str = Field(..., description="用户卡片ID")
    skill_id: str = Field(..., description="技能ID")
    is_enabled: Optional[bool] = Field(True, description="是否启用")
    skill_config: Optional[str] = Field(None, description="技能配置JSON")


class UserCardSkillCreate(UserCardSkillBase):
    """创建用户卡片技能关联模型"""
    pass


class UserCardSkillUpdate(BaseModel):
    """更新用户卡片技能关联模型"""
    is_enabled: Optional[bool] = Field(None, description="是否启用")
    skill_config: Optional[str] = Field(None, description="技能配置JSON")


class UserCardSkillResponse(UserCardSkillBase):
    """用户卡片技能关联响应模型"""
    id: str = Field(..., description="关联ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    # 关联的技能信息
    skill: Optional[AISkillResponse] = Field(None, description="技能信息")

    class Config:
        from_attributes = True


class UserCardSkillListResponse(BaseModel):
    """用户卡片技能关联列表响应模型"""
    skills: List[UserCardSkillResponse] = Field(..., description="技能列表")
    total_count: int = Field(..., description="总数量")


# 咖啡店推荐相关模型
class CoffeeShopRecommendation(BaseModel):
    """咖啡店推荐模型"""
    name: str = Field(..., description="咖啡店名称")
    address: str = Field(..., description="地址")
    distance: str = Field(..., description="距离")
    walking_time: str = Field(..., description="步行时间")
    rating: float = Field(..., description="评分")
    price_range: str = Field(..., description="价格区间")
    coffee_types: List[str] = Field(..., description="咖啡类型")
    features: List[str] = Field(..., description="特色功能")
    image: str = Field(..., description="图片URL")
    location: Dict[str, float] = Field(..., description="地理位置")
    recommendation_reason: str = Field(..., description="推荐理由")
    match_score: int = Field(..., description="匹配分数，基于用户画像计算")
    atmosphere_tags: List[str] = Field(default_factory=list, description="氛围标签")
    crowd_type: str = Field(..., description="人群类型")
    best_visit_time: str = Field(..., description="最佳访问时间")


class CoffeeShopRecommendationRequest(BaseModel):
    """咖啡店推荐请求模型"""
    user_card_id: str = Field(..., description="用户卡片ID")
    location: str = Field(..., description="目标地点")
    preferred_time: Optional[str] = Field(None, description="偏好时间")
    coffee_preferences: Optional[List[str]] = Field(None, description="咖啡偏好")
    atmosphere_preferences: Optional[List[str]] = Field(None, description="氛围偏好")
    budget_range: Optional[str] = Field(None, description="预算范围")
    max_distance: Optional[int] = Field(1000, description="最大距离（米）")


class CoffeeShopRecommendationResponse(BaseModel):
    """咖啡店推荐响应模型"""
    main_recommendation: CoffeeShopRecommendation = Field(..., description="主要推荐")
    alternative_options: List[CoffeeShopRecommendation] = Field(..., description="备选推荐")
    user_profile_match: Dict[str, Any] = Field(..., description="用户画像匹配分析")
    recommendation_strategy: str = Field(..., description="推荐策略说明")
    total_found: int = Field(..., description="找到的咖啡店总数")
