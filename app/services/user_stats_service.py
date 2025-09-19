"""
用户统计服务
提供用户相关的统计数据计算
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Dict, Any
from app.models.match_action import MatchResult, MatchResultStatus
from app.models.chat_message import ChatMessage
from app.models.user import User


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
            # 1. 获取匹配统计
            match_stats = self._get_match_stats(user_id)
            
            # 2. 获取消息统计
            message_stats = self._get_message_stats(user_id)
            
            # 3. 获取收藏统计（这里用喜欢数量代替）
            favorite_stats = self._get_collect_stats(user_id)
            
            return {
                "matchCount": match_stats["total_matches"],
                "messageCount": message_stats["total_messages"],
                "favoriteCount": favorite_stats["total_favorites"],
                "newMatches": match_stats["new_matches"],
                "unreadMessages": message_stats["unread_messages"],
                "activeMatches": match_stats["active_matches"]
            }
            
        except Exception as e:
            # 发生错误时返回默认值
            print(f"获取用户统计数据失败: {str(e)}")
            return {
                "matchCount": 0,
                "messageCount": 0,
                "favoriteCount": 0,
                "newMatches": 0,
                "unreadMessages": 0,
                "activeMatches": 0
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
            
            return {
                **basic_stats,
                "accountAgeDays": account_age_days,
                "profileCompletion": self._calculate_profile_completion(user_info),
                "lastActivity": user_info.updated_at.isoformat() if user_info.updated_at else None
            }
        
        return basic_stats
    
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