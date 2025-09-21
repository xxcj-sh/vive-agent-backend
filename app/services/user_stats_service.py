"""
用户统计服务
提供用户相关的统计数据计算
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Dict, Any
from app.models.match_action import MatchResult, MatchResultStatus, MatchAction, MatchActionType
from app.models.chat_message import ChatMessage
from app.models.user import User
from app.models.user_card_db import UserCard


class UserStatsService:
    """用户统计服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户的真实统计数据
        
        Args:
            user_id: 用户ID
            
        Returns:
            统计数据字典
        """
        try:
            # 1. 获取用户卡片统计
            card_stats = self._get_card_stats(user_id)
            
            # 2. 获取收藏的名片统计
            favorite_stats = self._get_favorite_stats(user_id)
            
            return {
                "cardCount": card_stats["total_cards"],
                "activeCardCount": card_stats["active_cards"],
                "favoriteCardCount": favorite_stats["favorite_cards"],
                "totalCardsCreated": card_stats["total_created"],
                "recentCards": card_stats["recent_cards"]
            }
            
        except Exception as e:
            # 发生错误时返回默认值
            print(f"获取用户统计数据失败: {str(e)}")
            return {
                "cardCount": 0,
                "activeCardCount": 0,
                "favoriteCardCount": 0,
                "totalCardsCreated": 0,
                "recentCards": 0
            }
    
    def _get_match_stats(self, user_id: str) -> Dict[str, int]:
        """获取匹配统计"""
        # 总匹配数
        total_matches = self.db.query(MatchResult).filter(
            or_(
                MatchResult.user1_id == user_id,
                MatchResult.user2_id == user_id
            )
        ).count()
        
        # 活跃匹配数（已接受状态）
        active_matches = self.db.query(MatchResult).filter(
            or_(
                MatchResult.user1_id == user_id,
                MatchResult.user2_id == user_id
            ),
            MatchResult.status == MatchResultStatus.MATCHED
        ).count()
        
        # 新匹配数（24小时内的匹配）
        from datetime import datetime, timedelta
        new_matches = self.db.query(MatchResult).filter(
            or_(
                MatchResult.user1_id == user_id,
                MatchResult.user2_id == user_id
            ),
            MatchResult.matched_at >= datetime.utcnow() - timedelta(days=1)
        ).count()
        
        return {
            "total_matches": total_matches,
            "active_matches": active_matches,
            "new_matches": new_matches
        }
    
    def _get_message_stats(self, user_id: str) -> Dict[str, int]:
        """获取消息统计"""
        # 总消息数（发送+接收）
        total_messages = self.db.query(ChatMessage).filter(
            or_(
                ChatMessage.sender_id == user_id,
                ChatMessage.receiver_id == user_id
            )
        ).count()
        
        # 未读消息数
        unread_messages = self.db.query(ChatMessage).filter(
            ChatMessage.receiver_id == user_id,
            ChatMessage.is_read == False
        ).count()
        
        return {
            "total_messages": total_messages,
            "unread_messages": unread_messages
        }
    
    def _get_card_stats(self, user_id: str) -> Dict[str, int]:
        """获取用户卡片统计"""
        from app.models.user_card_db import UserCard
        from datetime import datetime, timedelta
        
        # 总卡片数（未删除的）
        total_cards = self.db.query(UserCard).filter(
            UserCard.user_id == user_id,
            UserCard.is_deleted == 0
        ).count()
        
        # 激活卡片数
        active_cards = self.db.query(UserCard).filter(
            UserCard.user_id == user_id,
            UserCard.is_deleted == 0,
            UserCard.is_active == 1
        ).count()
        
        # 总创建数（包括已删除的）
        total_created = self.db.query(UserCard).filter(
            UserCard.user_id == user_id
        ).count()
        
        # 最近7天创建的卡片数
        recent_cards = self.db.query(UserCard).filter(
            UserCard.user_id == user_id,
            UserCard.created_at >= datetime.utcnow() - timedelta(days=7)
        ).count()
        
        return {
            "total_cards": total_cards,
            "active_cards": active_cards,
            "total_created": total_created,
            "recent_cards": recent_cards
        }
    
    def _get_favorite_stats(self, user_id: str) -> Dict[str, int]:
        """获取收藏的名片统计"""
        from app.models.match_action import MatchAction, MatchActionType
        
        # 用户收藏的名片数量（COLLECTION操作）
        favorite_cards = self.db.query(MatchAction).filter(
            MatchAction.user_id == user_id,
            MatchAction.action_type == MatchActionType.COLLECTION
        ).count()
        
        return {
            "favorite_cards": favorite_cards
        }
    
    def _get_collect_stats(self, user_id: str) -> Dict[str, int]:
        """获取收藏统计
        
        注意：由于系统架构，这里使用用户的收藏操作数量作为收藏统计
        实际收藏功能可能需要额外的收藏表
        """
        from app.models.match_action import MatchAction, MatchActionType
        
        # 用户的喜欢操作数量
        total_favorites = self.db.query(MatchAction).filter(
            MatchAction.user_id == user_id,
            MatchAction.action_type == MatchActionType.COLLECTION
        ).count()
        
        return {
            "total_favorites": total_favorites
        }
    
    def get_detailed_stats(self, user_id: str) -> Dict[str, Any]:
        """
        获取详细统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            详细统计数据
        """
        basic_stats = self.get_user_stats(user_id)
        
        # 获取额外统计
        user_info = self.db.query(User).filter(User.id == user_id).first()
        if user_info:
            account_age_days = 0
            if user_info.created_at:
                from datetime import datetime
                account_age_days = (datetime.utcnow() - user_info.created_at).days
            
            # 获取场景分布统计
            scene_stats = self._get_scene_stats(user_id)
            
            return {
                **basic_stats,
                "accountAgeDays": account_age_days,
                "profileCompletion": self._calculate_profile_completion(user_info),
                "lastActivity": user_info.updated_at.isoformat() if user_info.updated_at else None,
                "sceneDistribution": scene_stats
            }
        
        return basic_stats
    
    def _get_scene_stats(self, user_id: str) -> Dict[str, int]:
        """获取用户卡片的场景分布统计"""
        from app.models.user_card_db import UserCard
        from sqlalchemy import func
        
        # 查询每个场景的卡片数量
        scene_distribution = self.db.query(
            UserCard.scene_type,
            func.count(UserCard.id).label('count')
        ).filter(
            UserCard.user_id == user_id,
            UserCard.is_deleted == 0
        ).group_by(
            UserCard.scene_type
        ).all()
        
        # 转换为字典格式
        scene_stats = {}
        for scene_type, count in scene_distribution:
            scene_stats[scene_type] = count
            
        return scene_stats
    
    def _calculate_profile_completion(self, user: User) -> float:
        """计算用户资料完成度"""
        required_fields = [
            'nick_name', 'avatar_url', 'gender', 'age', 
            'occupation', 'location', 'education', 'bio'
        ]
        
        completed_fields = 0
        for field in required_fields:
            value = getattr(user, field, None)
            if value is not None and str(value).strip():
                completed_fields += 1
        
        return round((completed_fields / len(required_fields)) * 100, 2)