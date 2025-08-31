from fastapi import APIRouter, Depends, Query, Path, Request, HTTPException, status
from app.models.schemas import (
    ChatHistoryResponse, SendMessageRequest, SendMessageResponse, 
    ReadMessageRequest, BaseResponse
)
from app.services.auth import auth_service
# 移除mock_data依赖
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
    current_user: Dict[str, Any] = Depends(auth_service.get_current_user)
):
    """获取聊天记录"""
    try:
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
    except Exception as e:
        return BaseResponse(
            code=1001,
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
    current_user: Dict[str, Any] = Depends(auth_service.get_current_user)
):
    """发送消息"""
    try:
        # 简化消息发送，实际应保存到数据库
        result = {
            "messageId": str(uuid.uuid4()),
            "matchId": request.matchId,
            "senderId": current_user["id"],
            "content": request.content,
            "messageType": request.messageType,
            "timestamp": int(time.time()),
            "status": "sent"
        }
        
        return BaseResponse(
            code=0,
            message="消息发送成功",
            data=result
        )
    except Exception as e:
        return BaseResponse(
            code=1003,
            message=f"发送消息失败: {str(e)}",
            data=None
        )

@router.post("/read", response_model=BaseResponse)
async def mark_messages_as_read(
    request: ReadMessageRequest,
    current_user: Dict[str, Any] = Depends(auth_service.get_current_user)
):
    """标记消息为已读"""
    try:
        # 简化已读标记，实际应更新数据库
        return BaseResponse(
            code=0,
            message="消息已标记为已读",
            data={"success": True}
        )
    except Exception as e:
        return BaseResponse(
            code=1004,
            message=f"标记消息失败: {str(e)}",
            data=None
        )

@router.get("/{matchId}/unread-count", response_model=BaseResponse)
async def get_unread_count(
    matchId: str = Path(..., description="匹配ID"),
    current_user: Dict[str, Any] = Depends(auth_service.get_current_user)
):
    """获取未读消息数量"""
    try:
        # 返回0未读消息，实际应从数据库查询
        return BaseResponse(
            code=0,
            message="success",
            data={"unreadCount": 0}
        )
    except Exception as e:
        return BaseResponse(
            code=1005,
            message=f"获取未读消息数量失败: {str(e)}",
            data=None
        )

@router.delete("/{matchId}/messages/{messageId}", response_model=BaseResponse)
async def delete_message(
    matchId: str = Path(..., description="匹配ID"),
    messageId: str = Path(..., description="消息ID"),
    current_user: Dict[str, Any] = Depends(auth_service.get_current_user)
):
    """删除消息"""
    try:
        # 简化消息删除，实际应从数据库删除
        return BaseResponse(
            code=0,
            message="消息删除成功",
            data={"success": True}
        )
    except Exception as e:
        return BaseResponse(
            code=1006,
            message=f"删除消息失败: {str(e)}",
            data=None
        )