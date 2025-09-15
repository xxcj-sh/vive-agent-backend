"""
匹配卡片策略模块
整合了原有的 match_card_strategy.py 的功能
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.user import User
from app.models.match import Match  # 使用现有的Match模型替代HousingListing
from app.models.card_profiles import DatingProfile
from app.models.card_profiles import ActivityOrganizerProfile, ActivityParticipantProfile
from .models import MatchCard


class MatchCardStrategy:
    """匹配卡片策略类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_recommendation_cards(self, user_id: str, scene_type: str, 
                               role_type: str, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """
        获取匹配推荐卡片
        
        Args:
            user_id: 用户ID
            scene_type: 场景类型 (housing, dating, activity)
            role_type:
            page: 页码
            page_size: 每页数量
            
        Returns:
            包含卡片列表和分页信息的字典
        """
        try:
            # 获取当前用户信息
            current_user = self.db.query(User).filter(User.id == user_id).first()
            if not current_user:
                return {"cards": [], "total": 0}
            
            # 构建当前用户信息字典
            current_user_dict = self._build_user_dict(current_user)
            
            # 根据场景类型获取推荐卡片
            if scene_type == "socail":
                return self._get_dating_cards(role_type, page, page_size, current_user_dict)
            elif scene_type == "activity":
                return self._get_activity_cards(role_type, page, page_size, current_user_dict)
            else:
                return {"cards": [], "total": 0}
                
        except Exception as e:
            print(f"获取匹配推荐卡片失败: {str(e)}")
            return {"cards": [], "total": 0}

    def _get_dating_cards(self, role_type: str, page: int, page_size: int, 
                         current_user: Dict[str, Any]) -> Dict[str, Any]:
        """获取交友相关卡片"""
        try:
            offset = (page - 1) * page_size
            
            # 获取交友用户
            query = self.db.query(User).filter(
                User.id != current_user["id"]
            )
            
            # 应用性别筛选
            current_user_gender = current_user.get("gender", 0)
            preferences = current_user.get("preferences", {})
            target_gender = preferences.get("target_gender")
            if target_gender is not None:
                query = query.filter(User.gender == target_gender)
            
            total = query.count()
            users = query.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()
            
            # 导入匹配操作模型
            from app.models.match_action import MatchAction, MatchActionType
            
            cards = []
            for user in users:
                dating_profile = self.db.query(DatingProfile).filter(DatingProfile.user_id == user.id).first()
                
                # 检查对方是否已对当前用户表示兴趣
                target_user_interest = self.db.query(MatchAction).filter(
                    MatchAction.user_id == user.id,
                    MatchAction.target_user_id == current_user["id"],
                    MatchAction.action_type.in_([MatchActionType.AI_RECOMMEND_AFTER_USER_CHAT, MatchActionType.LIKE, MatchActionType.SUPER_LIKE])
                ).first()
                
                card_data = {
                    "id": f"{user.id}_{int(datetime.utcnow().timestamp())}",
                    "userId": str(user.id),
                    "name": getattr(user, 'nick_name', None) or getattr(user, 'name', '匿名用户'),
                    "avatar": getattr(user, 'avatar_url', None),
                    "age": getattr(user, 'age', 25),
                    "occupation": getattr(user, 'occupation', ''),
                    "location": getattr(user, 'location', ''),
                    "bio": getattr(user, 'bio', ''),
                    "interests": getattr(user, 'interests', []),
                    "sceneType": "dating",
                    "roleType": role_type,
                    "createdAt": user.created_at.isoformat(),
                    "matchScore": self._calculate_match_score(current_user, user),
                    "gender": getattr(user, 'gender', 0),
                    "education": getattr(user, 'education', ''),
                    "height": getattr(user, 'height', 170),
                    "relationshipStatus": getattr(dating_profile, 'relationship_status', 'single') if dating_profile else 'single',
                    "hasInterestInMe": target_user_interest is not None,
                    "mutualMatchAvailable": target_user_interest is not None
                }
                
                cards.append(card_data)
            
            return {"cards": cards, "total": total}
            
        except Exception as e:
            print(f"获取交友卡片失败: {str(e)}")
            return {"cards": [], "total": 0}
    
    def _get_activity_cards(self, role_type: str, page: int, page_size: int, 
                          current_user: Dict[str, Any]) -> Dict[str, Any]:
        """获取活动相关卡片"""
        try:
            offset = (page - 1) * page_size
            # 组织者看参与者卡片
            query = self.db.query(User).filter(
                User.user_type == "participant",
                User.id != current_user["id"]
            )
            scene_type = role_type.split("_")[0]
            total = query.count()
            participants = query.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()
            
            # 导入匹配操作模型
            from app.models.match_action import MatchAction, MatchActionType
            
            cards = []
            for participant in participants:
                # 检查对方是否已对当前用户表示兴趣
                target_user_interest = self.db.query(MatchAction).filter(
                    MatchAction.user_id == participant.id,
                    MatchAction.target_user_id == current_user["id"],
                    MatchAction.action_type.in_([MatchActionType.LIKE, MatchActionType.SUPER_LIKE])
                ).first()
                
                cards.append({
                    "id": f"{participant.id}_{int(datetime.utcnow().timestamp())}",
                    "userId": str(participant.id),
                    "name": getattr(participant, 'nick_name', None) or getattr(participant, 'name', '匿名用户'),
                    "avatar": getattr(participant, 'avatar_url', None),
                    "age": getattr(participant, 'age', 25),
                    "occupation": getattr(participant, 'occupation', ''),
                    "location": getattr(participant, 'location', ''),
                    "bio": getattr(participant, 'bio', ''),
                    "interests": getattr(participant, 'interests', []),
                    "sceneType": scene_type,
                    "roleType": role_type,
                    "createdAt": participant.created_at.isoformat(),
                    "matchScore": self._calculate_match_score(current_user, participant),
                    "preferredActivity": "社交活动",
                    "budgetRange": "100-500",
                    "availability": "周末",
                    "hasInterestInMe": target_user_interest is not None,
                    "mutualMatchAvailable": target_user_interest is not None
                })
            
            return {"cards": cards, "total": total}
            
        except Exception as e:
            print(f"获取活动卡片失败: {str(e)}")
            return {"cards": [], "total": 0}
    
    def _build_user_dict(self, user: User) -> Dict[str, Any]:
        """构建用户信息字典"""
        return {
            "id": str(user.id),
            "nickName": getattr(user, 'nick_name', None) or getattr(user, 'name', '匿名用户'),
            "gender": getattr(user, 'gender', 0),
            "age": getattr(user, 'age', 25),
            "occupation": getattr(user, 'occupation', ''),
            "location": getattr(user, 'location', ''),
            "bio": getattr(user, 'bio', ''),
            "interests": getattr(user, 'interests', []),
            "avatarUrl": getattr(user, 'avatar_url', None),
            "preferences": getattr(user, 'preferences', {})
        }
    
    def _calculate_match_score(self, current_user: Dict[str, Any], target_user: User) -> int:
        """计算匹配分数"""
        score = 50  # 基础分数
        
        # 地理位置匹配
        if current_user.get("location") and target_user.location:
            if current_user["location"] in target_user.location or target_user.location in current_user["location"]:
                score += 20
        
        # 兴趣匹配
        current_interests = set(current_user.get("interests", []))
        target_interests = set(getattr(target_user, 'interests', []))
        if current_interests and target_interests:
            common_interests = current_interests.intersection(target_interests)
            score += min(len(common_interests) * 5, 20)
        
        # 年龄匹配
        age_diff = abs(current_user.get("age", 25) - getattr(target_user, 'age', 25))
        if age_diff <= 5:
            score += 10
        
        return min(score, 100)
    
    def get_match_cards(self, scene_type: str, role_type: str, page: int = 1, 
                       page_size: int = 10, current_user: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        获取匹配卡片（兼容原有接口）
        
        Args:
            scene_type: 匹配类型
            role_type: 用户角色
            page: 页码
            page_size: 每页数量
            current_user: 当前用户信息
            
        Returns:
            包含卡片列表和分页信息的字典
        """
        if not current_user or "id" not in current_user:
            return {"list": [], "total": 0}
        
        result = self.get_recommendation_cards(
            user_id=current_user["id"],
            scene_type=scene_type,
            role_type=role_type,
            page=page,
            page_size=page_size
        )
        
        return {
            "list": result.get("cards", []),
            "total": result.get("total", 0)
        }