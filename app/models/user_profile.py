"""
用户画像数据模型
用于存储LLM生成的用户画像数据
"""

from sqlalchemy import Column, String, Text, DateTime, Integer, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import VECTOR
from app.database import Base
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid
import json


class VectorColumn:
    """自定义向量列类型，支持阿里云 RDS MySQL VECTOR 类型"""
    
    @staticmethod
    def create_vector_column(dimension: int = 1024):
        """创建向量列"""
        return Column(VECTOR(dimension), nullable=True, comment=f"用户画像语义向量（{dimension}维）")


# 向量维度配置
VECTOR_DIMENSION = 1024


class UserProfile(Base):
    """用户画像数据表"""
    __tablename__ = "user_profiles"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True, comment="用户ID")

    # 原始画像数据 - 存储LLM生成的完整用户画像
    raw_profile = Column(Text, nullable=True, comment="原始用户画像数据（JSON格式）")

    # 用户画像语义向量 - 使用阿里云 RDS MySQL VECTOR 类型
    raw_profile_embedding = Column(VECTOR(VECTOR_DIMENSION), nullable=True, comment=f"用户画像语义向量（{VECTOR_DIMENSION}维，豆包模型生成）")

    # 生成的总结文本 - LLM生成的自然语言用户画像描述（可直接阅读的文本）
    profile_summary = Column(Text, nullable=True, comment="用户画像总结文本（LLM生成的可读文本）")

    # 更新原因和时间戳
    update_reason = Column(String(500), nullable=True, comment="更新原因")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")

    # 关联关系 - 使用字符串引用避免循环导入
    history = relationship("UserProfileHistory", back_populates="profile", cascade="all, delete-orphan", lazy="selectin")

    # 向量索引 - 使用 HNSW 算法，支持余弦距离检索
    # 注意：阿里云 RDS MySQL 使用 VECTOR INDEX 语法，需通过迁移脚本创建
    # 示例 SQL: VECTOR INDEX idx_embedding(raw_profile_embedding) M=16 DISTANCE=COSINE


# Pydantic 模型用于API
class UserProfileBase(BaseModel):
    """用户画像基础模型"""
    user_id: str = Field(..., description="用户ID")
    raw_profile: Optional[str] = Field(None, description="原始用户画像数据（JSON格式）")
    raw_profile_embedding: Optional[str] = Field(None, description="用户画像语义向量（1024维，豆包模型生成）")
    profile_summary: Optional[str] = Field(None, description="用户画像总结文本（LLM生成的可读文本）")
    update_reason: Optional[str] = Field(None, description="更新原因")


class UserProfileCreate(UserProfileBase):
    """创建用户画像模型"""
    pass


class UserProfileUpdate(BaseModel):
    """更新用户画像模型"""
    raw_profile: Optional[str] = Field(None, description="原始用户画像数据（JSON格式）")
    profile_summary: Optional[str] = Field(None, description="用户画像总结文本（LLM生成的可读文本）")
    update_reason: Optional[str] = Field(None, description="更新原因")


class UserProfileResponse(UserProfileBase):
    """用户画像响应模型"""
    id: str = Field(..., description="画像ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    class Config:
        from_attributes = True


class UserProfileListResponse(BaseModel):
    """用户画像列表响应模型"""
    profiles: list[UserProfileResponse] = Field(..., description="用户画像列表")
    total_count: int = Field(..., description="总数量")