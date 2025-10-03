"""
用户画像服务
处理用户画像数据的创建、更新、查询和分析
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.models.user_profile import UserProfile, UserProfileCreate, UserProfileUpdate, UserProfileResponse
from app.models.user import User
import uuid
from datetime import datetime


class UserProfileService:
    """用户画像服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_user_profile(self, profile_data: UserProfileCreate) -> UserProfile:
        """
        创建用户画像
        
        Args:
            profile_data: 用户画像创建数据
            
        Returns:
            UserProfile: 创建的画像对象
        """
        # 检查用户是否存在
        user = self.db.query(User).filter(User.id == profile_data.user_id).first()
        if not user:
            raise ValueError(f"用户不存在: {profile_data.user_id}")
        
        # 检查是否已存在激活的画像
        existing_profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == profile_data.user_id,
            UserProfile.is_active == True
        ).first()
        
        if existing_profile:
            # 如果已存在激活的画像，将其设为非激活
            existing_profile.is_active = 0
            self.db.add(existing_profile)
        
        # 创建新的画像
        profile = UserProfile(
            user_id=profile_data.user_id,
            preferences=profile_data.preferences,
            personality_traits=profile_data.personality_traits,
            mood_state=profile_data.mood_state,
            behavior_patterns=profile_data.behavior_patterns,
            interest_tags=profile_data.interest_tags,
            social_preferences=profile_data.social_preferences,
            match_preferences=profile_data.match_preferences,
            data_source=profile_data.data_source,
            confidence_score=profile_data.confidence_score,
            update_reason=profile_data.update_reason
        )
        
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        
        return profile
    
    def update_user_profile(self, profile_id: str, update_data: UserProfileUpdate) -> Optional[UserProfile]:
        """
        更新用户画像
        
        Args:
            profile_id: 画像ID
            update_data: 更新数据
            
        Returns:
            Optional[UserProfile]: 更新后的画像对象，如果不存在返回None
        """
        profile = self.db.query(UserProfile).filter(UserProfile.id == profile_id).first()
        if not profile:
            return None
        
        # 更新字段
        if update_data.preferences is not None:
            profile.preferences = update_data.preferences
        if update_data.personality_traits is not None:
            profile.personality_traits = update_data.personality_traits
        if update_data.mood_state is not None:
            profile.mood_state = update_data.mood_state
        if update_data.behavior_patterns is not None:
            profile.behavior_patterns = update_data.behavior_patterns
        if update_data.interest_tags is not None:
            profile.interest_tags = update_data.interest_tags
        if update_data.social_preferences is not None:
            profile.social_preferences = update_data.social_preferences
        if update_data.match_preferences is not None:
            profile.match_preferences = update_data.match_preferences
        if update_data.data_source is not None:
            profile.data_source = update_data.data_source
        if update_data.confidence_score is not None:
            profile.confidence_score = update_data.confidence_score
        if update_data.update_reason is not None:
            profile.update_reason = update_data.update_reason
        
        profile.updated_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(profile)
        
        return profile
    
    def get_user_profile(self, profile_id: str) -> Optional[UserProfile]:
        """
        获取用户画像
        
        Args:
            profile_id: 画像ID
            
        Returns:
            Optional[UserProfile]: 画像对象，如果不存在返回None
        """
        return self.db.query(UserProfile).filter(UserProfile.id == profile_id).first()
    
    def get_active_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        获取用户的激活画像
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[UserProfile]: 激活的画像对象，如果不存在返回None
        """
        return self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id,
            UserProfile.is_active == True
        ).first()
    
    def get_user_profiles(self, user_id: str, include_inactive: bool = False) -> List[UserProfile]:
        """
        获取用户的所有画像
        
        Args:
            user_id: 用户ID
            include_inactive: 是否包含非激活的画像
            
        Returns:
            List[UserProfile]: 画像列表
        """
        query = self.db.query(UserProfile).filter(UserProfile.user_id == user_id)
        
        if not include_inactive:
            query = query.filter(UserProfile.is_active == True)
        
        return query.order_by(UserProfile.created_at.desc()).all()
    
    def deactivate_user_profile(self, profile_id: str) -> bool:
        """
        停用用户画像
        
        Args:
            profile_id: 画像ID
            
        Returns:
            bool: 是否成功停用
        """
        profile = self.db.query(UserProfile).filter(UserProfile.id == profile_id).first()
        if not profile:
            return False
        
        profile.is_active = False
        profile.updated_at = datetime.now()
        
        self.db.commit()
        return True
    
    def activate_user_profile(self, profile_id: str) -> bool:
        """
        激活用户画像
        
        Args:
            profile_id: 画像ID
            
        Returns:
            bool: 是否成功激活
        """
        profile = self.db.query(UserProfile).filter(UserProfile.id == profile_id).first()
        if not profile:
            return False
        
        # 停用该用户的其他激活画像
        self.db.query(UserProfile).filter(
            UserProfile.user_id == profile.user_id,
            UserProfile.is_active == True,
            UserProfile.id != profile_id
        ).update({"is_active": False})
        
        # 激活当前画像
        profile.is_active = True
        profile.updated_at = datetime.now()
        
        self.db.commit()
        return True
    
    def analyze_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """
        分析用户偏好
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 偏好分析结果
        """
        profile = self.get_active_user_profile(user_id)
        if not profile:
            return {"error": "用户画像不存在"}
        
        analysis_result = {
            "user_id": user_id,
            "analysis_type": "preferences",
            "preferences": profile.preferences or {},
            "interest_tags": profile.interest_tags or [],
            "social_preferences": profile.social_preferences or {},
            "match_preferences": profile.match_preferences or {},
            "confidence_score": profile.confidence_score or 0,
            "data_source": profile.data_source or "unknown",
            "generated_at": datetime.now().isoformat()
        }
        
        return analysis_result
    
    def analyze_user_personality(self, user_id: str) -> Dict[str, Any]:
        """
        分析用户个性
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 个性分析结果
        """
        profile = self.get_active_user_profile(user_id)
        if not profile:
            return {"error": "用户画像不存在"}
        
        analysis_result = {
            "user_id": user_id,
            "analysis_type": "personality",
            "personality_traits": profile.personality_traits or {},
            "behavior_patterns": profile.behavior_patterns or {},
            "confidence_score": profile.confidence_score or 0,
            "data_source": profile.data_source or "unknown",
            "generated_at": datetime.now().isoformat()
        }
        
        return analysis_result
    
    def analyze_user_mood(self, user_id: str) -> Dict[str, Any]:
        """
        分析用户心情
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 心情分析结果
        """
        profile = self.get_active_user_profile(user_id)
        if not profile:
            return {"error": "用户画像不存在"}
        
        analysis_result = {
            "user_id": user_id,
            "analysis_type": "mood",
            "mood_state": profile.mood_state or {},
            "confidence_score": profile.confidence_score or 0,
            "data_source": profile.data_source or "unknown",
            "generated_at": datetime.now().isoformat()
        }
        
        return analysis_result
    
    def get_profile_statistics(self, user_id: str) -> Dict[str, Any]:
        """
        获取用户画像统计信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        total_profiles = self.db.query(UserProfile).filter(UserProfile.user_id == user_id).count()
        active_profiles = self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id,
            UserProfile.is_active == True
        ).count()
        
        latest_profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).order_by(UserProfile.created_at.desc()).first()
        
        statistics = {
            "user_id": user_id,
            "total_profiles": total_profiles,
            "active_profiles": active_profiles,
            "latest_update": latest_profile.updated_at.isoformat() if latest_profile else None,
            "data_completeness": self._calculate_data_completeness(latest_profile) if latest_profile else 0
        }
        
        return statistics
    
    def _calculate_data_completeness(self, profile: UserProfile) -> float:
        """
        计算数据完整性
        
        Args:
            profile: 用户画像对象
            
        Returns:
            float: 完整性评分(0-100)
        """
        fields_to_check = [
            profile.preferences,
            profile.personality_traits,
            profile.mood_state,
            profile.behavior_patterns,
            profile.interest_tags,
            profile.social_preferences,
            profile.match_preferences
        ]
        
        filled_fields = sum(1 for field in fields_to_check if field is not None)
        total_fields = len(fields_to_check)
        
        return (filled_fields / total_fields) * 100 if total_fields > 0 else 0