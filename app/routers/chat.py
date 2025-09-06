from fastapi import APIRouter, Depends, Query, Path, Request, HTTPException, status
from sqlalchemy.orm import Session
from app.models.schemas import (
    ChatHistoryResponse, SendMessageRequest, SendMessageResponse, 
    ReadMessageRequest, BaseResponse, ConversationListResponse,
    UnreadCountResponse
)
from app.services.auth import auth_service
from app.services.chat_service import ChatService
from app.database import get_db
import uuid
import time
from typing import Dict, Any, Optional
from pydantic import BaseModel

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)

@router.get("/{matchId}/history", response_model=BaseResponse)
async def get_chat_history(
    matchId: str = Path(..., description="匹配ID"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: Dict[str, Any] = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """获取聊天记录"""
    try:
        chat_service = ChatService(db)
        result = chat_service.get_chat_history(
            match_id=matchId,
            user_id=current_user["id"],
            page=page,
            limit=limit
        )
        
        return BaseResponse(
            code=0,
            message="success",
            data={
                "messages": result.list,
                "total": result.pagination["total"],
                "page": result.pagination["page"],
                "limit": result.pagination["page_size"],
                "has_more": result.pagination["total"] > page * limit
            }
        )
    except ValueError as e:
        return BaseResponse(
            code=1001,
            message=str(e),
            data=None
        )
    except Exception as e:
        return BaseResponse(
            code=1002,
            message=f"获取聊天记录失败: {str(e)}",
            data=None
        )

def _get_chat_history_internal(
    matchId: str,
    page: int,
    limit: int,
    current_user: Dict[str, Any]
):
    """获取聊天记录内部实现"""
    # 返回空的聊天记录，实际应从数据库获取
    result = {
        "messages": [],
        "total": 0,
        "page": page,
        "limit": limit,
        "has_more": False
    }
    return BaseResponse(
        code=0,
        message="success",
        data=result
    )

@router.post("/send", response_model=BaseResponse)
async def send_message(
    request: SendMessageRequest,
    current_user: Dict[str, Any] = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """发送消息"""
    try:
        chat_service = ChatService(db)
        result = chat_service.send_message(request, current_user["id"])
        
        return BaseResponse(
            code=0,
            message="消息发送成功",
            data={
                "messageId": result["id"],
                "matchId": request.match_id,
                "senderId": current_user["id"],
                "content": request.content,
                "messageType": request.type,
                "timestamp": result["timestamp"],
                "status": result["status"]
            }
        )
    except ValueError as e:
        return BaseResponse(
            code=1003,
            message=str(e),
            data=None
        )
    except Exception as e:
        return BaseResponse(
            code=1004,
            message=f"发送消息失败: {str(e)}",
            data=None
        )

@router.post("/read", response_model=BaseResponse)
async def mark_messages_as_read(
    request: ReadMessageRequest,
    current_user: Dict[str, Any] = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """标记消息为已读"""
    try:
        chat_service = ChatService(db)
        success = chat_service.mark_messages_as_read(
            match_id=request.matchId,
            message_ids=request.messageIds,
            user_id=current_user["id"]
        )
        
        return BaseResponse(
            code=0,
            message="消息已标记为已读",
            data={"success": success}
        )
    except ValueError as e:
        return BaseResponse(
            code=1005,
            message=str(e),
            data=None
        )
    except Exception as e:
        return BaseResponse(
            code=1006,
            message=f"标记消息失败: {str(e)}",
            data=None
        )

@router.get("/{matchId}/unread-count", response_model=BaseResponse)
async def get_unread_count(
    matchId: str = Path(..., description="匹配ID"),
    current_user: Dict[str, Any] = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """获取未读消息数量"""
    try:
        chat_service = ChatService(db)
        result = chat_service.get_unread_count(matchId, current_user["id"])
        
        return BaseResponse(
            code=0,
            message="success",
            data={
                "unreadCount": result.unread_count,
                "lastMessage": result.last_message
            }
        )
    except ValueError as e:
        return BaseResponse(
            code=1007,
            message=str(e),
            data=None
        )
    except Exception as e:
        return BaseResponse(
            code=1008,
            message=f"获取未读消息数量失败: {str(e)}",
            data=None
        )

@router.delete("/{matchId}/messages/{messageId}", response_model=BaseResponse)
async def delete_message(
    matchId: str = Path(..., description="匹配ID"),
    messageId: str = Path(..., description="消息ID"),
    current_user: Dict[str, Any] = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """删除消息"""
    try:
        chat_service = ChatService(db)
        count = chat_service.delete_messages([messageId], current_user["id"])
        
        return BaseResponse(
            code=0,
            message=f"成功删除 {count} 条消息",
            data={"success": count > 0}
        )
    except ValueError as e:
        return BaseResponse(
            code=1009,
            message=str(e),
            data=None
        )
    except Exception as e:
        return BaseResponse(
            code=1010,
            message=f"删除消息失败: {str(e)}",
            data=None
        )

@router.get("/conversations", response_model=BaseResponse)
async def get_conversation_list(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: Dict[str, Any] = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db)
):
    """获取会话列表"""
    try:
        chat_service = ChatService(db)
        result = chat_service.get_conversation_list(
            user_id=current_user["id"],
            page=page,
            limit=limit
        )
        
        return BaseResponse(
            code=0,
            message="success",
            data={
                "conversations": result.list,
                "total": result.pagination["total"],
                "page": result.pagination["page"],
                "limit": result.pagination["page_size"],
                "has_more": result.pagination["total"] > page * limit
            }
        )
    except Exception as e:
        return BaseResponse(
            code=1011,
            message=f"获取会话列表失败: {str(e)}",
            data=None
        )