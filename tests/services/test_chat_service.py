import pytest
import uuid
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from sqlalchemy import and_, or_, desc

from app.services.chat_service import ChatService
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

class TestChatService:
    """聊天服务测试类"""
    
    @pytest.fixture
    def chat_service(self, mock_db):
        """创建聊天服务实例"""
        return ChatService(mock_db)
    
    @pytest.fixture
    def sample_match(self):
        """示例匹配数据"""
        match = Mock(spec=Match)
        match.id = str(uuid.uuid4())
        match.user_id = str(uuid.uuid4())
        return match
    
    @pytest.fixture
    def sample_message(self):
        """示例消息数据"""
        message = Mock(spec=ChatMessage)
        message.id = str(uuid.uuid4())
        message.match_id = str(uuid.uuid4())
        message.sender_id = str(uuid.uuid4())
        message.receiver_id = str(uuid.uuid4())
        message.content = "你好！"
        message.message_type = MessageType.TEXT
        message.is_read = False
        message.created_at = datetime.now()
        message.read_at = None
        message.status = MessageStatus.SENT
        message.media_url = None
        message.media_size = None
        message.media_duration = None
        message.reply_to_id = None
        message.system_type = None
        message.system_data = None
        return message
    
    @pytest.fixture
    def sample_user(self):
        """示例用户数据"""
        user = Mock(spec=User)
        user.id = str(uuid.uuid4())
        user.nick_name = "测试用户"
        user.avatar_url = "https://example.com/avatar.jpg"
        return user
    
    def test_get_chat_history_no_permission(self, chat_service, sample_match):
        """测试获取聊天记录无权限"""
        match_id = sample_match.id
        user_id = str(uuid.uuid4())
        
        # 设置无权限的情况
        chat_service.db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="无权访问此聊天记录"):
            chat_service.get_chat_history(match_id, user_id)
    
    def test_get_chat_history_success(self, chat_service, sample_match, sample_message, sample_user):
        """测试获取聊天记录成功"""
        match_id = sample_match.id
        user_id = sample_match.user_id
        
        # 设置有权限的情况
        chat_service.db.query.return_value.filter.return_value.first.return_value = sample_match
        
        # 设置消息查询
        mock_message_query = Mock()
        mock_message_query.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [sample_message]
        mock_message_query.filter.return_value.count.return_value = 1
        chat_service.db.query.side_effect = [
            Mock(filter=Mock(return_value=Mock(first=Mock(return_value=sample_match)))),  # 第一次查询匹配
            mock_message_query,  # 第二次查询消息
            mock_message_query   # 第三次查询总数
        ]
        
        # 设置用户查询
        chat_service.db.query.return_value.filter.return_value.first.side_effect = [sample_user, sample_user]
        
        result = chat_service.get_chat_history(match_id, user_id)
        
        assert isinstance(result, ChatHistoryResponse)
        assert result.pagination["total"] == 1
        assert len(result.list) == 1
        assert result.list[0].content == sample_message.content
    
    def test_send_message_match_not_found(self, chat_service):
        """测试发送消息匹配不存在"""
        request = SendMessageRequest(
            match_id=str(uuid.uuid4()),
            content="测试消息",
            type="text"
        )
        sender_id = str(uuid.uuid4())
        
        chat_service.db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="匹配不存在"):
            chat_service.send_message(request, sender_id)
    
    def test_send_message_no_permission(self, chat_service, sample_match):
        """测试发送消息无权限"""
        request = SendMessageRequest(
            match_id=sample_match.id,
            content="测试消息",
            type="text"
        )
        sender_id = str(uuid.uuid4())
        
        chat_service.db.query.return_value.filter.return_value.first.return_value = sample_match
        
        # 模拟用户不在匹配中
        with patch.object(chat_service, '_get_match_users', return_value=[str(uuid.uuid4()), str(uuid.uuid4())]):
            with pytest.raises(ValueError, match="无权在此匹配中发送消息"):
                chat_service.send_message(request, sender_id)
    
    def test_send_message_success(self, chat_service, sample_match, sample_user):
        """测试发送消息成功"""
        request = SendMessageRequest(
            match_id=sample_match.id,
            content="测试消息",
            type="text"
        )
        sender_id = str(uuid.uuid4())
        receiver_id = str(uuid.uuid4())
        
        chat_service.db.query.return_value.filter.return_value.first.return_value = sample_match
        
        # 模拟用户在匹配中
        with patch.object(chat_service, '_get_match_users', return_value=[sender_id, receiver_id]):
            with patch.object(chat_service, '_update_conversation'):
                with patch.object(chat_service, '_increment_unread_count'):
                    with patch('app.services.chat_service.uuid.uuid4', return_value="test-message-id"):
                        with patch('app.services.chat_service.ChatMessage') as mock_message_class:
                            mock_message = Mock(spec=ChatMessage)
                            mock_message.id = "test-message-id"
                            mock_message.created_at = datetime.now()
                            mock_message.status = MessageStatus.SENT
                            mock_message_class.return_value = mock_message
                            
                            result = chat_service.send_message(request, sender_id)
                            
                            assert result["id"] == "test-message-id"
                            assert result["status"] == "sent"
                            assert "timestamp" in result
                            
                            chat_service.db.add.assert_called_once()
                            chat_service.db.flush.assert_called_once()
                            chat_service.db.commit.assert_called_once()
    
    def test_mark_messages_as_read_match_not_found(self, chat_service):
        """测试标记消息已读匹配不存在"""
        match_id = str(uuid.uuid4())
        message_ids = [str(uuid.uuid4())]
        user_id = str(uuid.uuid4())
        
        chat_service.db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="匹配不存在"):
            chat_service.mark_messages_as_read(match_id, message_ids, user_id)
    
    def test_mark_messages_as_read_no_permission(self, chat_service, sample_match):
        """测试标记消息已读无权限"""
        match_id = sample_match.id
        message_ids = [str(uuid.uuid4())]
        user_id = str(uuid.uuid4())
        
        chat_service.db.query.return_value.filter.return_value.first.return_value = sample_match
        
        # 模拟用户不在匹配中
        with patch.object(chat_service, '_get_match_users', return_value=[str(uuid.uuid4()), str(uuid.uuid4())]):
            with pytest.raises(ValueError, match="无权操作此聊天"):
                chat_service.mark_messages_as_read(match_id, message_ids, user_id)
    
    def test_mark_messages_as_read_success(self, chat_service, sample_match):
        """测试标记消息已读成功"""
        match_id = sample_match.id
        message_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        user_id = str(uuid.uuid4())
        
        chat_service.db.query.return_value.filter.return_value.first.return_value = sample_match
        
        # 模拟用户在匹配中
        with patch.object(chat_service, '_get_match_users', return_value=[user_id, str(uuid.uuid4())]):
            # 模拟更新操作
            mock_update_result = Mock()
            mock_update_result.update.return_value = 2  # 更新了2条消息
            chat_service.db.query.return_value.filter.return_value = mock_update_result
            
            with patch.object(chat_service, '_reset_unread_count'):
                result = chat_service.mark_messages_as_read(match_id, message_ids, user_id)
                
                assert result is True
                mock_update_result.update.assert_called_once()
                chat_service.db.commit.assert_called_once()
    
    def test_mark_messages_as_read_no_updates(self, chat_service, sample_match):
        """测试标记消息已读无更新"""
        match_id = sample_match.id
        message_ids = [str(uuid.uuid4())]
        user_id = str(uuid.uuid4())
        
        chat_service.db.query.return_value.filter.return_value.first.return_value = sample_match
        
        # 模拟用户在匹配中
        with patch.object(chat_service, '_get_match_users', return_value=[user_id, str(uuid.uuid4())]):
            # 模拟更新操作无影响
            mock_update_result = Mock()
            mock_update_result.update.return_value = 0  # 没有更新任何消息
            chat_service.db.query.return_value.filter.return_value = mock_update_result
            
            result = chat_service.mark_messages_as_read(match_id, message_ids, user_id)
            
            assert result is False
            mock_update_result.update.assert_called_once()
            chat_service.db.commit.assert_not_called()  # 没有更新则不提交
    
    def test_get_conversation_list_success(self, chat_service, sample_user):
        """测试获取会话列表成功"""
        user_id = sample_user.id
        
        mock_conversations = [Mock(spec=ChatConversation), Mock(spec=ChatConversation)]
        
        # 设置查询链
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_conversations
        mock_query.filter.return_value.count.return_value = 2
        
        chat_service.db.query.side_effect = [
            mock_query,  # 第一次查询会话列表
            mock_query   # 第二次查询总数
        ]
        
        result = chat_service.get_conversation_list(user_id)
        
        assert isinstance(result, ConversationListResponse)
        assert result.pagination["total"] == 2
        assert len(result.list) == 2
    
    def test_get_conversation_list_empty(self, chat_service):
        """测试获取会话列表为空"""
        user_id = str(uuid.uuid4())
        
        # 设置空结果
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_query.filter.return_value.count.return_value = 0
        
        chat_service.db.query.side_effect = [
            mock_query,  # 第一次查询会话列表
            mock_query   # 第二次查询总数
        ]
        
        result = chat_service.get_conversation_list(user_id)
        
        assert isinstance(result, ConversationListResponse)
        assert result.pagination["total"] == 0
        assert len(result.list) == 0
    
    def test_get_unread_count_success(self, chat_service):
        """测试获取未读消息数成功"""
        user_id = str(uuid.uuid4())
        
        # 设置模拟查询
        mock_query = Mock()
        mock_query.filter.return_value.count.return_value = 5
        chat_service.db.query.return_value = mock_query
        
        result = chat_service.get_unread_count(user_id)
        
        assert isinstance(result, UnreadCountResponse)
        assert result.unread_count == 5
    
    def test_get_unread_count_zero(self, chat_service):
        """测试获取未读消息数为零"""
        user_id = str(uuid.uuid4())
        
        # 设置模拟查询
        mock_query = Mock()
        mock_query.filter.return_value.count.return_value = 0
        chat_service.db.query.return_value = mock_query
        
        result = chat_service.get_unread_count(user_id)
        
        assert isinstance(result, UnreadCountResponse)
        assert result.unread_count == 0
    
    def test_delete_message_success(self, chat_service, sample_message):
        """测试删除消息成功"""
        message_id = sample_message.id
        user_id = sample_message.sender_id
        
        # 设置消息查询
        chat_service.db.query.return_value.filter.return_value.first.return_value = sample_message
        
        result = chat_service.delete_message(message_id, user_id)
        
        assert result is True
        assert sample_message.is_deleted is True
        chat_service.db.commit.assert_called_once()
    
    def test_delete_message_not_found(self, chat_service):
        """测试删除消息不存在"""
        message_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # 设置消息不存在
        chat_service.db.query.return_value.filter.return_value.first.return_value = None
        
        result = chat_service.delete_message(message_id, user_id)
        
        assert result is False
        chat_service.db.commit.assert_not_called()
    
    def test_delete_message_no_permission(self, chat_service, sample_message):
        """测试删除消息无权限"""
        message_id = sample_message.id
        user_id = str(uuid.uuid4())  # 不同的用户ID
        
        # 设置消息存在但用户无权限
        chat_service.db.query.return_value.filter.return_value.first.return_value = sample_message
        
        result = chat_service.delete_message(message_id, user_id)
        
        assert result is False
        chat_service.db.commit.assert_not_called()
    
    def test_get_match_users_success(self, chat_service, sample_match):
        """测试获取匹配用户成功"""
        match_id = sample_match.id
        
        # 设置模拟用户查询
        mock_users = [
            Mock(spec=User, id=str(uuid.uuid4())),
            Mock(spec=User, id=str(uuid.uuid4()))
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = mock_users
        chat_service.db.query.return_value = mock_query
        
        # 调用私有方法
        result = chat_service._get_match_users(match_id)
        
        assert len(result) == 2
        assert all(isinstance(user_id, str) for user_id in result)
    
    def test_update_conversation_success(self, chat_service, sample_message):
        """测试更新会话成功"""
        match_id = sample_message.match_id
        
        # 设置模拟会话
        mock_conversation = Mock(spec=ChatConversation)
        mock_conversation.id = str(uuid.uuid4())
        mock_conversation.match_id = match_id
        
        chat_service.db.query.return_value.filter.return_value.first.return_value = mock_conversation
        
        # 调用私有方法
        chat_service._update_conversation(match_id, sample_message)
        
        # 验证会话被更新
        assert mock_conversation.last_message_id == sample_message.id
        assert mock_conversation.last_message_content == sample_message.content
        assert mock_conversation.last_message_at == sample_message.created_at
        chat_service.db.commit.assert_called_once()
    
    def test_update_conversation_create_new(self, chat_service, sample_message):
        """测试更新会话创建新会话"""
        match_id = sample_message.match_id
        
        # 设置会话不存在
        chat_service.db.query.return_value.filter.return_value.first.return_value = None
        
        with patch('app.services.chat_service.ChatConversation') as mock_conversation_class:
            mock_conversation = Mock(spec=ChatConversation)
            mock_conversation_class.return_value = mock_conversation
            
            # 调用私有方法
            chat_service._update_conversation(match_id, sample_message)
            
            # 验证新会话被创建
            mock_conversation_class.assert_called_once()
            chat_service.db.add.assert_called_once_with(mock_conversation)
            chat_service.db.commit.assert_called_once()
    
    def test_increment_unread_count_success(self, chat_service):
        """测试增加未读计数成功"""
        match_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # 设置模拟会话
        mock_conversation = Mock(spec=ChatConversation)
        mock_conversation.user1_id = user_id
        mock_conversation.user2_unread_count = 0
        
        chat_service.db.query.return_value.filter.return_value.first.return_value = mock_conversation
        
        # 调用私有方法
        chat_service._increment_unread_count(match_id, user_id)
        
        # 验证未读计数增加
        assert mock_conversation.user2_unread_count == 1
        chat_service.db.commit.assert_called_once()
    
    def test_reset_unread_count_success(self, chat_service):
        """测试重置未读计数成功"""
        match_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        
        # 设置模拟会话
        mock_conversation = Mock(spec=ChatConversation)
        mock_conversation.user1_id = user_id
        mock_conversation.user1_unread_count = 5
        
        chat_service.db.query.return_value.filter.return_value.first.return_value = mock_conversation
        
        # 调用私有方法
        chat_service._reset_unread_count(match_id, user_id)
        
        # 验证未读计数重置
        assert mock_conversation.user1_unread_count == 0
        chat_service.db.commit.assert_called_once()