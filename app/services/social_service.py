"""
社交场景服务类
"""

from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.enums import (
    SocialPurpose, SocialInterest, ProfessionalLevel, 
    ConnectionType, SocialActivity
)
from app.models.social_preferences import SocialPreference, SocialProfile, SocialMatchCriteria

class SocialService:
    """社交场景业务逻辑服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_social_preference(self, user_id: int, preference_data: Dict[str, Any]) -> SocialPreference:
        """创建社交偏好设置"""
        preference = SocialPreference(
            user_id=user_id,
            **preference_data
        )
        self.db.add(preference)
        self.db.commit()
        self.db.refresh(preference)
        return preference
    
    def update_social_preference(self, user_id: int, preference_data: Dict[str, Any]) -> SocialPreference:
        """更新社交偏好设置"""
        preference = self.db.query(SocialPreference).filter(
            SocialPreference.user_id == user_id
        ).first()
        
        if not preference:
            return self.create_social_preference(user_id, preference_data)
        
        for key, value in preference_data.items():
            setattr(preference, key, value)
        
        self.db.commit()
        self.db.refresh(preference)
        return preference
    
    def create_social_profile(self, user_id: int, profile_data: Dict[str, Any]) -> SocialProfile:
        """创建社交档案"""
        profile = SocialProfile(
            user_id=user_id,
            **profile_data
        )
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile
    
    def update_social_profile(self, user_id: int, profile_data: Dict[str, Any]) -> SocialProfile:
        """更新社交档案"""
        profile = self.db.query(SocialProfile).filter(
            SocialProfile.user_id == user_id
        ).first()
        
        if not profile:
            return self.create_social_profile(user_id, profile_data)
        
        for key, value in profile_data.items():
            setattr(profile, key, value)
        
        self.db.commit()
        self.db.refresh(profile)
        return profile
    
    def create_match_criteria(self, user_id: int, criteria_data: Dict[str, Any]) -> SocialMatchCriteria:
        """创建匹配标准"""
        criteria = SocialMatchCriteria(
            user_id=user_id,
            **criteria_data
        )
        self.db.add(criteria)
        self.db.commit()
        self.db.refresh(criteria)
        return criteria
    
    def get_social_matches(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """获取社交匹配推荐"""
        user_profile = self.db.query(SocialProfile).filter(
            SocialProfile.user_id == user_id
        ).first()
        
        user_preference = self.db.query(SocialPreference).filter(
            SocialPreference.user_id == user_id
        ).first()
        
        user_criteria = self.db.query(SocialMatchCriteria).filter(
            SocialMatchCriteria.user_id == user_id
        ).first()
        
        if not user_profile or not user_preference:
            return []
        
        # 构建查询条件
        query = self.db.query(SocialProfile).filter(
            SocialProfile.user_id != user_id
        )
        
        # 行业匹配
        if user_preference.target_industries:
            query = query.filter(
                SocialProfile.industry.in_(user_preference.target_industries)
            )
        
        # 兴趣匹配
        if user_preference.social_interests:
            query = query.filter(
                or_(
                    SocialProfile.social_interests.contains(interest)
                    for interest in user_preference.social_interests
                )
            )
        
        # 经验水平匹配
        if user_preference.experience_level_preference:
            query = query.filter(
                SocialProfile.professional_level.in_(
                    user_preference.experience_level_preference
                )
            )
        
        # 公司规模匹配
        if user_preference.company_size_preference:
            query = query.filter(
                SocialProfile.company_size.in_(
                    user_preference.company_size_preference
                )
            )
        
        # 地理位置匹配
        if user_preference.preferred_locations:
            query = query.filter(
                SocialProfile.current_company.in_(
                    user_preference.preferred_locations
                )
            )
        
        matches = query.limit(limit).all()
        
        # 计算匹配分数
        scored_matches = []
        for match in matches:
            score = self._calculate_social_match_score(
                user_profile, user_preference, match
            )
            scored_matches.append({
                'profile': match,
                'score': score,
                'common_interests': list(set(user_profile.social_interests or []) & set(match.social_interests or [])),
                'common_skills': list(set(user_profile.skills or []) & set(match.skills or []))
            })
        
        # 按分数排序
        scored_matches.sort(key=lambda x: x['score'], reverse=True)
        return scored_matches
    
    def _calculate_social_match_score(
        self, 
        user_profile: SocialProfile, 
        user_preference: SocialPreference, 
        candidate: SocialProfile
    ) -> float:
        """计算社交匹配分数"""
        score = 0.0
        max_score = 100.0
        
        # 行业匹配 (25分)
        if user_profile.industry and candidate.industry:
            if user_profile.industry == candidate.industry:
                score += 25
            elif candidate.industry in (user_preference.target_industries or []):
                score += 15
        
        # 兴趣匹配 (20分)
        user_interests = set(user_profile.social_interests or [])
        candidate_interests = set(candidate.social_interests or [])
        common_interests = user_interests.intersection(candidate_interests)
        score += (len(common_interests) / max(len(user_interests), 1)) * 20
        
        # 技能互补 (20分)
        user_skills = set(user_profile.skills or [])
        candidate_skills = set(candidate.skills or [])
        
        # 计算技能互补度
        user_wants = set(user_preference.skills_to_learn or [])
        candidate_offers = set(candidate.value_offerings or [])
        complementary = user_wants.intersection(candidate_offers)
        score += (len(complementary) / max(len(user_wants), 1)) * 20
        
        # 经验水平匹配 (15分)
        if user_profile.professional_level and candidate.professional_level:
            level_mapping = {
                'student': 1, 'entry_level': 2, 'mid_level': 3,
                'senior_level': 4, 'executive': 5, 'expert': 5
            }
            user_level = level_mapping.get(user_profile.professional_level, 3)
            candidate_level = level_mapping.get(candidate.professional_level, 3)
            
            # 理想差距为1-2级
            level_diff = abs(user_level - candidate_level)
            if level_diff <= 2:
                score += 15 * (1 - level_diff / 5)
        
        # 公司规模匹配 (10分)
        if user_profile.company_size and candidate.company_size:
            size_categories = ['startup', 'small', 'medium', 'large', 'enterprise']
            user_size = size_categories.index(user_profile.company_size.lower()) if user_profile.company_size.lower() in size_categories else 2
            candidate_size = size_categories.index(candidate.company_size.lower()) if candidate.company_size.lower() in size_categories else 2
            
            size_diff = abs(user_size - candidate_size)
            score += 10 * (1 - size_diff / 5)
        
        # 地理位置匹配 (10分)
        if user_preference.remote_preference:
            score += 10  # 支持远程的加分
        
        return min(score, max_score)
    
    def get_social_analytics(self, user_id: int) -> Dict[str, Any]:
        """获取社交分析数据"""
        profile = self.db.query(SocialProfile).filter(
            SocialProfile.user_id == user_id
        ).first()
        
        if not profile:
            return {}
        
        # 统计信息
        total_connections = self.db.query(SocialProfile).count() - 1
        
        # 技能分析
        skills = profile.skills or []
        expertise = profile.expertise_areas or []
        
        # 行业分布
        industry_stats = self._get_industry_distribution()
        
        return {
            'profile_completeness': self._calculate_profile_completeness(profile),
            'skills': skills,
            'expertise_areas': expertise,
            'industry_distribution': industry_stats,
            'total_network_size': total_connections,
            'activity_level': profile.activity_level
        }
    
    def _get_industry_distribution(self) -> Dict[str, int]:
        """获取行业分布统计"""
        from sqlalchemy import func
        
        result = self.db.query(
            SocialProfile.industry,
            func.count(SocialProfile.id)
        ).group_by(SocialProfile.industry).all()
        
        return {industry: count for industry, count in result if industry}
    
    def _calculate_profile_completeness(self, profile: SocialProfile) -> float:
        """计算档案完整度"""
        total_fields = 8
        completed_fields = 0
        
        if profile.headline:
            completed_fields += 1
        if profile.summary:
            completed_fields += 1
        if profile.current_role:
            completed_fields += 1
        if profile.current_company:
            completed_fields += 1
        if profile.industry:
            completed_fields += 1
        if profile.skills and len(profile.skills) > 0:
            completed_fields += 1
        if profile.social_interests and len(profile.social_interests) > 0:
            completed_fields += 1
        if profile.value_offerings and len(profile.value_offerings) > 0:
            completed_fields += 1
        
        return (completed_fields / total_fields) * 100