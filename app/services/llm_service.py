"""
大语言模型服务
提供统一的LLM API调用接口，支持多种提供商
"""

import time
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from sqlalchemy.orm import Session
import httpx
from openai import AsyncOpenAI

from app.config import settings
from app.models.llm_usage_log import LLMUsageLog, LLMProvider, LLMTaskType
from app.models.llm_schemas import (
    LLMRequest, ProfileAnalysisRequest, InterestAnalysisRequest,
    QuestionAnsweringRequest,
    LLMResponse, ProfileAnalysisResponse, InterestAnalysisResponse,
    QuestionAnsweringResponse
)

logger = logging.getLogger(__name__)

class LLMService:
    """大语言模型服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.clients = {}
        self._init_clients()
    
    def _init_clients(self):
        """初始化各个LLM客户端"""

        # 火山大语言模型客户端（使用通用配置）
        llm_api_key = settings.LLM_API_KEY
        if llm_api_key:
            self.clients[LLMProvider.VOLCENGINE] = AsyncOpenAI(
                base_url=settings.LLM_BASE_URL,
                api_key=llm_api_key
            )
        # 其他客户端初始化...
        # 可以根据需要添加更多提供商
    
    async def call_llm_api(
        self,
        request: LLMRequest,
        provider: LLMProvider = LLMProvider.VOLCENGINE,
        model_name: str = None
    ) -> LLMResponse:
        """
        调用LLM API的统一接口
        
        Args:
            request: LLM请求对象
            provider: LLM服务提供商
            model_name: 模型名称
            
        Returns:
            LLM响应对象
        """
        start_time = time.time()
        log_id = str(uuid.uuid4())
        
        # 设置默认模型名
        if model_name is None:
            model_name = getattr(settings, 'LLM_MODEL', 'unknown-model')
        # 确保model_name不为空
        if not model_name:
            model_name = 'unknown-model'
        
        try:
            # 记录开始时间
            request_start = time.time()
            
            # 根据提供商调用不同的API
            if provider == LLMProvider.VOLCENGINE:
                # 检查VOLCENGINE客户端是否已初始化
                if LLMProvider.VOLCENGINE in self.clients:
                    response = await self._call_volcengine_api(request, model_name)
                else:
                    # 如果客户端未初始化，降级使用模拟API
                    logger.warning(f"VOLCENGINE客户端未初始化，使用模拟API代替")
                    response = await self._call_mock_api(request, provider, model_name)
            else:
                # 可以扩展其他提供商
                response = await self._call_mock_api(request, provider, model_name)
            
            # 计算耗时
            duration = time.time() - request_start
            
            # 提取token使用信息
            usage = response.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)
            
            # 记录日志
            await self._log_usage(
                log_id=log_id,
                user_id=request.user_id,
                task_type=request.task_type,
                provider=provider,
                model_name=model_name,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                prompt_content=request.prompt,
                response_content=json.dumps(response, ensure_ascii=False),
                duration=duration,
                status="success"
            )
            
            return LLMResponse(
                success=True,
                data=response.get("choices", [{}])[0].get("message", {}).get("content", ""),
                usage={
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens
                },
                duration=duration
            )
            
        except Exception as e:
            duration = time.time() - start_time
            error_message = str(e)
            
            # 记录错误日志
            await self._log_usage(
                log_id=log_id,
                user_id=request.user_id,
                task_type=request.task_type,
                provider=provider,
                model_name=model_name,
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                prompt_content=request.prompt,
                response_content="",
                duration=duration,
                status="error",
                error_message=error_message
            )
            
            logger.error(f"LLM API调用失败: {error_message}")
            return LLMResponse(
                success=False,
                data=None,
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                duration=duration
            )
    


    async def _call_volcengine_api(self, request: LLMRequest, model_name: str) -> Dict[str, Any]:
        """调用火山引擎API"""
        client = self.clients.get(LLMProvider.VOLCENGINE)
        if not client:
            raise ValueError("火山引擎客户端未初始化")

        messages = [
            {"role": "system", "content": self._get_system_prompt(request.task_type)},
            {"role": "user", "content": request.prompt}
        ]

        response = await client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=1000,
            temperature=0.7
        )

        return {
            "choices": [
                {
                    "message": {
                        "content": response.choices[0].message.content
                    }
                }
            ],
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        }
    
    async def _call_mock_api(self, request: LLMRequest, provider: LLMProvider, model_name: str) -> Dict[str, Any]:
        """模拟API调用，用于测试"""
        await asyncio.sleep(1)  # 模拟网络延迟
        
        # 根据任务类型返回不同的模拟响应
        task_responses = {
            LLMTaskType.PROFILE_ANALYSIS: {
                "analysis": {
                    "personality": "外向开朗，善于沟通",
                    "interests": ["阅读", "旅行", "摄影"],
                    "values": ["家庭", "事业", "健康"]
                },
                "key_insights": [
                    "用户表现出较强的社交需求",
                    "对生活质量有较高要求"
                ],
                "recommendations": [
                    "建议多参与社交活动",
                    "推荐关注生活品质相关内容"
                ]
            },
            LLMTaskType.INTEREST_ANALYSIS: {
                "interests": ["音乐", "电影", "美食"],
                "categories": {
                    "entertainment": ["音乐", "电影"],
                    "lifestyle": ["美食", "旅行"]
                },
                "match_suggestions": [
                    "推荐同样喜欢音乐的用户",
                    "可以匹配美食爱好者"
                ]
            },

            LLMTaskType.QUESTION_ANSWERING: {
                "answer": "根据您的需求，我推荐您关注以下方面...",
                "confidence": 0.9,
                "sources": ["用户资料", "常见问题库"]
            },

        }
        
        task_type = request.task_type
        if task_type in task_responses:
            content = json.dumps(task_responses[task_type], ensure_ascii=False)
        else:
            content = f"这是来自{provider.value}的{model_name}模型的模拟响应"
        
        return {
            "choices": [
                {
                    "message": {
                        "content": content
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 50,
                "completion_tokens": 100,
                "total_tokens": 150
            }
        }
    
    def _get_system_prompt(self, task_type: LLMTaskType) -> str:
        """获取系统提示词"""
        prompts = {
            LLMTaskType.PROFILE_ANALYSIS: """
            你是一个专业的用户画像分析师。请分析用户的资料数据，
            提供深入的洞察和个性化建议。请用中文回复，
            确保分析结果准确、有用且易于理解。
            """,
            LLMTaskType.INTEREST_ANALYSIS: """
            你是一个兴趣匹配专家。请分析用户的兴趣爱好，
            识别兴趣类别，并提供相关的匹配建议。
            请用中文回复，确保分析结果实用且有趣。
            """,

            LLMTaskType.QUESTION_ANSWERING: """
            你是一个智能助手，专门帮助用户解答关于交友、租房、
            活动等方面的问题。请基于提供的上下文信息，
            给出准确、有用的回答。请用中文回复。
            """,

        }
        return prompts.get(task_type, "你是一个智能助手，请帮助用户解决问题。")
    
    async def _log_usage(
        self,
        log_id: str,
        user_id: Optional[str],
        task_type: LLMTaskType,
        provider: LLMProvider,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        prompt_content: Optional[str] = None,
        response_content: Optional[str] = None,
        duration: float = 0.0,
        status: str = "success",
        error_message: Optional[str] = None
    ):
        """记录API调用日志
        
        注意：如果日志记录失败，不会影响主要功能
        """
        try:
            # 使用简单的dict记录，避免数据库操作失败影响主流程
            log_data = {
                "id": log_id,
                "user_id": user_id,
                "task_type": task_type,
                "provider": provider,
                "model_name": model_name,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "duration": duration,
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"LLM API调用记录: {json.dumps(log_data, ensure_ascii=False)}")
            
            # 尝试数据库记录，但失败不影响功能
            try:
                # 显式设置创建和更新时间
                current_time = datetime.utcnow()
                log_entry = LLMUsageLog(
                    id=log_id,
                    user_id=user_id,
                    task_type=task_type,
                    provider=provider,
                    llm_model_name=model_name,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    prompt_content=prompt_content,
                    response_content=response_content,
                    request_duration=duration,
                    response_time=duration,
                    status=status,
                    error_message=error_message,
                    created_at=current_time,
                    updated_at=current_time
                )
                
                self.db.add(log_entry)
                self.db.commit()
            except Exception as db_error:
                logger.error(f"数据库日志记录失败，但不影响功能: {str(db_error)}")
                # 回滚事务
                self.db.rollback()
        except Exception as e:
            logger.error(f"LLM使用日志处理失败: {str(e)}")
    
    # 特定任务的便捷方法
    async def analyze_user_profile(
        self,
        user_id: str,
        profile_data: Dict[str, Any],
        card_type: str,
        provider: LLMProvider = LLMProvider.VOLCENGINE,
        model_name: str = settings.LLM_MODEL
    ) -> ProfileAnalysisResponse:
        """分析用户资料"""
        prompt = f"""
        请分析以下用户资料：
        
        卡片类型：{card_type}
        用户资料：{json.dumps(profile_data, ensure_ascii=False)}
        
        请提供：
        1. 用户画像分析（性格特点、价值观、生活方式等）
        2. 关键洞察（3-5个要点）
        3. 个性化建议（针对该用户的改进建议）
        
        请以JSON格式回复，包含analysis、key_insights和recommendations字段。
        """
        
        request = ProfileAnalysisRequest(
            user_id=user_id,
            task_type=LLMTaskType.PROFILE_ANALYSIS,
            profile_data=profile_data,
            card_type=card_type,
            prompt=prompt
        )
        
        response = await self.call_llm_api(request, provider, model_name)
        
        if response.success and response.data:
            try:
                data = json.loads(response.data)
                return ProfileAnalysisResponse(
                    success=True,
                    data=data,
                    usage=response.usage,
                    duration=response.duration,
                    analysis=data.get("analysis", {}),
                    key_insights=data.get("key_insights", []),
                    recommendations=data.get("recommendations", [])
                )
            except json.JSONDecodeError:
                pass
        
        return ProfileAnalysisResponse(
            success=False,
            data=None,
            usage=response.usage,
            duration=response.duration,
            analysis={},
            key_insights=[],
            recommendations=[]
        )
    
    async def analyze_user_interests(
        self,
        user_id: str,
        user_interests: List[str],
        context_data: Optional[Dict[str, Any]] = None,
        provider: LLMProvider = LLMProvider.VOLCENGINE,
        model_name: str = settings.LLM_MODEL
    ) -> InterestAnalysisResponse:
        """分析用户兴趣"""
        prompt = f"""
        请分析用户的兴趣爱好：
        
        兴趣列表：{json.dumps(user_interests, ensure_ascii=False)}
        上下文数据：{json.dumps(context_data, ensure_ascii=False) if context_data else "无"}
        
        请提供：
        1. 识别出的核心兴趣
        2. 兴趣分类（按类别分组）
        3. 基于兴趣的匹配建议
        
        请以JSON格式回复，包含interests、categories和match_suggestions字段。
        """
        
        request = InterestAnalysisRequest(
            user_id=user_id,
            task_type=LLMTaskType.INTEREST_ANALYSIS,
            user_interests=user_interests,
            context_data=context_data,
            prompt=prompt
        )
        
        response = await self.call_llm_api(request, provider, model_name)
        
        if response.success and response.data:
            try:
                data = json.loads(response.data)
                return InterestAnalysisResponse(
                    success=True,
                    data=data,
                    usage=response.usage,
                    duration=response.duration,
                    interests=data.get("interests", []),
                    categories=data.get("categories", {}),
                    match_suggestions=data.get("match_suggestions", [])
                )
            except json.JSONDecodeError:
                pass
        
        return InterestAnalysisResponse(
            success=False,
            data=None,
            usage=response.usage,
            duration=response.duration,
            interests=[],
            categories={},
            match_suggestions=[]
        )
    

    
    async def answer_user_question(
        self,
        user_id: str,
        question: str,
        context: Optional[Dict[str, Any]] = None,
        provider: LLMProvider = LLMProvider.VOLCENGINE,
        model_name: str = settings.LLM_MODEL
    ) -> QuestionAnsweringResponse:
        """回答用户问题"""
        context_str = json.dumps(context, ensure_ascii=False) if context else "无上下文信息"
        
        prompt = f"""
        用户问题：{question}
        
        上下文信息：{context_str}
        
        请基于提供的上下文信息，给出准确、有用的回答。
        如果上下文信息不足，请明确说明。
        
        请以JSON格式回复，包含answer、confidence和sources字段。
        """
        
        request = QuestionAnsweringRequest(
            user_id=user_id,
            task_type=LLMTaskType.QUESTION_ANSWERING,
            question=question,
            context=context,
            prompt=prompt
        )
        
        response = await self.call_llm_api(request, provider, model_name)
        
        if response.success and response.data:
            try:
                data = json.loads(response.data)
                return QuestionAnsweringResponse(
                    success=True,
                    data=data,
                    usage=response.usage,
                    duration=response.duration,
                    answer=data.get("answer", ""),
                    confidence=data.get("confidence", 0.8),
                    sources=data.get("sources", [])
                )
            except json.JSONDecodeError:
                pass
        
        return QuestionAnsweringResponse(
            success=False,
            data=None,
            usage=response.usage,
            duration=response.duration,
            answer="",
            confidence=0,
            sources=[]
        )

    async def comprehensive_analysis(
        self,
        user_id: str,
        profile_data: Dict[str, Any],
        interests: List[str],
        context: Optional[Dict[str, Any]] = None,
        analysis_types: Optional[List[str]] = None,
        provider: LLMProvider = LLMProvider.VOLCENGINE,
        model_name: str = settings.LLM_MODEL
    ) -> Dict[str, Any]:
        """
        综合分析：一次性完成用户画像、兴趣的综合分析
        
        Args:
            user_id: 用户ID
            profile_data: 用户资料数据
            user_interests: 用户兴趣列表
            context: 额外上下文信息
            provider: LLM服务提供商
            model_name: 模型名称
            
        Returns:
            包含所有分析结果的字典
        """
        
        # 构建综合分析提示词
        prompt = f"""
        请对以下用户进行综合分析：
        
        用户资料：{json.dumps(profile_data, ensure_ascii=False)}
        兴趣列表：{json.dumps(interests, ensure_ascii=False)}
        额外上下文：{json.dumps(context, ensure_ascii=False) if context else "无"}
        分析类型：{json.dumps(analysis_types, ensure_ascii=False) if analysis_types else "全部"}
        
        请提供以下方面的综合分析：
        1. 用户画像分析（性格、价值观、生活方式等）
        2. 兴趣分析与分类
        3. 个性化推荐与建议
        4. 匹配建议与潜在伙伴类型
        
        请以JSON格式回复，包含以下字段：
        - profile_analysis: 用户画像分析结果
        - interest_analysis: 兴趣分析结果
        - overall_insights: 综合洞察要点
        - recommendations: 个性化建议列表
        - match_suggestions: 匹配建议
        """
        
        # 创建LLM请求
        request = LLMRequest(
            user_id=user_id,
            task_type=LLMTaskType.COMPREHENSIVE_ANALYSIS,
            prompt=prompt
        )
        
        # 调用LLM API
        response = await self.call_llm_api(request, provider, model_name)
        
        if response.success and response.data:
            try:
                analysis_result = json.loads(response.data)
                return {
                    "success": True,
                    "data": analysis_result,
                    "usage": response.usage,
                    "duration": response.duration
                }
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "data": None,
                    "usage": response.usage,
                    "duration": response.duration,
                    "error": "分析结果格式错误"
                }
        
        return {
            "success": False,
            "data": None,
            "usage": response.usage,
            "duration": response.duration,
            "error": "综合分析失败"
        }



# 导入asyncio用于模拟API
import asyncio