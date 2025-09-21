"""
大语言模型API路由
提供LLM相关的RESTful API接口
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.config import settings

from app.database import get_db
from app.services.auth import auth_service
from app.services.llm_service import LLMService
from app.models.llm_schemas import ConversationSuggestionRequest

router = APIRouter(prefix="/llm", tags=["大语言模型"])



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
    print("response:", response)
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