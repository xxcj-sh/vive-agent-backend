"""
用户画像定期回顾服务
实现用户画像的定期回顾机制，包括季度回顾、月度回顾等
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.models.user_profile import UserProfile, UserProfileUpdate
from app.models.user_profile_history import UserProfileHistory
from app.models.user import User
from app.services.profile_learning_service import ProfileLearningService
from app.services.enhanced_user_profile_service import EnhancedUserProfileService
import logging
import asyncio

logger = logging.getLogger(__name__)


class ProfileReviewService:
    """用户画像定期回顾服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.learning_service = ProfileLearningService(db)
        self.profile_service = EnhancedUserProfileService(db)
    
    async def schedule_quarterly_review(self, user_id: str) -> Dict[str, Any]:
        """
        安排季度回顾
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 安排结果
        """
        try:
            # 获取用户当前画像
            current_profile = self.db.query(UserProfile).filter(
                UserProfile.user_id == user_id,
                UserProfile.is_active == True
            ).first()
            
            if not current_profile:
                return {"error": "用户画像不存在"}
            
            # 检查是否需要进行季度回顾
            if self._should_schedule_quarterly_review(user_id, current_profile):
                review_data = {
                    "user_id": user_id,
                    "profile_id": current_profile.id,
                    "review_type": "quarterly",
                    "scheduled_date": datetime.now() + timedelta(days=7),  # 一周后执行
                    "status": "scheduled",
                    "created_at": datetime.now()
                }
                
                # 在实际实现中，这里会将回顾任务添加到调度队列
                logger.info(f"已为用户 {user_id} 安排季度回顾")
                
                return {
                    "success": True,
                    "message": "季度回顾已安排",
                    "review_data": review_data
                }
            else:
                return {
                    "success": True,
                    "message": "暂不需要季度回顾",
                    "reason": "距离上次回顾时间太短"
                }
                
        except Exception as e:
            logger.error(f"安排季度回顾失败: {str(e)}")
            return {"error": f"安排季度回顾失败: {str(e)}"}
    
    async def perform_quarterly_review(self, user_id: str) -> Dict[str, Any]:
        """
        执行季度回顾
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 回顾结果
        """
        try:
            # 获取用户当前画像
            current_profile = self.db.query(UserProfile).filter(
                UserProfile.user_id == user_id,
                UserProfile.is_active == True
            ).first()
            
            if not current_profile:
                return {"error": "用户画像不存在"}
            
            # 获取用户基本信息
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"error": "用户不存在"}
            
            # 获取回顾期间的历史数据
            review_period_data = await self._collect_review_period_data(user_id, "quarterly")
            
            # 生成回顾报告
            review_report = await self._generate_quarterly_review_report(
                user, current_profile, review_period_data
            )
            
            # 获取用户确认
            user_confirmation = await self._get_user_confirmation(user_id, review_report)
            
            if user_confirmation["confirmed"]:
                # 应用用户确认的更新
                update_result = await self._apply_review_updates(
                    user_id, current_profile.id, user_confirmation["updates"]
                )
                
                return {
                    "success": True,
                    "review_completed": True,
                    "review_report": review_report,
                    "user_confirmation": user_confirmation,
                    "update_result": update_result
                }
            else:
                return {
                    "success": True,
                    "review_completed": False,
                    "review_report": review_report,
                    "user_confirmation": user_confirmation,
                    "message": "用户未确认更新"
                }
                
        except Exception as e:
            logger.error(f"执行季度回顾失败: {str(e)}")
            return {"error": f"执行季度回顾失败: {str(e)}"}
    
    async def perform_monthly_review(self, user_id: str) -> Dict[str, Any]:
        """
        执行月度回顾
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 回顾结果
        """
        try:
            # 获取用户当前画像
            current_profile = self.db.query(UserProfile).filter(
                UserProfile.user_id == user_id,
                UserProfile.is_active == True
            ).first()
            
            if not current_profile:
                return {"error": "用户画像不存在"}
            
            # 获取用户基本信息
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"error": "用户不存在"}
            
            # 获取回顾期间的历史数据
            review_period_data = await self._collect_review_period_data(user_id, "monthly")
            
            # 生成月度回顾报告
            review_report = await self._generate_monthly_review_report(
                user, current_profile, review_period_data
            )
            
            # 检查是否需要用户确认（月度回顾可能自动应用小的更新）
            if review_report["requires_confirmation"]:
                user_confirmation = await self._get_user_confirmation(user_id, review_report)
                
                if user_confirmation["confirmed"]:
                    update_result = await self._apply_review_updates(
                        user_id, current_profile.id, user_confirmation["updates"]
                    )
                    
                    return {
                        "success": True,
                        "review_completed": True,
                        "review_report": review_report,
                        "user_confirmation": user_confirmation,
                        "update_result": update_result
                    }
                else:
                    return {
                        "success": True,
                        "review_completed": False,
                        "review_report": review_report,
                        "user_confirmation": user_confirmation,
                        "message": "用户未确认更新"
                    }
            else:
                # 自动应用小的更新
                update_result = await self._apply_review_updates(
                    user_id, current_profile.id, review_report["auto_updates"]
                )
                
                return {
                    "success": True,
                    "review_completed": True,
                    "review_report": review_report,
                    "auto_update_result": update_result,
                    "message": "月度回顾已完成，自动应用了小的更新"
                }
                
        except Exception as e:
            logger.error(f"执行月度回顾失败: {str(e)}")
            return {"error": f"执行月度回顾失败: {str(e)}"}
    
    async def generate_review_reminder(self, user_id: str, review_type: str = "quarterly") -> Dict[str, Any]:
        """
        生成回顾提醒
        
        Args:
            user_id: 用户ID
            review_type: 回顾类型
            
        Returns:
            Dict[str, Any]: 提醒内容
        """
        try:
            # 获取用户当前画像
            current_profile = self.db.query(UserProfile).filter(
                UserProfile.user_id == user_id,
                UserProfile.is_active == True
            ).first()
            
            if not current_profile:
                return {"error": "用户画像不存在"}
            
            # 获取用户基本信息
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                return {"error": "用户不存在"}
            
            # 生成提醒内容
            reminder_content = await self._generate_review_reminder_content(
                user, current_profile, review_type
            )
            
            return {
                "success": True,
                "reminder_type": review_type,
                "reminder_content": reminder_content,
                "scheduled_for": datetime.now() + timedelta(days=7),
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"生成回顾提醒失败: {str(e)}")
            return {"error": f"生成回顾提醒失败: {str(e)}"}
    
    def _should_schedule_quarterly_review(self, user_id: str, current_profile: UserProfile) -> bool:
        """判断是否应该安排季度回顾"""
        # 获取最近的历史记录
        recent_history = self.db.query(UserProfileHistory).filter(
            UserProfileHistory.user_id == user_id,
            UserProfileHistory.change_type == "review_update"
        ).order_by(UserProfileHistory.created_at.desc()).first()
        
        if not recent_history:
            return True  # 从未进行过回顾
        
        # 检查距离上次回顾的时间
        days_since_last_review = (datetime.now() - recent_history.created_at).days
        return days_since_last_review >= 90  # 90天前进行过回顾
    
    async def _collect_review_period_data(self, user_id: str, review_type: str) -> Dict[str, Any]:
        """收集回顾期间的数据"""
        # 确定时间窗口
        if review_type == "quarterly":
            days_back = 90
        elif review_type == "monthly":
            days_back = 30
        else:
            days_back = 7  # weekly
        
        start_date = datetime.now() - timedelta(days=days_back)
        
        # 获取历史记录
        history_records = self.db.query(UserProfileHistory).filter(
            UserProfileHistory.user_id == user_id,
            UserProfileHistory.created_at >= start_date
        ).order_by(UserProfileHistory.created_at.desc()).all()
        
        # 获取行为数据（这里需要集成实际的行为数据服务）
        behavioral_data = await self._collect_behavioral_data_for_review(user_id, start_date)
        
        return {
            "review_period": {
                "type": review_type,
                "start_date": start_date.isoformat(),
                "end_date": datetime.now().isoformat(),
                "days": days_back
            },
            "history_summary": {
                "total_changes": len(history_records),
                "manual_updates": len([h for h in history_records if h.change_type == "manual_update"]),
                "auto_updates": len([h for h in history_records if h.change_type == "auto_update"]),
                "review_updates": len([h for h in history_records if h.change_type == "review_update"])
            },
            "behavioral_data": behavioral_data,
            "confidence_trend": self._calculate_confidence_trend(history_records)
        }
    
    async def _generate_quarterly_review_report(self, user: User, current_profile: UserProfile, review_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成季度回顾报告"""
        # 这里可以集成LLM来生成更智能的报告
        report = {
            "review_type": "quarterly",
            "user_id": user.id,
            "profile_id": current_profile.id,
            "review_period": review_data["review_period"],
            "summary": {
                "total_interactions": review_data["behavioral_data"]["total_interactions"],
                "profile_accuracy": current_profile.confidence_score or 0,
                "major_changes": review_data["history_summary"]["total_changes"]
            },
            "key_findings": [
                "用户在过去90天内表现出对技术话题的持续关注",
                "社交活跃度有所提升，但主要集中在晚间时段",
                "匹配偏好在过去季度内发生了显著变化"
            ],
            "suggested_updates": {
                "preferences": {
                    "technology_interest": 0.8,
                    "social_activity_time": "evening"
                },
                "behavior_patterns": {
                    "peak_activity_hours": [19, 20, 21],
                    "interaction_frequency": "increased"
                },
                "confidence_score": min(100, (current_profile.confidence_score or 0) + 5)
            },
            "requires_confirmation": True,  # 季度回顾需要用户确认
            "confidence_impact": "positive",
            "generated_at": datetime.now().isoformat()
        }
        
        return report
    
    async def _generate_monthly_review_report(self, user: User, current_profile: UserProfile, review_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成月度回顾报告"""
        report = {
            "review_type": "monthly",
            "user_id": user.id,
            "profile_id": current_profile.id,
            "review_period": review_data["review_period"],
            "summary": {
                "total_interactions": review_data["behavioral_data"]["total_interactions"],
                "profile_accuracy": current_profile.confidence_score or 0,
                "minor_changes": review_data["history_summary"]["total_changes"]
            },
            "minor_findings": [
                "用户在本月内对娱乐内容的兴趣略有增加",
                "社交互动时间主要集中在周末"
            ],
            "auto_updates": {
                "behavior_patterns": {
                    "weekend_activity": "increased"
                }
            },
            "suggested_updates": {
                "interest_tags": ["entertainment", "weekend_activities"]
            },
            "requires_confirmation": False,  # 月度回顾的小更新可以自动应用
            "confidence_impact": "neutral",
            "generated_at": datetime.now().isoformat()
        }
        
        return report
    
    async def _get_user_confirmation(self, user_id: str, review_report: Dict[str, Any]) -> Dict[str, Any]:
        """获取用户确认（这里模拟用户确认过程）"""
        # 在实际实现中，这里会通过消息系统向用户发送回顾报告并等待确认
        # 目前返回模拟的确认结果
        return {
            "confirmed": True,  # 假设用户确认了更新
            "confirmation_time": datetime.now().isoformat(),
            "user_feedback": "同意这些更新建议",
            "updates": review_report["suggested_updates"]
        }
    
    async def _apply_review_updates(self, user_id: str, profile_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """应用回顾更新"""
        try:
            # 创建更新数据
            update_data = UserProfileUpdate(
                **updates,
                update_reason="定期回顾更新",
                data_source="review_system"
            )
            
            # 使用增强服务更新画像
            updated_profile = self.profile_service.update_user_profile(
                profile_id=profile_id,
                update_data=update_data,
                change_source="system",
                change_reason="定期回顾更新"
            )
            
            if updated_profile:
                return {
                    "success": True,
                    "message": "回顾更新已成功应用",
                    "updated_profile_id": updated_profile.id,
                    "new_confidence_score": updated_profile.confidence_score
                }
            else:
                return {
                    "success": False,
                    "message": "更新失败"
                }
                
        except Exception as e:
            logger.error(f"应用回顾更新失败: {str(e)}")
            return {"error": f"应用回顾更新失败: {str(e)}"}
    
    async def _generate_review_reminder_content(self, user: User, current_profile: UserProfile, review_type: str) -> Dict[str, Any]:
        """生成回顾提醒内容"""
        reminder_templates = {
            "quarterly": {
                "title": "季度画像回顾提醒",
                "message": f"亲爱的{user.nickname or '用户'}，您的用户画像已经3个月没有更新了。我们建议您进行一次季度回顾，以确保画像准确反映您的当前状态。",
                "call_to_action": "点击进行季度回顾",
                "importance": "high"
            },
            "monthly": {
                "title": "月度画像优化提醒",
                "message": f"亲爱的{user.nickname or '用户'}，我们检测到您的行为模式有一些小变化。建议您进行月度画像优化。",
                "call_to_action": "点击进行月度优化",
                "importance": "medium"
            },
            "weekly": {
                "title": "周度画像微调提醒",
                "message": f"亲爱的{user.nickname or '用户'}，本周的画像微调可以帮助提升匹配准确度。",
                "call_to_action": "点击进行周度微调",
                "importance": "low"
            }
        }
        
        return reminder_templates.get(review_type, reminder_templates["quarterly"])
    
    def _calculate_confidence_trend(self, history_records: List[UserProfileHistory]) -> Dict[str, Any]:
        """计算置信度趋势"""
        if not history_records:
            return {"trend": "stable", "change": 0}
        
        # 按时间排序
        sorted_records = sorted(history_records, key=lambda x: x.created_at)
        
        # 计算置信度变化
        initial_confidence = sorted_records[0].confidence_score_after or 0
        final_confidence = sorted_records[-1].confidence_score_after or 0
        
        confidence_change = final_confidence - initial_confidence
        
        if confidence_change > 5:
            trend = "increasing"
        elif confidence_change < -5:
            trend = "decreasing"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "change": confidence_change,
            "initial_confidence": initial_confidence,
            "final_confidence": final_confidence
        }
    
    async def _collect_behavioral_data_for_review(self, user_id: str, start_date: datetime) -> Dict[str, Any]:
        """为回顾收集行为数据"""
        # 这里需要集成实际的行为数据收集逻辑
        # 目前返回模拟数据
        return {
            "total_interactions": 150,
            "interaction_types": {
                "chat": 80,
                "like": 40,
                "share": 20,
                "view": 10
            },
            "time_distribution": {
                "morning": 25,
                "afternoon": 35,
                "evening": 40
            },
            "engagement_metrics": {
                "average_session_duration": 15.5,
                "daily_active_rate": 0.8,
                "weekly_active_rate": 0.9
            }
        }