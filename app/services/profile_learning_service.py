"""
用户画像智能分析和学习服务
基于用户行为数据进行智能画像更新和学习
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from app.models.user_profile import UserProfile
from app.models.user import User
from app.models.llm_schemas import LLMRequest, LLMTaskType
from app.models.llm_usage_log import LLMProvider
from app.services.llm_service import LLMService
import json
import logging
from datetime import datetime
from typing import Tuple

logger = logging.getLogger(__name__)


class ProfileLearningService:
    """用户画像智能学习服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService(db)
        self.model_name = "ep-20251004235106-gklgg"
    
    async def analyze_user_interaction(self, user_id: str, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析用户交互行为并提取画像更新信息
        
        Args:
            user_id: 用户ID
            interaction_data: 交互数据，包含类型、内容、时间等
            
        Returns:
            Dict[str, Any]: 分析结果，包含是否需要更新画像、更新内容等
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
            
            # 构建分析提示词
            analysis_prompt = self._build_interaction_analysis_prompt(
                user, current_profile, interaction_data
            )
            
            # 调用LLM进行分析
            llm_request = LLMRequest(
                user_id=user_id,
                task_type=LLMTaskType.PROFILE_ANALYSIS,
                prompt=analysis_prompt,
                context={
                    "task": "interaction_analysis",
                    "interaction_type": interaction_data.get("type", "unknown"),
                    "user_id": user_id,
                    "current_confidence": current_profile.confidence_score or 0
                }
            )
            
            response = await self.llm_service.call_llm_api(
                request=llm_request,
                provider=LLMProvider.VOLCENGINE,
                model_name=self.model_name
            )
            
            if not response.success:
                return {"error": f"交互分析失败: {response.data}"}
            
            # 解析分析结果
            analysis_result = self._parse_interaction_analysis(response.data)
            
            return {
                "success": True,
                "should_update": analysis_result["should_update"],
                "update_fields": analysis_result["update_fields"],
                "confidence_change": analysis_result["confidence_change"],
                "reasoning": analysis_result["reasoning"],
                "interaction_insights": analysis_result.get("insights", [])
            }
            
        except Exception as e:
            logger.error(f"交互分析过程出错: {str(e)}")
            return {"error": f"交互分析过程出错: {str(e)}"}
    
    async def perform_behavioral_learning(self, user_id: str, time_window: str = "7d") -> Dict[str, Any]:
        """
        基于用户行为模式进行学习
        
        Args:
            user_id: 用户ID
            time_window: 时间窗口，如 "7d", "30d", "90d"
            
        Returns:
            Dict[str, Any]: 学习结果
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
            
            # 获取用户行为数据（这里需要集成实际的行为数据服务）
            behavioral_data = await self._collect_behavioral_data(user_id, time_window)
            
            # 构建学习提示词
            learning_prompt = self._build_behavioral_learning_prompt(
                user, current_profile, behavioral_data, time_window
            )
            
            # 调用LLM进行行为学习
            llm_request = LLMRequest(
                user_id=user_id,
                task_type=LLMTaskType.PROFILE_ANALYSIS,
                prompt=learning_prompt,
                context={
                    "task": "behavioral_learning",
                    "time_window": time_window,
                    "user_id": user_id,
                    "current_confidence": current_profile.confidence_score or 0
                }
            )
            
            response = await self.llm_service.call_llm_api(
                request=llm_request,
                provider=LLMProvider.VOLCENGINE,
                model_name=self.model_name
            )
            
            if not response.success:
                return {"error": f"行为学习失败: {response.data}"}
            
            # 解析学习结果
            learning_result = self._parse_behavioral_learning_response(response.data)
            
            return {
                "success": True,
                "should_update": learning_result["should_update"],
                "update_fields": learning_result["update_fields"],
                "learning_insights": learning_result["insights"],
                "confidence_change": learning_result["confidence_change"],
                "reasoning": learning_result["reasoning"],
                "behavioral_patterns": behavioral_data
            }
            
        except Exception as e:
            logger.error(f"行为学习过程出错: {str(e)}")
            return {"error": f"行为学习过程出错: {str(e)}"}
    
    async def perform_contextual_learning(self, user_id: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        基于上下文信息进行学习
        
        Args:
            user_id: 用户ID
            context_data: 上下文数据，如时间、地点、环境等
            
        Returns:
            Dict[str, Any]: 学习结果
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
            
            # 构建上下文学习提示词
            context_prompt = self._build_contextual_learning_prompt(
                user, current_profile, context_data
            )
            
            # 调用LLM进行上下文学习
            llm_request = LLMRequest(
                user_id=user_id,
                task_type=LLMTaskType.PROFILE_ANALYSIS,
                prompt=context_prompt,
                context={
                    "task": "contextual_learning",
                    "context_type": context_data.get("type", "unknown"),
                    "user_id": user_id,
                    "current_confidence": current_profile.confidence_score or 0
                }
            )
            
            response = await self.llm_service.call_llm_api(
                request=llm_request,
                provider=LLMProvider.VOLCENGINE,
                model_name=self.model_name
            )
            
            if not response.success:
                return {"error": f"上下文学习失败: {response.data}"}
            
            # 解析学习结果
            learning_result = self._parse_contextual_learning_response(response.data)
            
            return {
                "success": True,
                "should_update": learning_result["should_update"],
                "update_fields": learning_result["update_fields"],
                "contextual_insights": learning_result["insights"],
                "confidence_change": learning_result["confidence_change"],
                "reasoning": learning_result["reasoning"]
            }
            
        except Exception as e:
            logger.error(f"上下文学习过程出错: {str(e)}")
            return {"error": f"上下文学习过程出错: {str(e)}"}
    
    async def generate_profile_insights(self, user_id: str) -> Dict[str, Any]:
        """
        生成用户画像洞察报告
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 洞察报告
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
            
            # 获取用户历史行为数据
            historical_data = await self._collect_historical_data(user_id)
            
            # 构建洞察生成提示词
            insights_prompt = self._build_insights_generation_prompt(
                user, current_profile, historical_data
            )
            
            # 调用LLM生成洞察
            llm_request = LLMRequest(
                user_id=user_id,
                task_type=LLMTaskType.PROFILE_ANALYSIS,
                prompt=insights_prompt,
                context={
                    "task": "insights_generation",
                    "user_id": user_id,
                    "current_confidence": current_profile.confidence_score or 0
                }
            )
            
            response = await self.llm_service.call_llm_api(
                request=llm_request,
                provider=LLMProvider.VOLCENGINE,
                model_name=self.model_name
            )
            
            if not response.success:
                return {"error": f"洞察生成失败: {response.data}"}
            
            # 解析洞察结果
            insights = self._parse_insights_response(response.data)
            
            return {
                "success": True,
                "insights": insights["insights"],
                "confidence_score": insights["confidence_score"],
                "recommendations": insights["recommendations"],
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"洞察生成过程出错: {str(e)}")
            return {"error": f"洞察生成过程出错: {str(e)}"}
    
    def _build_interaction_analysis_prompt(self, user: User, current_profile: UserProfile, interaction_data: Dict[str, Any]) -> str:
        """构建交互分析提示词"""
        prompt = f"""
        作为用户行为分析专家，请分析以下用户交互行为，判断是否需要更新用户画像：
        
        用户基本信息：
        - 用户ID: {user.id}
        - 性别: {user.gender}
        - 年龄: {user.age}
        - 地区: {user.location or '未知地区'}
        
        当前用户画像（置信度: {current_profile.confidence_score or 0}%）：
        - 用户偏好: {json.dumps(current_profile.preferences or {}, ensure_ascii=False)}
        - 行为模式: {json.dumps(current_profile.behavior_patterns or {}, ensure_ascii=False)}
        - 兴趣标签: {json.dumps(current_profile.interest_tags or [], ensure_ascii=False)}
        - 社交偏好: {json.dumps(current_profile.social_preferences or {}, ensure_ascii=False)}
        
        交互数据：
        - 交互类型: {interaction_data.get('type', 'unknown')}
        - 交互时间: {interaction_data.get('timestamp', 'unknown')}
        - 交互内容: {json.dumps(interaction_data.get('content', {}), ensure_ascii=False)}
        - 交互结果: {json.dumps(interaction_data.get('result', {}), ensure_ascii=False)}
        - 交互上下文: {json.dumps(interaction_data.get('context', {}), ensure_ascii=False)}
        
        请分析这次交互是否反映了用户画像的变化，是否需要更新画像。
        返回JSON格式，包含：
        1. should_update: 是否需要更新画像(true/false)
        2. update_fields: 需要更新的字段和值
        3. confidence_change: 置信度变化(正负数值)
        4. reasoning: 分析理由
        5. insights: 交互洞察列表
        """
        return prompt
    
    def _build_behavioral_learning_prompt(self, user: User, current_profile: UserProfile, behavioral_data: Dict[str, Any], time_window: str) -> str:
        """构建行为学习提示词"""
        prompt = f"""
        作为用户行为模式分析专家，请基于用户的行为数据进行学习分析：
        
        用户基本信息：
        - 用户ID: {user.id}
        - 性别: {user.gender}
        - 年龄: {user.age}
        - 地区: {user.location or '未知地区'}
        
        当前用户画像（置信度: {current_profile.confidence_score or 0}%）：
        - 用户偏好: {json.dumps(current_profile.preferences or {}, ensure_ascii=False)}
        - 行为模式: {json.dumps(current_profile.behavior_patterns or {}, ensure_ascii=False)}
        - 兴趣标签: {json.dumps(current_profile.interest_tags or [], ensure_ascii=False)}
        - 社交偏好: {json.dumps(current_profile.social_preferences or {}, ensure_ascii=False)}
        
        行为数据（时间窗口: {time_window}）：
        {json.dumps(behavioral_data, ensure_ascii=False, indent=2)}
        
        请分析用户的行为模式，判断是否需要更新用户画像。
        返回JSON格式，包含：
        1. should_update: 是否需要更新画像(true/false)
        2. update_fields: 需要更新的字段和值
        3. insights: 行为洞察列表
        4. confidence_change: 置信度变化
        5. reasoning: 学习理由
        """
        return prompt
    
    def _build_contextual_learning_prompt(self, user: User, current_profile: UserProfile, context_data: Dict[str, Any]) -> str:
        """构建上下文学习提示词"""
        prompt = f"""
        作为上下文分析专家，请基于用户当前的上下文信息进行学习分析：
        
        用户基本信息：
        - 用户ID: {user.id}
        - 性别: {user.gender}
        - 年龄: {user.age}
        - 地区: {user.location or '未知地区'}
        
        当前用户画像（置信度: {current_profile.confidence_score or 0}%）：
        - 用户偏好: {json.dumps(current_profile.preferences or {}, ensure_ascii=False)}
        - 行为模式: {json.dumps(current_profile.behavior_patterns or {}, ensure_ascii=False)}
        - 兴趣标签: {json.dumps(current_profile.interest_tags or [], ensure_ascii=False)}
        - 社交偏好: {json.dumps(current_profile.social_preferences or {}, ensure_ascii=False)}
        
        上下文信息：
        {json.dumps(context_data, ensure_ascii=False, indent=2)}
        
        请分析上下文信息对用户画像的影响，判断是否需要更新画像。
        返回JSON格式，包含：
        1. should_update: 是否需要更新画像(true/false)
        2. update_fields: 需要更新的字段和值
        3. insights: 上下文洞察列表
        4. confidence_change: 置信度变化
        5. reasoning: 学习理由
        """
        return prompt
    
    def _build_insights_generation_prompt(self, user: User, current_profile: UserProfile, historical_data: Dict[str, Any]) -> str:
        """构建洞察生成提示词"""
        prompt = f"""
        作为用户画像洞察专家，请基于用户的历史数据生成深度洞察报告：
        
        用户基本信息：
        - 用户ID: {user.id}
        - 性别: {user.gender}
        - 年龄: {user.age}
        - 地区: {user.location or '未知地区'}
        
        当前用户画像（置信度: {current_profile.confidence_score or 0}%）：
        - 用户偏好: {json.dumps(current_profile.preferences or {}, ensure_ascii=False)}
        - 行为模式: {json.dumps(current_profile.behavior_patterns or {}, ensure_ascii=False)}
        - 兴趣标签: {json.dumps(current_profile.interest_tags or [], ensure_ascii=False)}
        - 社交偏好: {json.dumps(current_profile.social_preferences or {}, ensure_ascii=False)}
        
        历史数据：
        {json.dumps(historical_data, ensure_ascii=False, indent=2)}
        
        请生成用户画像的深度洞察报告。
        返回JSON格式，包含：
        1. insights: 洞察列表，每个洞察包含标题、描述、重要性
        2. confidence_score: 洞察的置信度评分
        3. recommendations: 基于洞察的个性化建议
        """
        return prompt
    
    async def _collect_behavioral_data(self, user_id: str, time_window: str) -> Dict[str, Any]:
        """收集用户行为数据"""
        # 这里需要集成实际的行为数据收集逻辑
        # 目前返回模拟数据
        return {
            "interaction_count": 50,
            "interaction_types": {
                "chat": 30,
                "like": 10,
                "share": 5,
                "view": 5
            },
            "time_distribution": {
                "morning": 20,
                "afternoon": 30,
                "evening": 50
            },
            "content_preferences": {
                "technology": 0.4,
                "entertainment": 0.3,
                "lifestyle": 0.3
            },
            "social_patterns": {
                "active_users": 15,
                "interaction_depth": "medium",
                "response_time": "fast"
            }
        }
    
    async def _collect_historical_data(self, user_id: str) -> Dict[str, Any]:
        """收集用户历史数据"""
        # 这里需要集成实际的历史数据收集逻辑
        # 目前返回模拟数据
        return {
            "profile_updates": 5,
            "interaction_history": [
                {"type": "chat", "count": 100},
                {"type": "like", "count": 50},
                {"type": "share", "count": 20}
            ],
            "behavior_changes": {
                "preference_shifts": 3,
                "interest_evolution": 2
            },
            "engagement_trends": {
                "increasing": ["technology", "travel"],
                "decreasing": ["sports", "music"],
                "stable": ["food", "movies"]
            }
        }
    
    def _parse_interaction_analysis(self, response_data: str) -> Dict[str, Any]:
        """解析交互分析结果"""
        try:
            if isinstance(response_data, str):
                import json
                data = json.loads(response_data)
            else:
                data = response_data
            
            return {
                "should_update": data.get("should_update", False),
                "update_fields": data.get("update_fields", {}),
                "confidence_change": data.get("confidence_change", 0),
                "reasoning": data.get("reasoning", ""),
                "insights": data.get("insights", [])
            }
        except Exception as e:
            logger.error(f"解析交互分析结果失败: {str(e)}")
            return {
                "should_update": False,
                "update_fields": {},
                "confidence_change": 0,
                "reasoning": "解析失败",
                "insights": []
            }
    
    def _parse_behavioral_learning_response(self, response_data: str) -> Dict[str, Any]:
        """解析行为学习响应"""
        try:
            if isinstance(response_data, str):
                import json
                data = json.loads(response_data)
            else:
                data = response_data
            
            return {
                "should_update": data.get("should_update", False),
                "update_fields": data.get("update_fields", {}),
                "insights": data.get("insights", []),
                "confidence_change": data.get("confidence_change", 0),
                "reasoning": data.get("reasoning", "")
            }
        except Exception as e:
            logger.error(f"解析行为学习响应失败: {str(e)}")
            return {
                "should_update": False,
                "update_fields": {},
                "insights": [],
                "confidence_change": 0,
                "reasoning": "解析失败"
            }
    
    def _parse_contextual_learning_response(self, response_data: str) -> Dict[str, Any]:
        """解析上下文学习响应"""
        try:
            if isinstance(response_data, str):
                import json
                data = json.loads(response_data)
            else:
                data = response_data
            
            return {
                "should_update": data.get("should_update", False),
                "update_fields": data.get("update_fields", {}),
                "insights": data.get("insights", []),
                "confidence_change": data.get("confidence_change", 0),
                "reasoning": data.get("reasoning", "")
            }
        except Exception as e:
            logger.error(f"解析上下文学习响应失败: {str(e)}")
            return {
                "should_update": False,
                "update_fields": {},
                "insights": [],
                "confidence_change": 0,
                "reasoning": "解析失败"
            }
    
    def _parse_insights_response(self, response_data: str) -> Dict[str, Any]:
        """解析洞察响应"""
        try:
            if isinstance(response_data, str):
                import json
                data = json.loads(response_data)
            else:
                data = response_data
            
            return {
                "insights": data.get("insights", []),
                "confidence_score": data.get("confidence_score", 0),
                "recommendations": data.get("recommendations", [])
            }
        except Exception as e:
            logger.error(f"解析洞察响应失败: {str(e)}")
            return {
                "insights": [],
                "confidence_score": 0,
                "recommendations": []
            }