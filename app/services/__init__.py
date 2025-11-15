"""
服务模块初始化文件
"""

# 用户画像服务
from .user_profile import UserProfileService

# 其他服务
from .auth import AuthService
from .enhanced_match_service import EnhancedMatchService
from .llm_service import LLMService
from .media_service import MediaService
from .subscribe_message_service import SubscribeMessageService
from .user_card_service import UserCardService
from .user_stats_service import UserStatsService
from .coffee_recommendation_service import CoffeeRecommendationService

__all__ = [
    # 用户画像服务
    'UserProfileService',
    # 其他服务
    'AuthService',
    'EnhancedMatchService',
    'LLMService',
    'MediaService',
    'SubscribeMessageService',
    'UserCardService',
    'UserStatsService',
    'CoffeeRecommendationService'
]