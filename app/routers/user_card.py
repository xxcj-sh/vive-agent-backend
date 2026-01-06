from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.utils.db_config import get_db
from app.services.user_card_service import UserCardService
from app.services.data_adapter import DataService
from app.services.llm_service import LLMService
from app.services.user_profile.user_profile_service import UserProfileService
from app.models.user_card import CardCreate, CardUpdate
from app.models.llm_schemas import ChatSuggestionRequest, ChatSuggestionResponse
from app.dependencies import get_current_user
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
import hashlib
import logging

logger = logging.getLogger(__name__)

# 简单的内存缓存，用于存储聊天建议
_chat_suggestions_cache: Dict[str, Dict[str, Any]] = {}
_CACHE_EXPIRY_MINUTES = 30  # 缓存过期时间（分钟）

def _generate_cache_key(user_id: str, card_id: str) -> str:
    """生成缓存键"""
    cache_data = f"{user_id}:{card_id}"
    return hashlib.md5(cache_data.encode('utf-8')).hexdigest()

def _get_cached_suggestions(cache_key: str) -> Optional[Dict[str, Any]]:
    """获取缓存的建议，如果缓存存在且未过期"""
    if cache_key in _chat_suggestions_cache:
        cached_data = _chat_suggestions_cache[cache_key]
        if datetime.utcnow() - cached_data['cached_at'] < timedelta(minutes=_CACHE_EXPIRY_MINUTES):
            logger.info(f"缓存命中: {cache_key}")
            return cached_data['data']
        else:
            del _chat_suggestions_cache[cache_key]
    return None

def _cache_suggestions(cache_key: str, suggestions: List[str], confidence: float):
    """缓存建议数据"""
    _chat_suggestions_cache[cache_key] = {
        'data': {
            'suggestions': suggestions,
            'confidence': confidence,
            'generated_at': datetime.utcnow()
        },
        'cached_at': datetime.utcnow()
    }
    logger.info(f"已缓存聊天建议: {cache_key}")

router = APIRouter(
    prefix="/user-cards",
    tags=["user-cards"],
    responses={404: {"description": "Not found"}},
)

@router.get("/{card_id}")
def get_card_details(
    card_id: str,
    db: Session = Depends(get_db)
):
    """通过card ID获取资料详情，包含卡片信息和用户基础资料"""
    from app.models.user import User
    
    card = UserCardService.get_card_by_id(db, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    # 检查卡片是否被删除或未激活
    if card.is_deleted == 1 or card.is_active == 0:
        raise HTTPException(status_code=404, detail="Card not found or inactive")
    
    # 获取用户基础信息
    user = db.query(User).filter(User.id == card.user_id).first()
    
    # 构建响应数据，包含卡片信息和用户基础资料
    response_data = {
        "id": card.id,
        "user_id": card.user_id,
        "role_type": card.role_type,
        "display_name": card.display_name,
        "avatar_url": card.avatar_url,
        "bio": card.bio,
        "profile_data": card.profile_data or {},
        "preferences": card.preferences or {},
        "visibility": card.visibility,
        "created_at": card.created_at,
        "updated_at": card.updated_at,
        # 用户基础信息
        "user_info": {
            "nick_name": user.nick_name if user else None,
            "age": user.age if user else None,
            "gender": user.gender if user else None,
            "occupation": getattr(user, 'occupation', None) if user else None,
            "location": getattr(user, 'location', None) if user else None,
            "education": getattr(user, 'education', None) if user else None,
            "interests": getattr(user, 'interests', []) if user else [],
            "avatar_url": user.avatar_url if user else None,
            # 社交媒体账号信息
            "xiaohongshu_id": getattr(user, 'xiaohongshu_id', None) if user else None,
            "douyin_id": getattr(user, 'douyin_id', None) if user else None,
            "wechat_official_account": getattr(user, 'wechat_official_account', None) if user else None,
            "xiaoyuzhou_id": getattr(user, 'xiaoyuzhou_id', None) if user else None
        } if user else None
    }
    
    return {
        "code": 0,
        "message": "success",
        "data": response_data
    }

@router.post("")
def create_card(
    card_data: CardCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建新的用户角色卡片"""
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
            
        new_card = UserCardService.create_card(db, user_id, card_data)
        return {
            "code": 0,
            "message": "success",
            "data": {
                "id": new_card.id,
                "user_id": new_card.user_id,
                "role_type": new_card.role_type,
                "display_name": new_card.display_name,
                "avatar_url": new_card.avatar_url,
                "bio": new_card.bio,
                "profile_data": new_card.profile_data or {},
                "preferences": new_card.preferences or {},
                "visibility": new_card.visibility,
                "created_at": new_card.created_at
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{card_id}")
def update_card(
    card_id: str,
    card_data: CardUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新用户角色卡片"""
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
        
    # 首先检查卡片是否存在且属于当前用户
    existing_card = UserCardService.get_card_by_id(db, card_id)
    if not existing_card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    if existing_card.user_id != user_id:
        raise HTTPException(status_code=403, detail="Permission denied")
    print("card_data:", card_data)
    # 执行更新
    updated_card = UserCardService.update_card(db, card_id, card_data.dict(exclude_unset=True))
    if not updated_card:
        raise HTTPException(status_code=404, detail="Failed to update card")
    
    return {
        "code": 0,
        "message": "success",
        "data": {
            "id": updated_card.id,
            "user_id": updated_card.user_id,
            "role_type": updated_card.role_type,
            "display_name": updated_card.display_name,
            "avatar_url": updated_card.avatar_url,
            "bio": updated_card.bio,
            "profile_data": updated_card.profile_data or {},
            "preferences": updated_card.preferences,
            "visibility": updated_card.visibility,
            "updated_at": updated_card.updated_at
        }
    }


@router.delete("/{card_id}")
def delete_card(
    card_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除用户角色卡片（软删除）"""
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
        
    # 首先检查卡片是否存在且属于当前用户
    existing_card = UserCardService.get_card_by_id(db, card_id)
    if not existing_card:
        raise HTTPException(status_code=404, detail="Card not found")
    
    if existing_card.user_id != user_id:
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # 执行软删除
    success = UserCardService.delete_card(db, card_id)
    if not success:
        raise HTTPException(status_code=404, detail="Failed to delete card")
    
    return {
        "code": 0,
        "message": "success",
        "data": {"deleted": True}
    }


@router.get("/{user_id}/recent-topics")
def get_user_recent_topics(
    user_id: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """获取指定用户最近参与讨论的话题信息，包括标题和观点总结"""
    try:
        # 创建DataService实例
        data_service = DataService()
        
        # 验证用户是否存在
        user = data_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # 获取用户最近参与的话题及观点总结
        recent_topics = UserCardService.get_user_recent_topics_with_opinion_summaries(
            db, user_id, limit
        )
        
        return {
            "code": 0,
            "message": "success",
            "data": {
                "user_id": user_id,
                "recent_topics": recent_topics,
                "total_count": len(recent_topics)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"获取用户最近话题失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取用户最近话题失败: {str(e)}")


@router.post("/chat-suggestions", response_model=ChatSuggestionResponse)
async def generate_chat_suggestions(
    request: ChatSuggestionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """生成个性化聊天建议
    根据双方的用户画像，为当前用户提供与目标用户的聊天建议，从当前用户的立场考虑
    """
    try:
        if not current_user:
            return ChatSuggestionResponse(
                suggestions=['没能获取到你的信息，可能是因为没登陆，暂时不能找到共同话题'],
                confidence=0
            )

        # 验证卡片是否存在
        card = UserCardService.get_card_by_id(db, request.card_id)
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")
        
        # 检查卡片是否被删除或未激活
        if card.is_deleted == 1 or card.is_active == 0:
            raise HTTPException(status_code=404, detail="Card not found or inactive")
        
        # 获取卡片主人的偏好和简介信息
        card_bio = request.card_bio or card.bio or ""
        card_preferences = request.card_preferences or (card.preferences or {})
        
        # 获取浏览用户的画像信息
        current_user_id = current_user.get("id")
        user_profile_summary = request.user_profile_summary
        user_raw_profile = request.user_raw_profile
        
        # 如果没有提供用户画像数据，尝试从数据库获取
        if not user_profile_summary and current_user_id:
            user_profile_service = UserProfileService(db)
            user_profile = user_profile_service.get_user_profile(current_user_id)
            if user_profile:
                user_profile_summary = user_profile.profile_summary
                user_raw_profile = user_profile.raw_profile
        
        # 检查缓存（使用当前用户的ID和卡片ID生成缓存键）
        cache_key = None
        cached_result = None
        if current_user_id:
            cache_key = _generate_cache_key(current_user_id, request.card_id)
            cached_result = _get_cached_suggestions(cache_key)
        
        if cached_result:
            return ChatSuggestionResponse(
                suggestions=cached_result['suggestions'],
                confidence=cached_result['confidence'],
                generated_at=cached_result['generated_at']
            )
        
        # 构建LLM提示词
        user_personality = user_profile_summary or "微分智能体的新用户"
        
        preferences_str = json.dumps(card_preferences, ensure_ascii=False, indent=2) if card_preferences else "无"
        
        prompt = f"""
## 当前浏览用户画像信息
用户画像摘要: {user_personality}
用户详细信息: {user_raw_profile}

## 被浏览用户的名片信息
身份简介: {card_bio}
偏好: {preferences_str}

## 任务
请从当前用户角度出发，分析当前用户既可以与对方交谈，又感兴趣的话题，可以考虑以下几点:
1. 当前用户可以从对方那里获得什么信息
2. 当前用户跟对方可能有哪些共同感兴趣的话题
3. 当前用户和对方有哪些共同点

以JSON格式回复，格式如下:
{{
    "suggestions": ["xxxx"],
    "confidence": 0.85
}}
"""
        
        # 调用LLM服务生成建议
        llm_service = LLMService(db)
        from app.models.llm_schemas import LLMRequest, LLMResponse
        from app.models.llm_usage_log import LLMTaskType
        
        llm_request = LLMRequest(
            user_id=current_user_id,
            task_type=LLMTaskType.CONVERSATION_SUGGESTION,
            prompt=prompt
        )
        
        response = await llm_service.call_llm_api(llm_request)
        
        if not response.success or not response.data:
            # 如果LLM调用失败，返回默认建议
            logger.warning(f"LLM生成聊天建议失败，使用默认建议: card_id={request.card_id}")
            default_suggestions = [
                f"可以和{card.display_name}聊聊ta的 bio：{card_bio[:50]}..." if card_bio else f"可以和{card.display_name}打个招呼",
                "问问{card.display_name}今天过得怎么样".format(card=card) if card else "询问对方今天的情况",
                "可以和{card.display_name}聊聊你们的共同兴趣".format(card=card) if card else "讨论共同话题"
            ][:request.max_suggestions]
            
            return ChatSuggestionResponse(
                suggestions=default_suggestions,
                confidence=0.5,
                generated_at=datetime.utcnow()
            )
        
        # 解析LLM响应
        try:
            # 尝试解析JSON格式的响应
            suggestion_data = json.loads(response.data)
            suggestions = suggestion_data.get("suggestions", [])
            confidence = suggestion_data.get("confidence", response.usage.get("total_tokens", 0) / 1000.0)
        except (json.JSONDecodeError, AttributeError):
            # 如果解析失败，将整个响应作为单条建议
            logger.warning(f"解析聊天建议JSON失败，使用原始响应: card_id={request.card_id}")
            suggestions = [response.data] if response.data else []
            confidence = 0.6
        
        # 确保返回指定数量的建议
        suggestions = suggestions[:request.max_suggestions]
        
        # 缓存结果
        if cache_key:
            _cache_suggestions(cache_key, suggestions, confidence)
        
        return ChatSuggestionResponse(
            suggestions=suggestions,
            confidence=confidence
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成聊天建议失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"生成聊天建议失败: {str(e)}")


