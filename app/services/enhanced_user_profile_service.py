"""
增强用户画像服务
提供用户画像的创建、更新、查询、分析、历史记录等完整功能
支持显式更新、隐式学习、定期回顾等机制
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Tuple
from app.models.user_profile import UserProfile, UserProfileCreate, UserProfileUpdate
from app.models.user_profile_history import UserProfileHistory, UserProfileHistoryCreate
from app.models.user import User
from app.services.user_profile_service import UserProfileService
from app.services.llm_service import LLMService
from app.models.llm_schemas import LLMRequest, LLMTaskType
from app.models.llm_usage_log import LLMProvider
import uuid
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class EnhancedUserProfileService(UserProfileService):
    """增强用户画像服务类"""
    
    def __init__(self, db: Session):
        super().__init__(db)
        self.llm_service = LLMService(db)
        self.model_name = "ep-20251004235106-gklgg"
    
    def create_user_profile(self, profile_data: UserProfileCreate, change_source: str = "user") -> UserProfile:
        """
        创建用户画像（带历史记录）
        
        Args:
            profile_data: 用户画像创建数据
            change_source: 变更来源: user, system, admin, llm
            
        Returns:
            UserProfile: 创建的画像对象
        """
        # 调用父类方法创建画像
        profile = super().create_user_profile(profile_data)
        
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
            Optional[UserProfile]: 更新后的画像对象
        """
        # 获取当前画像数据
        current_profile = self.get_user_profile(profile_id)
        if not current_profile:
            return None
        
        # 记录变更前的数据
        previous_data = self._extract_profile_data(current_profile)
        
        # 更新画像
        updated_profile = super().update_user_profile(profile_id, update_data)
        if not updated_profile:
            return None
        
        # 记录变更后的数据
        current_data = self._extract_profile_data(updated_profile)
        
        # 计算变更字段
        changed_fields = self._calculate_changed_fields(previous_data, current_data)
        
        # 确定变更类型
        change_type = self._determine_change_type(change_source, change_reason)
        
        # 创建历史记录
        history_data = UserProfileHistoryCreate(
            profile_id=profile_id,
            user_id=updated_profile.user_id,
            version=updated_profile.version,
            change_type=change_type,
            change_source=change_source,
            change_reason=change_reason or update_data.update_reason or "用户画像更新",
            confidence_score_before=current_profile.confidence_score,
            confidence_score_after=updated_profile.confidence_score,
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
        
        return updated_profile
    
    def get_profile_history(self, user_id: str, profile_id: Optional[str] = None,
                           limit: int = 50, offset: int = 0) -> List[UserProfileHistory]:
        """
        获取用户画像历史记录
        
        Args:
            user_id: 用户ID
            profile_id: 画像ID（可选）
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            List[UserProfileHistory]: 历史记录列表
        """
        query = self.db.query(UserProfileHistory).filter(UserProfileHistory.user_id == user_id)
        
        if profile_id:
            query = query.filter(UserProfileHistory.profile_id == profile_id)
        
        return query.order_by(UserProfileHistory.created_at.desc()).offset(offset).limit(limit).all()
    
    def compare_profile_versions(self, profile_id: str, version1: int, version2: int) -> Dict[str, Any]:
        """
        对比两个版本的用户画像
        
        Args:
            profile_id: 画像ID
            version1: 版本1
            version2: 版本2
            
        Returns:
            Dict[str, Any]: 对比结果
        """
        # 获取两个版本的历史记录
        history1 = self.db.query(UserProfileHistory).filter(
            UserProfileHistory.profile_id == profile_id,
            UserProfileHistory.version == version1
        ).first()
        
        history2 = self.db.query(UserProfileHistory).filter(
            UserProfileHistory.profile_id == profile_id,
            UserProfileHistory.version == version2
        ).first()
        
        if not history1 or not history2:
            return {"error": "找不到指定的版本记录"}
        
        # 提取数据
        data1 = self._extract_historical_data(history1, "previous")
        data2 = self._extract_historical_data(history2, "current")
        
        # 计算差异
        differences = self._calculate_detailed_differences(data1, data2)
        
        return {
            "profile_id": profile_id,
            "user_id": history1.user_id,
            "version1": version1,
            "version2": version2,
            "version1_data": data1,
            "version2_data": data2,
            "differences": differences,
            "change_summary": self._generate_detailed_summary(differences)
        }
    
    async def suggest_profile_updates(self, user_id: str, context_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        基于用户行为数据智能推荐画像更新
        
        Args:
            user_id: 用户ID
            context_data: 上下文数据
            
        Returns:
            Dict[str, Any]: 更新建议
        """
        # 获取当前激活的画像
        current_profile = self.get_active_user_profile(user_id)
        if not current_profile:
            return {"error": "用户画像不存在"}
        
        # 获取用户最新数据
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "用户不存在"}
        
        # 构建分析提示词
        analysis_prompt = self._build_suggestion_prompt(user, current_profile, context_data)
        
        # 调用LLM进行分析
        llm_request = LLMRequest(
            user_id=str(user_id),
            task_type=LLMTaskType.PROFILE_ANALYSIS,
            prompt=analysis_prompt,
            context={
                "task": "profile_suggestion",
                "user_id": str(user_id),
                "current_confidence": current_profile.confidence_score or 0
            }
        )
        
        response = await self.llm_service.call_llm_api(
            request=llm_request,
            provider=LLMProvider.VOLCENGINE,
            model_name=self.model_name
        )
        
        if not response.success:
            return {"error": f"LLM分析失败: {response.data}"}
        
        # 解析建议结果
        suggestions = self._parse_suggestion_response(response.data)
        
        return {
            "user_id": user_id,
            "suggestions": suggestions["suggestions"],
            "confidence_score": suggestions["confidence_score"],
            "reasoning": suggestions["reasoning"],
            "generated_at": datetime.now().isoformat()
        }
    
    async def perform_implicit_learning(self, user_id: str, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行隐式学习，基于用户交互行为更新画像
        
        Args:
            user_id: 用户ID
            interaction_data: 交互数据
            
        Returns:
            Dict[str, Any]: 学习结果
        """
        try:
            # 获取当前画像
            current_profile = self.get_active_user_profile(user_id)
            if not current_profile:
                return {"error": "用户画像不存在"}
            
            # 构建学习提示词
            learning_prompt = self._build_implicit_learning_prompt(user_id, current_profile, interaction_data)
            
            # 调用LLM进行隐式学习
            llm_request = LLMRequest(
                user_id=str(user_id),
                task_type=LLMTaskType.PROFILE_ANALYSIS,
                prompt=learning_prompt,
                context={
                    "task": "implicit_learning",
                    "user_id": str(user_id),
                    "interaction_type": interaction_data.get("type", "unknown")
                }
            )
            
            response = await self.llm_service.call_llm_api(
                request=llm_request,
                provider=LLMProvider.VOLCENGINE,
                model_name=self.model_name
            )
            
            if not response.success:
                return {"error": f"隐式学习失败: {response.data}"}
            
            # 解析学习结果
            learning_result = self._parse_learning_response(response.data)
            
            # 如果有重要的学习发现，更新画像
            if learning_result["should_update"] and learning_result["updates"]:
                update_data = UserProfileUpdate(
                    preferences=learning_result["updates"].get("preferences"),
                    behavior_patterns=learning_result["updates"].get("behavior_patterns"),
                    confidence_score=learning_result["updates"].get("confidence_score", current_profile.confidence_score),
                    update_reason=f"基于{interaction_data.get('type', '交互')}的隐式学习",
                    data_source="implicit_learning"
                )
                
                updated_profile = self.update_user_profile(
                    current_profile.id, 
                    update_data,
                    change_source="llm",
                    change_reason=learning_result["reasoning"]
                )
                
                return {
                    "success": True,
                    "updated": True,
                    "updates": learning_result["updates"],
                    "reasoning": learning_result["reasoning"],
                    "confidence_score": learning_result["updates"].get("confidence_score", current_profile.confidence_score)
                }
            
            return {
                "success": True,
                "updated": False,
                "reasoning": learning_result["reasoning"],
                "suggestions": learning_result.get("suggestions", [])
            }
            
        except Exception as e:
            logger.error(f"隐式学习过程出错: {str(e)}")
            return {"error": f"隐式学习过程出错: {str(e)}"}
    
    def schedule_profile_review(self, user_id: str, review_type: str = "quarterly") -> Dict[str, Any]:
        """
        安排用户画像定期回顾
        
        Args:
            user_id: 用户ID
            review_type: 回顾类型: quarterly, monthly, weekly
            
        Returns:
            Dict[str, Any]: 安排结果
        """
        # 这里可以集成到调度系统中
        review_schedule = {
            "user_id": user_id,
            "review_type": review_type,
            "scheduled_at": self._calculate_review_date(review_type),
            "status": "scheduled",
            "reminder_enabled": True
        }
        
        # 在实际实现中，这里会将回顾任务添加到调度队列
        logger.info(f"已为用户 {user_id} 安排 {review_type} 画像回顾")
        
        return review_schedule
    
    def _create_history_record(self, history_data: UserProfileHistoryCreate) -> UserProfileHistory:
        """创建历史记录"""
        history_record = UserProfileHistory(**history_data.dict())
        self.db.add(history_record)
        self.db.commit()
        self.db.refresh(history_record)
        return history_record
    
    def _extract_profile_data(self, profile: UserProfile) -> Dict[str, Any]:
        """提取画像数据"""
        return {
            "preferences": profile.preferences,
            "personality_traits": profile.personality_traits,
            "mood_state": profile.mood_state,
            "behavior_patterns": profile.behavior_patterns,
            "interest_tags": profile.interest_tags,
            "social_preferences": profile.social_preferences,
            "match_preferences": profile.match_preferences
        }
    
    def _calculate_changed_fields(self, previous_data: Dict[str, Any], current_data: Dict[str, Any]) -> List[str]:
        """计算变更的字段"""
        changed_fields = []
        
        for field in previous_data.keys():
            if previous_data[field] != current_data[field]:
                changed_fields.append(field)
        
        return changed_fields
    
    def _determine_change_type(self, change_source: str, change_reason: str) -> str:
        """确定变更类型"""
        if change_source == "user":
            return "manual_update"
        elif change_source == "llm":
            return "auto_update"
        elif change_source == "system":
            return "review_update"
        else:
            return "update"
    
    def _generate_change_summary(self, changed_fields: List[str]) -> str:
        """生成变更摘要"""
        if not changed_fields:
            return "无变更"
        
        field_names = {
            "preferences": "用户偏好",
            "personality_traits": "个性特征",
            "mood_state": "心情状态",
            "behavior_patterns": "行为模式",
            "interest_tags": "兴趣标签",
            "social_preferences": "社交偏好",
            "match_preferences": "匹配偏好"
        }
        
        changed_names = [field_names.get(field, field) for field in changed_fields]
        return f"更新了: {', '.join(changed_names)}"
    
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
    
    def _build_suggestion_prompt(self, user: User, current_profile: UserProfile, context_data: Optional[Dict[str, Any]]) -> str:
        """构建建议提示词"""
        prompt = f"""
        作为用户画像分析专家，请基于以下信息分析用户画像并提出更新建议：
        
        用户基本信息：
        - 用户ID: {user.id}
        - 性别: {user.gender}
        - 年龄: {user.age}
        - 地区: {user.location or '未知地区'}
        - 职业: {getattr(user, 'occupation', '未知')}
        
        当前用户画像（置信度: {current_profile.confidence_score or 0}%）：
        - 用户偏好: {json.dumps(current_profile.preferences or {}, ensure_ascii=False)}
        - 个性特征: {json.dumps(current_profile.personality_traits or {}, ensure_ascii=False)}
        - 心情状态: {json.dumps(current_profile.mood_state or {}, ensure_ascii=False)}
        - 行为模式: {json.dumps(current_profile.behavior_patterns or {}, ensure_ascii=False)}
        - 兴趣标签: {json.dumps(current_profile.interest_tags or [], ensure_ascii=False)}
        - 社交偏好: {json.dumps(current_profile.social_preferences or {}, ensure_ascii=False)}
        - 匹配偏好: {json.dumps(current_profile.match_preferences or {}, ensure_ascii=False)}
        
        上下文数据: {json.dumps(context_data or {}, ensure_ascii=False)}
        
        请分析当前画像的完整性和准确性，并提出具体的更新建议。
        返回JSON格式，包含：
        1. suggestions: 具体的更新建议列表
        2. confidence_score: 建议的置信度评分(0-100)
        3. reasoning: 建议的理由说明
        """
        return prompt
    
    def _parse_suggestion_response(self, response_data: str) -> Dict[str, Any]:
        """解析建议响应"""
        try:
            if isinstance(response_data, str):
                import json
                data = json.loads(response_data)
            else:
                data = response_data
            
            return {
                "suggestions": data.get("suggestions", []),
                "confidence_score": data.get("confidence_score", 0),
                "reasoning": data.get("reasoning", "")
            }
        except Exception as e:
            logger.error(f"解析建议响应失败: {str(e)}")
            return {
                "suggestions": [],
                "confidence_score": 0,
                "reasoning": "解析失败"
            }
    
    def _build_implicit_learning_prompt(self, user_id: str, current_profile: UserProfile, interaction_data: Dict[str, Any]) -> str:
        """构建隐式学习提示词"""
        prompt = f"""
        作为用户行为分析专家，请基于用户的交互行为进行隐式学习分析：
        
        用户ID: {user_id}
        当前画像置信度: {current_profile.confidence_score or 0}%
        
        交互数据:
        {json.dumps(interaction_data, ensure_ascii=False, indent=2)}
        
        当前用户画像:
        - 用户偏好: {json.dumps(current_profile.preferences or {}, ensure_ascii=False)}
        - 行为模式: {json.dumps(current_profile.behavior_patterns or {}, ensure_ascii=False)}
        - 兴趣标签: {json.dumps(current_profile.interest_tags or [], ensure_ascii=False)}
        - 社交偏好: {json.dumps(current_profile.social_preferences or {}, ensure_ascii=False)}
        
        请分析这次交互行为是否反映了用户画像的变化，是否需要更新画像。
        返回JSON格式，包含：
        1. should_update: 是否需要更新画像(true/false)
        2. updates: 需要更新的字段和值
        3. reasoning: 更新理由
        4. suggestions: 给用户的相关建议（可选）
        """
        return prompt
    
    def _parse_learning_response(self, response_data: str) -> Dict[str, Any]:
        """解析学习响应"""
        try:
            if isinstance(response_data, str):
                import json
                data = json.loads(response_data)
            else:
                data = response_data
            
            return {
                "should_update": data.get("should_update", False),
                "updates": data.get("updates", {}),
                "reasoning": data.get("reasoning", ""),
                "suggestions": data.get("suggestions", [])
            }
        except Exception as e:
            logger.error(f"解析学习响应失败: {str(e)}")
            return {
                "should_update": False,
                "updates": {},
                "reasoning": "解析失败",
                "suggestions": []
            }
    
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