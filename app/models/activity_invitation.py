"""
活动邀约数据模型
用于管理AI分身活动邀约功能
"""

from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, ForeignKey, Enum as SqlEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid
import enum


class InvitationStatus(enum.Enum):
    """邀约状态"""
    PENDING = "pending"  # 待确认
    ACCEPTED = "accepted"  # 已接受
    DECLINED = "declined"  # 已拒绝
    CANCELLED = "cancelled"  # 已取消
    EXPIRED = "expired"  # 已过期


class ActivityType(enum.Enum):
    """活动类型"""
    COFFEE = "coffee"  # 约咖啡
    MEAL = "meal"  # 约饭
    MOVIE = "movie"  # 看电影
    SPORT = "sport"  # 运动
    SHOPPING = "shopping"  # 购物
    TRAVEL = "travel"  # 旅游
    OTHER = "other"  # 其他


class ActivityInvitation(Base):
    """活动邀约表"""
    __tablename__ = "activity_invitations"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    invitation_code = Column(String(50), unique=True, nullable=False, comment="邀约码")
    inviter_id = Column(String(36), ForeignKey("users.id"), nullable=False, comment="发起人ID")
    inviter_name = Column(String(100), nullable=False, comment="发起人姓名")
    inviter_avatar = Column(String(500), nullable=True, comment="发起人头像")

    user_card_id = Column(String(36), ForeignKey("user_cards.id"), nullable=False, comment="AI分身ID")
    card_owner_id = Column(String(36), ForeignKey("users.id"), nullable=False, comment="卡片主人ID")

    activity_type = Column(SqlEnum(ActivityType), nullable=False, comment="活动类型")
    activity_title = Column(String(200), nullable=False, comment="活动标题")
    activity_description = Column(Text, nullable=True, comment="活动描述")

    # 活动详情
    proposed_time = Column(DateTime(timezone=True), nullable=True, comment="建议时间")
    proposed_location = Column(String(200), nullable=True, comment="建议地点")
    location_details = Column(Text, nullable=True, comment="地点详情")
    estimated_duration = Column(Integer, nullable=True, comment="预计时长（分钟）")

    # 邀约信息
    invitation_message = Column(Text, nullable=True, comment="邀约留言")
    status = Column(SqlEnum(InvitationStatus), default=InvitationStatus.PENDING, comment="邀约状态")
    expires_at = Column(DateTime(timezone=True), nullable=True, comment="过期时间")

    # 确认信息
    confirmed_time = Column(DateTime(timezone=True), nullable=True, comment="确认时间")
    response_message = Column(Text, nullable=True, comment="回复留言")

    # LLM推荐信息
    llm_recommendations = Column(Text, nullable=True, comment="LLM推荐信息（JSON格式）")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")


class ActivityParticipant(Base):
    """活动参与者表"""
    __tablename__ = "activity_participants"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    invitation_id = Column(String(36), ForeignKey("activity_invitations.id"), nullable=False, comment="邀约ID")
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, comment="用户ID")
    user_name = Column(String(100), nullable=False, comment="用户姓名")
    user_avatar = Column(String(500), nullable=True, comment="用户头像")
    role = Column(String(20), nullable=False, comment="角色：inviter（发起人）, owner（主人）")
    is_confirmed = Column(Boolean, default=False, comment="是否确认")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")


class ActivityLocation(Base):
    """活动地点推荐表"""
    __tablename__ = "activity_locations"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    invitation_id = Column(String(36), ForeignKey("activity_invitations.id"), nullable=False, comment="邀约ID")
    location_name = Column(String(200), nullable=False, comment="地点名称")
    location_address = Column(String(500), nullable=False, comment="地点地址")
    location_type = Column(String(50), nullable=True, comment="地点类型")
    distance = Column(String(50), nullable=True, comment="距离")
    rating = Column(Integer, nullable=True, comment="评分（1-5）")
    price_level = Column(Integer, nullable=True, comment="价格等级（1-4）")
    opening_hours = Column(Text, nullable=True, comment="营业时间")
    phone = Column(String(50), nullable=True, comment="电话")
    recommendation_reason = Column(Text, nullable=True, comment="推荐理由")
    is_selected = Column(Boolean, default=False, comment="是否被选中")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")


# Pydantic 模型用于API
class ActivityInvitationBase(BaseModel):
    """活动邀约基础模型"""
    user_card_id: str = Field(..., description="AI分身ID")
    activity_type: str = Field(..., description="活动类型")
    activity_title: str = Field(..., description="活动标题")
    activity_description: Optional[str] = Field(None, description="活动描述")
    proposed_time: Optional[datetime] = Field(None, description="建议时间")
    proposed_location: Optional[str] = Field(None, description="建议地点")
    location_details: Optional[str] = Field(None, description="地点详情")
    estimated_duration: Optional[int] = Field(None, description="预计时长（分钟）")
    invitation_message: Optional[str] = Field(None, description="邀约留言")
    llm_recommendations: Optional[str] = Field(None, description="LLM推荐信息（JSON格式）")


class ActivityInvitationCreate(ActivityInvitationBase):
    """创建活动邀约模型"""
    pass


class ActivityInvitationUpdate(BaseModel):
    """更新活动邀约模型"""
    activity_title: Optional[str] = Field(None, description="活动标题")
    activity_description: Optional[str] = Field(None, description="活动描述")
    proposed_time: Optional[datetime] = Field(None, description="建议时间")
    proposed_location: Optional[str] = Field(None, description="建议地点")
    location_details: Optional[str] = Field(None, description="地点详情")
    estimated_duration: Optional[int] = Field(None, description="预计时长（分钟）")
    invitation_message: Optional[str] = Field(None, description="邀约留言")


class ActivityInvitationResponse(ActivityInvitationBase):
    """活动邀约响应模型"""
    id: str = Field(..., description="邀约ID")
    invitation_code: str = Field(..., description="邀约码")
    inviter_id: str = Field(..., description="发起人ID")
    inviter_name: str = Field(..., description="发起人姓名")
    inviter_avatar: Optional[str] = Field(None, description="发起人头像")
    card_owner_id: str = Field(..., description="卡片主人ID")
    status: str = Field(..., description="邀约状态")
    confirmed_time: Optional[datetime] = Field(None, description="确认时间")
    response_message: Optional[str] = Field(None, description="回复留言")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    class Config:
        from_attributes = True


class ActivityInvitationListResponse(BaseModel):
    """活动邀约列表响应模型"""
    invitations: List[ActivityInvitationResponse] = Field(..., description="邀约列表")
    total_count: int = Field(..., description="总数量")
    pending_count: int = Field(..., description="待确认数量")
    accepted_count: int = Field(..., description="已接受数量")


class ActivityInvitationAction(BaseModel):
    """活动邀约操作模型"""
    response_message: Optional[str] = Field(None, description="回复留言")


class LocationRecommendation(BaseModel):
    """地点推荐模型"""
    name: str = Field(..., description="地点名称")
    address: str = Field(..., description="地点地址")
    type: Optional[str] = Field(None, description="地点类型")
    distance: Optional[str] = Field(None, description="距离")
    rating: Optional[int] = Field(None, description="评分（1-5）")
    price_level: Optional[int] = Field(None, description="价格等级（1-4）")
    opening_hours: Optional[str] = Field(None, description="营业时间")
    phone: Optional[str] = Field(None, description="电话")
    recommendation_reason: Optional[str] = Field(None, description="推荐理由")


class CoffeeRecommendationRequest(BaseModel):
    """咖啡推荐请求模型"""
    user_card_id: str = Field(..., description="AI分身ID")
    time_preference: Optional[str] = Field(None, description="时间偏好")
    location_preference: Optional[str] = Field(None, description="地点偏好")
    budget_range: Optional[str] = Field(None, description="预算范围")
    coffee_type: Optional[str] = Field(None, description="咖啡类型偏好")
    atmosphere: Optional[str] = Field(None, description="氛围偏好")


class CoffeeRecommendationResponse(BaseModel):
    """咖啡推荐响应模型"""
    locations: List[LocationRecommendation] = Field(..., description="推荐地点列表")
    coffee_suggestions: List[str] = Field(..., description="推荐咖啡列表")
    summary: str = Field(..., description="推荐总结")
