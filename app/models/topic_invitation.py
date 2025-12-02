"""
话题邀请数据模型
用于管理话题邀请功能
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, Enum as SqlEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid
import enum


class InvitationStatus(str, enum.Enum):
    """邀请状态枚举"""
    PENDING = "pending"      # 待处理
    ACCEPTED = "accepted"  # 已接受
    REJECTED = "rejected"  # 已拒绝
    EXPIRED = "expired"    # 已过期


class InvitationType(str, enum.Enum):
    """邀请类型枚举"""
    TOPIC_DISCUSSION = "topic_discussion"  # 话题讨论
    TOPIC_ANSWER = "topic_answer"          # 话题回答


class TopicInvitation(Base):
    """话题邀请数据模型"""
    __tablename__ = "topic_invitations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    topic_id = Column(String(36), ForeignKey("topic_cards.id"), nullable=False, index=True)
    inviter_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    invitee_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    
    # 邀请基本信息
    invitation_type = Column(SqlEnum(InvitationType), nullable=False, default=InvitationType.TOPIC_DISCUSSION)
    is_anonymous = Column(Boolean, default=False, nullable=False)
    inviter_role = Column(String(50), nullable=True)  # 邀请人角色
    invite_mode = Column(String(50), nullable=True)   # 邀请模式：answer_directly 或 participate_directly
    message = Column(Text, nullable=True)  # 邀请留言
    
    # 邀请状态
    status = Column(SqlEnum(InvitationStatus), nullable=False, default=InvitationStatus.PENDING, index=True)
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    expired_at = Column(DateTime, nullable=True)  # 过期时间
    
    # 关系定义
    topic = relationship("TopicCard", foreign_keys=[topic_id], back_populates="invitations")
    inviter = relationship("User", foreign_keys=[inviter_id], back_populates="sent_topic_invitations")
    invitee = relationship("User", foreign_keys=[invitee_id], back_populates="received_topic_invitations")


# Pydantic 模型用于API
class TopicInvitationBase(BaseModel):
    """话题邀请基础模型"""
    topic_id: str = Field(..., description="话题ID")
    invitee_id: str = Field(..., description="被邀请人ID")
    invitation_type: InvitationType = Field(default=InvitationType.TOPIC_DISCUSSION, description="邀请类型")
    is_anonymous: bool = Field(default=False, description="是否匿名邀请")
    inviter_role: Optional[str] = Field(None, description="邀请人角色")
    invite_mode: Optional[str] = Field(None, description="邀请模式")
    message: Optional[str] = Field(None, description="邀请留言")


class TopicInvitationCreate(TopicInvitationBase):
    """创建话题邀请模型"""
    pass


class TopicInvitationUpdate(BaseModel):
    """更新话题邀请模型"""
    status: Optional[InvitationStatus] = Field(None, description="邀请状态")
    message: Optional[str] = Field(None, description="邀请留言")


class TopicInvitationResponse(BaseModel):
    """话题邀请响应模型"""
    id: str = Field(..., description="邀请ID")
    topic_id: str = Field(..., description="话题ID")
    topic_title: Optional[str] = Field(None, description="话题标题")
    inviter_id: str = Field(..., description="邀请人ID")
    inviter_name: Optional[str] = Field(None, description="邀请人姓名")
    inviter_avatar: Optional[str] = Field(None, description="邀请人头像")
    invitee_id: str = Field(..., description="被邀请人ID")
    invitee_name: Optional[str] = Field(None, description="被邀请人姓名")
    invitation_type: InvitationType = Field(..., description="邀请类型")
    is_anonymous: bool = Field(..., description="是否匿名邀请")
    inviter_role: Optional[str] = Field(None, description="邀请人角色")
    invite_mode: Optional[str] = Field(None, description="邀请模式")
    message: Optional[str] = Field(None, description="邀请留言")
    status: InvitationStatus = Field(..., description="邀请状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    expired_at: Optional[datetime] = Field(None, description="过期时间")
    
    class Config:
        from_attributes = True


class TopicInvitationListResponse(BaseModel):
    """话题邀请列表响应模型"""
    invitations: List[TopicInvitationResponse] = Field(..., description="邀请列表")
    total_count: int = Field(..., description="总数量")
    pending_count: int = Field(..., description="待处理数量")
    accepted_count: int = Field(..., description="已接受数量")
    rejected_count: int = Field(..., description="已拒绝数量")
    expired_count: int = Field(..., description="已过期数量")