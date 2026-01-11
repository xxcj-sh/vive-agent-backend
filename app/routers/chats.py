"""聊天相关路由

提供聊天历史查询、消息发送等功能
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime

from app.database import get_db
from app.models.chat_message import ChatMessage, ChatSummary
from app.models.schemas import ChatMessageResponse, ChatMessageCreate, ChatListResponse, ChatSummaryResponse, ChatSummaryCreate
from app.services.llm_service import LLMService

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
        # 从数据库查询消息
        query = db.query(ChatMessage).filter(ChatMessage.session_id == chat_id)
        
        # 按创建时间排序（升序）
        query = query.order_by(ChatMessage.created_at.asc())
        
        # 应用分页
        offset = (page - 1) * limit
        messages = query.offset(offset).limit(limit).all()
        
        return [msg.to_dict() for msg in messages]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取聊天消息失败: {str(e)}")


@router.post("/{chat_id}/messages", response_model=ChatMessageResponse)
async def send_chat_message(
    chat_id: str,
    message_data: ChatMessageCreate,
    db: Session = Depends(get_db)
):
    """发送聊天消息
    
    支持匿名消息和普通消息的发送，保存到数据库
    """
    try:
        # 判断是否为匿名消息
        is_anonymous = getattr(message_data, 'is_anonymous', False) or False
        
        # 从请求中获取用户ID和卡片ID（如果有的话）
        user_id = getattr(message_data, 'user_id', None) or None
        card_id = getattr(message_data, 'card_id', None) or None
        
        # 创建消息记录
        new_message = ChatMessage(
            user_id=user_id,
            card_id=card_id,
            content=message_data.content,
            message_type=message_data.type or "text",
            sender_type="user",
            session_id=chat_id,
            is_anonymous=is_anonymous,
            is_read=False
        )
        
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        
        return {
            "id": new_message.id,
            "content": new_message.content,
            "type": new_message.message_type,
            "sender": new_message.sender_type,
            "created_at": new_message.created_at.isoformat()
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"发送消息失败: {str(e)}")


@router.delete("/{chat_id}/messages/{message_id}")
async def delete_chat_message(
    chat_id: str,
    message_id: str,
    db: Session = Depends(get_db)
):
    """删除聊天消息
    
    根据消息ID删除指定的聊天消息
    """
    try:
        message = db.query(ChatMessage).filter(
            ChatMessage.id == message_id,
            ChatMessage.session_id == chat_id
        ).first()
        
        if not message:
            raise HTTPException(status_code=404, detail="消息不存在")
        
        db.delete(message)
        db.commit()
        
        return {"message": "消息删除成功", "message_id": message_id}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除消息失败: {str(e)}")


@router.post("/{chat_id}/messages/ai", response_model=ChatMessageResponse)
async def save_ai_message(
    chat_id: str,
    message_data: ChatMessageCreate,
    db: Session = Depends(get_db)
):
    """保存AI回复消息
    
    在AI生成回复后，保存AI的回复消息到数据库
    """
    try:
        # 从请求中获取卡片ID
        card_id = getattr(message_data, 'card_id', None) or None
        
        # 创建AI消息记录
        new_message = ChatMessage(
            user_id=None,
            card_id=card_id,
            content=message_data.content,
            message_type=message_data.type or "text",
            sender_type="ai",
            session_id=chat_id,
            is_anonymous=False,
            is_read=False
        )
        
        db.add(new_message)
        db.commit()
        db.refresh(new_message)
        
        return {
            "id": new_message.id,
            "content": new_message.content,
            "type": new_message.message_type,
            "sender": new_message.sender_type,
            "created_at": new_message.created_at.isoformat()
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"保存AI消息失败: {str(e)}")


@router.delete("/{chat_id}/messages")
async def delete_chat_messages(
    chat_id: str,
    db: Session = Depends(get_db)
):
    """清空聊天会话
    
    删除指定聊天会话的所有消息
    """
    try:
        # 查询该会话的所有消息
        messages = db.query(ChatMessage).filter(ChatMessage.session_id == chat_id).all()
        
        if not messages:
            return {"message": "该会话没有消息需要删除", "deleted_count": 0}
        
        # 删除所有消息
        for message in messages:
            db.delete(message)
        
        db.commit()
        
        return {"message": "会话消息删除成功", "deleted_count": len(messages)}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除会话消息失败: {str(e)}")


@router.post("/summaries", response_model=ChatSummaryResponse)
async def create_chat_summary(
    summary_data: ChatSummaryCreate,
    db: Session = Depends(get_db)
):
    """创建聊天总结
    
    保存用户聊天的AI总结内容，并发送通知给卡片所有者
    如果提供了user_messages，将使用LLM服务生成总结内容
    """
    try:
        user_messages = summary_data.user_messages
        
        # 使用LLM服务生成总结
        llm_service = LLMService(db)
        summary_result = await llm_service.generate_chat_summary(
            user_id=summary_data.user_id,
            chat_messages=user_messages
        )
        
        if summary_result.get("success"):
            summary_content = summary_result["summary"]
            # 更新消息数量
            summary_data.chat_messages_count = summary_result["message_count"]
        else:
            # LLM生成失败，使用备用方案
            summary_content = f"共{len(user_messages)}条消息，主要关注{user_messages[0][:50] if user_messages and user_messages[0] else '相关话题'}..."
            summary_data.chat_messages_count = str(len(user_messages))
        
        # 创建新的聊天总结记录
        new_summary = ChatSummary(
            user_id=summary_data.user_id,
            card_id=summary_data.card_id,
            session_id=summary_data.session_id,
            summary_type=summary_data.summary_type or 'chat',
            summary_content=summary_content,
            chat_messages_count=summary_data.chat_messages_count,
            summary_language=summary_data.summary_language or 'zh',
            is_read=summary_data.is_read or False
        )
        
        db.add(new_summary)
        db.commit()
        db.refresh(new_summary)
        
        return new_summary.to_dict()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建聊天总结失败: {str(e)}")


@router.get("/summaries/unread-count")
async def get_unread_chat_summaries_count(
    user_id: str = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """获取未读聊天总结数量
    
    获取用户未读的聊天总结数量
    """
    try:
        # 首先查询当前用户拥有的所有card_id
        from sqlalchemy import select
        user_card_ids = select(UserCard.id).filter(
            UserCard.user_id == user_id
        )
        
        # 然后查询这些card相关的未读ChatSummary
        count = db.query(ChatSummary).filter(
            ChatSummary.card_id.in_(user_card_ids),
            ChatSummary.is_read == False
        ).count()
        
        return {"count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取未读聊天总结数量失败: {str(e)}")


@router.get("/summaries", response_model=List[ChatSummaryResponse])
async def get_chat_summaries(
    user_id: Optional[str] = Query(None, description="用户ID，用于筛选用户相关的聊天总结"),
    card_id: Optional[str] = Query(None, description="卡片ID，用于筛选卡片相关的聊天总结"),
    session_id: Optional[str] = Query(None, description="会话ID，用于筛选会话相关的聊天总结"),
    summary_type: Optional[str] = Query(None, description="总结类型，用于筛选特定类型的总结"),
    is_read: Optional[bool] = Query(None, description="是否已读，用于筛选已读/未读状态"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取聊天总结列表
    
    支持多条件筛选和分页查询聊天总结
    """
    try:
        query = db.query(ChatSummary)
        
        # 应用筛选条件
        if user_id:
            # 首先查询当前用户拥有的所有card_id
            from sqlalchemy import select
            user_card_ids = select(UserCard.id).filter(
                UserCard.user_id == user_id
            )
            # 然后查询这些card相关的ChatSummary
            query = query.filter(ChatSummary.card_id.in_(user_card_ids))
        if card_id:
            query = query.filter(ChatSummary.card_id == card_id)
        if session_id:
            query = query.filter(ChatSummary.session_id == session_id)
        if summary_type:
            query = query.filter(ChatSummary.summary_type == summary_type)
        if is_read is not None:
            query = query.filter(ChatSummary.is_read == is_read)
        
        # 按创建时间倒序排序
        query = query.order_by(ChatSummary.created_at.desc())
        
        # 应用分页
        offset = (page - 1) * limit
        summaries = query.offset(offset).limit(limit).all()
        
        return [summary.to_dict() for summary in summaries]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取聊天总结列表失败: {str(e)}")


@router.get("/summaries/{summary_id}", response_model=ChatSummaryResponse)
async def get_chat_summary(
    summary_id: str,
    db: Session = Depends(get_db)
):
    """获取聊天总结详情
    
    根据总结ID获取聊天总结的详细信息
    """
    try:
        summary = db.query(ChatSummary).filter(ChatSummary.id == summary_id).first()
        
        if not summary:
            raise HTTPException(status_code=404, detail="聊天总结不存在")
        
        return summary.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取聊天总结失败: {str(e)}")


@router.put("/summaries/{summary_id}/read", response_model=ChatSummaryResponse)
async def mark_chat_summary_as_read(
    summary_id: str,
    db: Session = Depends(get_db)
):
    """标记聊天总结为已读
    
    更新聊天总结的已读状态
    """
    try:
        summary = db.query(ChatSummary).filter(ChatSummary.id == summary_id).first()
        
        if not summary:
            raise HTTPException(status_code=404, detail="聊天总结不存在")
        
        # 只有在未读状态下才更新
        if not summary.is_read:
            summary.is_read = True
            summary.read_at = datetime.now()
            db.commit()
            db.refresh(summary)
        
        return summary.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"标记聊天总结已读失败: {str(e)}")


@router.delete("/summaries/{summary_id}")
async def delete_chat_summary(
    summary_id: str,
    db: Session = Depends(get_db)
):
    """删除聊天总结
    
    根据总结ID删除聊天总结记录
    """
    try:
        summary = db.query(ChatSummary).filter(ChatSummary.id == summary_id).first()
        
        if not summary:
            raise HTTPException(status_code=404, detail="聊天总结不存在")
        
        db.delete(summary)
        db.commit()
        
        return {"message": "聊天总结删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除聊天总结失败: {str(e)}")