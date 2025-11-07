"""
用户画像评分服务
提供用户画像的可信度、完整度、准确度、活跃度等评分功能
"""

import json
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta
from app.models.user_profile_score import (
    UserProfileScore, UserProfileScoreHistory, UserProfileSkill, 
    ScoreType, ScoreCalculationRequest
)
from app.models.user_profile import UserProfile
from app.services.user_profile.user_profile_service import UserProfileService
from app.utils.logger import logger


class UserProfileScoreService:
    """用户画像评分服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.profile_service = UserProfileService(db)
    
    def get_user_score(self, user_id: str) -> Optional[UserProfileScore]:
        """获取用户评分"""
        return self.db.query(UserProfileScore).filter(
            UserProfileScore.user_id == user_id
        ).first()
    
    def get_or_create_user_score(self, user_id: str) -> UserProfileScore:
        """获取或创建用户评分"""
        score = self.get_user_score(user_id)
        if not score:
            score = UserProfileScore(user_id=user_id)
            self.db.add(score)
            self.db.commit()
            self.db.refresh(score)
            logger.info(f"创建用户评分记录: user_id={user_id}")
        return score
    
    def update_user_profile_score(self, user_id: str, score_update: Dict[str, Any]) -> UserProfileScore:
        """更新用户画像评分"""
        score = self.get_or_create_user_score(user_id)
        
        # 更新评分字段
        for field, value in score_update.items():
            if hasattr(score, field) and value is not None:
                setattr(score, field, value)
        
        # 重新计算总体评分
        scores_dict = {
            "completeness": score.completeness_score,
            "accuracy": score.accuracy_score,
            "activity": score.activity_score,
            "credibility": score.credibility_score
        }
        score.overall_score = self.calculate_overall_score(scores_dict)
        
        self.db.commit()
        self.db.refresh(score)
        
        logger.info(f"更新用户画像评分: user_id={user_id}, overall_score={score.overall_score}")
        return score
    
    def calculate_credibility_score(self, profile: UserProfile) -> int:
        """计算可信度评分"""
        # 基础分数
        base_score = 50
        
        if not profile or not profile.raw_profile:
            return base_score
        
        try:
            # 解析用户画像数据
            profile_data = json.loads(profile.raw_profile) if isinstance(profile.raw_profile, str) else profile.raw_profile
            
            # 信息完整度加分
            completeness_bonus = 0
            if isinstance(profile_data, dict):
                # 基础信息完整度
                basic_fields = ['basic_info', 'personality_traits', 'chat_style', 'interest', 'preferences']
                filled_fields = sum(1 for field in basic_fields if field in profile_data and profile_data[field])
                completeness_bonus += filled_fields * 8
                
                # 详细信息加分
                detailed_fields = ['background', 'values', 'lifestyle', 'goals']
                detailed_filled = sum(1 for field in detailed_fields if field in profile_data and profile_data[field])
                completeness_bonus += detailed_filled * 5
            
            # 数据一致性检查
            consistency_bonus = 0
            if isinstance(profile_data, dict):
                # 检查性格特征的一致性
                personality = profile_data.get('personality_traits', '')
                if personality and isinstance(personality, str):
                    # 简单的关键词检查
                    consistent_keywords = ['开放性', '尽责性', '外向性', '宜人性', '神经质']
                    keyword_count = sum(1 for keyword in consistent_keywords if keyword in personality)
                    if keyword_count >= 3:
                        consistency_bonus += 10
                
                # 检查兴趣与偏好的匹配度
                interests = profile_data.get('interest', '')
                preferences = profile_data.get('preferences', '')
                if interests and preferences and isinstance(interests, str) and isinstance(preferences, str):
                    # 简单的关键词匹配
                    if any(word in interests and word in preferences for word in ['运动', '音乐', '阅读']):
                        consistency_bonus += 8
            
            # 计算最终分数
            final_score = base_score + completeness_bonus + consistency_bonus
            
            # 确保分数在合理范围内
            return min(100, max(0, final_score))
            
        except (json.JSONDecodeError, AttributeError, TypeError) as e:
            logger.warning(f"解析用户画像数据失败: {e}")
            return base_score
    
    def calculate_overall_score(self, scores_dict: Dict[str, float]) -> int:
        """计算总体评分"""
        # 默认权重配置
        weight_config = {
            "completeness": 0.3,  # 完整度 (30%)
            "accuracy": 0.3,  # 准确度 (30%)
            "activity": 0.2,  # 活跃度 (20%)
            "credibility": 0.2  # 可信度 (20%)
        }
        
        total_score = 0
        total_weight = 0
        
        for score_type, score_value in scores_dict.items():
            if score_value is not None:
                weight = weight_config.get(score_type, 0.25)
                total_score += score_value * weight
                total_weight += weight
        
        # 如果没有任何评分，返回默认值
        if total_weight == 0:
            return 50
        
        return int(total_score / total_weight)
    
    def create_score_history(self, user_id: str, change_type: str, reason: str, score_changes: Dict[str, float] = None) -> UserProfileScoreHistory:
        """创建评分历史记录"""
        score = self.get_or_create_user_score(user_id)
        
        history_record = UserProfileScoreHistory(
            score_id=score.id,
            user_id=user_id,
            change_reason=reason,
            trigger_event=change_type,
            credibility_score=score.credibility_score,
            completeness_score=score.completeness_score,
            accuracy_score=score.accuracy_score,
            activity_score=score.activity_score,
            overall_score=score.overall_score
        )
        
        # 应用评分变化
        score_changes = score_changes or {}
        for score_type, change_value in score_changes.items():
            if score_type == "credibility":
                history_record.credibility_score += change_value
                score.credibility_score += change_value
            elif score_type == "completeness":
                history_record.completeness_score += change_value
                score.completeness_score += change_value
            elif score_type == "accuracy":
                history_record.accuracy_score += change_value
                score.accuracy_score += change_value
            elif score_type == "activity":
                history_record.activity_score += change_value
                score.activity_score += change_value
            elif score_type == "overall":
                history_record.overall_score += change_value
                score.overall_score += change_value
        
        # 确保分数在有效范围内
        score.credibility_score = max(0, min(100, score.credibility_score))
        score.completeness_score = max(0, min(100, score.completeness_score))
        score.accuracy_score = max(0, min(100, score.accuracy_score))
        score.activity_score = max(0, min(100, score.activity_score))
        score.overall_score = max(0, min(100, score.overall_score))
        
        self.db.add(history_record)
        self.db.commit()
        self.db.refresh(history_record)
        
        logger.info(f"创建评分历史记录: user_id={user_id}, change_type={change_type}")
        return history_record
    
    def get_user_score_history(self, user_id: str, limit: int = 10) -> List[UserProfileScoreHistory]:
        """获取用户评分历史"""
        return self.db.query(UserProfileScoreHistory).filter(
            UserProfileScoreHistory.user_id == user_id
        ).order_by(desc(UserProfileScoreHistory.recorded_at)).limit(limit).all()
    
    def _check_and_unlock_skills(self, score: UserProfileScore) -> None:
        """检查并解锁技能"""
        # 基于总体评分解锁技能
        if score.overall_score >= 80:
            # 解锁高级技能
            advanced_skills = ["advanced_matching", "priority_support", "expert_recommendations"]
            for skill_name in advanced_skills:
                existing_skill = self.db.query(UserProfileSkill).filter_by(
                    user_id=score.user_id, skill_name=skill_name
                ).first()
                if not existing_skill:
                    skill = UserProfileSkill(
                        user_id=score.user_id,
                        skill_name=skill_name,
                        unlock_score=score.overall_score,
                        is_unlocked=True
                    )
                    self.db.add(skill)
        
        if score.overall_score >= 60:
            # 解锁中级技能
            intermediate_skills = ["enhanced_matching", "basic_recommendations"]
            for skill_name in intermediate_skills:
                existing_skill = self.db.query(UserProfileSkill).filter_by(
                    user_id=score.user_id, skill_name=skill_name
                ).first()
                if not existing_skill:
                    skill = UserProfileSkill(
                        user_id=score.user_id,
                        skill_name=skill_name,
                        unlock_score=score.overall_score,
                        is_unlocked=True
                    )
                    self.db.add(skill)
        
        if score.overall_score >= 40:
            # 解锁基础技能
            basic_skills = ["basic_matching", "profile_insights"]
            for skill_name in basic_skills:
                existing_skill = self.db.query(UserProfileSkill).filter_by(
                    user_id=score.user_id, skill_name=skill_name
                ).first()
                if not existing_skill:
                    skill = UserProfileSkill(
                        user_id=score.user_id,
                        skill_name=skill_name,
                        unlock_score=score.overall_score,
                        is_unlocked=True
                    )
                    self.db.add(skill)
    
    def get_user_profile_score(self, user_id: str) -> Dict[str, Any]:
        """获取用户画像评分信息"""
        score = self.get_or_create_user_score(user_id)
        
        # 获取用户技能
        skills = self.db.query(UserProfileSkill).filter_by(user_id=user_id, is_unlocked=True).all()
        
        return {
            "user_id": user_id,
            "credibility_score": score.credibility_score,
            "completeness_score": score.completeness_score,
            "accuracy_score": score.accuracy_score,
            "activity_score": score.activity_score,
            "overall_score": score.overall_score,
            "unlocked_skills": [skill.skill_name for skill in skills],
            "last_updated": score.updated_at.isoformat() if score.updated_at else None
        }