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
    LLMRequest,
    LLMResponse, ConversationSuggestionResponse, ProfileAnalysisResponse,
    ActivityInfoExtractionRequest, ActivityInfoExtractionResponse
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
        model_name: str = None,
        stream: bool = False
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
                    if stream:
                        # 流式调用，返回异步生成器
                        return self._call_volcengine_api_stream(request, model_name)
                    else:
                        response = await self._call_volcengine_api(request, model_name)
                else:
                    # 如果客户端未初始化，降级使用模拟API
                    logger.warning(f"VOLCENGINE客户端未初始化，使用模拟API代替")
                    if stream:
                        return await self._call_mock_api_stream(request, provider, model_name)
                    else:
                        response = await self._call_mock_api(request, provider, model_name)
            else:
                # 可以扩展其他提供商
                if stream:
                    return await self._call_mock_api_stream(request, provider, model_name)
                else:
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
            
            # 流式调用直接返回异步生成器
            if stream:
                return response
                
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
    


    async def _call_volcengine_api_stream(self, request: LLMRequest, model_name: str):
        """流式调用火山引擎API"""
        client = self.clients.get(LLMProvider.VOLCENGINE)
        if not client:
            raise ValueError("火山引擎客户端未初始化")

        messages = [
            {"role": "system", "content": self._get_system_prompt(request.task_type)},
            {"role": "user", "content": request.prompt}
        ]

        # 流式调用
        stream = await client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
            stream=True
        )
        
        # 返回流式响应生成器
        async for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                yield {
                    "type": "text",
                    "content": content,
                    "finished": False
                }
        
        # 发送结束标记
        yield {"type": "end"}

    async def _call_mock_api_stream(self, request: LLMRequest, provider: LLMProvider, model_name: str):
        """模拟流式API调用，用于测试"""
        import asyncio
        
        # 模拟响应内容
        mock_content = "这是来自{}的{}模型的模拟流式响应。我会为您提供一些有用的建议和信息。".format(
            provider.value, model_name
        )
        
        # 模拟流式输出，每50ms发送一个字符块
        chunk_size = 3  # 每次发送3个字符
        for i in range(0, len(mock_content), chunk_size):
            chunk = mock_content[i:i + chunk_size]
            yield {
                "type": "text", 
                "content": chunk,
                "finished": i + chunk_size >= len(mock_content)
            }
            await asyncio.sleep(0.05)  # 50ms延迟
        
        # 发送元数据
        await asyncio.sleep(0.2)
        yield {
            "type": "metadata",
            "confidence": 0.85,
            "is_meet_preference": True,
            "preference_judgement": "用户的兴趣爱好与卡片主人的偏好相符",
            "usage": {"prompt_tokens": 50, "completion_tokens": 100, "total_tokens": 150},
            "duration": 2.5
        }
        
        # 发送结束标记
        yield {"type": "end"}

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
        LLMTaskType.ACTIVITY_INFO_EXTRACTION: """
            你是一个专业的信息提取助手。请从对话历史中提取
            关于活动的关键信息，如时间、地点、偏好等。
            请用中文思考，严格按照JSON格式输出结果，
            确保提取的信息准确且完整。
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
    
    # 活动信息提取功能
    async def extract_activity_info(
        self,
        user_id: str,
        conversation_history: List[Dict[str, Any]],
        provider: LLMProvider = LLMProvider.VOLCENGINE,
        model_name: str = settings.LLM_MODEL
    ) -> ActivityInfoExtractionResponse:
        """
        从对话历史中提取活动相关信息
        
        Args:
            user_id: 用户ID
            conversation_history: 对话历史记录
            provider: LLM服务提供商
            model_name: 模型名称
            
        Returns:
            包含提取的活动信息的响应对象
        """
        prompt = f"""
        请从以下对话历史中提取活动相关的关键信息，包括但不限于：
        1. 时间 (time)：活动计划的时间
        2. 地点 (location)：活动计划的地点
        3. 偏好 (preferences)：用户表达的任何偏好
        
        对话历史：
        {json.dumps(conversation_history, ensure_ascii=False)}
        
        请严格按照以下JSON格式输出，不要包含任何额外的说明文字：
        {{
            "time": "提取的时间信息，如果未提取到则为null",
            "location": "提取的地点信息，如果未提取到则为null",
            "preferences": {{}}
        }}
        """
        
        request = ActivityInfoExtractionRequest(
            user_id=user_id,
            task_type=LLMTaskType.ACTIVITY_INFO_EXTRACTION,
            conversation_history=conversation_history,
            prompt=prompt
        )
        
        response = await self.call_llm_api(request, provider, model_name)
        
        if response.success and response.data:
            try:
                data = json.loads(response.data)
                # 确保返回的数据结构完整
                data.setdefault('time', None)
                data.setdefault('location', None)
                data.setdefault('preferences', {})
                
                return ActivityInfoExtractionResponse(
                    success=True,
                    data=json.dumps(data, ensure_ascii=False),
                    usage=response.usage,
                    duration=response.duration,
                    time_info=data.get('time'),
                    location_info=data.get('location'),
                    preference_info=data.get('preferences')
                )
            except json.JSONDecodeError:
                pass
        
        # 默认返回
        return ActivityInfoExtractionResponse(
            success=False,
            data=None,
            usage=response.usage,
            duration=response.duration,
            time_info=None,
            location_info=None,
            preference_info={}
        )
    
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
    

    def _get_role_specific_prompt(
        self,
        role_type: str,
        prompt_type: str,
        chatId: str,
        userPersonality: Dict[str, Any],
        chatHistory: List[Dict[str, Any]],
        suggestionType: str,
        maxSuggestions: int,
        preferences: Dict[str, Any],
        bio: str,
        trigger_and_output: Dict[str, Any]
    ) -> str:
        """获取特定角色类型的提示词模板"""
        # 基础信息
        base_info = f"""
        聊天ID: {chatId}
        用户性格特点: {json.dumps(userPersonality, ensure_ascii=False)}
        聊天记录: {json.dumps(chatHistory, ensure_ascii=False)}
        建议类型: {suggestionType}
        """
        
        # 根据角色类型选择不同的提示词模板
        if role_type == "trade_landlord":
            # 针对房东角色的特定提示词
            role_specific_info = f"""
            房东偏好信息: {json.dumps(preferences, ensure_ascii=False)}
            房东简介信息: {bio}
            隐藏触发条件和输出信息: {json.dumps(trigger_and_output, ensure_ascii=False)}
            """
            
            if prompt_type == "stream":
                # 流式响应的提示词模板
                return f"""
                请根据以下信息生成适合房东角色的对话建议：
                {base_info}
                {role_specific_info}
                
                请生成{maxSuggestions}条适合当前对话情境的房东回复建议，要求：
                1. 符合房东身份，自然流畅
                2. 关注收集潜在租户的关键信息（如工作稳定性、入住时间、租期要求、生活习惯等）
                3. 保持友好但专业的态度进行租金和条款协商
                4. 适当引导对话向签约意向发展
                5. 如偏好信息不为空，注意筛选符合条件的租户
                6. 每条建议独立完整
                
                直接返回建议回复内容文本
                """
            else:
                # 非流式响应的提示词模板
                return f"""
                请根据以下信息生成适合房东角色的对话建议：
                {base_info}
                {role_specific_info}
                
                请生成{maxSuggestions}条适合当前对话情境的房东回复建议，要求：
                1. 符合房东身份，以用户的身份对话，避免出现身份混淆和不符合逻辑事实的情况
                2. 自然流畅，符合对话上下文
                3. 关注收集潜在租户的关键信息（如工作稳定性、入住时间、租期要求、生活习惯等）
                4. 保持友好但专业的态度进行租金和条款协商
                5. 适当引导对话向签约意向发展
                6. 每条建议是独立完整的回复
                7. 如果偏好信息不为空，建议内容应适当引导用户回答问题，以帮助判断用户是否满足房东的偏好要求
                8. 根据用户配置的触发条件，引导用户回答问题，判断用户是否满足房东的偏好要求，在满足触发条件时也视为满足房东的偏好要求，根据用户配置的输出信息，生成建议回复消息
                9. 回复的内容需要保持公开可接受
                
                请以JSON格式回复，包含 summary(对于租客租房需求的总结，包括起租时间，租期，租金以及其他特别要求等), suggestions（为房东提供的参考建议）和 confidence（租客可靠程度）字段，is_meet_preference（是否满足房东偏好的布尔类型）字段，
                preference_judgement（满足偏好的判断论述）字段，trigger_output（触发条件后提供给租客的信息）字段
                
                参考如下格式
                """ + """
                {
                    "summary": "租客工作稳定，在互联网公司上班，希望起租时间为11月1日，租金预算 5000 每月，租期 1 年",
                    "confidence": 0.95,
                    "is_meet_preference": true,
                    "preference_judgement": "用户的租房需求与房东的偏好相符，用户对房子的基本情况表示满意，初步达成租房意向",
                    "trigger_output": "房东收到通知后会通过微信与您联系，商定签约事宜"
                }
                """
        else:
            # 默认提示词模板
            default_info = f"""
            卡片主人偏好信息: {json.dumps(preferences, ensure_ascii=False)}
            卡片简介信息（仅作为回答问题时的参考）: {bio}
            聊天隐藏触发条件和输出信息: {json.dumps(trigger_and_output, ensure_ascii=False)}
            """
            
            if prompt_type == "stream":
                # 流式响应的默认提示词模板
                return f"""
                请根据以下信息生成对话建议：
                {base_info}
                {default_info}
                
                请生成{maxSuggestions}条适合当前对话情境的回复建议，要求：
                1. 符合卡片主人性格设定，自然流畅
                2. 内容积极友好，每条建议独立完整  
                3. 如卡片主人偏好信息不为空，适当引导用户回答问题
                4. 根据触发条件判断用户是否满足偏好要求
                
                直接返回建议回复内容文本
                """
            else:
                # 非流式响应的默认提示词模板
                return f"""
                请根据以下信息生成对话建议：
                {base_info}
                {default_info}
                
                请生成{maxSuggestions}条适合当前对话情境的回复建议，要求：
                1. 符合卡片主人性格设定，以用户的身份对话，避免出现身份混淆和不符合逻辑事实的情况
                2. 自然流畅，符合对话上下文
                3. 内容积极友好
                4. 每条建议是独立完整的回复
                5. 如果卡片主人偏好信息不为空，建议内容应适当引导用户回答问题，
                   以帮助判断用户是否满足卡片主人的偏好要求
                6. 根据用户配置的触发条件，引导用户回答问题，判断用户是否满足卡片主人的偏好要求，在满足触发条件时也视为满足卡片主人的偏好要求，根据用户配置的输出信息，生成建议回复消息
                
                请以JSON格式回复，包含suggestions（建议列表）和confidence（置信度）字段，is_meet_preference（是否满足卡片主人偏好的布尔类型）字段，
                preference_judgement（满足偏好的判断论述）字段，trigger_output（触发条件后的输出信息）字段
                
                参考如下格式
                """ + """
                {
                    "confidence": 0.92,
                    "suggestions": ["欢迎参加活动", "您可以参加活动"],
                    "is_meet_preference": true,
                    "preference_judgement": "用户的兴趣爱好与卡片主人的偏好相符，用户的生活方式与卡片主人的偏好相符",
                    "trigger_output": "欢迎加我微信联系，记得备注来源哦"
                }
                """
                
    async def generate_conversation_suggestion(
        self,
        card_id: str,
        user_id: str,
        chatId: str,
        context: Dict[str, Any],
        suggestionType: str = "reply",
        maxSuggestions: int = 3,
        provider: LLMProvider = LLMProvider.VOLCENGINE,
        model_name: str = settings.LLM_MODEL
    ) -> ConversationSuggestionResponse:
        """生成对话建议"""
        # 从上下文中提取用户性格和聊天记录
        userPersonality = context.get("userPersonality", {})
        chatHistory = context.get("chatHistory", [])
        
        # 获取卡片主人信息
        card_owner_preferences = {}
        cart_trigger_and_output = {}
        card_bio = ""
        role_type = ""
        try:
            from app.models.user_card_db import UserCard
            from app.services.user_card_service import UserCardService

            user_card = UserCardService.get_card_by_id(self.db, card_id)
            if user_card:
                # 正常模式下的处理
                if hasattr(user_card, 'preferences') and user_card.preferences:
                    card_owner_preferences = user_card.preferences
                if hasattr(user_card, 'trigger_and_output') and user_card.trigger_and_output:
                    cart_trigger_and_output = user_card.trigger_and_output
                if hasattr(user_card, 'bio') and user_card.bio:
                    card_bio = user_card.bio
                if hasattr(user_card, 'role_type'):
                    role_type = user_card.role_type
        except Exception as e:
            logger.error(f"获取卡片主人信息失败: {str(e)}")

        # 获取角色特定的提示词
        prompt = self._get_role_specific_prompt(
            role_type,
            "normal",
            chatId,
            userPersonality,
            chatHistory,
            suggestionType,
            maxSuggestions,
            card_owner_preferences,
            card_bio,
            cart_trigger_and_output
        )
        
        # 创建请求对象
        request = LLMRequest(
            user_id=user_id,
            task_type=LLMTaskType.CONVERSATION_SUGGESTION,
            prompt=prompt
        )
        
        # 调用LLM API
        response = await self.call_llm_api(request, provider, model_name)
        
        if response.success and response.data:
            try:
                data = json.loads(response.data)
                # Ensure suggestions is always a list
                suggestions = data.get("suggestions", [])
                if isinstance(suggestions, str):
                    suggestions = [suggestions]
                
                return ConversationSuggestionResponse(
                    success=True,
                    data=response.data,  # 保持原始字符串格式
                    usage=response.usage,
                    duration=response.duration,
                    suggestions=suggestions,
                    confidence=data.get("confidence", 0.8),
                    is_meet_preference=data.get("is_meet_preference", False),
                    preference_judgement=data.get("preference_judgement", "")
                )
            except json.JSONDecodeError:
                # 如果解析失败，尝试将响应内容直接作为单条建议
                return ConversationSuggestionResponse(
                    success=True,
                    data=response.data,
                    usage=response.usage,
                    duration=response.duration,
                    suggestions=[response.data],
                    confidence=0.7,
                    is_meet_preference=False,
                    preference_judgement=""
                )
        
        return ConversationSuggestionResponse(
            success=False,
            data=None,
            usage=response.usage,
            duration=response.duration,
            suggestions=[],
            confidence=0,
            is_meet_preference=False,
            preference_judgement=""
        )

    async def generate_conversation_suggestion_stream(
        self,
        card_id: str,
        user_id: str,
        chatId: str,
        context: Dict[str, Any],
        suggestionType: str = "reply",
        maxSuggestions: int = 3,
        provider: LLMProvider = LLMProvider.VOLCENGINE,
        model_name: str = settings.LLM_MODEL
    ):
        """生成流式对话建议 - 真正的流式处理"""
        # 从上下文中提取用户性格和聊天记录
        userPersonality = context.get("userPersonality", {})
        chatHistory = context.get("chatHistory", [])
        
        # 获取卡片主人信息
        card_owner_preferences = {}
        cart_trigger_and_output = {}
        card_bio = ""
        role_type = ""
        try:
            from app.models.user_card_db import UserCard
            from app.services.user_card_service import UserCardService

            user_card = UserCardService.get_card_by_id(self.db, card_id)
            if user_card:
                # 正常模式下的处理
                if hasattr(user_card, 'preferences') and user_card.preferences:
                    card_owner_preferences = user_card.preferences
                if hasattr(user_card, 'trigger_and_output') and user_card.trigger_and_output:
                    cart_trigger_and_output = user_card.trigger_and_output
                if hasattr(user_card, 'bio') and user_card.bio:
                    card_bio = user_card.bio
                if hasattr(user_card, 'role_type'):
                    role_type = user_card.role_type
        except Exception as e:
            logger.warning(f"获取卡片主人信息失败: {str(e)}")
        
        # 获取角色特定的提示词
        prompt = self._get_role_specific_prompt(
            role_type,
            "stream",
            chatId,
            userPersonality,
            chatHistory,
            suggestionType,
            maxSuggestions,
            card_owner_preferences,
            card_bio,
            cart_trigger_and_output
        )
        
        # 创建LLM请求
        llm_request = LLMRequest(
            user_id=user_id,
            task_type=LLMTaskType.CONVERSATION_SUGGESTION,
            prompt=prompt
        )
        print("stream calling llm")
        # 流式调用LLM API
        return await self.call_llm_api(llm_request, provider, model_name, stream=True)


    async def generate_simple_chat_stream(
        self,
        user_id: str,
        card_id: str,
        chat_id: str,
        message: str,
        context: Dict[str, Any] = {},
        personality: Optional[str] = None,
        provider: LLMProvider = LLMProvider.VOLCENGINE,
        model_name: str = settings.LLM_MODEL
    ):
        """生成简单聊天流式回复 - 仅返回纯文本"""
        
        # 获取聊天记录和上下文
        chat_history = context.get("chatHistory", [])
        
        # 获取卡片信息
        card_bio = ""
        card_preferences = {}
        try:
            from app.models.user_card_db import UserCard
            from app.services.user_card_service import UserCardService

            user_card = UserCardService.get_card_by_id(self.db, card_id)
            if user_card:
                # 正常模式下的处理
                if hasattr(user_card, 'bio') and user_card.bio:
                    card_bio = user_card.bio
                if hasattr(user_card, 'preferences') and user_card.preferences:
                    card_preferences = user_card.preferences
        except Exception as e:
            logger.warning(f"获取卡片信息失败: {str(e)}")
        
        # 构建简洁的提示词 - 专注于生成自然流畅的回复
        prompt = f"""
        你是一个友好、自然的聊天助手。请根据以下信息回复用户的消息：
        
        聊天ID: {chat_id}
        用户消息: {message}
        卡片简介: {card_bio}
        卡片偏好: {json.dumps(card_preferences, ensure_ascii=False)}
        聊天历史: {json.dumps(chat_history[-5:], ensure_ascii=False) if chat_history else '无历史记录'}
        {f'卡片主人性格: {personality}' if personality else ''}
        
        要求：
        1. 回复要自然流畅，像真人对话
        2. 内容要积极友好
        3. 根据卡片主人的性格和偏好来回复
        4. 直接给出回复内容，不要包含其他解释
        5. 回复长度适中，像日常聊天一样
        
        请直接给出回复内容：
        """

        # 创建LLM请求
        llm_request = LLMRequest(
            user_id=user_id,
            task_type=LLMTaskType.CONVERSATION_SUGGESTION,
            prompt=prompt
        )

        # 流式调用LLM API
        return await self.call_llm_api(llm_request, provider, model_name, stream=True)

    async def generate_coffee_recommendation(
        self,
        user_id: str,
        time_preference: str = None,
        location_preference: str = None,
        budget_range: str = None,
        coffee_type: str = None,
        atmosphere: str = None,
        provider: LLMProvider = LLMProvider.VOLCENGINE,
        model_name: str = settings.LLM_MODEL
    ) -> LLMResponse:
        """
        生成咖啡推荐

        Args:
            user_id: 用户ID
            time_preference: 时间偏好
            location_preference: 地点偏好
            budget_range: 预算范围
            coffee_type: 咖啡类型偏好
            atmosphere: 氛围偏好

        Returns:
            LLM响应对象
        """
        prompt = f"""
        请根据以下信息为用户推荐咖啡店和咖啡：

        时间偏好：{time_preference or '无特殊要求'}
        地点偏好：{location_preference or '无特殊要求'}
        预算范围：{budget_range or '无特殊要求'}
        咖啡类型：{coffee_type or '无特殊要求'}
        氛围偏好：{atmosphere or '无特殊要求'}

        请推荐3-5家咖啡店，包括：
        1. 咖啡店名称
        2. 地址
        3. 距离
        4. 评分
        5. 价格等级（1-4）
        6. 特色
        7. 营业时间
        8. 推荐理由

        请用JSON格式回复，包含以下字段：
        - locations: 地点推荐列表
        - coffee_suggestions: 推荐咖啡列表
        - summary: 总结
        """

        llm_request = LLMRequest(
            user_id=user_id,
            task_type=LLMTaskType.INTEREST_ANALYSIS,  # 使用现有任务类型
            prompt=prompt
        )

        return await self.call_llm_api(llm_request, provider, model_name)

    async def generate_coffee_chat_response(
        self,
        user_id: str,
        user_message: str,
        conversation_history: List[Dict[str, Any]] = None,
        extracted_info: Dict[str, Any] = None,
        dialog_count: int = 0,
        provider: LLMProvider = LLMProvider.VOLCENGINE,
        model_name: str = settings.LLM_MODEL
    ) -> LLMResponse:
        """
        生成咖啡聊天场景下的对话回复
        
        Args:
            user_id: 用户ID
            user_message: 用户输入消息
            conversation_history: 对话历史记录
            extracted_info: 已提取的信息（时间、地点、偏好等）
            dialog_count: 对话轮数
            provider: LLM服务提供商
            model_name: 模型名称
            
        Returns:
            LLM响应对象
        """
        # 构建上下文信息
        time_info = extracted_info.get('time') if extracted_info else None
        location_info = extracted_info.get('location') if extracted_info else None
        preferences = extracted_info.get('preferences') if extracted_info else {}
        
        # 根据对话进度构建不同的提示词
        if dialog_count == 0:
            # 初次对话
            prompt = f"""
            你是一个友好的咖啡约会安排助手。用户说："{user_message}"
            
            请用温暖、自然的语气回复，表达你帮助安排咖啡约会的意愿。
            回复要简洁友好，像真人对话一样，可以询问用户的基本偏好。
            
            直接给出回复内容，不要包含其他解释。
            """
        elif time_info and location_info:
            # 已有足够信息，提供推荐
            prompt = f"""
            用户说："{user_message}"
            
            已收集的信息：
            - 时间：{time_info}
            - 地点：{location_info}
            - 偏好：{json.dumps(preferences, ensure_ascii=False) if preferences else '无特殊要求'}
            
            请基于这些信息为用户推荐具体的咖啡店，包括店名、地址、特色等。
            语气要热情专业，提供实用建议。
            
            直接给出回复内容，不要包含其他解释。
            """
        elif time_info and not location_info:
            # 有时间缺地点
            prompt = f"""
            用户说："{user_message}"
            
            已知用户希望在 {time_info} 见面。
            
            请用自然的语气询问用户希望在哪个区域或具体地点喝咖啡，
            可以提供一些热门区域作为参考。
            
            直接给出回复内容，不要包含其他解释。
            """
        elif location_info and not time_info:
            # 有地点缺时间
            prompt = f"""
            用户说："{user_message}"
            
            已知用户希望在 {location_info} 区域喝咖啡。
            
            请用自然的语气询问用户希望什么时间见面，
            可以提供一些时间建议。
            
            直接给出回复内容，不要包含其他解释。
            """
        else:
            # 信息不足，继续收集
            prompt = f"""
            用户说："{user_message}"
            
            对话历史：{json.dumps(conversation_history[-3:], ensure_ascii=False) if conversation_history else '无历史'}
            
            请用友好、耐心的语气继续收集用户的信息，
            可以询问时间、地点或偏好，帮助用户明确需求。
            
            直接给出回复内容，不要包含其他解释。
            """

        llm_request = LLMRequest(
            user_id=user_id,
            task_type=LLMTaskType.CONVERSATION_SUGGESTION,
            prompt=prompt.strip()
        )

        return await self.call_llm_api(llm_request, provider, model_name)