"""
用户画像服务
处理用户画像数据的创建、更新、查询和分析
提供用户画像的创建、更新、查询、分析、历史记录等完整功能
支持显式更新、隐式学习、定期回顾等机制
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Tuple
from app.models.user_profile import UserProfile, UserProfileCreate, UserProfileUpdate, UserProfileResponse
from app.models.user_profile_history import UserProfileHistory, UserProfileHistoryCreate
from app.models.user import User
from app.services.llm_service import LLMService
from app.models.llm_schemas import LLMRequest, LLMTaskType
from app.models.llm_usage_log import LLMProvider
from datetime import datetime, timedelta
import json
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class UserProfileService:
    """用户画像服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService(db)
        
        self.model_name = settings.USER_PROFILE_MODEL_NAME
    
    def create_user_profile(self, profile_data: UserProfileCreate, change_source: str = "user") -> UserProfile:
        """
        创建用户画像（带历史记录）
        
        Args:
            profile_data: 用户画像创建数据
            change_source: 变更来源: user, system, admin, llm
            
        Returns:
            UserProfile: 创建的画像对象
        """
        # 检查用户是否存在
        user = self.db.query(User).filter(User.id == profile_data.user_id).first()
        if not user:
            raise ValueError(f"用户不存在: {profile_data.user_id}")
        
        # 检查是否已存在画像
        existing_profile = self.db.query(UserProfile).filter(
            UserProfile.user_id == profile_data.user_id
        ).first()
        
        if existing_profile:
            # 如果已存在画像，更新它
            existing_profile.updated_at = datetime.now()
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
        
        # 创建历史记录
        history_data = UserProfileHistoryCreate(
            profile_id=profile.id,
            user_id=profile.user_id,
            version=1,
            change_type="create",
            change_source=change_source,
            change_reason=profile_data.update_reason or "初始创建",
            confidence_score_before=None,
            confidence_score_after=profile.confidence_score,
            changed_fields=["all"],
            change_summary="用户画像初始创建"
        )
        
        self._create_history_record(history_data)
        
        return profile
    
    def _extract_profile_data(self, profile: UserProfile) -> dict:
        """提取用户画像数据用于比较"""
        return {
            "preferences": profile.preferences,
            "personality_traits": profile.personality_traits,
            "mood_state": profile.mood_state,
            "behavior_patterns": profile.behavior_patterns,
            "interest_tags": profile.interest_tags,
            "social_preferences": profile.social_preferences,
            "match_preferences": profile.match_preferences,
            "confidence_score": profile.confidence_score
        }
    
    def _calculate_changed_fields(self, previous_data: dict, current_data: dict) -> List[str]:
        """计算变更的字段"""
        changed_fields = []
        
        for field in ["preferences", "personality_traits", "mood_state", 
                     "behavior_patterns", "interest_tags", "social_preferences", 
                     "match_preferences", "confidence_score"]:
            if previous_data.get(field) != current_data.get(field):
                changed_fields.append(field)
        
        return changed_fields
    
    def _determine_change_type(self, change_source: str, change_reason: str) -> str:
        """确定变更类型"""
        if change_source == "system":
            return "automatic"
        elif change_source == "ai_suggestion":
            return "ai_recommended"
        elif change_source == "implicit_learning":
            return "implicit_learning"
        else:
            return "manual"
    
    def _generate_change_summary(self, changed_fields: List[str]) -> str:
        """生成变更摘要"""
        if not changed_fields:
            return "无变更"
        
        field_names = {
            "preferences": "个人偏好",
            "personality_traits": "性格特征", 
            "mood_state": "情绪状态",
            "behavior_patterns": "行为模式",
            "interest_tags": "兴趣标签",
            "social_preferences": "社交偏好",
            "match_preferences": "匹配偏好",
            "confidence_score": "置信度分数"
        }
        
        changed_field_names = [field_names.get(field, field) for field in changed_fields]
        return f"更新了: {', '.join(changed_field_names)}"
    
    def _get_next_version(self, profile_id: str) -> int:
        """
        获取用户画像的下一个版本号
        
        Args:
            profile_id: 画像ID
            
        Returns:
            int: 下一个版本号
        """
        # 查询该画像的历史记录，获取最大的版本号
        latest_history = self.db.query(UserProfileHistory).filter(
            UserProfileHistory.profile_id == profile_id
        ).order_by(UserProfileHistory.version.desc()).first()
        
        if latest_history:
            return latest_history.version + 1
        else:
            return 1  # 如果没有历史记录，从版本1开始

    def _create_history_record(self, history_data: UserProfileHistoryCreate) -> UserProfileHistory:
        """
        创建用户画像历史记录
        
        Args:
            history_data: 历史记录创建数据
            
        Returns:
            UserProfileHistory: 创建的历史记录对象
        """
        try:
            # 创建历史记录对象
            history_record = UserProfileHistory(
                profile_id=history_data.profile_id,
                user_id=history_data.user_id,
                version=history_data.version,
                change_type=history_data.change_type,
                change_source=history_data.change_source,
                change_reason=history_data.change_reason,
                change_summary=history_data.change_summary,
                confidence_score_before=history_data.confidence_score_before,
                confidence_score_after=history_data.confidence_score_after,
                changed_fields=history_data.changed_fields,
                # 变更前数据快照
                previous_preferences=history_data.previous_preferences,
                previous_personality_traits=history_data.previous_personality_traits,
                previous_mood_state=history_data.previous_mood_state,
                previous_behavior_patterns=history_data.previous_behavior_patterns,
                previous_interest_tags=history_data.previous_interest_tags,
                previous_social_preferences=history_data.previous_social_preferences,
                previous_match_preferences=history_data.previous_match_preferences,
                # 变更后数据快照
                current_preferences=history_data.current_preferences,
                current_personality_traits=history_data.current_personality_traits,
                current_mood_state=history_data.current_mood_state,
                current_behavior_patterns=history_data.current_behavior_patterns,
                current_interest_tags=history_data.current_interest_tags,
                current_social_preferences=history_data.current_social_preferences,
                current_match_preferences=history_data.current_match_preferences
            )
            
            self.db.add(history_record)
            self.db.commit()
            self.db.refresh(history_record)
            
            logger.info(f"用户画像历史记录创建成功: profile_id={history_data.profile_id}, "
                       f"user_id={history_data.user_id}, version={history_data.version}")
            
            return history_record
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"创建用户画像历史记录失败: {str(e)}")
            raise
    
    def generate_update_suggestions(self, profile_id: str, user_feedback: str = None, 
                                  context: dict = None) -> Dict[str, Any]:
        """
        基于用户反馈和当前画像生成更新建议
        
        Args:
            profile_id: 画像ID
            user_feedback: 用户反馈
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 更新建议结果
        """
        try:
            profile = self.get_user_profile(profile_id)
            if not profile:
                return {"success": False, "error": "用户画像不存在"}
            
            # 获取历史记录
            history = self.get_profile_history(profile_id, limit=5)
            
            # 构建建议提示词
            prompt = self._build_suggestion_prompt(profile, user_feedback, history, context)
            
            # 调用LLM生成建议
            llm_response = self.llm_service.generate_response(
                prompt,
                model=self.model_name,
                max_tokens=1000,
                temperature=0.7
            )
            
            # 解析建议响应
            suggestions = self._parse_suggestion_response(llm_response)
            
            return {
                "success": True,
                "suggestions": suggestions,
                "llm_response": llm_response,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"生成更新建议失败: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _build_suggestion_prompt(self, profile: UserProfile, user_feedback: str = None, 
                                history: List[UserProfileHistory] = None, context: dict = None) -> str:
        """构建建议提示词"""
        prompt = f"""基于以下用户画像信息，请提供更新建议：

当前用户画像：
- 个人偏好: {profile.preferences}
- 性格特征: {profile.personality_traits}
- 情绪状态: {profile.mood_state}
- 行为模式: {profile.behavior_patterns}
- 兴趣标签: {profile.interest_tags}
- 社交偏好: {profile.social_preferences}
- 匹配偏好: {profile.match_preferences}
- 置信度分数: {profile.confidence_score}

"""
        
        if user_feedback:
            prompt += f"用户反馈: {user_feedback}\n\n"
        
        if history:
            prompt += "最近变更历史:\n"
            for h in history[:3]:
                prompt += f"- {h.change_summary} (置信度: {h.confidence_score_after})\n"
            prompt += "\n"
        
        if context:
            prompt += f"上下文信息: {json.dumps(context, ensure_ascii=False)}\n\n"
        
        prompt += """请提供具体的更新建议，格式如下：
{
    "suggestions": {
        "preferences": "建议的个人偏好",
        "personality_traits": "建议的性格特征", 
        "mood_state": "建议的情绪状态",
        "behavior_patterns": "建议的行为模式",
        "interest_tags": "建议的兴趣标签",
        "social_preferences": "建议的社交偏好",
        "match_preferences": "建议的匹配偏好"
    },
    "reasoning": "更新理由",
    "confidence": 0.8,
    "priority_fields": ["preferences", "mood_state"]
}

请确保建议合理且基于用户画像分析。"""
        
        return prompt
    
    def _parse_suggestion_response(self, llm_response: str) -> Dict[str, Any]:
        """解析建议响应"""
        try:
            # 尝试从响应中提取JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', llm_response)
            if json_match:
                suggestions = json.loads(json_match.group())
                return suggestions
            else:
                # 如果无法解析JSON，返回结构化响应
                return {
                    "suggestions": {},
                    "reasoning": llm_response,
                    "confidence": 0.5,
                    "priority_fields": []
                }
        except Exception as e:
            logger.error(f"解析建议响应失败: {str(e)}")
            return {
                "suggestions": {},
                "reasoning": llm_response,
                "confidence": 0.3,
                "priority_fields": [],
                "parsing_error": str(e)
            }
    
    def _build_implicit_learning_prompt(self, profile: UserProfile, interaction_data: Dict[str, Any], 
                                       history: List[UserProfileHistory] = None) -> str:
        """构建隐式学习提示词"""
        prompt = f"""基于用户交互数据进行隐式学习分析：

当前用户画像：
- 个人偏好: {profile.preferences}
- 性格特征: {profile.personality_traits}
- 情绪状态: {profile.mood_state}
- 行为模式: {profile.behavior_patterns}
- 兴趣标签: {profile.interest_tags}
- 社交偏好: {profile.social_preferences}
- 匹配偏好: {profile.match_preferences}

交互数据：
{json.dumps(interaction_data, ensure_ascii=False, indent=2)}

"""
        
        if history:
            prompt += "相关历史记录:\n"
            for h in history[:5]:
                if h.change_type in ["implicit_learning", "automatic"]:
                    prompt += f"- {h.change_summary} (置信度变化: {h.confidence_score_before} -> {h.confidence_score_after})\n"
            prompt += "\n"
        
        prompt += """请分析用户行为模式，判断是否需要更新用户画像，格式如下：
{
    "should_update": true/false,
    "updates": {
        "preferences": "更新的个人偏好",
        "personality_traits": "更新的性格特征",
        "mood_state": "更新的情绪状态",
        "behavior_patterns": "更新的行为模式",
        "interest_tags": "更新的兴趣标签",
        "social_preferences": "更新的社交偏好",
        "match_preferences": "更新的匹配偏好"
    },
    "insights": {
        "behavior_pattern": "发现的行为模式",
        "preference_trend": "偏好趋势",
        "confidence_level": "置信度评估"
    },
    "reasoning": "更新理由",
    "confidence": 0.7
}

请基于交互数据中的行为模式、时间模式、偏好变化等进行分析。"""
        
        return prompt
    
    def _parse_learning_response(self, llm_response: str) -> Dict[str, Any]:
        """解析学习响应"""
        try:
            # 尝试从响应中提取JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', llm_response)
            if json_match:
                learning_result = json.loads(json_match.group())
                return learning_result
            else:
                # 如果无法解析JSON，返回默认响应
                return {
                    "should_update": False,
                    "updates": {},
                    "insights": {},
                    "reasoning": llm_response,
                    "confidence": 0.3
                }
        except Exception as e:
            logger.error(f"解析学习响应失败: {str(e)}")
            return {
                "should_update": False,
                "updates": {},
                "insights": {},
                "reasoning": llm_response,
                "confidence": 0.1,
                "parsing_error": str(e)
            }
    
    def _validate_suggestions(self, profile: UserProfile, suggestions: Dict[str, Any]) -> Dict[str, Any]:
        """验证建议的合理性"""
        validated = {}
        
        # 获取建议字段
        suggested_fields = suggestions.get("suggestions", {})
        
        # 验证每个字段
        field_validators = {
            "preferences": lambda x: isinstance(x, dict),
            "personality_traits": lambda x: isinstance(x, dict),
            "mood_state": lambda x: isinstance(x, dict),
            "behavior_patterns": lambda x: isinstance(x, dict),
            "interest_tags": lambda x: isinstance(x, list),
            "social_preferences": lambda x: isinstance(x, dict),
            "match_preferences": lambda x: isinstance(x, dict)
        }
        
        for field, validator in field_validators.items():
            if field in suggested_fields and validator(suggested_fields[field]):
                validated[field] = suggested_fields[field]
        
        return validated
    
    def get_profile_history(self, profile_id: str, limit: int = 50, 
                          change_type: str = None) -> List[UserProfileHistory]:
        """
        获取用户画像历史记录
        
        Args:
            profile_id: 画像ID
            limit: 返回记录数量限制
            change_type: 变更类型过滤
            
        Returns:
            List[UserProfileHistory]: 历史记录列表
        """
        query = self.db.query(UserProfileHistory).filter(
            UserProfileHistory.profile_id == profile_id
        ).order_by(UserProfileHistory.created_at.desc())
        
        if change_type:
            query = query.filter(UserProfileHistory.change_type == change_type)
        
        return query.limit(limit).all()
    
    def get_profile_history_by_date_range(self, profile_id: str, start_date: datetime, 
                                        end_date: datetime) -> List[UserProfileHistory]:
        """
        获取指定日期范围内的历史记录
        
        Args:
            profile_id: 画像ID
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            List[UserProfileHistory]: 历史记录列表
        """
        return self.db.query(UserProfileHistory).filter(
            UserProfileHistory.profile_id == profile_id,
            UserProfileHistory.created_at >= start_date,
            UserProfileHistory.created_at <= end_date
        ).order_by(UserProfileHistory.created_at.desc()).all()
    
    def get_profile_change_statistics(self, profile_id: str, days: int = 30) -> Dict[str, Any]:
        """
        获取用户画像变更统计
        
        Args:
            profile_id: 画像ID
            days: 统计天数
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        start_date = datetime.now() - timedelta(days=days)
        
        history = self.get_profile_history_by_date_range(
            profile_id, start_date, datetime.now()
        )
        
        if not history:
            return {
                "total_changes": 0,
                "change_types": {},
                "most_changed_fields": [],
                "average_confidence_change": 0.0,
                "trend": "stable"
            }
        
        # 统计变更类型
        change_types = {}
        field_changes = {}
        confidence_changes = []
        
        for record in history:
            # 变更类型统计
            change_type = record.change_type
            change_types[change_type] = change_types.get(change_type, 0) + 1
            
            # 字段变更统计
            for field in record.changed_fields:
                field_changes[field] = field_changes.get(field, 0) + 1
            
            # 置信度变化统计
            if record.confidence_score_before is not None and record.confidence_score_after is not None:
                confidence_changes.append(record.confidence_score_after - record.confidence_score_before)
        
        # 排序获取最频繁变更的字段
        most_changed_fields = sorted(field_changes.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # 计算平均置信度变化
        avg_confidence_change = sum(confidence_changes) / len(confidence_changes) if confidence_changes else 0.0
        
        # 判断趋势
        if avg_confidence_change > 0.1:
            trend = "improving"
        elif avg_confidence_change < -0.1:
            trend = "declining"
        else:
            trend = "stable"
        
        return {
            "total_changes": len(history),
            "change_types": change_types,
            "most_changed_fields": [field for field, count in most_changed_fields],
            "average_confidence_change": avg_confidence_change,
            "trend": trend,
            "period_days": days
        }
    
    def get_user_profile_with_history(self, profile_id: str, history_limit: int = 10) -> Dict[str, Any]:
        """
        获取用户画像及其历史记录
        
        Args:
            profile_id: 画像ID
            history_limit: 历史记录数量限制
            
        Returns:
            Dict[str, Any]: 包含画像和历史记录的数据
        """
        profile = self.get_user_profile(profile_id)
        if not profile:
            return {"success": False, "error": "用户画像不存在"}
        
        history = self.get_profile_history(profile_id, limit=history_limit)
        statistics = self.get_profile_change_statistics(profile_id, days=30)
        
        return {
            "success": True,
            "profile": profile,
            "history": history,
            "statistics": statistics,
            "total_history_records": len(history)
        }
    
    def batch_update_profiles(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        批量更新用户画像
        
        Args:
            updates: 更新列表，每个元素包含profile_id和update_data
            
        Returns:
            Dict[str, Any]: 批量更新结果
        """
        results = {
            "success": 0,
            "failed": 0,
            "errors": [],
            "updated_profiles": []
        }
        
        for update_item in updates:
            try:
                profile_id = update_item.get("profile_id")
                update_data = update_item.get("update_data")
                change_source = update_item.get("change_source", "batch")
                change_reason = update_item.get("change_reason", "批量更新")
                
                if not profile_id or not update_data:
                    results["failed"] += 1
                    results["errors"].append(f"缺少必要参数: profile_id={profile_id}")
                    continue
                
                # 转换update_data为UserProfileUpdate
                user_profile_update = UserProfileUpdate(**update_data)
                
                updated_profile = self.update_user_profile(
                    profile_id,
                    user_profile_update,
                    change_source=change_source,
                    change_reason=change_reason
                )
                
                if updated_profile:
                    results["success"] += 1
                    results["updated_profiles"].append(updated_profile)
                else:
                    results["failed"] += 1
                    results["errors"].append(f"画像不存在: {profile_id}")
                    
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(f"更新失败: {str(e)}")
        
        return results
    
    def analyze_profile_trends(self, profile_id: str, days: int = 30) -> Dict[str, Any]:
        """
        分析用户画像趋势
        
        Args:
            profile_id: 画像ID
            days: 分析天数
            
        Returns:
            Dict[str, Any]: 趋势分析结果
        """
        try:
            start_date = datetime.now() - timedelta(days=days)
            history = self.get_profile_history_by_date_range(profile_id, start_date, datetime.now())
            
            if not history:
                return {
                    "success": False,
                    "error": "历史记录不足，无法分析趋势"
                }
            
            # 按时间排序
            history.sort(key=lambda x: x.created_at)
            
            # 分析各个字段的变化趋势
            trends = {}
            
            # 置信度趋势
            confidence_scores = [h.confidence_score_after for h in history if h.confidence_score_after is not None]
            if confidence_scores:
                trends["confidence"] = {
                    "start": confidence_scores[0],
                    "end": confidence_scores[-1],
                    "trend": "up" if confidence_scores[-1] > confidence_scores[0] else "down" if confidence_scores[-1] < confidence_scores[0] else "stable",
                    "volatility": self._calculate_volatility(confidence_scores)
                }
            
            # 变更频率趋势
            daily_changes = {}
            for record in history:
                date_str = record.created_at.date().isoformat()
                daily_changes[date_str] = daily_changes.get(date_str, 0) + 1
            
            if daily_changes:
                change_counts = list(daily_changes.values())
                trends["change_frequency"] = {
                    "average_daily_changes": sum(change_counts) / len(change_counts),
                    "max_daily_changes": max(change_counts),
                    "active_days": len(daily_changes),
                    "total_changes": len(history)
                }
            
            # 变更类型分布
            change_type_dist = {}
            for record in history:
                change_type = record.change_type
                change_type_dist[change_type] = change_type_dist.get(change_type, 0) + 1
            
            trends["change_types"] = change_type_dist
            
            # 最常变更的字段
            field_changes = {}
            for record in history:
                for field in record.changed_fields:
                    field_changes[field] = field_changes.get(field, 0) + 1
            
            trends["field_changes"] = dict(sorted(field_changes.items(), key=lambda x: x[1], reverse=True)[:5])
            
            return {
                "success": True,
                "profile_id": profile_id,
                "analysis_period_days": days,
                "total_records": len(history),
                "trends": trends,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"分析画像趋势失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _calculate_volatility(self, values: List[float]) -> float:
        """计算波动性"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def export_profile_data(self, profile_id: str, include_history: bool = True) -> Dict[str, Any]:
        """
        导出用户画像数据
        
        Args:
            profile_id: 画像ID
            include_history: 是否包含历史记录
            
        Returns:
            Dict[str, Any]: 导出的数据
        """
        try:
            profile_data = self.get_user_profile_with_history(profile_id)
            
            if not profile_data["success"]:
                return profile_data
            
            export_data = {
                "profile": profile_data["profile"],
                "statistics": profile_data["statistics"],
                "export_timestamp": datetime.now().isoformat()
            }
            
            if include_history:
                export_data["history"] = profile_data["history"]
            
            return {
                "success": True,
                "export_data": export_data
            }
            
        except Exception as e:
            logger.error(f"导出画像数据失败: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def _extract_historical_data(self, history: UserProfileHistory, data_type: str) -> Dict[str, Any]:
        """从历史记录中提取数据"""
        if data_type == "previous":
            return {
                "preferences": history.previous_preferences,
                "personality_traits": history.previous_personality_traits,
                "mood_state": history.previous_mood_state,
                "behavior_patterns": history.previous_behavior_patterns,
                "interest_tags": history.previous_interest_tags,
                "social_preferences": history.previous_social_preferences,
                "match_preferences": history.previous_match_preferences
            }
        else:  # current
            return {
                "preferences": history.current_preferences,
                "personality_traits": history.current_personality_traits,
                "mood_state": history.current_mood_state,
                "behavior_patterns": history.current_behavior_patterns,
                "interest_tags": history.current_interest_tags,
                "social_preferences": history.current_social_preferences,
                "match_preferences": history.current_match_preferences
            }

    def _calculate_detailed_differences(self, data1: Dict[str, Any], data2: Dict[str, Any]) -> Dict[str, Any]:
        """计算详细差异"""
        differences = {}
        
        for field in data1.keys():
            if data1[field] != data2[field]:
                differences[field] = {
                    "before": data1[field],
                    "after": data2[field],
                    "change_type": self._determine_field_change_type(data1[field], data2[field])
                }
        
        return differences

    def _determine_field_change_type(self, before: Any, after: Any) -> str:
        """确定字段变更类型"""
        if before is None and after is not None:
            return "added"
        elif before is not None and after is None:
            return "removed"
        else:
            return "modified"

    def _generate_detailed_summary(self, differences: Dict[str, Any]) -> str:
        """生成详细摘要"""
        if not differences:
            return "两个版本之间没有差异"
        
        summary_parts = []
        for field, diff in differences.items():
            field_name = self._get_field_display_name(field)
            change_type = diff["change_type"]
            
            if change_type == "added":
                summary_parts.append(f"新增{field_name}")
            elif change_type == "removed":
                summary_parts.append(f"删除{field_name}")
            else:
                summary_parts.append(f"修改{field_name}")
        
        return "；".join(summary_parts)

    def _get_field_display_name(self, field: str) -> str:
        """获取字段显示名称"""
        field_names = {
            "preferences": "用户偏好",
            "personality_traits": "个性特征",
            "mood_state": "心情状态",
            "behavior_patterns": "行为模式",
            "interest_tags": "兴趣标签",
            "social_preferences": "社交偏好",
            "match_preferences": "匹配偏好"
        }
        return field_names.get(field, field)

    def compare_profile_versions(self, user_id: str, version1: int, version2: int) -> Dict[str, Any]:
        """
        比较两个版本的用户画像
        
        Args:
            user_id: 用户ID
            version1: 第一个版本号
            version2: 第二个版本号
            
        Returns:
            Dict[str, Any]: 版本比较结果
        """
        try:
            # 获取两个版本的历史记录
            history1 = self.db.query(UserProfileHistory).filter_by(
                user_id=user_id, version=version1
            ).first()
            
            history2 = self.db.query(UserProfileHistory).filter_by(
                user_id=user_id, version=version2
            ).first()
            
            if not history1 or not history2:
                return {"error": "找不到指定的版本记录"}
            
            # 提取数据
            data1 = self._extract_historical_data(history1, "current")
            data2 = self._extract_historical_data(history2, "current")
            
            # 计算差异
            differences = self._calculate_detailed_differences(data1, data2)
            summary = self._generate_detailed_summary(differences)
            
            return {
                "version1": version1,
                "version2": version2,
                "differences": differences,
                "summary": summary,
                "total_changes": len(differences),
                "comparison_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"比较版本失败: {str(e)}")
            return {"error": f"版本比较失败: {str(e)}"}

    def schedule_profile_review(self, user_id: str, review_type: str = "quarterly") -> Dict[str, Any]:
        """
        安排用户画像定期回顾
        
        Args:
            user_id: 用户ID
            review_type: 回顾类型 (weekly/monthly/quarterly)
            
        Returns:
            Dict[str, Any]: 安排结果
        """
        try:
            profile = self.get_active_user_profile(user_id)
            if not profile:
                return {"error": "用户画像不存在"}
            
            review_date = self._calculate_review_date(review_type)
            
            # 这里可以集成到任务调度系统
            # 现在只是返回计划信息
            return {
                "user_id": user_id,
                "review_type": review_type,
                "scheduled_date": review_date.isoformat(),
                "current_confidence": profile.confidence_score,
                "message": f"已安排{review_type}回顾，计划在 {review_date.strftime('%Y-%m-%d')} 进行"
            }
            
        except Exception as e:
            logger.error(f"安排回顾失败: {str(e)}")
            return {"error": f"安排回顾失败: {str(e)}"}

    def _calculate_review_date(self, review_type: str) -> datetime:
        """计算回顾日期"""
        now = datetime.now()
        
        if review_type == "weekly":
            return now + timedelta(days=7)
        elif review_type == "monthly":
            return now + timedelta(days=30)
        elif review_type == "quarterly":
            return now + timedelta(days=90)
        else:
            return now + timedelta(days=90)  # 默认季度回顾

    def _convert_to_csv_format(self, data: Dict[str, Any]) -> str:
        """转换为CSV格式"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 写入表头
        writer.writerow(['Field', 'Value'])
        
        # 写入数据
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            writer.writerow([key, value])
        
        return output.getvalue()
    
    def apply_ai_suggestions(self, profile_id: str, suggestions: Dict[str, Any], 
                           user_confirmation: bool = True) -> Dict[str, Any]:
        """
        应用AI建议更新用户画像
        
        Args:
            profile_id: 画像ID
            suggestions: AI建议
            user_confirmation: 是否需要用户确认
            
        Returns:
            Dict[str, Any]: 应用结果
        """
        try:
            profile = self.get_user_profile(profile_id)
            if not profile:
                return {"success": False, "error": "用户画像不存在"}
            
            # 验证建议的合理性
            validated_suggestions = self._validate_suggestions(profile, suggestions)
            
            if not validated_suggestions:
                return {"success": False, "error": "没有有效的更新建议"}
            
            # 构建更新数据
            update_data = UserProfileUpdate(**validated_suggestions)
            
            # 应用更新
            updated_profile = self.update_user_profile(
                profile_id,
                update_data,
                change_source="ai_suggestion",
                change_reason=f"AI建议更新: {suggestions.get('reasoning', '基于用户反馈和画像分析')}"
            )
            
            if updated_profile:
                return {
                    "success": True,
                    "profile": updated_profile,
                    "applied_changes": validated_suggestions,
                    "message": "AI建议已成功应用"
                }
            else:
                return {"success": False, "error": "更新失败"}
                
        except Exception as e:
            logger.error(f"应用AI建议失败: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def suggest_profile_updates(self, user_id: str, context_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        基于用户行为数据推荐画像更新
        
        Args:
            user_id: 用户ID
            context_data: 可选的上下文数据
            
        Returns:
            Dict[str, Any]: 更新建议结果
        """
        try:
            # 获取用户画像历史记录
            history_records = self.db.query(UserProfileHistory).filter(
                UserProfileHistory.user_id == user_id
            ).order_by(UserProfileHistory.created_at.desc()).limit(10).all()
            
            if not history_records:
                return {
                    "user_id": user_id,
                    "suggestions": [],
                    "confidence": 0.0,
                    "reasoning": "暂无历史数据可供分析",
                    "recommended_actions": []
                }
            
            # 分析最近的变更模式
            recent_changes = []
            for record in history_records:
                if record.change_type in ["update", "enhancement"]:
                    recent_changes.append({
                        "type": record.change_type,
                        "description": record.change_summary,
                        "timestamp": record.created_at,
                        "snapshot": record.current_snapshot
                    })
            
            # 基于模式生成建议
            suggestions = []
            confidence = 0.0
            reasoning = ""
            
            if len(recent_changes) >= 3:
                # 分析变更频率和模式
                change_frequency = len(recent_changes)
                last_change = recent_changes[0]
                
                # 生成智能建议
                if change_frequency > 5:
                    suggestions.append({
                        "type": "frequency_warning",
                        "field": "profile_stability",
                        "suggestion": "用户画像变更频率较高，建议保持稳定性",
                        "priority": "medium"
                    })
                
                # 基于上下文数据生成建议
                if context_data:
                    if "interaction_patterns" in context_data:
                        suggestions.append({
                            "type": "behavioral_insight",
                            "field": "interaction_preferences",
                            "suggestion": "基于交互模式，建议更新用户偏好设置",
                            "priority": "high"
                        })
                
                confidence = min(0.8, change_frequency * 0.1)
                reasoning = f"基于最近{change_frequency}次变更分析生成建议"
            
            return {
                "user_id": user_id,
                "suggestions": suggestions,
                "confidence": confidence,
                "reasoning": reasoning,
                "recommended_actions": [
                    "review_profile_consistency",
                    "analyze_user_behavior",
                    "update_preferences_if_needed"
                ]
            }
            
        except Exception as e:
            logger.error(f"生成用户画像更新建议失败: {str(e)}")
            return {
                "user_id": user_id,
                "suggestions": [],
                "confidence": 0.0,
                "reasoning": f"分析失败: {str(e)}",
                "recommended_actions": [],
                "error": str(e)
            }

    def perform_implicit_learning(self, profile_id: str, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        基于用户交互数据进行隐式学习
        
        Args:
            profile_id: 画像ID
            interaction_data: 交互数据
            
        Returns:
            Dict[str, Any]: 学习结果
        """
        try:
            profile = self.get_user_profile(profile_id)
            if not profile:
                return {"success": False, "error": "用户画像不存在"}
            
            # 获取相关历史记录
            history = self.get_profile_history(profile_id, limit=10)
            
            # 构建学习提示词
            prompt = self._build_implicit_learning_prompt(profile, interaction_data, history)
            
            # 调用LLM进行隐式学习
            llm_response = self.llm_service.generate_response(
                prompt,
                model=self.model_name,
                max_tokens=800,
                temperature=0.6
            )
            
            # 解析学习结果
            learning_result = self._parse_learning_response(llm_response)
            
            if learning_result.get("should_update", False):
                # 应用隐式学习结果
                update_data = UserProfileUpdate(**learning_result["updates"])
                
                updated_profile = self.update_user_profile(
                    profile_id,
                    update_data,
                    change_source="implicit_learning",
                    change_reason=f"隐式学习: {learning_result.get('reasoning', '基于用户行为模式分析')}"
                )
                
                return {
                    "success": True,
                    "profile": updated_profile,
                    "learning_insights": learning_result.get("insights", {}),
                    "applied_updates": learning_result.get("updates", {}),
                    "confidence": learning_result.get("confidence", 0.0),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "success": True,
                    "profile": profile,
                    "learning_insights": learning_result.get("insights", {}),
                    "message": "当前无需更新",
                    "confidence": learning_result.get("confidence", 0.0),
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"隐式学习失败: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def update_user_profile(self, profile_id: str, update_data: UserProfileUpdate, 
                          change_source: str = "user", change_reason: str = None) -> Optional[UserProfile]:
        """
        更新用户画像（带历史记录）
        
        Args:
            profile_id: 画像ID
            update_data: 更新数据
            change_source: 变更来源
            change_reason: 变更原因
            
        Returns:
            Optional[UserProfile]: 更新后的画像对象，如果不存在返回None
        """
        # 获取当前画像数据
        current_profile = self.get_user_profile(profile_id)
        if not current_profile:
            return None
        
        # 记录变更前的数据
        previous_data = self._extract_profile_data(current_profile)
        
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
        
        # 记录变更后的数据
        current_data = self._extract_profile_data(profile)
        
        # 计算变更字段
        changed_fields = self._calculate_changed_fields(previous_data, current_data)
        
        # 确定变更类型
        change_type = self._determine_change_type(change_source, change_reason)
        
        # 获取下一个版本号
        next_version = self._get_next_version(profile_id)
        
        # 创建历史记录
        history_data = UserProfileHistoryCreate(
            profile_id=profile_id,
            user_id=profile.user_id,
            version=next_version,
            change_type=change_type,
            change_source=change_source,
            change_reason=change_reason or update_data.update_reason or "用户画像更新",
            confidence_score_before=current_profile.confidence_score,
            confidence_score_after=profile.confidence_score,
            changed_fields=changed_fields,
            change_summary=self._generate_change_summary(changed_fields),
            # 变更前数据
            previous_preferences=previous_data["preferences"],
            previous_personality_traits=previous_data["personality_traits"],
            previous_mood_state=previous_data["mood_state"],
            previous_behavior_patterns=previous_data["behavior_patterns"],
            previous_interest_tags=previous_data["interest_tags"],
            previous_social_preferences=previous_data["social_preferences"],
            previous_match_preferences=previous_data["match_preferences"],
            # 变更后数据
            current_preferences=current_data["preferences"],
            current_personality_traits=current_data["personality_traits"],
            current_mood_state=current_data["mood_state"],
            current_behavior_patterns=current_data["behavior_patterns"],
            current_interest_tags=current_data["interest_tags"],
            current_social_preferences=current_data["social_preferences"],
            current_match_preferences=current_data["match_preferences"]
        )
        
        self._create_history_record(history_data)
        
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
        获取用户的画像（UserProfile模型没有is_active字段）
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[UserProfile]: 画像对象，如果不存在返回None
        """
        return self.db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()

    def get_user_profile_by_user_id(self, user_id: str, include_history: bool = False, history_limit: int = 10) -> Dict[str, Any]:
        """
        通过用户ID获取用户画像，可选包含历史记录
        
        Args:
            user_id: 用户ID
            include_history: 是否包含历史记录
            history_limit: 历史记录数量限制
            
        Returns:
            Dict[str, Any]: 包含画像信息的结果
        """
        profile = self.get_active_user_profile(user_id)
        
        if not profile:
            return {"success": False, "error": "用户画像不存在"}
        
        if include_history:
            history = self.get_profile_history(profile.id, limit=history_limit)
            statistics = self.get_profile_change_statistics(profile.id, days=30)
            
            return {
                "success": True,
                "profile": profile,
                "history": history,
                "statistics": statistics,
                "total_history_records": len(history)
            }
        else:
            return {
                "success": True,
                "profile": profile
            }
    
    def get_user_profiles(self, user_id: str, include_inactive: bool = False) -> List[UserProfile]:
        """
        获取用户的所有画像（UserProfile模型没有is_active字段）
        
        Args:
            user_id: 用户ID
            include_inactive: 参数已废弃，UserProfile模型没有is_active字段
            
        Returns:
            List[UserProfile]: 画像列表
        """
        query = self.db.query(UserProfile).filter(UserProfile.user_id == user_id)
        
        # UserProfile模型没有is_active字段，忽略include_inactive参数
        return query.order_by(UserProfile.created_at.desc()).all()
    
    def deactivate_user_profile(self, profile_id: str) -> bool:
        """
        停用用户画像（UserProfile模型没有is_active字段，此方法已废弃）
        
        Args:
            profile_id: 画像ID
            
        Returns:
            bool: 总是返回False，因为UserProfile模型没有is_active字段
        """
        # UserProfile模型没有is_active字段，此方法无法使用
        return False
    
    def activate_user_profile(self, profile_id: str) -> bool:
        """
        激活用户画像（UserProfile模型没有is_active字段，此方法已废弃）
        
        Args:
            profile_id: 画像ID
            
        Returns:
            bool: 总是返回False，因为UserProfile模型没有is_active字段
        """
        # UserProfile模型没有is_active字段，此方法无法使用
        return False
    
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
        获取用户画像统计信息（UserProfile模型没有is_active字段）
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        total_profiles = self.db.query(UserProfile).filter(UserProfile.user_id == user_id).count()
        # UserProfile模型没有is_active字段，所以总画像数就是激活画像数
        active_profiles = total_profiles
        
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