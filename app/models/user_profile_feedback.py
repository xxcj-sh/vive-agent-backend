"""
用户画像反馈评价数据模型
用于存储用户对画像的反馈评价，支持LLM基于反馈更新画像
"""

from sqlalchemy import Column, String, Text, DateTime, JSON, Integer, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid


class UserProfileFeedback(Base):
    """用户画像反馈评价表"""
    __tablename__ = "user_profile_feedback"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    profile_id = Column(String(36), ForeignKey("user_profiles.id"), nullable=False, index=True)
    
    # 评价信息
    rating = Column(Integer, nullable=False)  # 1-5分
    evaluation_type = Column(String(50), nullable=False, default="overall")  # 评价类型
    comment = Column(Text)  # 评价备注
    tags = Column(JSON)  # 评价标签列表
    
    # 用户反馈的具体内容
    feedback_content = Column(JSON)  # 详细的反馈内容，包括用户指出的具体问题
    suggested_improvements = Column(JSON)  # 用户建议的改进点
    
    # 处理状态
    is_processed = Column(Boolean, default=False, index=True)  # 是否已处理
    processed_at = Column(DateTime)  # 处理时间
    processing_result = Column(JSON)  # 处理结果
    
    # 关联的用户画像更新
    updated_profile_id = Column(String(36), ForeignKey("user_profiles.id"))  # 更新后的画像ID
    
    # 时间戳
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关联关系
    user = relationship("User", foreign_keys=[user_id], backref="profile_feedback")
    profile = relationship("UserProfile", foreign_keys=[profile_id], backref="feedback")
    updated_profile = relationship("UserProfile", foreign_keys=[updated_profile_id])


# Pydantic 模型用于API
class UserProfileFeedbackBase(BaseModel):
    """用户画像反馈评价基础模型"""
    user_id: str = Field(..., description="用户ID")
    profile_id: str = Field(..., description="画像ID")
    rating: int = Field(..., ge=1, le=5, description="评分，1-5分")
    evaluation_type: str = Field(default="overall", description="评价类型")
    comment: Optional[str] = Field(None, description="评价备注")
    tags: Optional[List[str]] = Field(None, description="评价标签")
    feedback_content: Optional[Dict[str, Any]] = Field(None, description="详细反馈内容")
    suggested_improvements: Optional[List[str]] = Field(None, description="建议改进点")


class UserProfileFeedbackCreate(UserProfileFeedbackBase):
    """创建用户画像反馈评价请求模型"""
    pass


class UserProfileFeedbackUpdate(BaseModel):
    """更新用户画像反馈评价请求模型"""
    is_processed: Optional[bool] = Field(None, description="是否已处理")
    processed_at: Optional[datetime] = Field(None, description="处理时间")
    processing_result: Optional[Dict[str, Any]] = Field(None, description="处理结果")
    updated_profile_id: Optional[str] = Field(None, description="更新后的画像ID")


class UserProfileFeedbackResponse(UserProfileFeedbackBase):
    """用户画像反馈评价响应模型"""
    id: str = Field(..., description="反馈ID")
    is_processed: bool = Field(..., description="是否已处理")
    processed_at: Optional[datetime] = Field(None, description="处理时间")
    processing_result: Optional[Dict[str, Any]] = Field(None, description="处理结果")
    updated_profile_id: Optional[str] = Field(None, description="更新后的画像ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    
    class Config:
        from_attributes = True


class UserProfileFeedbackListResponse(BaseModel):
    """用户画像反馈评价列表响应模型"""
    feedbacks: List[UserProfileFeedbackResponse] = Field(..., description="反馈列表")
    total_count: int = Field(..., description="总数量")
    unprocessed_count: int = Field(..., description="未处理数量")


class UserProfileFeedbackProcessingRequest(BaseModel):
    """用户画像反馈处理请求模型"""
    feedback_ids: List[str] = Field(..., description="要处理的反馈ID列表")
    processing_mode: str = Field(default="batch", description="处理模式: single, batch")
    auto_approve: bool = Field(default=False, description="是否自动批准更新")


class UserProfileFeedbackProcessingResponse(BaseModel):
    """用户画像反馈处理响应模型"""
    processed_count: int = Field(..., description="处理数量")
    success_count: int = Field(..., description="成功数量")
    failure_count: int = Field(..., description="失败数量")
    processing_results: List[Dict[str, Any]] = Field(..., description="详细处理结果")