"""
增强的匹配撮合服务
实现智能匹配算法和离线匹配列表生成功能
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import uuid
import random
import math
from collections import defaultdict

from app.models.match_action import MatchAction, MatchResult
from app.models.enums import MatchActionType, MatchResultStatus
from app.models.user import User
from app.models.user_card_db import UserCard
from app.services.match_service import MatchService


class MatchCompatibilityCalculator:
    """匹配兼容性计算器"""
    
    @staticmethod
    def calculate_compatibility_score(user1_profile: Dict, user2_profile: Dict, match_type: str) -> float:
        """
        计算两个用户的兼容性分数
        
        Args:
            user1_profile: 用户1的资料信息
            user2_profile: 用户2的资料信息
            match_type: 匹配类型
            
        Returns:
            兼容性分数 (0-100)
        """
        if match_type == "housing":
            return MatchCompatibilityCalculator._calculate_housing_compatibility(user1_profile, user2_profile)
        elif match_type == "dating":
            return MatchCompatibilityCalculator._calculate_dating_compatibility(user1_profile, user2_profile)
        elif match_type == "activity":
            return MatchCompatibilityCalculator._calculate_activity_compatibility(user1_profile, user2_profile)
        else:
            return 50.0  # 默认中等兼容性
    
    @staticmethod
    def _calculate_housing_compatibility(landlord_profile: Dict, tenant_profile: Dict) -> float:
        """计算房源匹配兼容性"""
        score = 0.0
        max_score = 0.0
        
        # 价格匹配 (权重: 30%)
        landlord_price = landlord_profile.get('housing_price', 0)
        tenant_budget_min = tenant_profile.get('housing_budget_min', 0)
        tenant_budget_max = tenant_profile.get('housing_budget_max', 0)
        
        if tenant_budget_min <= landlord_price <= tenant_budget_max:
            score += 30
        elif abs(landlord_price - (tenant_budget_min + tenant_budget_max) / 2) <= 500:
            score += 20  # 价格接近但不完全匹配
        max_score += 30
        
        # 地理位置匹配 (权重: 25%)
        landlord_location = landlord_profile.get('location', '')
        tenant_preferred_location = tenant_profile.get('preferred_location', '')
        if landlord_location and tenant_preferred_location:
            if landlord_location == tenant_preferred_location:
                score += 25
            elif any(loc in landlord_location for loc in tenant_preferred_location.split(',')):
                score += 15
        max_score += 25
        
        # 房屋类型匹配 (权重: 20%)
        landlord_housing_type = landlord_profile.get('housing_type', '')
        tenant_preferred_type = tenant_profile.get('preferred_housing_type', '')
        if landlord_housing_type == tenant_preferred_type:
            score += 20
        elif landlord_housing_type and tenant_preferred_type:
            score += 10
        max_score += 20
        
        # 租期匹配 (权重: 15%)
        landlord_lease_term = landlord_profile.get('housing_lease_term', '')
        tenant_lease_duration = tenant_profile.get('housing_lease_duration', '')
        if landlord_lease_term == tenant_lease_duration:
            score += 15
        elif landlord_lease_term and tenant_lease_duration:
            score += 8
        max_score += 15
        
        # 生活习惯匹配 (权重: 10%)
        landlord_preferences = set(landlord_profile.get('housing_preferences', '').split(','))
        tenant_habits = set(tenant_profile.get('living_habits', '').split(','))
        common_preferences = landlord_preferences.intersection(tenant_habits)
        if common_preferences:
            score += min(10, len(common_preferences) * 2)
        max_score += 10
        
        return (score / max_score * 100) if max_score > 0 else 50.0
    
    @staticmethod
    def _calculate_dating_compatibility(user1_profile: Dict, user2_profile: Dict) -> float:
        """计算交友匹配兼容性"""
        score = 0.0
        max_score = 0.0
        
        # 年龄匹配 (权重: 20%)
        age1 = user1_profile.get('age', 25)
        age2 = user2_profile.get('age', 25)
        age_diff = abs(age1 - age2)
        if age_diff <= 3:
            score += 20
        elif age_diff <= 5:
            score += 15
        elif age_diff <= 10:
            score += 10
        max_score += 20
        
        # 兴趣爱好匹配 (权重: 30%)
        interests1 = set(user1_profile.get('interests', '').split(','))
        interests2 = set(user2_profile.get('interests', '').split(','))
        common_interests = interests1.intersection(interests2)
        if common_interests:
            score += min(30, len(common_interests) * 6)
        max_score += 30
        
        # 地理位置匹配 (权重: 20%)
        location1 = user1_profile.get('location', '')
        location2 = user2_profile.get('location', '')
        if location1 == location2:
            score += 20
        elif location1 and location2 and any(loc in location1 for loc in location2.split(',')):
            score += 12
        max_score += 20
        
        # 教育背景匹配 (权重: 15%)
        education1 = user1_profile.get('education', '')
        education2 = user2_profile.get('education', '')
        if education1 == education2:
            score += 15
        elif education1 and education2:
            score += 8
        max_score += 15
        
        # 职业匹配 (权重: 15%)
        occupation1 = user1_profile.get('occupation', '')
        occupation2 = user2_profile.get('occupation', '')
        if occupation1 == occupation2:
            score += 15
        elif occupation1 and occupation2:
            # 相关职业给予部分分数
            score += 7
        max_score += 15
        
        return (score / max_score * 100) if max_score > 0 else 50.0
    
    @staticmethod
    def _calculate_activity_compatibility(organizer_profile: Dict, participant_profile: Dict) -> float:
        """计算活动匹配兼容性"""
        score = 0.0
        max_score = 0.0
        
        # 活动类型匹配 (权重: 35%)
        activity_type = organizer_profile.get('activity_type', '')
        preferred_activity = participant_profile.get('preferred_activity_type', '')
        if activity_type == preferred_activity:
            score += 35
        elif activity_type and preferred_activity:
            score += 20
        max_score += 35
        
        # 时间匹配 (权重: 25%)
        activity_time = organizer_profile.get('activity_time', '')
        preferred_time = participant_profile.get('preferred_activity_time', '')
        if activity_time == preferred_time:
            score += 25
        elif activity_time and preferred_time:
            score += 15
        max_score += 25
        
        # 地点匹配 (权重: 20%)
        activity_location = organizer_profile.get('activity_location', '')
        preferred_location = participant_profile.get('preferred_activity_location', '')
        if activity_location == preferred_location:
            score += 20
        elif activity_location and preferred_location:
            score += 12
        max_score += 20
        
        # 预算匹配 (权重: 20%)
        activity_price = organizer_profile.get('activity_price', 0)
        budget_min = participant_profile.get('activity_budget_min', 0)
        budget_max = participant_profile.get('activity_budget_max', 0)
        if budget_min <= activity_price <= budget_max:
            score += 20
        elif abs(activity_price - (budget_min + budget_max) / 2) <= 50:
            score += 12
        max_score += 20
        
        return (score / max_score * 100) if max_score > 0 else 50.0


class EnhancedMatchService(MatchService):
    """增强的匹配服务，包含智能撮合功能"""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.compatibility_calculator = MatchCompatibilityCalculator()
    
    def generate_daily_match_recommendations(self, user_id: str, match_type: str, 
                                           max_recommendations: int = 10) -> List[Dict[str, Any]]:
        """
        为用户生成每日匹配推荐列表
        
        Args:
            user_id: 用户ID
            match_type: 匹配类型
            max_recommendations: 最大推荐数量
            
        Returns:
            推荐用户列表，按兼容性分数排序
        """
        try:
            # 获取当前用户信息
            current_user = self.db.query(User).filter(User.id == user_id).first()
            if not current_user:
                return []
            
            # 获取用户卡片
            current_user_card = self._get_user_card_data(user_id, match_type)
            if not current_user_card:
                return []
            
            # 获取用户角色
            user_role = current_user_card.get('role_type')
            
            # 根据角色获取候选用户
            candidates = self._get_match_candidates(user_id, match_type, user_role)
            
            # 计算兼容性分数并排序
            scored_candidates = []
            for candidate in candidates:
                candidate_card = self._get_user_card_data(candidate.id, match_type)
                if candidate_card:
                    compatibility_score = self.compatibility_calculator.calculate_compatibility_score(
                        current_user_card, candidate_card, match_type
                    )
                    
                    scored_candidates.append({
                        'user_id': candidate.id,
                        'user_info': {
                            'id': candidate.id,
                            'name': candidate.nick_name or candidate.username or f"用户{candidate.id}",
                            'avatar': candidate.avatar_url,
                            'age': candidate.age,
                            'occupation': candidate.occupation,
                            'location': candidate.location
                        },
                        'card_data': candidate_card,
                        'compatibility_score': compatibility_score,
                        'match_reasons': self._generate_match_reasons(
                            current_user_card, candidate_card, match_type
                        )
                    })
            
            # 按兼容性分数排序
            scored_candidates.sort(key=lambda x: x['compatibility_score'], reverse=True)
            
            # 返回前N个推荐
            return scored_candidates[:max_recommendations]
            
        except Exception as e:
            print(f"生成匹配推荐失败: {str(e)}")
            return []
    
    def _get_match_candidates(self, user_id: str, match_type: str, user_role: str) -> List[User]:
        """
        获取匹配候选用户
        
        Args:
            user_id: 当前用户ID
            match_type: 匹配类型
            user_role: 用户角色
            
        Returns:
            候选用户列表
        """
        # 确定目标角色
        if user_role == 'seeker':
            target_role = 'provider'
        elif user_role == 'provider':
            target_role = 'seeker'
        else:
            target_role = None
        
        # 构建查询
        query = self.db.query(User).join(UserCard).filter(
            User.id != user_id,  # 排除自己
            UserCard.scene_type == match_type,
            UserCard.is_active == 1
        )
        
        if target_role:
            query = query.filter(UserCard.role_type.like(f'%{target_role}%'))
        
        # 排除已经操作过的用户
        acted_user_ids = self.db.query(MatchAction.target_user_id).filter(
            MatchAction.user_id == user_id,
            MatchAction.match_type == match_type
        ).subquery()
        
        query = query.filter(~User.id.in_(acted_user_ids))
        
        # 限制候选数量，提高查询效率
        return query.limit(50).all()
    
    def _get_user_card_data(self, user_id: str, match_type: str) -> Optional[Dict[str, Any]]:
        """获取用户在特定场景下的卡片数据"""
        card = self.db.query(UserCard).filter(
            UserCard.user_id == user_id,
            UserCard.scene_type == match_type,
            UserCard.is_active == 1
        ).first()
        
        if not card:
            return None
        
        # 合并基础用户信息和卡片数据
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        card_data = card.card_data or {}
        card_data.update({
            'role_type': card.role_type,
            'scene_type': card.scene_type,
            'display_name': card.display_name,
            'bio': card.bio,
            'tags': card.tags or [],
            'preferences': card.preferences or {},
            # 用户基础信息
            'age': user.age,
            'gender': user.gender,
            'occupation': user.occupation,
            'location': user.location,
            'interests': user.interests or []
        })
        
        return card_data
    
    def _generate_match_reasons(self, user1_card: Dict, user2_card: Dict, 
                               match_type: str) -> List[str]:
        """生成匹配原因列表"""
        reasons = []
        
        if match_type == "housing":
            # 房源匹配原因
            if user1_card.get('housing_price', 0) and user2_card.get('housing_budget_min', 0):
                price = user1_card.get('housing_price', 0)
                budget_min = user2_card.get('housing_budget_min', 0)
                budget_max = user2_card.get('housing_budget_max', 0)
                if budget_min <= price <= budget_max:
                    reasons.append("价格符合预算")
            
            if user1_card.get('location') == user2_card.get('preferred_location'):
                reasons.append("地理位置匹配")
            
            if user1_card.get('housing_type') == user2_card.get('preferred_housing_type'):
                reasons.append("房屋类型匹配")
                
        elif match_type == "dating":
            # 交友匹配原因
            interests1 = set(str(user1_card.get('interests', '')).split(','))
            interests2 = set(str(user2_card.get('interests', '')).split(','))
            common_interests = interests1.intersection(interests2)
            if common_interests:
                reasons.append(f"共同兴趣: {', '.join(list(common_interests)[:3])}")
            
            age1 = user1_card.get('age', 0)
            age2 = user2_card.get('age', 0)
            if abs(age1 - age2) <= 5:
                reasons.append("年龄相近")
            
            if user1_card.get('location') == user2_card.get('location'):
                reasons.append("同城用户")
                
        elif match_type == "activity":
            # 活动匹配原因
            if user1_card.get('activity_type') == user2_card.get('preferred_activity_type'):
                reasons.append("活动类型匹配")
            
            if user1_card.get('activity_location') == user2_card.get('preferred_activity_location'):
                reasons.append("活动地点匹配")
            
            activity_price = user1_card.get('activity_price', 0)
            budget_min = user2_card.get('activity_budget_min', 0)
            budget_max = user2_card.get('activity_budget_max', 0)
            if budget_min <= activity_price <= budget_max:
                reasons.append("价格合适")
        
        if not reasons:
            reasons.append("系统智能推荐")
        
        return reasons
    
    def get_match_statistics(self, user_id: str, match_type: str = None) -> Dict[str, Any]:
        """
        获取用户匹配统计信息
        
        Args:
            user_id: 用户ID
            match_type: 匹配类型筛选
            
        Returns:
            统计信息字典
        """
        try:
            # 基础查询
            actions_query = self.db.query(MatchAction).filter(MatchAction.user_id == user_id)
            matches_query = self.db.query(MatchResult).filter(
                (MatchResult.user1_id == user_id) | (MatchResult.user2_id == user_id)
            )
            
            if match_type:
                actions_query = actions_query.filter(MatchAction.match_type == match_type)
                matches_query = matches_query.filter(MatchResult.match_type == match_type)
            
            # 统计各种操作
            total_actions = actions_query.count()
            likes_count = actions_query.filter(MatchAction.action_type == MatchActionType.LIKE).count()
            super_likes_count = actions_query.filter(MatchAction.action_type == MatchActionType.SUPER_LIKE).count()
            dislikes_count = actions_query.filter(MatchAction.action_type == MatchActionType.DISLIKE).count()
            
            # 匹配统计
            total_matches = matches_query.count()
            active_matches = matches_query.filter(MatchResult.is_active == True).count()
            
            # 计算匹配率
            positive_actions = likes_count + super_likes_count
            match_rate = (total_matches / positive_actions * 100) if positive_actions > 0 else 0
            
            # 最近活动
            recent_actions = actions_query.filter(
                MatchAction.created_at >= datetime.now() - timedelta(days=7)
            ).count()
            
            recent_matches = matches_query.filter(
                MatchResult.matched_at >= datetime.now() - timedelta(days=7)
            ).count()
            
            return {
                "total_actions": total_actions,
                "likes_count": likes_count,
                "super_likes_count": super_likes_count,
                "dislikes_count": dislikes_count,
                "total_matches": total_matches,
                "active_matches": active_matches,
                "match_rate": round(match_rate, 2),
                "recent_actions": recent_actions,
                "recent_matches": recent_matches,
                "activity_level": self._calculate_activity_level(recent_actions, recent_matches)
            }
            
        except Exception as e:
            print(f"获取匹配统计失败: {str(e)}")
            return {}
    
    def _calculate_activity_level(self, recent_actions: int, recent_matches: int) -> str:
        """计算用户活跃度等级"""
        total_activity = recent_actions + recent_matches * 2  # 匹配权重更高
        
        if total_activity >= 20:
            return "非常活跃"
        elif total_activity >= 10:
            return "活跃"
        elif total_activity >= 5:
            return "一般"
        else:
            return "不活跃"
    
    def batch_generate_recommendations(self, match_type: str, batch_size: int = 100) -> Dict[str, Any]:
        """
        批量生成匹配推荐（用于离线任务）
        
        Args:
            match_type: 匹配类型
            batch_size: 批处理大小
            
        Returns:
            处理结果统计
        """
        try:
            # 获取活跃用户列表
            active_users = self.db.query(User).join(UserCard).filter(
                UserCard.scene_type == match_type,
                UserCard.is_active == 1,
                User.is_active == True
            ).limit(batch_size).all()
            
            processed_count = 0
            success_count = 0
            
            for user in active_users:
                try:
                    recommendations = self.generate_daily_match_recommendations(
                        user.id, match_type, max_recommendations=10
                    )
                    
                    if recommendations:
                        # 这里可以将推荐结果存储到缓存或推荐表中
                        # 暂时只统计成功数量
                        success_count += 1
                    
                    processed_count += 1
                    
                except Exception as e:
                    print(f"为用户 {user.id} 生成推荐失败: {str(e)}")
                    processed_count += 1
            
            return {
                "match_type": match_type,
                "processed_count": processed_count,
                "success_count": success_count,
                "success_rate": (success_count / processed_count * 100) if processed_count > 0 else 0,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"批量生成推荐失败: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }