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
from app.models.llm_schemas import ConversationSuggestionRequest, SimpleChatStreamRequest, ActivityInfoExtractionRequest, ActivityInfoExtractionResponse

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
    current_user: dict = Depends(auth_service.get_current_user)
):
    """
    生成流式对话建议
    
    提供流式文本响应，先返回聊天文本，后异步返回其他数据（置信度、偏好判断等）
    用于优化用户体验，让用户先看到AI回复内容
    """
    from fastapi.responses import StreamingResponse
    
    service = LLMService(db)
    
    # 如果request中没有user_id，使用当前登录用户
    if not request.userId:
        request.userId = current_user["id"]
    
    async def generate_stream():
        """生成流式响应 - 使用真正的LLM流式调用"""
        import json
        import asyncio
        import re
        try:
            # 调用专门的流式对话建议方法
            stream_response = await service.generate_conversation_suggestion_stream(
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
                        logger.info(f"成功解析metadata: confidence={metadata['confidence']}, is_meet_preference={metadata['is_meet_preference']}")
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
    current_user: dict = Depends(auth_service.get_current_user)
):
    """
    简单聊天流式接口 - 仅返回纯文本
    
    专为微信小程序流式聊天设计，只返回纯文本内容，不包含复杂的JSON结构
    用于实时的聊天响应，提升用户体验
    """
    from fastapi.responses import StreamingResponse
    
    service = LLMService(db)
    
    # 如果request中没有user_id，使用当前登录用户
    if not request.userId:
        request.userId = current_user["id"]
    
    async def generate_text_stream():
        """生成纯文本流式响应"""
        import json
        try:
            # 调用简单聊天流式方法
            stream_response = await service.generate_simple_chat_stream(
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
                    print("content:", content)
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
    current_user: dict = Depends(auth_service.get_current_user)
):
    """
    生成对话建议
    
    分析用户聊天记录信息，生成一条或多条适合当前对话情境的回复建议
    上下文引入卡片主人的偏好信息，引导用户回答问题，以判断用户是否满足卡片主人的偏好
    """
    service = LLMService(db)
    
    # 如果request中没有user_id，使用当前登录用户
    if not request.userId:
        request.userId = current_user["id"]
    
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


@router.post("/extract-activity-info")
async def extract_activity_info(
    request: ActivityInfoExtractionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_service.get_current_user)
):
    """
    提取活动信息
    
    从对话历史中提取活动相关信息，包括时间、地点和用户偏好等
    用于咖啡聊天等场景的信息自动提取，优化用户体验
    """
    service = LLMService(db)
    
    # 如果request中没有user_id，使用当前登录用户
    if not request.user_id:
        request.user_id = current_user["id"]
    
    response = await service.extract_activity_info(
        user_id=request.user_id,
        conversation_history=request.conversation_history,
        provider=settings.LLM_PROVIDER,
        model_name=settings.LLM_MODEL
    )
    
    if not response.success:
        raise HTTPException(status_code=500, detail="提取活动信息失败")
    
    return {
        "code": 0,
        "message": "success",
        "data": {
            "time_info": response.time_info,
            "location_info": response.location_info,
            "preference_info": response.preference_info,
            "usage": response.usage,
            "duration": response.duration
        }
    }


@router.post("/generate-coffee-chat-response")
async def generate_coffee_chat_response(
    request: dict,
    db: Session = Depends(get_db)
):
    """
    生成咖啡聊天对话回复
    
    专为咖啡聊天场景设计的对话生成接口，根据用户消息、对话历史和已提取的信息
    生成自然、友好的咖啡约会安排对话回复
    
    测试接口，无需认证
    """
    service = LLMService(db)
    
    # 获取用户ID，默认为测试用户
    user_id = request.get("user_id", "test-coffee-user")
    user_message = request.get("user_message", "")
    conversation_history = request.get("conversation_history", [])
    extracted_info = request.get("extracted_info", {})
    dialog_count = request.get("dialog_count", 0)
    
    try:
        response = await service.generate_coffee_chat_response(
            user_id=user_id,
            user_message=user_message,
            conversation_history=conversation_history,
            extracted_info=extracted_info,
            dialog_count=dialog_count,
            provider=settings.LLM_PROVIDER,
            model_name=settings.LLM_MODEL
        )
        
        if not response.success:
            raise HTTPException(status_code=500, detail="生成咖啡聊天回复失败")
        
        return {
            "code": 0,
            "message": "success",
            "data": {
                "response": response.data,
                "usage": response.usage,
                "duration": response.duration
            }
        }
    except Exception as e:
        logger.error(f"生成咖啡聊天回复失败: {str(e)}")
        return {
            "code": 500,
            "message": f"生成失败: {str(e)}",
            "data": {
                "response": "抱歉，我现在无法生成回复，请稍后再试。",
                "usage": {},
                "duration": 0,
                "error": str(e)
            }
        }