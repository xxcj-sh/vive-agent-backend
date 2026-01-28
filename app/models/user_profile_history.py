"""
用户画像历史记录模型
用于存储用户画像的变更历史
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class UserProfileHistory(Base):
    """用户画像历史记录表"""
    __tablename__ = "user_profile_history"
    
    id = Column(String(64), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String(64), ForeignKey("user_profiles.id"), nullable=False, index=True, comment="画像ID")
    user_id = Column(String(64), nullable=False, index=True, comment="用户ID")
    
    # 历史记录版本信息
    version = Column(Integer, nullable=False, comment="版本号")
    change_type = Column(String(50), nullable=False, comment="变更类型: create, update, manual_update, auto_update")
    
    # 变更后的数据快照
    current_raw_profile = Column(Text, nullable=True, comment="变更后的原始用户画像数据")
    
    # 变更元数据
    change_reason = Column(String(500), nullable=True, comment="变更原因")
    change_source = Column(String(100), nullable=False, comment="变更来源: user, system, admin, llm")
    
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


class UserProfileHistoryCreate(UserProfileHistoryBase):
    """创建用户画像历史记录模型"""
    current_raw_profile: Optional[str] = Field(None, description="变更后的原始用户画像数据")


class UserProfileHistoryResponse(UserProfileHistoryBase):
    """用户画像历史记录响应模型"""
    id: str = Field(..., description="历史记录ID")
    created_at: datetime = Field(..., description="创建时间")
    current_raw_profile: Optional[str] = Field(None, description="变更后的原始用户画像数据")
    
    class Config:
        from_attributes = True


class UserProfileHistoryListResponse(BaseModel):
    """用户画像历史记录列表响应模型"""
    history: list[UserProfileHistoryResponse] = Field(..., description="历史记录列表")
    total_count: int = Field(..., description="总数量")
    user_id: str = Field(..., description="用户ID")