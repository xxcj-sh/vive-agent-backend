"""
用户画像离线建模服务
实现人设真实性验证、内容合规性验证、用户画像分析更新等功能
"""

import json
import time
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.user_card_db import UserCard
from app.models.user_profile import UserProfile, UserProfileUpdate
from app.models.chat_message import ChatMessage
from app.services.llm_service import LLMService
from app.models.llm_schemas import LLMRequest, LLMTaskType
from app.models.llm_usage_log import LLMProvider

logger = logging.getLogger(__name__)


class ProfileModelingService:
    """用户画像离线建模服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.llm_service = LLMService(db)
        # 从配置中读取模型名称
        from app.config import settings
        self.model_name = settings.USER_PROFILE_MODEL_NAME
    
    async def verify_profile_authenticity(self, user_id: str, card_id: str = None) -> Dict[str, Any]:
        """
        人设真实性验证
        
        Args:
            user_id: 用户ID
            card_id: 卡片ID（可选，如果提供则验证特定卡片）
            
        Returns:
            Dict[str, Any]: 验证结果，包含真实性评分和详细分析
        """
        try:
            # 获取用户基本信息和卡片信息
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"用户不存在: {user_id}")
            
            # 获取用户的卡片信息
            cards = []
            if card_id:
                card = self.db.query(UserCard).filter(
                UserCard.id == card_id,
                UserCard.user_id == user_id
            ).first()
                if card:
                    cards = [card]
            else:
                cards = self.db.query(UserCard).filter(
                    UserCard.user_id == user_id,
                    UserCard.is_active == True
                ).all()
            
            if not cards:
                return {
                    "success": False,
                    "error": "未找到有效的用户卡片",
                    "authenticity_score": 0,
                    "details": {}
                }
            
            # 构建验证提示词
            verification_prompt = self._build_authenticity_verification_prompt(user, cards)
            
            # 调用大语言模型进行真实性验证
            llm_request = LLMRequest(
                user_id=user_id,
                task_type=LLMTaskType.PROFILE_ANALYSIS,
                prompt=verification_prompt,
                context={
                    "task": "authenticity_verification",
                    "user_id": user_id,
                    "card_count": len(cards)
                }
            )
            
            response = await self.llm_service.call_llm_api(
                request=llm_request,
                provider=LLMProvider.VOLCENGINE,
                model_name=self.model_name
            )
            
            if not response.success:
                raise Exception(f"LLM调用失败: {response.data}")
            
            # 解析LLM响应
            verification_result = self._parse_authenticity_response(response.data)
            
            # 记录验证结果
            logger.info(f"用户 {user_id} 人设真实性验证完成，评分: {verification_result['authenticity_score']}")
            
            return {
                "success": True,
                "authenticity_score": verification_result["authenticity_score"],
                "risk_level": verification_result["risk_level"],
                "details": verification_result["details"],
                "recommendations": verification_result["recommendations"],
                "verified_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"人设真实性验证失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "authenticity_score": 0,
                "details": {}
            }
    
    async def verify_content_compliance(self, card_id: str) -> Dict[str, Any]:
        """
        内容合规性验证
        
        Args:
            card_id: 卡片ID
            
        Returns:
            Dict[str, Any]: 合规性验证结果
        """
        try:
            # 获取卡片信息
            card = self.db.query(UserCard).filter(UserCard.id == card_id).first()
            if not card:
                raise ValueError(f"卡片不存在: {card_id}")
            
            # 构建合规性验证提示词
            compliance_prompt = self._build_compliance_verification_prompt(card)
            
            # 调用大语言模型进行合规性验证
            llm_request = LLMRequest(
                user_id=card.user_id,
                task_type=LLMTaskType.CONTENT_MODERATION,
                prompt=compliance_prompt,
                context={
                    "task": "compliance_verification",
                    "card_id": card_id,
                    "card_type": card.role_type
                }
            )
            
            response = await self.llm_service.call_llm_api(
                request=llm_request,
                provider=LLMProvider.VOLCENGINE,
                model_name=self.model_name
            )
            
            if not response.success:
                raise Exception(f"LLM调用失败: {response.data}")
            
            # 解析合规性验证结果
            compliance_result = self._parse_compliance_response(response.data)
            
            # 更新卡片的合规状态
            if compliance_result["is_compliant"]:
                card.compliance_status = "approved"
                card.compliance_score = compliance_result["compliance_score"]
            else:
                card.compliance_status = "rejected"
                card.compliance_score = compliance_result["compliance_score"]
            
            card.compliance_check_at = datetime.now()
            card.compliance_details = compliance_result["violations"]
            
            self.db.commit()
            
            logger.info(f"卡片 {card_id} 合规性验证完成，状态: {card.compliance_status}")
            
            return {
                "success": True,
                "is_compliant": compliance_result["is_compliant"],
                "compliance_score": compliance_result["compliance_score"],
                "violations": compliance_result["violations"],
                "recommendations": compliance_result["recommendations"],
                "verified_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"内容合规性验证失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "is_compliant": False,
                "compliance_score": 0,
                "violations": []
            }
    
    async def update_user_profile_analysis(self, user_id: str) -> Dict[str, Any]:
        """
        基于用户最新聊天记录和卡片内容更新用户画像
        
        Args:
            user_id: 用户ID
            
        Returns:
            Dict[str, Any]: 更新结果
        """
        try:
            # 获取用户最新数据
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError(f"用户不存在: {user_id}")
            
            # 获取最新聊天记录（最近30天）
            recent_chats = self.db.query(ChatMessage).filter(
                ChatMessage.user_id == user_id,
                ChatMessage.created_at >= datetime.now().replace(day=1) if datetime.now().day > 1 else datetime.now().replace(month=datetime.now().month-1, day=1)
            ).order_by(ChatMessage.created_at.desc()).limit(100).all()
            
            # 获取用户的激活卡片
            active_cards = self.db.query(UserCard).filter(
                UserCard.user_id == user_id,
                UserCard.is_active == True
            ).all()
            
            if not recent_chats and not active_cards:
                return {
                    "success": False,
                    "error": "没有足够的数据进行画像分析",
                    "updated_profile": None
                }
            
            # 构建画像分析提示词
            analysis_prompt = self._build_profile_analysis_prompt(user, recent_chats, active_cards)
            
            # 调用大语言模型进行画像分析
            llm_request = LLMRequest(
                user_id=str(user_id),
                task_type=LLMTaskType.PROFILE_ANALYSIS,
                prompt=analysis_prompt,
                context={
                    "task": "profile_update",
                    "user_id": str(user_id),
                    "chat_count": len(recent_chats) if hasattr(recent_chats, '__len__') else 0,
                    "card_count": len(active_cards) if hasattr(active_cards, '__len__') else 0
                }
            )
            
            response = await self.llm_service.call_llm_api(
                request=llm_request,
                provider=LLMProvider.VOLCENGINE,
                model_name=self.model_name
            )
            
            if not response.success:
                raise Exception(f"LLM调用失败: {response.data}")
            
            # 解析画像分析结果
            profile_data = self._parse_profile_analysis_response(response.data)
            
            # 更新用户画像
            updated_profile = await self._update_user_profile_in_db(user_id, profile_data)
            
            logger.info(f"用户 {user_id} 画像更新完成")
            
            return {
                "success": True,
                "updated_profile": updated_profile,
                "analysis_summary": profile_data["summary"],
                "confidence_score": profile_data["confidence_score"],
                "updated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"用户画像更新失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "updated_profile": None
            }
    
    def _build_authenticity_verification_prompt(self, user: User, cards: List[UserCard]) -> str:
        """构建人设真实性验证提示词"""
        prompt = f"""
        请作为人设真实性验证专家，分析以下用户信息和卡片内容的真实性。
        
        用户信息：
        - 用户ID: {user.id}
        - 性别: {user.gender}
        - 年龄: {user.age}
        - 地区: {user.location}
        - 注册时间: {user.created_at}
        
        用户卡片信息：
        """
        
        for i, card in enumerate(cards, 1):
            prompt += f"""
        卡片 {i}:
        - 角色类型: {card.role_type}
        - 场景类型: {card.scene_type}
        - 显示名称: {card.display_name}
        - 简介: {card.bio or '无'}
        - 偏好: {', '.join(card.preferences) if card.preferences else '无'}
        """
        
        prompt += """
        
        请基于以下维度进行真实性评估：
        1. 信息一致性：用户基本信息与卡片内容是否一致
        2. 内容合理性：卡片内容是否符合逻辑和现实
        3. 行为模式：用户的整体行为模式是否自然
        4. 风险评估：是否存在虚假、欺诈等风险
        
        请以JSON格式返回评估结果，包含：
        {
            "authenticity_score": 0-100的整数评分,
            "risk_level": "low"/"medium"/"high",
            "details": {
                "consistency_analysis": "一致性分析",
                "content_rationality": "内容合理性分析",
                "behavior_pattern": "行为模式分析",
                "risk_factors": ["风险因素列表"]
            },
            "recommendations": ["建议措施列表"]
        }
        """
        
        return prompt
    
    def _build_compliance_verification_prompt(self, card: UserCard) -> str:
        """构建内容合规性验证提示词"""
        tags_str = ', '.join(card.tags) if card.tags else '无'
        bio_str = card.bio or '无'
        
        prompt = f"""
        请作为内容合规性审核专家，分析以下用户卡片内容是否符合社交平台和法律法规要求。
        
        卡片信息：
        - 卡片ID: {card.id}
        - 角色类型: {card.role_type}
        - 场景类型: {card.scene_type}
        - 显示名称: {card.display_name}
        - 简介: {bio_str}
        - 标签: {tags_str}
        - 可见性: {card.visibility}
        
        请检查以下合规性要求：
        1. 内容合法性：不包含违法、违规内容
        2. 社交适宜性：适合社交平台展示
        3. 道德规范：符合社会道德标准
        4. 平台政策：不违反平台使用政策
        5. 用户安全：不包含可能危害用户的内容
        
        请以JSON格式返回审核结果，包含：
        {{
            "is_compliant": true/false,
            "compliance_score": 0-100的整数评分,
            "violations": ["违规内容列表，如果没有则为空数组"],
            "violation_severity": "minor"/"major"/"critical",
            "recommendations": ["改进建议列表"]
        }}
        """
        
        return prompt
    
    def _build_profile_analysis_prompt(self, user: User, chats: List[ChatMessage], cards: List[UserCard]) -> str:
        """构建用户画像分析提示词"""
        prompt = f"""
        请作为用户画像分析专家，基于用户的聊天记录和卡片内容，分析用户的偏好、个性特征和当前心情状态。
        
        用户基本信息：
        - 用户ID: {user.id}
        - 性别: {user.gender}
        - 年龄: {user.age}
        - 地区: {user.location or '未知地区'}
        
        最新聊天记录（最近{len(chats) if hasattr(chats, '__len__') else '若干'}条）：
        """
        
        # 安全处理聊天记录，支持Mock对象
        if hasattr(chats, '__len__') and hasattr(chats, '__getitem__'):
            # 真实列表对象
            recent_chats = chats[-20:] if len(chats) > 20 else chats
        else:
            # Mock对象或其他不支持切片的对象，直接使用
            recent_chats = chats
        
        for i, chat in enumerate(recent_chats, 1):  # 只分析最近20条记录
            prompt += f"""
        {i}. [{chat.created_at}] {chat.sender_type}: {chat.content[:200]}{'...' if len(chat.content) > 200 else ''}
        """
        
        prompt += f"""
        
        用户激活卡片（{len(cards) if hasattr(cards, '__len__') else '若干'}张）：
        """
        
        for i, card in enumerate(cards, 1):
            prompt += f"""
        卡片 {i}: {card.display_name} ({card.role_type} - {card.scene_type})
        简介: {card.bio or '无'}
        标签: {', '.join(card.tags) if card.tags else '无'}
        """
        
        prompt += """
        
        请基于以上数据，分析以下方面：
        1. 用户偏好：兴趣、爱好、社交偏好等
        2. 个性特征：性格特点、行为模式等
        3. 当前心情：情感状态、心理状态等
        4. 匹配偏好：对潜在匹配对象的偏好
        
        请以JSON格式返回分析结果，包含：
        {
            "preferences": {
                "interests": ["兴趣列表"],
                "hobbies": ["爱好列表"],
                "social_preferences": {"社交偏好键值对"}
            },
            "personality_traits": {
                "main_traits": ["主要性格特征"],
                "behavior_patterns": ["行为模式描述"],
                "communication_style": "沟通风格"
            },
            "mood_state": {
                "current_mood": "当前心情状态",
                "emotional_tendency": "情感倾向",
                "stress_level": "压力水平"
            },
            "match_preferences": {
                "preferred_types": ["偏好类型"],
                "deal_breakers": ["不可接受的特点"],
                "importance_ranking": {"各因素重要性排序"}
            },
            "confidence_score": 0-100的分析置信度,
            "summary": "整体分析总结"
        }
        """
        
        return prompt
    
    def _parse_authenticity_response(self, response_data: str) -> Dict[str, Any]:
        """解析真实性验证响应"""
        try:
            # 尝试从响应中提取JSON
            import re
            json_match = re.search(r'\{.*\}', response_data, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                # 如果无法提取JSON，返回默认结果
                result = {
                    "authenticity_score": 50,
                    "risk_level": "medium",
                    "details": {"analysis": "无法解析响应"},
                    "recommendations": ["需要人工审核"]
                }
            
            # 确保包含必要字段
            return {
                "authenticity_score": result.get("authenticity_score", 50),
                "risk_level": result.get("risk_level", "medium"),
                "details": result.get("details", {}),
                "recommendations": result.get("recommendations", [])
            }
        except Exception as e:
            logger.error(f"解析真实性验证响应失败: {str(e)}")
            return {
                "authenticity_score": 50,
                "risk_level": "medium",
                "details": {"error": "解析失败"},
                "recommendations": ["需要人工审核"]
            }
    
    def _parse_compliance_response(self, response_data: str) -> Dict[str, Any]:
        """解析合规性验证响应"""
        try:
            # 尝试从响应中提取JSON
            import re
            json_match = re.search(r'\{.*\}', response_data, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                # 如果无法提取JSON，返回默认结果
                result = {
                    "is_compliant": False,
                    "compliance_score": 0,
                    "violations": ["无法解析响应内容"],
                    "recommendations": ["需要人工审核"]
                }
            
            # 确保包含必要字段
            return {
                "is_compliant": result.get("is_compliant", False),
                "compliance_score": result.get("compliance_score", 0),
                "violations": result.get("violations", []),
                "recommendations": result.get("recommendations", [])
            }
        except Exception as e:
            logger.error(f"解析合规性验证响应失败: {str(e)}")
            return {
                "is_compliant": False,
                "compliance_score": 0,
                "violations": ["解析失败"],
                "recommendations": ["需要人工审核"]
            }
    
    def _parse_profile_analysis_response(self, response_data: str) -> Dict[str, Any]:
        """解析用户画像分析响应"""
        try:
            # 尝试从响应中提取JSON
            import re
            json_match = re.search(r'\{.*\}', response_data, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
            else:
                # 如果无法提取JSON，返回默认结果
                result = {
                    "preferences": {},
                    "personality_traits": {},
                    "mood_state": {},
                    "match_preferences": {},
                    "confidence_score": 0,
                    "summary": "分析失败"
                }
            
            # 确保包含必要字段
            return {
                "preferences": result.get("preferences", {}),
                "personality_traits": result.get("personality_traits", {}),
                "mood_state": result.get("mood_state", {}),
                "match_preferences": result.get("match_preferences", {}),
                "confidence_score": result.get("confidence_score", 0),
                "summary": result.get("summary", "分析完成")
            }
        except Exception as e:
            logger.error(f"解析用户画像分析响应失败: {str(e)}")
            return {
                "preferences": {},
                "personality_traits": {},
                "mood_state": {},
                "match_preferences": {},
                "confidence_score": 0,
                "summary": "分析失败"
            }
    
    async def _update_user_profile_in_db(self, user_id: str, profile_data: Dict[str, Any]) -> Optional[UserProfile]:
        """更新数据库中的用户画像"""
        try:
            from app.services.user_profile_service import UserProfileService
            
            profile_service = UserProfileService(self.db)
            
            # 获取当前激活的用户画像
            current_profile = profile_service.get_active_user_profile(user_id)
            
            # 准备更新数据
            update_data = UserProfileUpdate(
                preferences=profile_data.get("preferences"),
                personality_traits=profile_data.get("personality_traits"),
                mood_state=profile_data.get("mood_state"),
                match_preferences=profile_data.get("match_preferences"),
                data_source="llm_analysis",
                confidence_score=profile_data.get("confidence_score", 0),
                update_reason="基于聊天记录和卡片内容的自动分析更新"
            )
            
            if current_profile:
                # 更新现有画像
                updated_profile = profile_service.update_user_profile(
                    current_profile.id, update_data
                )
            else:
                # 创建新画像
                from app.models.user_profile import UserProfileCreate
                create_data = UserProfileCreate(
                    user_id=user_id,
                    preferences=profile_data.get("preferences"),
                    personality_traits=profile_data.get("personality_traits"),
                    mood_state=profile_data.get("mood_state"),
                    match_preferences=profile_data.get("match_preferences"),
                    data_source="llm_analysis",
                    confidence_score=profile_data.get("confidence_score", 0),
                    update_reason="基于聊天记录和卡片内容的自动分析创建"
                )
                updated_profile = profile_service.create_user_profile(create_data)
            
            return updated_profile
            
        except Exception as e:
            logger.error(f"更新用户画像数据库失败: {str(e)}")
            return None