"""
匹配服务的数据模型和枚举类型
"""

from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass


class MatchActionType(Enum):
    """匹配操作类型枚举"""
    LIKE = "like"
    SUPER_LIKE = "super_like"
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


@dataclass
class MatchResult:
    """匹配结果数据类"""
    is_match: bool
    match_id: Optional[str] = None
    action_id: Optional[str] = None
    message: str = ""
    existing_action: Optional[str] = None
    source: str = "user"


@dataclass
class MatchCard:
    """匹配卡片数据类"""
    id: str
    user_id: str
    name: str
    avatar: Optional[str] = None
    age: int = 25
    occupation: str = ""
    location: str = ""
    bio: str = ""
    interests: list = None
    scene_type: str = ""
    user_role: str = ""
    created_at: str = ""
    match_score: int = 75
    
    # 场景特定字段
    additional_fields: Dict[str, Any] = None

    def __post_init__(self):
        if self.interests is None:
            self.interests = []
        if self.additional_fields is None:
            self.additional_fields = {}


@dataclass
class MatchStatistics:
    """匹配统计数据类"""
    total_actions: int
    action_breakdown: Dict[str, int]
    ai_recommendations: int
    period: str


@dataclass
class AIRecommendation:
    """AI推荐数据类"""
    id: str
    target_user_id: str
    target_card_id: str
    action_type: str
    scene_context: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: str = ""
    target_user: Optional[Dict[str, Any]] = None