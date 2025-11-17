from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class TriggerCondition(BaseModel):
    """触发条件模型"""
    condition_type: str = Field(..., description="条件类型: time, keyword, participant_count, manual")
    condition_value: Optional[Dict[str, Any]] = Field(None, description="条件值")
    is_enabled: int = Field(1, description="是否启用")

class TopicCardBase(BaseModel):
    """话题卡片基础模型"""
    title: str = Field(..., description="话题标题", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="话题描述", max_length=1000)
    discussion_goal: Optional[str] = Field(None, description="讨论目标/期待", max_length=500)
    category: Optional[str] = Field(None, description="话题分类", max_length=50)
    tags: Optional[List[str]] = Field(default_factory=list, description="话题标签")
    cover_image: Optional[str] = Field(None, description="封面图片URL")
    visibility: str = Field("public", description="可见性: public, private")
    trigger_conditions: Optional[List[TriggerCondition]] = Field(default_factory=list, description="触发条件列表")

class TopicCardCreate(TopicCardBase):
    """创建话题卡片模型"""
    pass

class TopicCardUpdate(BaseModel):
    """更新话题卡片模型"""
    title: Optional[str] = Field(None, description="话题标题", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="话题描述", max_length=1000)
    discussion_goal: Optional[str] = Field(None, description="讨论目标/期待", max_length=500)
    category: Optional[str] = Field(None, description="话题分类", max_length=50)
    tags: Optional[List[str]] = Field(None, description="话题标签")
    cover_image: Optional[str] = Field(None, description="封面图片URL")
    visibility: Optional[str] = Field(None, description="可见性: public, private")
    is_active: Optional[int] = Field(None, description="是否激活")

class TopicCardResponse(BaseModel):
    """话题卡片响应模型"""
    id: str = Field(..., description="话题卡片ID")
    user_id: str = Field(..., description="创建者用户ID")
    title: str = Field(..., description="话题标题")
    description: Optional[str] = Field(None, description="话题描述")
    discussion_goal: Optional[str] = Field(None, description="讨论目标/期待")
    category: Optional[str] = Field(None, description="话题分类")
    tags: Optional[List[str]] = Field(default_factory=list, description="话题标签")
    cover_image: Optional[str] = Field(None, description="封面图片URL")
    visibility: str = Field(..., description="可见性")
    is_active: int = Field(..., description="是否激活")
    view_count: int = Field(0, description="浏览次数")
    like_count: int = Field(0, description="点赞次数")
    discussion_count: int = Field(0, description="讨论次数")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    # 创建者信息
    creator_nickname: Optional[str] = Field(None, description="创建者昵称")
    creator_avatar: Optional[str] = Field(None, description="创建者头像")
    trigger_conditions: Optional[List[TriggerCondition]] = Field(default_factory=list, description="触发条件列表")
    
    class Config:
        """Pydantic配置"""
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class TopicCardListResponse(BaseModel):
    """话题卡片列表响应模型"""
    total: int = Field(..., description="总数")
    items: List[TopicCardResponse] = Field(..., description="话题卡片列表")
    page: int = Field(..., description="当前页码")
    pageSize: int = Field(..., description="每页数量")
    totalPages: int = Field(..., description="总页数")

class TriggerConditionResponse(BaseModel):
    """触发条件响应模型"""
    id: str = Field(..., description="触发条件ID")
    topic_card_id: str = Field(..., description="话题卡片ID")
    condition_type: str = Field(..., description="条件类型: time, keyword, participant_count, manual")
    condition_value: Optional[Dict[str, Any]] = Field(None, description="条件值")
    is_enabled: int = Field(1, description="是否启用")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

class TriggerConditionListResponse(BaseModel):
    """触发条件列表响应模型"""
    items: List[TriggerConditionResponse] = Field(..., description="触发条件列表")
    total: int = Field(..., description="总数")

class TopicDiscussionBase(BaseModel):
    """话题讨论基础模型"""
    message: str = Field(..., description="讨论消息内容", min_length=1, max_length=2000)
    message_type: str = Field("text", description="消息类型: text, image, voice")
    is_anonymous: int = Field(1, description="是否匿名")

class TopicDiscussionCreate(TopicDiscussionBase):
    """创建话题讨论模型"""
    topic_card_id: str = Field(..., description="话题卡片ID")

class TopicDiscussionResponse(BaseModel):
    """话题讨论响应模型"""
    id: str = Field(..., description="讨论记录ID")
    topic_card_id: str = Field(..., description="话题卡片ID")
    participant_id: str = Field(..., description="参与者用户ID")
    host_id: str = Field(..., description="话题主持人用户ID")
    message: str = Field(..., description="讨论消息内容")
    message_type: str = Field(..., description="消息类型")
    is_anonymous: int = Field(..., description="是否匿名")
    created_at: datetime = Field(..., description="创建时间")
    # 参与者信息（匿名时不显示）
    participant_nickname: Optional[str] = Field(None, description="参与者昵称")
    participant_avatar: Optional[str] = Field(None, description="参与者头像")

class TopicDiscussionListResponse(BaseModel):
    """话题讨论列表响应模型"""
    total: int = Field(..., description="总数")
    list: List[TopicDiscussionResponse] = Field(..., description="讨论记录列表")