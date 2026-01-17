"""
大语言模型服务
提供统一的LLM API调用接口,支持多种提供商
"""

import time
import json
import uuid
import asyncio
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
    LLMResponse, ConversationSuggestionResponse,
    OpinionSummarizationResponse, ProfileSummaryResponse
)
from app.configs.prompt_config_manager import prompt_config_manager
from app.models.user_card_db import UserCard
from app.models.user_profile import UserProfile

logger = logging.getLogger(__name__)

class LLMService:
    """大语言模型服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.clients = {}
        self._init_clients()
    
    def _init_clients(self):
        """初始化各个LLM客户端"""

        # 火山大语言模型客户端(使用通用配置)
        llm_api_key = settings.LLM_API_KEY
        if llm_api_key:
            self.clients[LLMProvider.VOLCENGINE] = AsyncOpenAI(
                base_url=settings.LLM_BASE_URL,
                api_key=llm_api_key
            )
        # 其他客户端初始化...
        # 可以根据需要添加更多提供商

    def _get_card_preferences(self, card_id: str):
        """获取卡片的偏好设置用于引导对话生成"""
        if not card_id:
            return '', ''
        try:
            card = self.db.query(UserCard).filter(UserCard.id == card_id).first()
            if card and card.preferences:
                return card.preferences, card.user_id
        except Exception as e:
            logger.warning(f"获取卡片偏好设置失败: {e}")
        return '', ''

    def _get_user_raw_profile(self, creator_id: str) -> str:
        """获取创建者的用户画像原始数据"""
        if not creator_id:
            return ''
        try:
            profile = self.db.query(UserProfile).filter(UserProfile.user_id == creator_id).first()
            if profile and profile.raw_profile:
                if isinstance(profile.raw_profile, str):
                    return profile.raw_profile
                return json.dumps(profile.raw_profile, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"获取用户画像失败: {e}")
        return ''
    
    async def call_llm_api(
        self,
        request: LLMRequest,
        provider: LLMProvider = LLMProvider.VOLCENGINE,
        model_name: str = None
    ) -> LLMResponse:
        """
        调用LLM API的统一接口（非流式）
        
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
                    # 如果客户端未初始化,降级使用模拟API
                    logger.warning(f"VOLCENGINE客户端未初始化,使用模拟API代替")
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
            
            # 非流式调用返回LLMResponse对象
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

    async def call_llm_api_stream(
        self,
        request: LLMRequest,
        provider: LLMProvider = LLMProvider.VOLCENGINE,
        model_name: str = None
    ):
        """
        调用LLM API的流式接口
        
        Args:
            request: LLM请求对象
            provider: LLM服务提供商
            model_name: 模型名称
            
        Yields:
            流式响应块
        """
        try:
            # 设置默认模型名
            if model_name is None:
                model_name = getattr(settings, 'LLM_MODEL', 'unknown-model')
            # 确保model_name不为空
            if not model_name:
                model_name = 'unknown-model'
            
            # 根据提供商调用不同的API
            if provider == LLMProvider.VOLCENGINE:
                # 检查VOLCENGINE客户端是否已初始化
                if LLMProvider.VOLCENGINE in self.clients:
                    async for chunk in self._call_volcengine_api_stream(request, model_name):
                        yield chunk
                else:
                    # 如果客户端未初始化,降级使用模拟API
                    logger.warning(f"VOLCENGINE客户端未初始化,使用模拟API代替")
                    async for chunk in self._call_mock_api_stream(request, provider, model_name):
                        yield chunk
            else:
                # 可以扩展其他提供商
                async for chunk in self._call_mock_api_stream(request, provider, model_name):
                    yield chunk
                    
        except Exception as e:
            logger.error(f"LLM API流式调用失败: {str(e)}")
            yield {
                "type": "error",
                "message": str(e)
            }
    


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
        """模拟流式API调用,用于测试"""
        import asyncio
        
        # 从配置管理器获取流式配置
        stream_config = prompt_config_manager.get_stream_config('stream_responses')
        mock_stream_config = stream_config.get('mock_stream', {})
        
        # 获取模拟响应内容模板并替换变量
        mock_content_template = mock_stream_config.get('content', 
            "这是来自{provider}的{model_name}模型的模拟流式响应。我会为您提供一些有用的建议和信息。")
        mock_content = mock_content_template.format(provider=provider.value, model_name=model_name)
        
        # 获取配置参数
        chunk_size = mock_stream_config.get('chunk_size', 3)
        delay_ms = mock_stream_config.get('delay_ms', 50)
        delay_seconds = delay_ms / 1000.0
        
        # 模拟流式输出
        for i in range(0, len(mock_content), chunk_size):
            chunk = mock_content[i:i + chunk_size]
            yield {
                "type": "text", 
                "content": chunk,
                "finished": i + chunk_size >= len(mock_content)
            }
            await asyncio.sleep(delay_seconds)
        
        # 发送元数据
        metadata_delay = mock_stream_config.get('metadata_delay_ms', 200) / 1000.0
        await asyncio.sleep(metadata_delay)
        
        metadata = mock_stream_config.get('metadata', {})
        yield {
            "type": "metadata",
            **metadata
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
        """模拟API调用,用于测试"""
        await asyncio.sleep(1)  # 模拟网络延迟
        
        # 从配置管理器获取模拟响应数据
        mock_response_data = prompt_config_manager.get_mock_response(request.task_type.name)
        content = json.dumps(mock_response_data, ensure_ascii=False)
        
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
        return prompt_config_manager.get_system_prompt(task_type.name)
    
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
        
        注意:如果日志记录失败,不会影响主要功能
        """
        try:
            # 验证用户是否存在,如果不存在则使用None作为user_id
            validated_user_id = None
            if user_id:
                try:
                    from app.models.user import User
                    user = self.db.query(User).filter(User.id == user_id).first()
                    validated_user_id = user_id if user else None
                    if not user:
                        logger.warning(f"用户不存在,日志记录将使用null user_id: {user_id}")
                    else:
                        logger.info(f"用户验证成功,记录LLM使用日志: user_id={user_id}")
                except Exception as user_check_error:
                    logger.warning(f"验证用户存在性失败,使用null user_id: {user_check_error}")
                    validated_user_id = None
            else:
                logger.info("user_id为null,记录匿名LLM使用日志")
            
            # 使用简单的dict记录,避免数据库操作失败影响主流程
            log_data = {
                "id": log_id,
                "user_id": validated_user_id,
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
                        
            # 尝试数据库记录,但失败不影响功能
            try:
                # 显式设置创建和更新时间
                current_time = datetime.utcnow()
                log_entry = LLMUsageLog(
                    id=log_id,
                    user_id=validated_user_id,  # 使用验证后的user_id
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
                logger.error(f"数据库日志记录失败,但不影响功能: {str(db_error)}")
                # 回滚事务
                self.db.rollback()
        except Exception as e:
            logger.error(f"LLM使用日志处理失败: {str(e)}")
    

    async def generate_profile_summary(
        self,
        user_id: str,
        profile_data_str: str,
        provider: LLMProvider = LLMProvider.VOLCENGINE,
        model_name: str = settings.LLM_MODEL,
        existing_profile_str:str = None
    ) -> ProfileSummaryResponse:
        """分析用户资料"""
        prompt = f"""
        请分析提供的用户数据，得到用户画像描述（少于 1000 个字），以及用户画像总结文本（字数少于 100 字），并以 JSON 格式输出
        要求以事实为依据，不凭空臆测，可以进行适当信息压缩。
        最新提交的用户数据:{profile_data_str}

        以 JSON 输出格式：
        {{
            "description": "用户画像描述",
            "summary": "用户画像总结"
        }}
        """
        if existing_profile_str:
            prompt += f"""
                当前的用户画像数据:{existing_profile_str}
                """
        request = LLMRequest(
            user_id=user_id,
            task_type=LLMTaskType.PROFILE_ANALYSIS,
            prompt=prompt
        )
        
        response = await self.call_llm_api(request, provider, model_name)
        
        if response.success:
            try:
                rs = json.loads(response.data)
                return ProfileSummaryResponse(
                    success=True,
                    data=response.data,
                    profile_summary=rs.get('summary', ''),
                    profile_description=rs.get('description', ''),
                    usage=response.usage,
                    duration=response.duration
                )
            except json.JSONDecodeError:
                return ProfileSummaryResponse(
                    success=True,
                    profile_summary=response.data,
                    profile_description=response.data,
                    usage=response.usage,
                    duration=response.duration
                )
        
        return ProfileSummaryResponse(
            success=False,
            profile_summary=None,
            profile_description=None,
            usage=response.usage,
            duration=response.duration,
            personality='',
            interests=[],
            values=[]
        )

    # 统一的场景化LLM调用方法 - 非流式版本
    async def process_scene_request(
        self,
        user_id: str,
        scene_config_key: str,
        params: Dict[str, Any],
        provider: LLMProvider = LLMProvider.VOLCENGINE,
        model_name: str = settings.LLM_MODEL,
        stream: bool = False
    ):
        """
        统一的场景化LLM调用接口
        
        Args:
            user_id: 用户ID
            scene_config_key: 场景配置键,用于区分不同的LLM使用场景
            params: 场景特定的参数
            provider: LLM服务提供商
            model_name: 模型名称
            stream: 是否使用流式输出
            
        Returns:
            统一格式的响应数据 (非流式)
            
        Note:
            对于流式处理,请使用 process_scene_request_stream 方法
        """
        if stream:
            raise ValueError("流式处理请使用 process_scene_request_stream 方法")
        
        return await self._process_scene_request_non_stream(user_id, scene_config_key, params, provider, model_name)

    async def process_scene_request_stream(
        self,
        user_id: str,
        scene_config_key: str,
        params: Dict[str, Any],
        provider: LLMProvider = LLMProvider.VOLCENGINE,
        model_name: str = settings.LLM_MODEL
    ):
        """
        统一的场景化LLM调用接口 - 流式版本
        
        Args:
            user_id: 用户ID
            scene_config_key: 场景配置键,用于区分不同的LLM使用场景
            params: 包含用户输入和上下文信息
            provider: LLM服务提供商
            model_name: 模型名称
            
        Yields:
            流式响应块
        """
        async for chunk in self._process_scene_request_stream(user_id, scene_config_key, params, provider, model_name):
            yield chunk

    async def _process_scene_request_non_stream(
        self,
        user_id: str,
        scene_config_key: str,
        params: Dict[str, Any],
        provider: LLMProvider = LLMProvider.VOLCENGINE,
        model_name: str = settings.LLM_MODEL
    ):
        """非流式场景化LLM调用"""
        try:
            # 根据场景配置键处理不同的LLM调用
            if scene_config_key == "conversation-suggestions":
                result = await self._handle_conversation_suggestions_non_stream(user_id, params, provider, model_name)
                return result
            elif scene_config_key == "simple-chat":
                result = await self._handle_simple_chat_non_stream(user_id, params, provider, model_name)
                return result
            elif scene_config_key == "topic-discussion":
                result = await self._handle_topic_discussion_non_stream(user_id, params, provider, model_name)
                return result
            elif scene_config_key == "generate-opinion-summary":
                return await self._handle_generate_opinion_summary(user_id, params, provider, model_name)
            else:
                logger.warning(f"未知的场景配置键: {scene_config_key}")
                return {
                    "success": False,
                    "error": f"未知的场景配置键: {scene_config_key}",
                    "scene_config_key": scene_config_key
                }
        except Exception as e:
            logger.error(f"场景化LLM调用失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "scene_config_key": scene_config_key
            }

    async def _process_scene_request_stream(
        self,
        user_id: str,
        scene_config_key: str,
        params: Dict[str, Any],
        provider: LLMProvider = LLMProvider.VOLCENGINE,
        model_name: str = settings.LLM_MODEL
    ):
        """流式场景化LLM调用"""
        try:
            # 根据场景配置键处理不同的LLM调用
            if scene_config_key == "conversation-suggestions":
                async for chunk in self._handle_conversation_suggestions_stream(user_id, params, provider, model_name):
                    yield chunk
            elif scene_config_key == "simple-chat":
                async for chunk in self._handle_simple_chat_stream(user_id, params, provider, model_name):
                    yield chunk
            elif scene_config_key == "topic-discussion":
                async for chunk in self._handle_topic_discussion_stream(user_id, params, provider, model_name):
                    yield chunk
            else:
                logger.warning(f"未知的场景配置键(不支持流式): {scene_config_key}")
                yield {
                    "success": False,
                    "error": f"未知的场景配置键(不支持流式): {scene_config_key}",
                    "scene_config_key": scene_config_key
                }
        except Exception as e:
            logger.error(f"场景化LLM流式调用失败: {str(e)}")
            yield {
                "success": False,
                "error": str(e),
                "scene_config_key": scene_config_key
            }

    async def _handle_conversation_suggestions(
        self,
        user_id: str,
        params: Dict[str, Any],
        provider: LLMProvider,
        model_name: str,
        stream: bool
    ):
        """处理对话建议场景 - 根据stream参数选择处理方式"""
        if stream:
            async for chunk in self._handle_conversation_suggestions_stream(user_id, params, provider, model_name):
                yield chunk
            return
        else:
            result = await self._handle_conversation_suggestions_non_stream(user_id, params, provider, model_name)
            yield result

    async def _handle_conversation_suggestions_non_stream(
        self,
        user_id: str,
        params: Dict[str, Any],
        provider: LLMProvider,
        model_name: str
    ):
        """处理对话建议场景 - 非流式"""
        conversation_history = params.get("conversation_history", [])
        context = params.get("context", {})
        card_id = params.get("cardId", "")
        card_preferences, card_creator_id = self._get_card_preferences(card_id)
        preferences_str = json.dumps(card_preferences, ensure_ascii=False) if card_preferences else "{}"

        prompt = f"""
        基于以下对话历史、上下文和用户卡片偏好设置,生成3个合适的对话建议:
        
        用户卡片偏好设置:{preferences_str}
        
        对话历史:{json.dumps(conversation_history, ensure_ascii=False)}
        
        上下文:{json.dumps(context, ensure_ascii=False)}
        
        请根据用户卡片偏好设置,生成3个自然,有趣且符合上下文的对话建议,帮助用户继续对话.
        """
        
        request = LLMRequest(
            user_id=user_id,
            task_type=LLMTaskType.QUESTION_ANSWERING,
            prompt=prompt
        )
        
        response = await self.call_llm_api(request, provider, model_name)
        return {
            "success": response.success,
            "data": response.data,
            "usage": response.usage,
            "duration": response.duration,
            "scene_config_key": "conversation-suggestions"
        }

    async def _handle_conversation_suggestions_stream(
        self,
        user_id: str,
        params: Dict[str, Any],
        provider: LLMProvider,
        model_name: str
    ):
        """处理对话建议场景 - 流式"""
        conversation_history = params.get("conversation_history", [])
        context = params.get("context", {})
        card_id = params.get("cardId", "")
        card_preferences, card_creator_id = self._get_card_preferences(card_id)
        preferences_str = json.dumps(card_preferences, ensure_ascii=False) if card_preferences else "{}"

        prompt = f"""
        基于以下对话历史、上下文和用户卡片偏好设置,生成3个合适的对话建议:
        
        用户卡片偏好设置:{preferences_str}
        
        对话历史:{json.dumps(conversation_history, ensure_ascii=False)}
        
        上下文:{json.dumps(context, ensure_ascii=False)}
        
        请根据用户卡片偏好设置,生成3个自然,有趣且符合上下文的对话建议,帮助用户继续对话.
        """
        
        request = LLMRequest(
            user_id=user_id,
            task_type=LLMTaskType.QUESTION_ANSWERING,
            prompt=prompt
        )
        
        # 调用流式API并直接迭代结果
        stream = self.call_llm_api_stream(request, provider, model_name)
        async for chunk in stream:
            yield chunk

    async def _handle_simple_chat(
        self,
        user_id: str,
        params: Dict[str, Any],
        provider: LLMProvider,
        model_name: str,
        stream: bool
    ):
        """处理简单聊天场景 - 根据stream参数选择处理方式"""
        if stream:
            async for chunk in self._handle_simple_chat_stream(user_id, params, provider, model_name):
                yield chunk
            return
        else:
            result = await self._handle_simple_chat_non_stream(user_id, params, provider, model_name)
            yield result

    async def _handle_simple_chat_non_stream(
        self,
        user_id: str,
        params: Dict[str, Any],
        provider: LLMProvider,
        model_name: str
    ):
        """处理简单聊天场景 - 非流式"""
        message = params.get("message", "")
        # 处理匿名模式
        context = params.get("context", {})
        is_anonymous = context.get("isAnonymous", False)
        chat_type = context.get("chatType", "general")
        card_id = context.get("cardId", "")
        card_preferences, card_creator_id = self._get_card_preferences(card_id)
        preferences_str = json.dumps(card_preferences, ensure_ascii=False) if card_preferences else "{}"

        conversation_history = context.get("recentMessages", [])
        conversation_context = json.dumps(conversation_history, ensure_ascii=False)
        
        # 匿名模式使用特殊的人物设定
        if is_anonymous:
            system_prompt = "你正在与匿名用户对话。请保持专业、友善的态度，不要询问或假设用户的个人身份信息。"
        else:
            system_prompts = {
                "general": "请自然地和用户对话，回复内容不宜太长，可以模拟对话体的兴趣，长短相接",
                "topic": "请帮助用户深入讨论话题.",
                "sports": "请和用户讨论体育相关话题."
            }
            system_prompt = system_prompts.get(chat_type, system_prompts['general'])
        
        character_profile = self._get_user_raw_profile(card_creator_id)
        prompt = f"""
        {system_prompt}
        你的人物设定 {character_profile}
        聊天过程中需要完成的任务 {preferences_str}
        对话历史 {conversation_context}
        
        用户消息: {message}
        
        请给出自然，与设定相关的回复.
        """
        request = LLMRequest(
            user_id=user_id,
            task_type=LLMTaskType.QUESTION_ANSWERING,
            prompt=prompt
        )
        
        response = await self.call_llm_api(request, provider, model_name)
        return {
            "success": response.success,
            "data": response.data,
            "usage": response.usage,
            "duration": response.duration,
            "scene_config_key": "simple-chat",
            "chat_type": chat_type
        }

    async def _handle_simple_chat_stream(
        self,
        user_id: str,
        params: Dict[str, Any],
        provider: LLMProvider,
        model_name: str
    ):
        """处理简单聊天场景 - 流式"""
        message = params.get("message", "")
        
        # 处理匿名模式
        context = params.get("context", {})
        is_anonymous = context.get("isAnonymous", False)
        chat_type = context.get("chatType", "general")
        # 匿名模式使用特殊的人物设定
        if is_anonymous:
            system_prompt = "你正在与匿名用户对话。请保持专业、友善的态度，不要询问或假设用户的个人身份信息。"
        else:
            system_prompts = {
                "general": "请自然地和用户对话.",
                "topic": "请帮助用户深入讨论话题.",
                "sports": "请和用户讨论体育相关话题."
            }
            system_prompt = system_prompts.get(chat_type, system_prompts['general'])
        # 获取对话历史（兼容旧格式和新格式）
        conversation_history = params.get("conversation_history", [])
        if not conversation_history and context:
            # 尝试从上下文中获取历史记录
            conversation_history = context.get("conversationHistory", [])
        
        conversation_context = json.dumps(conversation_history, ensure_ascii=False)
        
        # 匿名模式使用特殊的人物设定
        character_profile = params.get("character_profile", "")
        
        prompt = f"""        
        你的人物设定：{character_profile}

        {system_prompt}

        对话历史:{conversation_context}
        
        用户消息:{message}
        
        请结合人物设定，给出自然，像人类一样的拥有情感随机性的回复.
        """
        request = LLMRequest(
            user_id=user_id,
            task_type=LLMTaskType.QUESTION_ANSWERING,
            prompt=prompt
        )
        
        # 调用流式API并直接迭代结果
        stream = self.call_llm_api_stream(request, provider, model_name)
        async for chunk in stream:
            yield chunk

    async def _handle_topic_discussion_stream(
        self,
        user_id: str,
        params: Dict[str, Any],
        provider: LLMProvider,
        model_name: str
    ):
        """处理话题讨论场景（流式）"""
        message = params.get("message", "")
        conversation_history = params.get("conversation_history", [])
        topic_context = params.get("topic_context", {})
        
        conversation_context = json.dumps(conversation_history, ensure_ascii=False)
        topic_context_str = json.dumps(topic_context, ensure_ascii=False)
        
        prompt = f"""
        你是一个话题讨论专家.请基于以下信息参与话题讨论:
        
        对话历史:{conversation_context}
        
        用户消息:{message}
        
        话题上下文:{topic_context_str}
        
        请给出有深度,有趣且能促进话题讨论继续的回复，字数限定在 200 字以内.
        """
        
        request = LLMRequest(
            user_id=user_id,
            task_type=LLMTaskType.QUESTION_ANSWERING,
            prompt=prompt
        )
        
        # 调用流式API并直接迭代结果
        stream = self.call_llm_api_stream(request, provider, model_name)
        async for chunk in stream:
            yield chunk

    async def _handle_topic_discussion_non_stream(
        self,
        user_id: str,
        params: Dict[str, Any],
        provider: LLMProvider,
        model_name: str
    ):
        """处理话题讨论场景（非流式）"""
        message = params.get("message", "")
        conversation_history = params.get("conversation_history", [])
        topic_context = params.get("topic_context", {})
        
        conversation_context = json.dumps(conversation_history, ensure_ascii=False)
        topic_context_str = json.dumps(topic_context, ensure_ascii=False)
        
        prompt = f"""
        你是一个话题讨论专家.请基于以下信息参与话题讨论:
        
        对话历史:{conversation_context}
        
        用户消息:{message}
        
        话题上下文:{topic_context_str}
        
        请给出有深度,有趣且能促进话题讨论继续的回复.
        """
        
        request = LLMRequest(
            user_id=user_id,
            task_type=LLMTaskType.QUESTION_ANSWERING,
            prompt=prompt
        )
        
        response = await self.call_llm_api(request, provider, model_name)
        return {
            "success": response.success,
            "data": response.data,
            "usage": response.usage,
            "duration": response.duration,
            "scene_config_key": "topic-discussion"
        }

    async def _handle_topic_discussion(
        self,
        user_id: str,
        params: Dict[str, Any],
        provider: LLMProvider,
        model_name: str,
        stream: bool
    ):
        """处理话题讨论场景"""
        if stream:
            async for chunk in self._handle_topic_discussion_stream(user_id, params, provider, model_name):
                yield chunk
            return
        else:
            result = await self._handle_topic_discussion_non_stream(user_id, params, provider, model_name)
            yield result

    async def _handle_sports_chat_stream(
        self,
        user_id: str,
        params: Dict[str, Any],
        provider: LLMProvider,
        model_name: str
    ):
        """处理体育聊天场景（流式）"""
        message = params.get("message", "")
        conversation_history = params.get("conversation_history", [])
        sports_context = params.get("sports_context", {})
        
        conversation_context = json.dumps(conversation_history, ensure_ascii=False)
        sports_context_str = json.dumps(sports_context, ensure_ascii=False)
        
        prompt = f"""
        你是一个体育话题专家.请基于以下信息参与体育相关讨论:
        
        对话历史:{conversation_context}
        
        用户消息:{message}
        
        体育上下文:{sports_context_str}
        
        请给出专业,有趣且能促进体育话题讨论继续的回复.
        """
        
        request = LLMRequest(
            user_id=user_id,
            task_type=LLMTaskType.QUESTION_ANSWERING,
            prompt=prompt
        )
        
        # 调用流式API并直接迭代结果
        stream = self.call_llm_api_stream(request, provider, model_name)
        async for chunk in stream:
            yield chunk

    async def _handle_generate_opinion_summary(
        self,
        user_id: str,
        params: Dict[str, Any],
        provider: LLMProvider,
        model_name: str
    ) -> Dict[str, Any]:
        """处理观点总结场景"""
        discussion_content = params.get("discussion_content", "")
        participants = params.get("participants", [])
        
        participants_str = json.dumps(participants, ensure_ascii=False)
        
        prompt = f"""
        你是一个观点总结专家.请基于以下讨论内容生成观点总结:
        
        讨论内容:{discussion_content}
        
        参与者:{participants_str}
        
        请提取关键观点,生成简洁准确的总结,帮助用户快速了解讨论的核心内容.
        """
        
        request = LLMRequest(
            user_id=user_id,
            task_type=LLMTaskType.OPINION_SUMMARIZATION,
            prompt=prompt
        )
        
        response = await self.call_llm_api(request, provider, model_name)
        return {
            "success": response.success,
            "data": response.data,
            "usage": response.usage,
            "duration": response.duration,
            "scene_config_key": "generate-opinion-summary"
        }
    

    def _get_role_specific_prompt(
        self,
        role_type: str,
        prompt_type: str,
        chatId: str,
        userPersonality: Dict[str, Any],
        chatHistory: List[Dict[str, Any]],
        suggestionType: str,
        maxSuggestions: int,
        preferences: str,
        bio: str,
        trigger_and_output: Dict[str, Any]
    ) -> str:
        """获取特定角色类型的提示词模板"""
        # 基础信息
        base_info_parts = [
            f"聊天ID: {chatId}",
            f"用户性格特点: {json.dumps(userPersonality, ensure_ascii=False)}",
            f"聊天记录: {json.dumps(chatHistory, ensure_ascii=False)}",
            f"建议类型: {suggestionType}"
        ]
        base_info = "\n".join(base_info_parts)
        
        # 根据角色类型选择不同的提示词模板
        if role_type == "trade_landlord":
            # 针对房东角色的特定提示词 - 使用配置文件中的专用模板
            return prompt_config_manager.get_specialized_scene_prompt(
                "conversation_suggestions", 
                "house_renting",
                base_info=base_info,
                max_suggestions=maxSuggestions,
                preferences=preferences if preferences else "",
                bio=bio,
                trigger_and_output=json.dumps(trigger_and_output, ensure_ascii=False)
            )
        else:
            # 使用通用场景提示词
            return prompt_config_manager.get_scene_prompt(
                "conversation_suggestions",
                prompt_type,
                base_info=base_info,
                max_suggestions=maxSuggestions,
                preferences=preferences if preferences else "",
                bio=bio,
                trigger_and_output=json.dumps(trigger_and_output, ensure_ascii=False)
            )
    
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
        card_owner_preferences = ""
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
                # 如果解析失败,尝试将响应内容直接作为单条建议
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
        card_owner_preferences = ""
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
        # 流式调用LLM API
        return self.call_llm_api_stream(llm_request, provider, model_name)


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
        card_preferences = ""
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
        请根据以下信息回复用户的消息:
        聊天ID: {chat_id}
        用户消息: {message}
        你的身份简介: {card_bio}
        你的偏好: {card_preferences}
        你们的聊天历史: {json.dumps(chat_history[-5:], ensure_ascii=False) if chat_history else '无历史记录'}
        {f'卡片主人性格: {personality}' if personality else ''}
        
        要求:
        1. 回复要自然流畅, 像真人对话
        2. 内容要积极友好
        3. 根据卡片主人的性格和偏好来回复
        4. 直接给出回复内容, 不要包含其他解释
        5. 回复长度适中, 像日常聊天一样
        
        请直接给出回复内容:
        """
        # 创建LLM请求
        llm_request = LLMRequest(
            user_id=user_id,
            task_type=LLMTaskType.CONVERSATION_SUGGESTION,
            prompt=prompt
        )

        # 流式调用LLM API
        return self.call_llm_api_stream(llm_request, provider, model_name)



    async def summarize_opinions(
        self,
        user_id: str,
        conversation_history: List[Dict[str, Any]],
        topic_title: str,
        topic_description: str,
        provider: LLMProvider = LLMProvider.VOLCENGINE,
        model_name: str = settings.LLM_MODEL
    ) -> OpinionSummarizationResponse:
        """
        生成观点总结
        
        Args:
            user_id: 用户ID
            conversation_history: 对话历史记录
            topic_title: 话题标题
            topic_description: 话题描述
            provider: LLM服务提供商
            model_name: 模型名称
            
        Returns:
            观点总结响应对象
        """
        # 构建用户提示词
        user_prompt = """
        请分析以下话题讨论中的用户观点:
        
        话题标题: {}
        话题描述: {}
        讨论内容: {}
        
        请提取并总结用户的观点, 包括:
        1. 观点总结: 用简洁的语言概括用户表达的主要观点
        2. 关键点: 列出核心要点
        3. 情感分析: 分析用户的情感倾向(积极/中性/消极)
        4. confidence: provide your confidence in the analysis result (0-1)
        
        请严格按照以下JSON格式回复:
        {{
            "summary": "用户的观点总结",
            "key_points": ["要点1", "要点2", "要点3"],
            "sentiment": "positive/neutral/negative",
            "confidence_score": 0.85
        }}
        """.format(topic_title, topic_description, json.dumps(conversation_history, ensure_ascii=False))

        # 创建LLM请求
        llm_request = LLMRequest(
            user_id=user_id,
            task_type=LLMTaskType.OPINION_SUMMARIZATION,
            prompt=user_prompt
        )

        # 调用LLM API
        response = await self.call_llm_api(llm_request, provider, model_name)
        
        if response.success and response.data:
            try:
                # 解析LLM返回的JSON数据
                result = json.loads(response.data)
                
                # 创建响应对象
                return OpinionSummarizationResponse(
                    success=True,
                    data=response.data,
                    usage=response.usage,
                    duration=response.duration,
                    summary=result.get("summary", ""),
                    key_points=result.get("key_points", []),
                    sentiment=result.get("sentiment", "neutral"),
                    confidence_score=result.get("confidence_score", 0.5)
                )
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"解析观点总结结果失败: {str(e)}, 原始数据: {response.data}")
                # 如果解析失败,返回默认值
                return OpinionSummarizationResponse(
                    success=False,
                    data=None,
                    usage=response.usage if hasattr(response, 'usage') else {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                    duration=response.duration if hasattr(response, 'duration') else 0.0,
                    summary="观点总结生成失败",
                    key_points=[],
                    sentiment="neutral",
                    confidence_score=0.0
                )
        else:
            logger.error(f"观点总结LLM调用失败: {response.error_message}")
            return OpinionSummarizationResponse(
                success=False,
                data=None,
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                duration=0.0,
                summary="观点总结生成失败",
                key_points=[],
                sentiment="neutral",
                confidence_score=0.0
            )

    async def generate_chat_summary(
        self,
        user_id: str,
        chat_messages: List[str],
        provider: LLMProvider = LLMProvider.VOLCENGINE,
        model_name: str = settings.LLM_MODEL
    ) -> Dict[str, Any]:
        """
        生成聊天内容总结
        
        Args:
            user_id: 用户ID
            chat_messages: 聊天消息列表
            provider: LLM服务提供商
            model_name: 模型名称
            
        Returns:
            包含总结内容、消息数量、语言等信息的字典
        """
        try:
            # 构建聊天内容上下文
            chat_context = "\n".join([
                f"{i+1} {msg}" for i, msg in enumerate(chat_messages)
            ])
            
            # 构建总结提示词
            prompt = f"""请提供简洁明了地总结用户表达意图和主题，不需要总结 AI 的回复内容，不超过200字。用户和 AI 的聊天记录：{chat_context}"""            
            llm_request = LLMRequest(
                user_id=user_id,
                task_type=LLMTaskType.CHAT_SUMMARIZATION,
                prompt=prompt.strip()
            )
            
            # 调用LLM API
            response = await self.call_llm_api(llm_request, provider, model_name)
            
            if response.success and response.data:
                return {
                    "success": True,
                    "summary": response.data,
                    "content": response.data,
                    "message_count": str(len(chat_messages)),
                    "language": "zh",
                    "usage": response.usage,
                    "duration": response.duration
                }
            else:
                return {
                    "success": False,
                    "summary": "",
                    "content": "",
                    "message_count": str(len(chat_messages)),
                    "language": "zh",
                    "usage": response.usage,
                    "duration": response.duration,
                    "error": "LLM调用失败"
                }
                
        except Exception as e:
            logger.error(f"生成聊天总结失败: {str(e)}")
            return {
                "success": False,
                "summary": "",
                "content": "",
                "message_count": str(len(chat_messages)),
                "language": "zh",
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "duration": 0,
                "error": str(e)
            }