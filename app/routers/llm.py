"""
大语言模型API路由
提供LLM相关的RESTful API接口
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.config import settings
import logging

from app.database import get_db
from app.services.auth import auth_service
from app.services.llm_service import LLMService
from app.services.user_card_service import UserCardService
from app.models.llm_schemas import ConversationSuggestionRequest, SimpleChatStreamRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/llm", tags=["大语言模型"])


def _infer_preference_from_content(content: str) -> bool:
    """从内容中推断是否满足偏好
    
    通过关键词匹配来推断用户是否可能满足卡片主人的偏好要求
    """
    content_lower = content.lower()
    
    # 正面关键词 - 表示匹配
    positive_keywords = [
        '符合', '匹配', '适合', '满足', '达标', '合格',
        '很好', '不错', '推荐', '喜欢', '感兴趣',
        '符合要求', '满足条件', '达到标准'
    ]
    
    # 负面关键词 - 表示不匹配  
    negative_keywords = [
        '不符合', '不匹配', '不适合', '不满足', '不达标', '不合格',
        '不推荐', '不喜欢', '不感兴趣'
    ]
    
    positive_count = sum(1 for keyword in positive_keywords if keyword in content_lower)
    negative_count = sum(1 for keyword in negative_keywords if keyword in content_lower)
    
    # 简单的评分机制 - 负面关键词权重更高
    score = positive_count - (negative_count * 2)
    
    # 如果得分大于0，认为可能满足偏好；否则认为不满足
    return score > 0

@router.post("/conversation-suggestions/stream")
async def generate_conversation_suggestions_stream(
    request: ConversationSuggestionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_service.get_current_user_optional)
):
    """
    生成流式对话建议
    
    提供流式文本响应，先返回聊天文本，后异步返回其他数据（置信度、偏好判断等）
    用于优化用户体验，让用户先看到AI回复内容
    """
    from fastapi.responses import StreamingResponse
    
    service = LLMService(db)
    
    # 如果request中没有user_id，使用当前登录用户或匿名用户
    if not request.userId:
        if current_user:
            request.userId = current_user["id"]
        else:
            # 使用匿名用户
            anonymous_user = auth_service.get_anonymous_user()
            request.userId = anonymous_user["id"]
            current_user = anonymous_user
    
    async def generate_stream():
        """生成流式响应 - 使用真正的LLM流式调用"""
        import json
        import asyncio
        import re
        try:
            # 调用专门的流式对话建议方法
            stream_response = service.generate_conversation_suggestion_stream(
                user_id=request.userId,
                card_id=request.cardId,
                chatId=request.chatId,
                context=request.context,
                suggestionType=request.suggestionType,
                maxSuggestions=request.maxSuggestions,
                provider=settings.LLM_PROVIDER,
                model_name=settings.LLM_MODEL
            )
            
            # 收集完整响应用于后续处理
            full_content = ""
            
            # 流式发送文本内容
            async for chunk in stream_response:
                if chunk["type"] == "text":
                    content = chunk["content"]
                    full_content += content
                    data = {
                        "type": "text",
                        "content": content,
                        "finished": chunk.get("finished", False)
                    }
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                elif chunk["type"] == "end":
                    break
            
            # 解析完整响应获取元数据
            try:
                # 尝试从完整内容中提取JSON部分
                json_match = re.search(r'\{[\s\S]*\}', full_content, re.DOTALL)
                if json_match:
                    try:
                        response_data = json.loads(json_match.group())
                        
                        # 发送元数据
                        await asyncio.sleep(0.2)
                        metadata = {
                            "type": "metadata",
                            "confidence": response_data.get("confidence", 0.8),
                            "is_meet_preference": response_data.get("is_meet_preference", False),
                            "preference_judgement": response_data.get("preference_judgement", ""),
                            "usage": {"prompt_tokens": 50, "completion_tokens": len(full_content), "total_tokens": 50 + len(full_content)},
                            "duration": 2.0
                        }
                        yield f"data: {json.dumps(metadata, ensure_ascii=False)}\n\n"
                    except json.JSONDecodeError as json_error:
                        logger.warning(f"JSON解析失败: {str(json_error)}, 内容: {json_match.group()[:200]}")
                        # 发送默认元数据
                        await asyncio.sleep(0.2)
                        metadata = {
                            "type": "metadata",
                            "confidence": 0.7,
                            "is_meet_preference": True,
                            "preference_judgement": "分析完成",
                            "usage": {"prompt_tokens": 50, "completion_tokens": len(full_content), "total_tokens": 50 + len(full_content)},
                            "duration": 2.0
                        }
                        yield f"data: {json.dumps(metadata, ensure_ascii=False)}\n\n"
                else:
                    # 如果没有找到JSON格式，尝试查找其他模式
                    logger.warning(f"未找到JSON格式，完整内容预览: {full_content[:300]}")
                    
                    # 尝试从内容中推断偏好匹配
                    is_meet_preference = _infer_preference_from_content(full_content)
                    
                    await asyncio.sleep(0.2)
                    metadata = {
                        "type": "metadata",
                        "confidence": 0.6,
                        "is_meet_preference": is_meet_preference,
                        "preference_judgement": "基于内容分析",
                        "usage": {"prompt_tokens": 50, "completion_tokens": len(full_content), "total_tokens": 50 + len(full_content)},
                        "duration": 2.0
                    }
                    yield f"data: {json.dumps(metadata, ensure_ascii=False)}\n\n"
            except Exception as e:
                logger.error(f"解析响应数据失败: {str(e)}")
                # 发送默认元数据
                metadata = {
                    "type": "metadata",
                    "confidence": 0.5,
                    "is_meet_preference": True,
                    "preference_judgement": "默认分析结果",
                    "usage": {"prompt_tokens": 50, "completion_tokens": len(full_content), "total_tokens": 50 + len(full_content)},
                    "duration": 2.0
                }
                yield f"data: {json.dumps(metadata, ensure_ascii=False)}\n\n"
            
            # 发送结束标记
            yield f"data: {json.dumps({'type': 'end'}, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            logger.error(f"流式生成对话建议失败: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/simple-chat/stream")
async def generate_simple_chat_stream(
    request: SimpleChatStreamRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_service.get_current_user_optional)
):
    """
    简单聊天流式接口 - 仅返回纯文本
    
    专为微信小程序流式聊天设计，只返回纯文本内容，不包含复杂的JSON结构
    用于实时的聊天响应，提升用户体验
    """
    from fastapi.responses import StreamingResponse
    
    service = LLMService(db)
    
    # 如果request中没有user_id，使用当前登录用户或匿名用户
    if not request.userId:
        if current_user:
            request.userId = current_user["id"]
        else:
            # 使用匿名用户
            anonymous_user = auth_service.get_anonymous_user()
            request.userId = anonymous_user["id"]
            current_user = anonymous_user
    
    async def generate_text_stream():
        """生成纯文本流式响应"""
        import json
        try:
            # 调用简单聊天流式方法
            stream_response = service.generate_simple_chat_stream(
                user_id=request.userId,
                card_id=request.cardId,
                chat_id=request.chatId,
                message=request.message,
                context=request.context,
                personality=request.personality,
                provider=settings.LLM_PROVIDER,
                model_name=settings.LLM_MODEL
            )
            
            # 流式发送纯文本内容
            async for chunk in stream_response:
                if chunk["type"] == "text":
                    
                    content = chunk["content"]
                    # 直接发送纯文本数据，格式更简洁
                    data = {
                        "type": "text", 
                        "content": content,
                        "finished": chunk.get("finished", False)
                    }
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                elif chunk["type"] == "end":
                    break
            
            # 发送结束标记
            yield f"data: {json.dumps({'type': 'end'}, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            logger.error(f"简单聊天流式生成失败: {str(e)}")
            # 发送错误信息
            error_data = {
                "type": "error",
                "message": str(e)
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate_text_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive", 
            "X-Accel-Buffering": "no"
        }
    )

@router.post("/conversation-suggestions")
async def generate_conversation_suggestions(
    request: ConversationSuggestionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_service.get_current_user_optional)
):
    """
    生成对话建议
    
    分析用户聊天记录信息，生成一条或多条适合当前对话情境的回复建议
    上下文引入卡片主人的偏好信息，引导用户回答问题，以判断用户是否满足卡片主人的偏好
    """
    service = LLMService(db)
    
    # 如果request中没有user_id，使用当前登录用户或匿名用户
    if not request.userId:
        if current_user:
            request.userId = current_user["id"]
        else:
            # 使用匿名用户
            anonymous_user = auth_service.get_anonymous_user()
            request.userId = anonymous_user["id"]
            current_user = anonymous_user
    
    response = await service.generate_conversation_suggestion(
        user_id=request.userId,
        card_id=request.cardId,
        chatId=request.chatId,
        context=request.context,
        suggestionType=request.suggestionType,
        maxSuggestions=request.maxSuggestions,
        provider=settings.LLM_PROVIDER,
        model_name=settings.LLM_MODEL
    )
    if not response.success:
        raise HTTPException(status_code=500, detail="生成对话建议失败")
    
    return {
        "code": 0,
        "message": "success",
        "data": {
            "suggestions": response.suggestions,
            "confidence": response.confidence,
            "usage": response.usage,
            "duration": response.duration,
            "is_meet_preference": response.is_meet_preference,
            "preference_judgement": response.preference_judgement
        }
    }


@router.post("/process-scene")
async def process_scene_request(
    request: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_service.get_current_user_optional)
):
    """
    统一的场景化LLM处理接口
    
    通过scene_config_key参数来区分不同的LLM使用场景，实现所有LLM调用的统一管理和调试
    
    支持的scene_config_key:
    - conversation-suggestions: 对话建议生成
    - simple-chat: 简单聊天（支持general/topic/sports子类型）
    - extract-activity-info: 活动信息提取
    - topic-discussion: 话题讨论
    - generate-opinion-summary: 观点总结生成
    
    请求格式：
    {
        "scene_config_key": "coffee-chat",
        "params": {
            "message": "用户消息",
            "conversation_history": [],
            "extracted_info": {},
            "dialog_count": 0
        },
        "stream": false,
        "provider": "volcengine",
        "model_name": "doubao-pro-32k"
    }
    """
    service = LLMService(db)
    
    # 获取用户ID，默认为当前登录用户或匿名用户
    if current_user:
        user_id = request.get("user_id", current_user["id"])
    else:
        anonymous_user = auth_service.get_anonymous_user()
        user_id = request.get("user_id", anonymous_user["id"])
        current_user = anonymous_user
    scene_config_key = request.get("scene_config_key", "")
    params = request.get("params", {})
    stream = request.get("stream", False)
    provider = request.get("provider", settings.LLM_PROVIDER)
    model_name = request.get("model_name", settings.LLM_MODEL)
    
    if not scene_config_key:
        raise HTTPException(status_code=400, detail="scene_config_key不能为空")
    
    try:
        # 调用统一的场景化处理方法
        response = await service.process_scene_request(
            user_id=user_id,
            scene_config_key=scene_config_key,
            params=params,
            provider=provider,
            model_name=model_name,
            stream=stream
        )
        
        if not response.get("success", False):
            error_msg = response.get("error", "处理失败")
            raise HTTPException(status_code=500, detail=error_msg)
        
        return {
            "code": 0,
            "message": "success",
            "data": response
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"场景化LLM处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@router.post("/process-scene/stream")
async def process_scene_stream(
    request: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_service.get_current_user_optional)
):
    """
    统一的场景化LLM流式处理接口
    
    支持流式输出的场景化LLM调用，用于实时聊天等需要流式响应的场景
    
    支持的scene_config_key:
    - conversation-suggestions: 对话建议生成（流式）
    - simple-chat: 简单聊天（流式）
    - topic-discussion: 话题讨论（流式）
    """
    from fastapi.responses import StreamingResponse
    
    service = LLMService(db)
    
    # 获取用户ID，默认为当前登录用户或匿名用户
    if current_user:
        user_id = request.get("user_id", current_user["id"])
    else:
        anonymous_user = auth_service.get_anonymous_user()
        user_id = request.get("user_id", anonymous_user["id"])
        current_user = anonymous_user
    scene_config_key = request.get("scene_config_key", "")
    params = request.get("params", {})
    provider = request.get("provider", settings.LLM_PROVIDER)
    model_name = request.get("model_name", settings.LLM_MODEL)
    card_id = params.get("context", {}).get("cardId", "")
    if card_id:
        user_card = UserCardService.get_card_by_id(db, card_id)
        if user_card:
            import json
            try:
                profile_data = json.loads(user_card.profile_data) if user_card.profile_data else {}
            except (json.JSONDecodeError, TypeError):
                profile_data = {}
            
            params["character_profile"] = {
                "display_name": user_card.display_name,
                "bio": user_card.bio or "",
                "role_type": user_card.role_type,
                "profile_data": profile_data
            }
    
    if not scene_config_key:
        raise HTTPException(status_code=400, detail="scene_config_key不能为空")
    
    # 检查是否支持流式处理
    streamable_scenes = ["conversation-suggestions", "simple-chat", "topic-discussion"]
    if scene_config_key not in streamable_scenes:
        raise HTTPException(status_code=400, detail=f"场景 {scene_config_key} 不支持流式处理")
    
    async def generate_stream():
        """生成流式响应"""
        import json
        try:
            # 调用统一的场景化处理方法（启用流式）
            stream_response = service.process_scene_request_stream(
                user_id=user_id,
                scene_config_key=scene_config_key,
                params=params,
                provider=provider,
                model_name=model_name
            )
            # 流式发送响应内容
            async for chunk in stream_response:
                if chunk["type"] == "text":
                    data = {
                        "type": "text",
                        "content": chunk["content"],
                        "finished": chunk.get("finished", False)
                    }
                    yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                elif chunk["type"] == "end":
                    break
            
            # 发送结束标记
            yield f"data: {json.dumps({'type': 'end'}, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            logger.error(f"场景化LLM流式处理失败: {str(e)}")
            error_data = {
                "type": "error",
                "message": str(e)
            }
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )