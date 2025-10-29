"""
用户画像反馈处理服务
基于用户评价反馈，使用LLM智能更新用户画像
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.user_profile import UserProfile, UserProfileUpdate
from app.models.user_profile_feedback import UserProfileFeedback, UserProfileFeedbackProcessingResponse
from app.models.user import User
from app.models.llm_schemas import LLMRequest, LLMTaskType
from app.models.llm_usage_log import LLMProvider
from app.services.llm_service import LLMService
from app.services.user_profile_service import UserProfileService

logger = logging.getLogger(__name__)


class UserProfileFeedbackService:
    """用户画像反馈处理服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService(db)
        self.profile_service = UserProfileService(db)
        self.model_name = "ep-20251004235106-gklgg"
    
    async def process_pending_feedback(self, batch_size: int = 50) -> UserProfileFeedbackProcessingResponse:
        """
        处理待处理的用户评价反馈
        
        Args:
            batch_size: 每批处理的最大反馈数量
            
        Returns:
            处理结果统计
        """
        logger.info(f"开始处理用户评价反馈，批次大小: {batch_size}")
        start_time = datetime.now()
        
        try:
            # 获取待处理的反馈
            pending_feedback = self.get_pending_feedback(limit=batch_size)
            
            if not pending_feedback:
                logger.info("没有待处理的用户评价反馈")
                return UserProfileFeedbackProcessingResponse(
                    processed_count=0,
                    success_count=0,
                    failure_count=0,
                    processing_results=[]
                )
            
            logger.info(f"找到 {len(pending_feedback)} 条待处理的反馈")
            
            # 处理反馈
            processing_results = []
            success_count = 0
            failure_count = 0
            
            for feedback in pending_feedback:
                try:
                    result = await self._process_single_feedback(feedback)
                    processing_results.append(result)
                    
                    if result["success"]:
                        success_count += 1
                    else:
                        failure_count += 1
                        
                except Exception as e:
                    failure_count += 1
                    error_result = {
                        "feedback_id": feedback.id,
                        "success": False,
                        "error": f"处理反馈时发生异常: {str(e)}",
                        "user_id": feedback.user_id
                    }
                    processing_results.append(error_result)
                    logger.error(f"处理反馈 {feedback.id} 时发生异常: {str(e)}")
            
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"用户评价反馈处理完成，成功: {success_count}, 失败: {failure_count}, 耗时: {duration:.2f}秒")
            
            return UserProfileFeedbackProcessingResponse(
                processed_count=len(pending_feedback),
                success_count=success_count,
                failure_count=failure_count,
                processing_results=processing_results
            )
            
        except Exception as e:
            logger.error(f"处理用户评价反馈失败: {str(e)}")
            raise
    
    def get_pending_feedback(self, user_id: str = None, limit: int = 50) -> List[UserProfileFeedback]:
        """获取待处理的用户评价反馈
        
        Args:
            user_id: 指定用户ID，如果为None则获取所有用户的待处理反馈
            limit: 最大返回数量
            
        Returns:
            待处理的反馈列表
        """
        try:
            # 获取最近30天内创建的、未处理的反馈
            cutoff_date = datetime.now() - timedelta(days=30)
            
            query = self.db.query(UserProfileFeedback).filter(
                and_(
                    UserProfileFeedback.is_processed == False,
                    UserProfileFeedback.created_at >= cutoff_date
                )
            )
            
            # 如果指定了用户ID，添加用户过滤条件
            if user_id:
                query = query.filter(UserProfileFeedback.user_id == user_id)
            
            feedback = query.order_by(
                UserProfileFeedback.created_at.asc()
            ).limit(limit).all()
            
            return feedback
            
        except Exception as e:
            logger.error(f"获取待处理反馈失败: {str(e)}")
            return []
    
    async def _process_single_feedback(self, feedback: UserProfileFeedback) -> Dict[str, Any]:
        """处理单条用户反馈"""
        try:
            logger.info(f"开始处理反馈 {feedback.id}，用户 {feedback.user_id}")
            
            # 获取用户当前画像
            current_profile = self.profile_service.get_active_user_profile(feedback.user_id)
            if not current_profile:
                return {
                    "feedback_id": feedback.id,
                    "success": False,
                    "error": "用户画像不存在",
                    "user_id": feedback.user_id
                }
            
            # 获取用户信息
            user = self.db.query(User).filter(User.id == feedback.user_id).first()
            if not user:
                return {
                    "feedback_id": feedback.id,
                    "success": False,
                    "error": "用户不存在",
                    "user_id": feedback.user_id
                }
            
            # 使用LLM分析用户反馈并生成画像更新建议
            update_suggestion = await self._analyze_feedback_with_llm(
                user, current_profile, feedback
            )
            
            if not update_suggestion["success"]:
                return {
                    "feedback_id": feedback.id,
                    "success": False,
                    "error": f"LLM分析失败: {update_suggestion.get('error', '未知错误')}",
                    "user_id": feedback.user_id
                }
            
            # 应用画像更新
            update_result = await self._apply_profile_update(
                feedback.user_id, current_profile, update_suggestion["update_data"]
            )
            
            if not update_result["success"]:
                return {
                    "feedback_id": feedback.id,
                    "success": False,
                    "error": f"画像更新失败: {update_result.get('error', '未知错误')}",
                    "user_id": feedback.user_id
                }
            
            # 标记反馈为已处理
            feedback.is_processed = True
            feedback.processed_at = datetime.now()
            feedback.processing_result = {
                "update_suggestion": update_suggestion["update_data"],
                "confidence_score": update_suggestion["confidence_score"],
                "applied_changes": update_result["applied_changes"]
            }
            feedback.updated_profile_id = update_result["new_profile_id"]
            
            self.db.commit()
            
            logger.info(f"反馈 {feedback.id} 处理成功，用户 {feedback.user_id}")
            
            return {
                "feedback_id": feedback.id,
                "success": True,
                "user_id": feedback.user_id,
                "confidence_score": update_suggestion["confidence_score"],
                "applied_changes": update_result["applied_changes"]
            }
            
        except Exception as e:
            logger.error(f"处理反馈 {feedback.id} 时发生异常: {str(e)}")
            self.db.rollback()
            return {
                "feedback_id": feedback.id,
                "success": False,
                "error": f"处理异常: {str(e)}",
                "user_id": feedback.user_id
            }
    
    async def _analyze_feedback_with_llm(
        self, 
        user: User, 
        current_profile: UserProfile, 
        feedback: UserProfileFeedback
    ) -> Dict[str, Any]:
        """使用LLM分析用户反馈并生成画像更新建议"""
        try:
            # 构建分析提示词
            analysis_prompt = self._build_feedback_analysis_prompt(
                user, current_profile, feedback
            )
            
            # 调用LLM进行分析
            llm_request = LLMRequest(
                user_id=str(user.id),
                task_type=LLMTaskType.PROFILE_ANALYSIS,
                prompt=analysis_prompt,
                context={
                    "task": "feedback_analysis",
                    "feedback_id": feedback.id,
                    "current_profile_id": current_profile.id,
                    "rating": feedback.rating,
                    "evaluation_type": feedback.evaluation_type
                }
            )
            
            response = await self.llm_service.call_llm_api(
                request=llm_request,
                provider=LLMProvider.VOLCENGINE,
                model_name=self.model_name
            )
            
            if not response.success:
                return {
                    "success": False,
                    "error": f"LLM调用失败: {response.data}"
                }
            
            # 解析LLM响应
            update_data = self._parse_feedback_analysis_response(response.data)
            
            return {
                "success": True,
                "update_data": update_data,
                "confidence_score": update_data.get("confidence_score", 70)
            }
            
        except Exception as e:
            logger.error(f"LLM分析用户反馈失败: {str(e)}")
            return {
                "success": False,
                "error": f"LLM分析异常: {str(e)}"
            }
    
    def _build_feedback_analysis_prompt(
        self, 
        user: User, 
        current_profile: UserProfile, 
        feedback: UserProfileFeedback
    ) -> str:
        """构建反馈分析提示词"""
        
        prompt = f"""
        你是一位专业的用户画像分析师，需要根据用户的反馈评价来分析和更新用户画像。
        
        当前用户信息：
        - 用户昵称：{user.nickname or '未知'}
        - 用户性别：{user.gender or '未知'}
        - 用户年龄：{user.age or '未知'}
        
        当前用户画像信息：
        - 用户偏好：{json.dumps(current_profile.preferences or {}, ensure_ascii=False)}
        - 个性特征：{json.dumps(current_profile.personality_traits or {}, ensure_ascii=False)}
        - 心情状态：{json.dumps(current_profile.mood_state or {}, ensure_ascii=False)}
        - 兴趣标签：{json.dumps(current_profile.interest_tags or [], ensure_ascii=False)}
        - 社交偏好：{json.dumps(current_profile.social_preferences or {}, ensure_ascii=False)}
        - 匹配偏好：{json.dumps(current_profile.match_preferences or {}, ensure_ascii=False)}
        
        用户反馈信息：
        - 评分：{feedback.rating}/5分
        - 评价类型：{feedback.evaluation_type}
        - 评价备注：{feedback.comment or '无'}
        - 详细反馈：{json.dumps(feedback.feedback_content or {}, ensure_ascii=False)}
        - 建议改进：{json.dumps(feedback.suggested_improvements or [], ensure_ascii=False)}
        
        任务要求：
        1. 分析用户的反馈，理解用户对当前画像的不满意之处
        2. 基于用户反馈，生成具体的画像更新建议
        3. 更新应该针对性强，直接回应用户的关切
        4. 保持画像的连贯性和合理性
        5. 为每个更新项提供置信度评分（0-100）
        
        请按以下JSON格式返回分析结果：
        {{
            "preferences": {{"更新内容": "具体更新", "confidence": 85}},
            "personality_traits": {{"更新内容": "具体更新", "confidence": 80}},
            "mood_state": {{"更新内容": "具体更新", "confidence": 75}},
            "interest_tags": ["新增标签1", "新增标签2"],
            "social_preferences": {{"更新内容": "具体更新", "confidence": 82}},
            "match_preferences": {{"更新内容": "具体更新", "confidence": 88}},
            "summary": "更新总结",
            "confidence_score": 82,
            "reasoning": "更新理由说明"
        }}
        """
        
        return prompt
    
    def _parse_feedback_analysis_response(self, response_data: str) -> Dict[str, Any]:
        """解析LLM反馈分析响应"""
        try:
            # 尝试直接解析JSON
            if isinstance(response_data, str):
                import json
                parsed_data = json.loads(response_data)
            else:
                parsed_data = response_data
            
            # 验证必要的字段
            required_fields = ["preferences", "personality_traits", "mood_state", 
                             "interest_tags", "social_preferences", "match_preferences"]
            
            # 如果缺少必要字段，构建默认响应
            for field in required_fields:
                if field not in parsed_data:
                    if field == "interest_tags":
                        parsed_data[field] = []
                    else:
                        parsed_data[field] = {"更新内容": "基于用户反馈调整", "confidence": 70}
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"解析LLM响应失败: {str(e)}")
            # 返回默认结构
            return {
                "preferences": {"更新内容": "基于用户反馈调整", "confidence": 70},
                "personality_traits": {"更新内容": "基于用户反馈调整", "confidence": 70},
                "mood_state": {"更新内容": "基于用户反馈调整", "confidence": 70},
                "interest_tags": [],
                "social_preferences": {"更新内容": "基于用户反馈调整", "confidence": 70},
                "match_preferences": {"更新内容": "基于用户反馈调整", "confidence": 70},
                "summary": "基于用户反馈的画像调整",
                "confidence_score": 70,
                "reasoning": "默认更新"
            }
    
    async def _apply_profile_update(
        self, 
        user_id: str, 
        current_profile: UserProfile, 
        update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """应用画像更新"""
        try:
            # 构建更新数据
            profile_update = UserProfileUpdate()
            applied_changes = []
            
            # 更新用户偏好
            if "preferences" in update_data and update_data["preferences"].get("更新内容"):
                current_prefs = current_profile.preferences or {}
                new_prefs = current_prefs.copy()
                new_prefs["feedback_based_updates"] = update_data["preferences"]["更新内容"]
                profile_update.preferences = new_prefs
                applied_changes.append("preferences")
            
            # 更新个性特征
            if "personality_traits" in update_data and update_data["personality_traits"].get("更新内容"):
                current_traits = current_profile.personality_traits or {}
                new_traits = current_traits.copy()
                new_traits["feedback_based_updates"] = update_data["personality_traits"]["更新内容"]
                profile_update.personality_traits = new_traits
                applied_changes.append("personality_traits")
            
            # 更新心情状态
            if "mood_state" in update_data and update_data["mood_state"].get("更新内容"):
                current_mood = current_profile.mood_state or {}
                new_mood = current_mood.copy()
                new_mood["feedback_based_updates"] = update_data["mood_state"]["更新内容"]
                profile_update.mood_state = new_mood
                applied_changes.append("mood_state")
            
            # 更新兴趣标签
            if "interest_tags" in update_data and update_data["interest_tags"]:
                current_tags = current_profile.interest_tags or []
                new_tags = list(set(current_tags + update_data["interest_tags"]))
                profile_update.interest_tags = new_tags
                applied_changes.append("interest_tags")
            
            # 更新社交偏好
            if "social_preferences" in update_data and update_data["social_preferences"].get("更新内容"):
                current_social = current_profile.social_preferences or {}
                new_social = current_social.copy()
                new_social["feedback_based_updates"] = update_data["social_preferences"]["更新内容"]
                profile_update.social_preferences = new_social
                applied_changes.append("social_preferences")
            
            # 更新匹配偏好
            if "match_preferences" in update_data and update_data["match_preferences"].get("更新内容"):
                current_match = current_profile.match_preferences or {}
                new_match = current_match.copy()
                new_match["feedback_based_updates"] = update_data["match_preferences"]["更新内容"]
                profile_update.match_preferences = new_match
                applied_changes.append("match_preferences")
            
            # 设置更新原因和置信度
            profile_update.update_reason = f"基于用户反馈的画像更新 - {update_data.get('summary', '反馈驱动更新')}"
            profile_update.confidence_score = update_data.get("confidence_score", 70)
            
            # 执行更新
            updated_profile = self.profile_service.update_user_profile(
                current_profile.id,
                profile_update,
                change_source="feedback_processing",
                change_reason=f"基于用户反馈的自动更新 - {update_data.get('reasoning', '反馈分析')}"
            )
            
            if not updated_profile:
                return {
                    "success": False,
                    "error": "画像更新失败"
                }
            
            return {
                "success": True,
                "new_profile_id": updated_profile.id,
                "applied_changes": applied_changes
            }
            
        except Exception as e:
            logger.error(f"应用画像更新失败: {str(e)}")
            return {
                "success": False,
                "error": f"应用更新异常: {str(e)}"
            }
    
    def get_unprocessed_feedback_count(self) -> int:
        """获取未处理的反馈数量"""
        try:
            count = self.db.query(UserProfileFeedback).filter(
                UserProfileFeedback.is_processed == False
            ).count()
            return count
        except Exception as e:
            logger.error(f"获取未处理反馈数量失败: {str(e)}")
            return 0
    
    def get_feedback_statistics(self, days: int = 30) -> Dict[str, Any]:
        """获取反馈统计信息"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # 总反馈数量
            total_feedback = self.db.query(UserProfileFeedback).filter(
                UserProfileFeedback.created_at >= cutoff_date
            ).count()
            
            # 已处理反馈数量
            processed_feedback = self.db.query(UserProfileFeedback).filter(
                and_(
                    UserProfileFeedback.created_at >= cutoff_date,
                    UserProfileFeedback.is_processed == True
                )
            ).count()
            
            # 平均评分
            avg_rating = self.db.query(func.avg(UserProfileFeedback.rating)).filter(
                UserProfileFeedback.created_at >= cutoff_date
            ).scalar() or 0
            
            # 按评分分布
            rating_distribution = {}
            for rating in range(1, 6):
                count = self.db.query(UserProfileFeedback).filter(
                    and_(
                        UserProfileFeedback.created_at >= cutoff_date,
                        UserProfileFeedback.rating == rating
                    )
                ).count()
                rating_distribution[str(rating)] = count
            
            return {
                "total_feedback": total_feedback,
                "processed_feedback": processed_feedback,
                "unprocessed_feedback": total_feedback - processed_feedback,
                "processing_rate": processed_feedback / total_feedback if total_feedback > 0 else 0,
                "average_rating": round(float(avg_rating), 2),
                "rating_distribution": rating_distribution,
                "statistics_period_days": days
            }
            
        except Exception as e:
            logger.error(f"获取反馈统计失败: {str(e)}")
            return {
                "total_feedback": 0,
                "processed_feedback": 0,
                "unprocessed_feedback": 0,
                "processing_rate": 0,
                "average_rating": 0,
                "rating_distribution": {},
                "statistics_period_days": days,
                "error": str(e)
            }