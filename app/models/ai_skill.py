"""
AI分身技能数据模型
用于管理AI分身可配置的技能
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from pydantic import BaseModel, Field
from typing import Optional, List
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
