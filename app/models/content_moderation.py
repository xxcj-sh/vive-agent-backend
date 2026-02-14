from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ModerationStatus(str, Enum):
    """审核状态枚举"""
    PENDING = "pending"  # 待审核
    PASS = "pass"        # 未违规，通过审核
    REJECT = "reject"    # 违规，拒绝
    REVIEW = "review"    # 需要人工复审

class ContentType(str, Enum):
    """内容类型枚举"""
    USER_CARD = "user_card"      # 用户卡片
    VOTE_CARD = "vote_card"      # 投票卡片
    TOPIC_CARD = "topic_card"    # 话题卡片

class ContentModerationBase(BaseModel):
    """内容审核基础模型"""
    object_id: str = Field(..., description="对象ID，对应用户卡片ID、投票卡片ID、话题卡片ID")
    object_type: ContentType = Field(..., description="对象类型: user_card, vote_card, topic_card")
    
    # 图片审核相关字段
    image_moderation_result: Optional[Dict[str, Any]] = Field(None, description="图片审核结果详情")
    image_status: Optional[ModerationStatus] = Field(None, description="图片审核状态")
    image_trace_id: Optional[str] = Field(None, description="图片审核请求的唯一标识")
    
    # 文本内容审核相关字段
    text_moderation_result: Optional[Dict[str, Any]] = Field(None, description="文本内容审核结果详情")
    text_status: Optional[ModerationStatus] = Field(None, description="文本审核状态")
    text_trace_id: Optional[str] = Field(None, description="文本审核请求的唯一标识")
    
    # 音频/视频审核相关字段
    media_moderation_result: Optional[Dict[str, Any]] = Field(None, description="音视频审核结果详情")
    media_status: Optional[ModerationStatus] = Field(None, description="音视频审核状态")
    media_trace_id: Optional[str] = Field(None, description="音视频审核请求的唯一标识")
    
    # 综合审核状态
    overall_status: ModerationStatus = Field(ModerationStatus.PENDING, description="综合审核状态")
    moderation_remark: Optional[str] = Field(None, description="审核备注信息")
    
    # 回调相关字段
    callback_received: int = Field(0, description="是否已接收回调: 0-未接收, 1-已接收")
    callback_data: Optional[Dict[str, Any]] = Field(None, description="回调数据")
    callback_time: Optional[datetime] = Field(None, description="回调接收时间")
    
    # 审核结果更新时间
    result_updated_at: Optional[datetime] = Field(None, description="审核结果更新时间")

class ContentModerationCreate(ContentModerationBase):
    """创建内容审核记录模型"""
    pass

class ContentModerationUpdate(BaseModel):
    """更新内容审核记录模型"""
    # 图片审核相关字段
    image_moderation_result: Optional[Dict[str, Any]] = Field(None, description="图片审核结果详情")
    image_status: Optional[ModerationStatus] = Field(None, description="图片审核状态")
    image_trace_id: Optional[str] = Field(None, description="图片审核请求的唯一标识")
    
    # 文本内容审核相关字段
    text_moderation_result: Optional[Dict[str, Any]] = Field(None, description="文本内容审核结果详情")
    text_status: Optional[ModerationStatus] = Field(None, description="文本审核状态")
    text_trace_id: Optional[str] = Field(None, description="文本审核请求的唯一标识")
    
    # 音频/视频审核相关字段
    media_moderation_result: Optional[Dict[str, Any]] = Field(None, description="音视频审核结果详情")
    media_status: Optional[ModerationStatus] = Field(None, description="音视频审核状态")
    media_trace_id: Optional[str] = Field(None, description="音视频审核请求的唯一标识")
    
    # 综合审核状态
    overall_status: Optional[ModerationStatus] = Field(None, description="综合审核状态")
    moderation_remark: Optional[str] = Field(None, description="审核备注信息")
    
    # 回调相关字段
    callback_received: Optional[int] = Field(None, description="是否已接收回调: 0-未接收, 1-已接收")
    callback_data: Optional[Dict[str, Any]] = Field(None, description="回调数据")
    callback_time: Optional[datetime] = Field(None, description="回调接收时间")
    
    # 审核结果更新时间
    result_updated_at: Optional[datetime] = Field(None, description="审核结果更新时间")

class ContentModerationResponse(ContentModerationBase):
    """内容审核记录响应模型"""
    id: str = Field(..., description="审核记录ID")
    created_at: Optional[datetime] = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    
    class Config:
        from_attributes = True

class ContentModerationListResponse(BaseModel):
    """内容审核记录列表响应模型"""
    total: int = Field(..., description="总数")
    items: list[ContentModerationResponse] = Field(..., description="审核记录列表")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")

class WeChatModerationCallback(BaseModel):
    """微信内容安全审核回调模型"""
    # 微信回调的基础字段
    ToUserName: str = Field(..., description="开发者微信号")
    FromUserName: str = Field(..., description="发送方帐号")
    CreateTime: int = Field(..., description="消息创建时间")
    MsgType: str = Field(..., description="消息类型")
    Event: str = Field(..., description="事件类型")
    
    # 审核相关字段
    appid: str = Field(..., description="小程序唯一标识")
    trace_id: str = Field(..., description="审核单号")
    status: str = Field(..., description="审核结果: pass, reject, review")
    
    # 详细审核结果
    detail: Optional[list[Dict[str, Any]]] = Field(None, description="详细审核结果")
    errcode: Optional[int] = Field(None, description="错误码")
    errmsg: Optional[str] = Field(None, description="错误信息")
    
    # 额外信息
    extra_info: Optional[Dict[str, Any]] = Field(None, description="额外信息")

class ModerationStatistics(BaseModel):
    """审核统计信息"""
    total_count: int = Field(..., description="总审核数量")
    pending_count: int = Field(..., description="待审核数量")
    pass_count: int = Field(..., description="通过审核数量")
    reject_count: int = Field(..., description="拒绝审核数量")
    review_count: int = Field(..., description="需要复审数量")
    callback_received_count: int = Field(..., description="已接收回调数量")