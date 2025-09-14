"""
兼容性层，确保原有代码能够无缝迁移到新模块
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from .core import MatchService as NewMatchService
from .card_strategy import MatchCardStrategy as NewMatchCardStrategy


class MatchService(NewMatchService):
    """兼容原有 MatchService 接口"""
    
    def __init__(self, db: Session):
        super().__init__(db)
    
    def submit_match_action(self, user_id: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """兼容原有 submit_match_action 接口"""
        result = super().submit_match_action(user_id, action_data)
        return {
            "isMatch": result.is_match,
            "matchId": result.match_id,
            "actionId": result.action_id,
            "message": result.message,
            "source": result.source,
            "existingAction": result.existing_action
        }
    
    def get_recommendation_cards(self, user_id: str, scene_type: str, 
                               user_role: str, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """兼容原有 get_recommendation_cards 接口"""
        return super().get_recommendation_cards(user_id, scene_type, user_role, page, page_size)
    
    def get_user_matches(self, user_id: str, status: str = "all", 
                        page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """兼容原有 get_user_matches 接口"""
        return super().get_user_matches(user_id, status, page, page_size)
    
    def get_ai_recommendations(self, user_id: str, scene_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """兼容原有 get_ai_recommendations 接口"""
        recommendations = super().get_ai_recommendations(user_id, scene_type, limit)
        return [
            {
                "id": rec.id,
                "targetUserId": rec.target_user_id,
                "targetCardId": rec.target_card_id,
                "actionType": rec.action_type,
                "sceneContext": rec.scene_context,
                "metadata": rec.metadata,
                "createdAt": rec.created_at,
                "targetUser": rec.target_user
            }
            for rec in recommendations
        ]
    
    def get_match_statistics(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """兼容原有 get_match_statistics 接口"""
        stats = super().get_match_statistics(user_id, days)
        return {
            "totalActions": stats.total_actions,
            "actionBreakdown": stats.action_breakdown,
            "aiRecommendations": stats.ai_recommendations,
            "period": stats.period
        }


class MatchServiceSimple(NewMatchService):
    """兼容原有 MatchServiceSimple 接口"""
    
    def __init__(self, db: Session):
        super().__init__(db)
    
    def submit_match_action(self, user_id: str, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """兼容原有简单接口"""
        return super().submit_match_action(user_id, action_data)
    
    def get_user_matches(self, user_id: str, status: str = "all") -> Dict[str, Any]:
        """兼容原有简单接口"""
        return super().get_user_matches(user_id, status, page=1, page_size=100)


class MatchCardStrategyCompat:
    """兼容原有 MatchCardStrategy 接口"""
    
    def __init__(self, db: Session):
        self.strategy = NewMatchCardStrategy(db)
    
    def get_match_cards(self, match_type: str, user_role: str, page: int = 1, 
                       page_size: int = 10, current_user: Dict[str, Any] = None) -> Dict[str, Any]:
        """兼容原有 get_match_cards 接口"""
        return self.strategy.get_match_cards(match_type, user_role, page, page_size, current_user)


# 全局实例，保持原有使用方式
match_card_strategy = None


def init_legacy_compat(db: Session):
    """初始化兼容性层"""
    global match_card_strategy
    match_card_strategy = MatchCardStrategyCompat(db)


# 保持原有导入路径可用
__all__ = [
    "MatchService",
    "MatchServiceSimple", 
    "MatchCardStrategyCompat",
    "match_card_strategy",
    "init_legacy_compat"
]