from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid
from enum import Enum as PyEnum

class ModerationStatus(PyEnum):
    """审核状态枚举"""
    PENDING = "pending"  # 待审核
    PASS = "pass"        # 未违规，通过审核
    REJECT = "reject"    # 违规，拒绝
    REVIEW = "review"    # 需要人工复审

class ContentType(PyEnum):
    """内容类型枚举"""
    USER_CARD = "user_card"      # 用户卡片
    VOTE_CARD = "vote_card"      # 投票卡片
    TOPIC_CARD = "topic_card"    # 话题卡片

class ContentModeration(Base):
    """内容审核状态表 - 用于接收回调消息，记录各类卡片中多媒体内容的审核状态"""
    __tablename__ = "content_moderations"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    object_id = Column(String(36), nullable=False, index=True, comment="对象ID，对应用户卡片ID、投票卡片ID、话题卡片ID")
    object_type = Column(String(20), nullable=False, comment="对象类型: user_card, vote_card, topic_card")
    
    # 图片审核相关字段
    image_moderation_result = Column(JSON, nullable=True, comment="图片审核结果详情")
    image_status = Column(String(20), nullable=True, comment="图片审核状态: pending, pass, reject, review")
    image_trace_id = Column(String(100), nullable=True, comment="图片审核请求的唯一标识")
    
    # 文本内容审核相关字段
    text_moderation_result = Column(JSON, nullable=True, comment="文本内容审核结果详情")
    text_status = Column(String(20), nullable=True, comment="文本审核状态: pending, pass, reject, review")
    text_trace_id = Column(String(100), nullable=True, comment="文本审核请求的唯一标识")
    
    # 音频/视频审核相关字段
    media_moderation_result = Column(JSON, nullable=True, comment="音视频审核结果详情")
    media_status = Column(String(20), nullable=True, comment="音视频审核状态: pending, pass, reject, review")
    media_trace_id = Column(String(100), nullable=True, comment="音视频审核请求的唯一标识")
    
    # 综合审核状态
    overall_status = Column(String(20), nullable=False, default="pending", comment="综合审核状态: pending, pass, reject, review")
    moderation_remark = Column(Text, nullable=True, comment="审核备注信息")
    
    # 回调相关字段
    callback_received = Column(Integer, default=0, comment="是否已接收回调: 0-未接收, 1-已接收")
    callback_data = Column(JSON, nullable=True, comment="回调数据")
    callback_time = Column(DateTime(timezone=True), nullable=True, comment="回调接收时间")
    
    # 审核结果更新时间
    result_updated_at = Column(DateTime(timezone=True), nullable=True, comment="审核结果更新时间")
    
    # 基础字段
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")
    
    # 建立联合索引
    __table_args__ = (
        # 唯一索引：object_id + object_type
        {'sqlite_autoincrement': False},
    )

    def __repr__(self):
        return f"<ContentModeration(id='{self.id}', object_id='{self.object_id}', object_type='{self.object_type}', overall_status='{self.overall_status}')>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "object_id": self.object_id,
            "object_type": self.object_type,
            "image_moderation_result": self.image_moderation_result,
            "image_status": self.image_status,
            "image_trace_id": self.image_trace_id,
            "text_moderation_result": self.text_moderation_result,
            "text_status": self.text_status,
            "text_trace_id": self.text_trace_id,
            "media_moderation_result": self.media_moderation_result,
            "media_status": self.media_status,
            "media_trace_id": self.media_trace_id,
            "overall_status": self.overall_status,
            "moderation_remark": self.moderation_remark,
            "callback_received": self.callback_received,
            "callback_data": self.callback_data,
            "callback_time": self.callback_time.isoformat() if self.callback_time else None,
            "result_updated_at": self.result_updated_at.isoformat() if self.result_updated_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def update_overall_status(self):
        """根据各项审核结果更新综合审核状态"""
        statuses = []
        
        if self.image_status:
            statuses.append(self.image_status)
        if self.text_status:
            statuses.append(self.text_status)
        if self.media_status:
            statuses.append(self.media_status)
        
        if not statuses:
            self.overall_status = "pending"
            return
        
        # 如果有任何一项为reject，则综合状态为reject
        if "reject" in statuses:
            self.overall_status = "reject"
        # 如果有任何一项为review，则综合状态为review
        elif "review" in statuses:
            self.overall_status = "review"
        # 如果所有项都为pass，则综合状态为pass
        elif all(status == "pass" for status in statuses):
            self.overall_status = "pass"
        # 如果所有项都为pending，则综合状态为pending
        elif all(status == "pending" for status in statuses):
            self.overall_status = "pending"
        else:
            # 其他情况，如果有pass和其他状态混合，设为review
            self.overall_status = "review"
        
        self.result_updated_at = func.now()