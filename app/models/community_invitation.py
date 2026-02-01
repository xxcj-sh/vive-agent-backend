from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Index, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum
import uuid


class InvitationStatus(enum.Enum):
    """邀请状态枚举"""
    PENDING = "pending"      # 待使用
    USED = "used"           # 已使用
    EXPIRED = "expired"     # 已过期
    CANCELLED = "cancelled" # 已取消


class CommunityInvitation(Base):
    """社群邀请模型"""
    __tablename__ = "community_invitations"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    code = Column(String(36), unique=True, nullable=False, index=True, comment="邀请码")
    tag_id = Column(Integer, ForeignKey('tags.id', ondelete='CASCADE'), nullable=False, index=True, comment="社群标签ID")
    inviter_user_id = Column(String(36), nullable=False, index=True, comment="邀请人用户ID")
    description = Column(String(255), default='', comment="邀请描述")
    max_uses = Column(Integer, default=1, comment="最大使用次数，NULL表示无限制")
    used_count = Column(Integer, default=0, comment="已使用次数")
    expires_at = Column(DateTime(timezone=True), nullable=True, comment="过期时间")
    status = Column(Enum(InvitationStatus), default=InvitationStatus.PENDING, comment="状态")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 关系
    tag = relationship("Tag", back_populates="invitations")
    usages = relationship("InvitationUsage", back_populates="invitation", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index('idx_invitation_tag_id', 'tag_id'),
        Index('idx_invitation_inviter', 'inviter_user_id'),
        Index('idx_invitation_status', 'status'),
    )


class InvitationUsage(Base):
    """邀请使用记录模型"""
    __tablename__ = "invitation_usage"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    invitation_id = Column(Integer, ForeignKey('community_invitations.id', ondelete='CASCADE'), nullable=False, index=True, comment="邀请ID")
    invited_user_id = Column(String(36), nullable=False, index=True, comment="被邀请用户ID")
    used_at = Column(DateTime(timezone=True), server_default=func.now(), comment="使用时间")
    
    # 关系
    invitation = relationship("CommunityInvitation", back_populates="usages")
    
    # 索引
    __table_args__ = (
        Index('idx_usage_invitation', 'invitation_id'),
        Index('idx_usage_user', 'invited_user_id'),
    )


def create_invitation_code():
    """生成邀请码"""
    return str(uuid.uuid4())
