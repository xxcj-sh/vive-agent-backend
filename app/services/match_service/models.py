"""
匹配服务的数据模型和枚举类型
"""

from enum import Enum
from typing import Dict, Any, Optional

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


class MatchResult:
    """匹配结果数据类"""
    def __init__(self, is_match: bool, match_id: Optional[str] = None, 
                 action_id: Optional[str] = None, message: str = "",
                 existing_action: Optional[str] = None, source: str = "user"):
        self.is_match = is_match
        self.match_id = match_id
        self.action_id = action_id
        self.message = message
        self.existing_action = existing_action
        self.source = source


class MatchCard:
    """匹配卡片数据类"""
    def __init__(self, id: str, user_id: str, name: str, avatar: Optional[str] = None,
                 age: int = 25, occupation: str = "", location: str = "", 
                 bio: str = "", interests: list = None, scene_type: str = "",
                 user_role: str = "", created_at: str = "", match_score: int = 75,
                 additional_fields: Dict[str, Any] = None):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.avatar = avatar
        self.age = age
        self.occupation = occupation
        self.location = location
        self.bio = bio
        self.interests = interests if interests is not None else []
        self.scene_type = scene_type
        self.user_role = user_role
        self.created_at = created_at
        self.match_score = match_score
        self.additional_fields = additional_fields if additional_fields is not None else {}


class MatchStatistics:
    """匹配统计数据类"""
    def __init__(self, total_actions: int, action_breakdown: Dict[str, int],
                 ai_recommendations: int, period: str):
        self.total_actions = total_actions
        self.action_breakdown = action_breakdown
        self.ai_recommendations = ai_recommendations
        self.period = period


class AIRecommendation:
    """AI推荐数据类"""
    def __init__(self, id: str, target_user_id: str, target_card_id: str, action_type: str,
                 scene_context: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None,
                 created_at: str = "", target_user: Optional[Dict[str, Any]] = None):
        self.id = id
        self.target_user_id = target_user_id
        self.target_card_id = target_card_id
        self.action_type = action_type
        self.scene_context = scene_context
        self.metadata = metadata
        self.created_at = created_at
        self.target_user = target_user