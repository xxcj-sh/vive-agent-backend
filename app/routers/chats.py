"""聊天相关路由

提供聊天历史查询、消息发送等功能
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime

from app.database import get_db
from app.models.schemas import ChatMessageResponse, ChatMessageCreate, ChatListResponse

# 注意：匿名聊天API不需要认证，因为它是公开访问的
router = APIRouter(prefix="/chats", tags=["聊天"])  # 设置/chats前缀，结合main.py中的/api/v1前缀得到/api/v1/chats

# 模拟数据存储
mock_messages = []

@router.get("", response_model=ChatListResponse)
async def get_chat_list(
    db: Session = Depends(get_db),
    user_id: Optional[str] = Query(None, description="用户ID，用于筛选用户相关的聊天")
):
    """获取聊天列表
    
    返回用户的聊天会话列表，支持按用户ID筛选
    """
    try:
        # 返回模拟数据
        return {
            "chats": [],
            "total": 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取聊天列表失败: {str(e)}")


@router.get("/{chat_id}/messages", response_model=List[ChatMessageResponse])
async def get_chat_messages(
    chat_id: str,
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取聊天历史记录
    
    根据聊天ID获取消息历史，支持分页
    """
    try:
        # 返回模拟数据
        chat_messages = [msg for msg in mock_messages if msg['session_id'] == chat_id]
        
        # 按创建时间排序
        chat_messages.sort(key=lambda x: x['created_at'])
        
        # 转换为响应格式
        result = []
        for msg in chat_messages:
            result.append({
                "id": msg['id'],
                "content": msg['content'],
                "type": msg['message_type'],
                "sender": msg['sender_type'],
                "created_at": msg['created_at'].isoformat()
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取聊天消息失败: {str(e)}")


@router.post("/{chat_id}/messages", response_model=ChatMessageResponse)
async def send_chat_message(
    chat_id: str,
    message_data: ChatMessageCreate,
    db: Session = Depends(get_db)
):
    """发送聊天消息
    
    支持匿名消息和普通消息的发送
    """
    try:
        # 判断是否为匿名消息
        is_anonymous = hasattr(message_data, 'is_anonymous') and message_data.is_anonymous
        
        # 创建模拟消息对象
        new_message = {
            'id': str(uuid.uuid4()),
            'user_id': None if is_anonymous else "default_user",
            'content': message_data.content,
            'message_type': message_data.type or "text",
            'sender_type': "user",
            'session_id': chat_id,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        
        # 保存到模拟存储
        mock_messages.append(new_message)
        
        # 返回响应
        return {
            "id": new_message['id'],
            "content": new_message['content'],
            "type": new_message['message_type'],
            "sender": new_message['sender_type'],
            "created_at": new_message['created_at'].isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发送消息失败: {str(e)}")