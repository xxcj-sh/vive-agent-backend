"""
匹配服务的数据模型和枚举类型
"""

from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class MatchActionType(Enum):
    """匹配操作类型枚举"""
    LIKE = "like"
    SUPER_LIKE = "super_like"
    COLLECTION = "collection"
    REJECT = "reject"
    MUTUAL_MATCH = "mutual_match"
    AI_RECOMMEND_AFTER_USER_CHAT = "ai_recommend_after_user_chat"
    AI_RECOMMEND_BY_SYSTEM = "ai_recommend_by_system"


class MatchStatus(Enum):
    """匹配状态枚举"""
    PENDING = "pending"
    MATCHED = "matched"
    REJECTED = "rejected"
    EXPIRED = "expired"
    ALL = "all"


class MatchResult(BaseModel):
    """匹配结果数据类"""
    is_match: bool = Field(..., description="是否匹配成功")
    match_id: Optional[str] = Field(None, description="匹配ID")
    action_id: Optional[str] = Field(None, description="操作ID")
    message: str = Field("", description="匹配消息")
    existing_action: Optional[str] = Field(None, description="已存在的操作类型")
    source: str = Field("user", description="操作来源")


class MatchCard(BaseModel):
    """匹配卡片数据类"""
    id: str = Field(..., description="卡片ID")
    user_id: str = Field(..., description="用户ID")
    name: str = Field(..., description="姓名")
    avatar: Optional[str] = Field(None, description="头像URL")
    age: int = Field(25, description="年龄")
    occupation: str = Field("", description="职业")
    location: str = Field("", description="位置")
    bio: str = Field("", description="个人简介")
    interests: list = Field(default_factory=list, description="兴趣爱好")
    scene_type: str = Field("", description="场景类型")
    user_role: str = Field("", description="用户角色")
    created_at: str = Field("", description="创建时间")
    match_score: int = Field(75, description="匹配分数")
    additional_fields: Dict[str, Any] = Field(default_factory=dict, description="额外字段")


class MatchStatistics(BaseModel):
    """匹配统计数据类"""
    total_actions: int = Field(..., description="总操作数")
    action_breakdown: Dict[str, int] = Field(..., description="操作类型分布")
    ai_recommendations: int = Field(..., description="AI推荐数")
    period: str = Field(..., description="统计周期")


class AIRecommendation(BaseModel):
    """AI推荐数据类"""
    id: str = Field(..., description="推荐ID")
    target_user_id: str = Field(..., description="目标用户ID")
    target_card_id: str = Field(..., description="目标卡片ID")
    action_type: str = Field(..., description="操作类型")
    scene_context: Optional[str] = Field(None, description="场景上下文")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    created_at: str = Field("", description="创建时间")
    target_user: Optional[Dict[str, Any]] = Field(None, description="目标用户信息")