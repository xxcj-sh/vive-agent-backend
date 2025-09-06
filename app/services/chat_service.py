from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from app.models.chat_message import ChatMessage, ChatConversation, MessageType, MessageStatus
from app.models.match import Match
from app.models.user import User
from app.models.schemas import (
    ChatMessage as ChatMessageSchema,
    SendMessageRequest,
    ChatHistoryResponse,
    ConversationListResponse,
    ConversationListItem,
    UnreadCountResponse
)

class ChatService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_chat_history(
        self, 
        match_id: str, 
        user_id: str, 
        page: int = 1, 
        limit: int = 20
    ) -> ChatHistoryResponse:
        """获取聊天记录"""
        # 验证用户是否有权限访问此聊天
        match = self.db.query(Match).filter(
            Match.id == match_id,
            or_(
                Match.user_id == user_id,
                Match.id.in_(
                    self.db.query(Match.id).filter(
                        Match.user_id != user_id
                    )
                )
            )
        ).first()
        
        if not match:
            raise ValueError("无权访问此聊天记录")
        
        # 计算分页
        offset = (page - 1) * limit
        
        # 查询消息
        messages = self.db.query(ChatMessage).filter(
            ChatMessage.match_id == match_id,
            ChatMessage.is_deleted == False
        ).order_by(desc(ChatMessage.created_at)).offset(offset).limit(limit).all()
        
        # 获取总数
        total = self.db.query(ChatMessage).filter(
            ChatMessage.match_id == match_id,
            ChatMessage.is_deleted == False
        ).count()
        
        # 转换为响应格式
        message_list = []
        for msg in reversed(messages):  # 反转顺序，按时间升序
            sender = self.db.query(User).filter(User.id == msg.sender_id).first()
            receiver = self.db.query(User).filter(User.id == msg.receiver_id).first()
            
            message_list.append(ChatMessageSchema(
                id=msg.id,
                content=msg.content,
                type=msg.message_type.value,
                sender_id=msg.sender_id,
                sender_avatar=sender.avatar_url if sender else "",
                sender_name=sender.nick_name if sender else "Unknown",
                receiver_id=msg.receiver_id,
                timestamp=int(msg.created_at.timestamp() * 1000),
                is_read=msg.is_read,
                read_at=int(msg.read_at.timestamp() * 1000) if msg.read_at else None,
                status=msg.status.value,
                media_url=msg.media_url,
                media_size=msg.media_size,
                media_duration=msg.media_duration,
                reply_to_id=msg.reply_to_id,
                system_type=msg.system_type,
                system_data={} if msg.system_data else None
            ))
        
        return ChatHistoryResponse(
            pagination={
                "page": page,
                "page_size": limit,
                "total": total
            },
            list=message_list
        )
    
    def send_message(
        self, 
        request: SendMessageRequest, 
        sender_id: str
    ) -> Dict[str, Any]:
        """发送消息"""
        # 验证匹配是否存在且用户有权限
        match = self.db.query(Match).filter(Match.id == request.match_id).first()
        if not match:
            raise ValueError("匹配不存在")
        
        # 获取匹配中的两个用户
        users = self._get_match_users(match.id)
        if sender_id not in users:
            raise ValueError("无权在此匹配中发送消息")
        
        receiver_id = users[0] if users[1] == sender_id else users[1]
        
        # 创建消息
        message = ChatMessage(
            id=str(uuid.uuid4()),
            match_id=request.match_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=request.content,
            message_type=request.type,
            media_url=request.media_url,
            media_size=request.media_size,
            media_duration=request.media_duration,
            reply_to_id=request.reply_to_id
        )
        
        self.db.add(message)
        self.db.flush()
        
        # 更新会话信息
        self._update_conversation(request.match_id, message)
        
        # 增加未读计数
        self._increment_unread_count(request.match_id, receiver_id)
        
        self.db.commit()
        
        return {
            "id": message.id,
            "timestamp": int(message.created_at.timestamp() * 1000),
            "status": message.status.value
        }
    
    def mark_messages_as_read(
        self, 
        match_id: str, 
        message_ids: List[str], 
        user_id: str
    ) -> bool:
        """标记消息为已读"""
        # 验证权限
        match = self.db.query(Match).filter(Match.id == match_id).first()
        if not match:
            raise ValueError("匹配不存在")
        
        users = self._get_match_users(match_id)
        if user_id not in users:
            raise ValueError("无权操作此聊天")
        
        # 更新消息状态
        updated_count = self.db.query(ChatMessage).filter(
            ChatMessage.id.in_(message_ids),
            ChatMessage.receiver_id == user_id,
            ChatMessage.is_read == False
        ).update({
            ChatMessage.is_read: True,
            ChatMessage.read_at: datetime.utcnow(),
            ChatMessage.status: MessageStatus.READ
        }, synchronize_session=False)
        
        if updated_count > 0:
            # 更新未读计数
            self._reset_unread_count(match_id, user_id)
            self.db.commit()
        
        return updated_count > 0
    
    def get_conversation_list(
        self, 
        user_id: str, 
        page: int = 1, 
        limit: int = 20
    ) -> ConversationListResponse:
        """获取会话列表"""
        offset = (page - 1) * limit
        
        # 查询用户的所有会话
        conversations = self.db.query(ChatConversation).filter(
            or_(
                ChatConversation.user1_id == user_id,
                ChatConversation.user2_id == user_id
            ),
            ChatConversation.is_active == True
        ).order_by(desc(ChatConversation.updated_at)).offset(offset).limit(limit).all()
        
        # 获取总数
        total = self.db.query(ChatConversation).filter(
            or_(
                ChatConversation.user1_id == user_id,
                ChatConversation.user2_id == user_id
            ),
            ChatConversation.is_active == True
        ).count()
        
        conversation_list = []
        for conv in conversations:
            # 确定对方用户信息
            other_user_id = conv.user2_id if conv.user1_id == user_id else conv.user1_id
            other_user = self.db.query(User).filter(User.id == other_user_id).first()
            
            # 获取未读计数
            unread_count = conv.user1_unread_count if conv.user2_id == user_id else conv.user2_unread_count
            
            # 获取最后一条消息
            last_message = None
            if conv.last_message_id:
                last_msg = self.db.query(ChatMessage).filter(ChatMessage.id == conv.last_message_id).first()
                if last_msg:
                    sender = self.db.query(User).filter(User.id == last_msg.sender_id).first()
                    last_message = ChatMessageSchema(
                        id=last_msg.id,
                        content=last_msg.content,
                        type=last_msg.message_type.value,
                        sender_id=last_msg.sender_id,
                        sender_avatar=sender.avatar_url if sender else "",
                        sender_name=sender.nick_name if sender else "Unknown",
                        receiver_id=last_msg.receiver_id,
                        timestamp=int(last_msg.created_at.timestamp() * 1000),
                        is_read=last_msg.is_read,
                        status=last_msg.status.value
                    )
            
            conversation_list.append(ConversationListItem(
                match_id=conv.match_id,
                user_id=other_user_id,
                user_name=other_user.nick_name if other_user else "Unknown",
                user_avatar=other_user.avatar_url if other_user else "",
                last_message=last_message,
                unread_count=unread_count,
                updated_at=int(conv.updated_at.timestamp() * 1000) if conv.updated_at else 0,
                is_active=conv.is_active
            ))
        
        return ConversationListResponse(
            pagination={
                "page": page,
                "page_size": limit,
                "total": total
            },
            list=conversation_list
        )
    
    def get_unread_count(self, match_id: str, user_id: str) -> UnreadCountResponse:
        """获取未读消息数量"""
        # 验证权限
        match = self.db.query(Match).filter(Match.id == match_id).first()
        if not match:
            raise ValueError("匹配不存在")
        
        users = self._get_match_users(match_id)
        if user_id not in users:
            raise ValueError("无权访问此聊天")
        
        # 查询未读消息数量
        unread_count = self.db.query(ChatMessage).filter(
            ChatMessage.match_id == match_id,
            ChatMessage.receiver_id == user_id,
            ChatMessage.is_read == False,
            ChatMessage.is_deleted == False
        ).count()
        
        # 获取最后一条消息
        last_message = self.db.query(ChatMessage).filter(
            ChatMessage.match_id == match_id,
            ChatMessage.is_deleted == False
        ).order_by(desc(ChatMessage.created_at)).first()
        
        last_message_schema = None
        if last_message:
            sender = self.db.query(User).filter(User.id == last_message.sender_id).first()
            last_message_schema = ChatMessageSchema(
                id=last_message.id,
                content=last_message.content,
                type=last_message.message_type.value,
                sender_id=last_message.sender_id,
                sender_avatar=sender.avatar_url if sender else "",
                sender_name=sender.nick_name if sender else "Unknown",
                receiver_id=last_message.receiver_id,
                timestamp=int(last_message.created_at.timestamp() * 1000),
                is_read=last_message.is_read,
                status=last_message.status.value
            )
        
        return UnreadCountResponse(
            unread_count=unread_count,
            last_message=last_message_schema
        )
    
    def delete_messages(
        self, 
        message_ids: List[str], 
        user_id: str,
        delete_type: str = "soft"
    ) -> int:
        """删除消息"""
        if delete_type == "soft":
            # 软删除
            updated_count = self.db.query(ChatMessage).filter(
                ChatMessage.id.in_(message_ids),
                ChatMessage.sender_id == user_id,
                ChatMessage.is_deleted == False
            ).update({
                ChatMessage.is_deleted: True,
                ChatMessage.deleted_at: datetime.utcnow(),
                ChatMessage.deleted_by: user_id
            }, synchronize_session=False)
        else:
            # 硬删除
            updated_count = self.db.query(ChatMessage).filter(
                ChatMessage.id.in_(message_ids),
                ChatMessage.sender_id == user_id
            ).delete(synchronize_session=False)
        
        self.db.commit()
        return updated_count
    
    def _get_match_users(self, match_id: str) -> List[str]:
        """获取匹配中的用户ID列表"""
        # 这里需要根据实际的匹配逻辑获取两个用户的ID
        # 简化实现，假设Match表中存储了相关关系
        match = self.db.query(Match).filter(Match.id == match_id).first()
        if not match:
            return []
        
        # 实际应用中，这里应该从匹配详情中获取两个用户的ID
        # 这里简化处理，假设match.user_id是其中一个用户
        # 需要根据实际业务逻辑完善
        return [match.user_id, "other_user_id"]  # 需要根据实际情况调整
    
    def _update_conversation(self, match_id: str, message: ChatMessage):
        """更新会话信息"""
        conversation = self.db.query(ChatConversation).filter(
            ChatConversation.match_id == match_id
        ).first()
        
        if not conversation:
            # 创建新的会话
            users = self._get_match_users(match_id)
            if len(users) >= 2:
                conversation = ChatConversation(
                    id=str(uuid.uuid4()),
                    match_id=match_id,
                    user1_id=users[0],
                    user2_id=users[1]
                )
                self.db.add(conversation)
        
        if conversation:
            conversation.last_message_id = message.id
            conversation.last_message_content = message.content
            conversation.last_message_time = message.created_at
    
    def _increment_unread_count(self, match_id: str, receiver_id: str):
        """增加未读计数"""
        conversation = self.db.query(ChatConversation).filter(
            ChatConversation.match_id == match_id
        ).first()
        
        if conversation:
            if conversation.user1_id == receiver_id:
                conversation.user1_unread_count += 1
            else:
                conversation.user2_unread_count += 1
    
    def _reset_unread_count(self, match_id: str, user_id: str):
        """重置未读计数"""
        conversation = self.db.query(ChatConversation).filter(
            ChatConversation.match_id == match_id
        ).first()
        
        if conversation:
            if conversation.user1_id == user_id:
                conversation.user1_unread_count = 0
            else:
                conversation.user2_unread_count = 0