"""
简单聊天流式接口测试 - 测试 /llm/simple-chat/stream 端点
"""
import unittest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, Generator
import json
import asyncio

from app.database import get_db
from app.services.auth import auth_service
from app.models.llm_schemas import SimpleChatStreamRequest


def override_get_db() -> Generator[Session, None, None]:
    """覆盖数据库依赖"""
    db = Mock(spec=Session)
    db.query.return_value.filter.return_value.first.return_value = None
    yield db


def override_get_current_user_logged_in() -> dict:
    """覆盖当前用户为登录用户"""
    return {
        "id": "test_user_123",
        "nick_name": "测试用户",
        "avatar_url": "http://example.com/avatar.jpg"
    }


def override_get_current_user_optional() -> Optional[dict]:
    """覆盖当前用户为匿名用户"""
    return None


class TestSimpleChatStreamMocked(unittest.TestCase):
    """测试简单聊天流式接口 - 直接测试路由函数"""

    def test_simple_chat_stream_with_anonymous_user(self):
        """测试匿名用户访问简单聊天流式接口"""
        from app.routers.llm import generate_simple_chat_stream
        from fastapi.responses import StreamingResponse
        
        request = SimpleChatStreamRequest(
            chatId="test_chat_001",
            message="你好",
            context={},
            cardId="test_card_001"
        )
        
        db_mock = Mock(spec=Session)
        
        async def mock_stream():
            """模拟流式响应生成器"""
            yield {"type": "text", "content": "你好！", "finished": False}
            yield {"type": "text", "content": "有什么我可以帮助你的吗？", "finished": True}
            yield {"type": "end"}
        
        with patch('app.routers.llm.LLMService') as mock_service_class, \
             patch('app.routers.llm.auth_service') as mock_auth_service:
            
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            mock_anonymous_user = {"id": "anonymous_user_123"}
            mock_auth_service.get_anonymous_user.return_value = mock_anonymous_user
            
            mock_service.generate_simple_chat_stream.return_value = mock_stream()
            
            response = asyncio.run(generate_simple_chat_stream(
                request=request,
                db=db_mock,
                current_user=None
            ))
            
            self.assertIsNotNone(response)
            self.assertIsInstance(response, StreamingResponse)
            
            mock_service.generate_simple_chat_stream.assert_called_once()
            call_kwargs = mock_service.generate_simple_chat_stream.call_args[1]
            self.assertEqual(call_kwargs["user_id"], "anonymous_user_123")
            self.assertEqual(call_kwargs["message"], "你好")
            self.assertEqual(call_kwargs["card_id"], "test_card_001")

    def test_simple_chat_stream_with_logged_in_user(self):
        """测试登录用户访问简单聊天流式接口"""
        from app.routers.llm import generate_simple_chat_stream
        from fastapi.responses import StreamingResponse
        
        request = SimpleChatStreamRequest(
            chatId="test_chat_002",
            message="今天天气怎么样？",
            context={"chatHistory": []},
            cardId="test_card_002",
            userId="test_user_123"
        )
        
        db_mock = Mock(spec=Session)
        current_user = {
            "id": "test_user_123",
            "nick_name": "测试用户"
        }
        
        async def mock_stream():
            yield {"type": "text", "content": "今天天气晴朗，", "finished": False}
            yield {"type": "text", "content": "适合外出活动。", "finished": True}
            yield {"type": "end"}
        
        with patch('app.routers.llm.LLMService') as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            mock_service.generate_simple_chat_stream.return_value = mock_stream()
            
            response = asyncio.run(generate_simple_chat_stream(
                request=request,
                db=db_mock,
                current_user=current_user
            ))
            
            self.assertIsNotNone(response)
            self.assertIsInstance(response, StreamingResponse)
            
            mock_service.generate_simple_chat_stream.assert_called_once()
            call_kwargs = mock_service.generate_simple_chat_stream.call_args[1]
            self.assertEqual(call_kwargs["user_id"], "test_user_123")

    def test_simple_chat_stream_with_personality(self):
        """测试带性格描述的流式聊天"""
        from app.routers.llm import generate_simple_chat_stream
        from fastapi.responses import StreamingResponse
        
        request = SimpleChatStreamRequest(
            chatId="test_chat_004",
            message="给我讲个笑话",
            context={},
            cardId="test_card_003",
            personality="外向、幽默、善于表达"
        )
        
        db_mock = Mock(spec=Session)
        
        async def mock_stream():
            yield {"type": "text", "content": "哈哈！", "finished": False}
            yield {"type": "text", "content": "给你讲个笑话：从", "finished": False}
            yield {"type": "text", "content": "前有只企鹅...", "finished": True}
            yield {"type": "end"}
        
        with patch('app.routers.llm.LLMService') as mock_service_class, \
             patch('app.routers.llm.auth_service') as mock_auth_service:
            
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            mock_anonymous_user = {"id": "anonymous_user_456"}
            mock_auth_service.get_anonymous_user.return_value = mock_anonymous_user
            
            mock_service.generate_simple_chat_stream.return_value = mock_stream()
            
            response = asyncio.run(generate_simple_chat_stream(
                request=request,
                db=db_mock,
                current_user=None
            ))
            
            self.assertIsNotNone(response)
            self.assertIsInstance(response, StreamingResponse)
            
            mock_service.generate_simple_chat_stream.assert_called_once()
            call_kwargs = mock_service.generate_simple_chat_stream.call_args[1]
            self.assertEqual(call_kwargs["personality"], "外向、幽默、善于表达")

    def test_simple_chat_stream_empty_message_validation(self):
        """测试空消息参数验证 - 消息字段允许为空字符串"""
        from pydantic import ValidationError
        
        request = SimpleChatStreamRequest(
            chatId="test_chat_005",
            message="",
            context={}
        )
        
        self.assertEqual(request.message, "")

    def test_simple_chat_stream_missing_chat_id_validation(self):
        """测试缺少必要参数验证"""
        from pydantic import ValidationError
        
        try:
            request = SimpleChatStreamRequest(
                message="测试消息"
            )
            self.fail("应该抛出 ValidationError")
        except ValidationError as e:
            self.assertGreater(len(e.errors()), 0)

    def test_simple_chat_stream_with_context(self):
        """测试带上下文的流式响应"""
        from app.routers.llm import generate_simple_chat_stream
        from fastapi.responses import StreamingResponse
        
        context_data = {
            "chatHistory": [
                {"role": "user", "content": "你好"},
                {"role": "assistant", "content": "你好！有什么可以帮你的？"}
            ]
        }
        
        request = SimpleChatStreamRequest(
            chatId="test_chat_008",
            message="再见",
            context=context_data
        )
        
        db_mock = Mock(spec=Session)
        
        async def mock_stream():
            yield {"type": "text", "content": "再见！", "finished": True}
            yield {"type": "end"}
        
        with patch('app.routers.llm.LLMService') as mock_service_class, \
             patch('app.routers.llm.auth_service') as mock_auth_service:
            
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            mock_anonymous_user = {"id": "anonymous_user_789"}
            mock_auth_service.get_anonymous_user.return_value = mock_anonymous_user
            
            mock_service.generate_simple_chat_stream.return_value = mock_stream()
            
            response = asyncio.run(generate_simple_chat_stream(
                request=request,
                db=db_mock,
                current_user=None
            ))
            
            self.assertIsNotNone(response)
            self.assertIsInstance(response, StreamingResponse)
            
            mock_service.generate_simple_chat_stream.assert_called_once()
            call_kwargs = mock_service.generate_simple_chat_stream.call_args[1]
            self.assertEqual(call_kwargs["context"], context_data)

    def test_simple_chat_stream_service_error_handling(self):
        """测试服务错误处理"""
        from app.routers.llm import generate_simple_chat_stream
        from fastapi.responses import StreamingResponse
        
        request = SimpleChatStreamRequest(
            chatId="test_chat_009",
            message="测试错误",
            context={}
        )
        
        db_mock = Mock(spec=Session)
        
        async def mock_stream():
            raise Exception("模拟服务错误")
        
        with patch('app.routers.llm.LLMService') as mock_service_class, \
             patch('app.routers.llm.auth_service') as mock_auth_service:
            
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            
            mock_anonymous_user = {"id": "anonymous_user_error"}
            mock_auth_service.get_anonymous_user.return_value = mock_anonymous_user
            
            mock_service.generate_simple_chat_stream.return_value = mock_stream()
            
            response = asyncio.run(generate_simple_chat_stream(
                request=request,
                db=db_mock,
                current_user=None
            ))
            
            self.assertIsNotNone(response)
            self.assertIsInstance(response, StreamingResponse)


class TestSimpleChatStreamRequestModel(unittest.TestCase):
    """测试 SimpleChatStreamRequest 模型"""

    def test_valid_request_with_all_fields(self):
        """测试完整的请求模型"""
        request = SimpleChatStreamRequest(
            userId="user_123",
            cardId="card_456",
            chatId="chat_789",
            message="你好",
            context={"key": "value"},
            personality="性格描述"
        )
        
        self.assertEqual(request.userId, "user_123")
        self.assertEqual(request.cardId, "card_456")
        self.assertEqual(request.chatId, "chat_789")
        self.assertEqual(request.message, "你好")
        self.assertEqual(request.context, {"key": "value"})
        self.assertEqual(request.personality, "性格描述")

    def test_valid_request_minimal_fields(self):
        """测试最小字段的请求模型"""
        request = SimpleChatStreamRequest(
            chatId="chat_001",
            message="测试消息"
        )
        
        self.assertIsNone(request.userId)
        self.assertIsNone(request.cardId)
        self.assertEqual(request.chatId, "chat_001")
        self.assertEqual(request.message, "测试消息")
        self.assertEqual(request.context, {})
        self.assertIsNone(request.personality)

    def test_request_default_context(self):
        """测试默认上下文"""
        request = SimpleChatStreamRequest(
            chatId="chat_001",
            message="测试"
        )
        
        self.assertEqual(request.context, {})

    def test_request_with_chat_history(self):
        """测试带聊天历史的请求"""
        chat_history = [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "你好！"}
        ]
        
        request = SimpleChatStreamRequest(
            chatId="chat_002",
            message="再见",
            context={"chatHistory": chat_history}
        )
        
        self.assertEqual(request.context["chatHistory"], chat_history)


class TestSimpleChatStreamResponse(unittest.TestCase):
    """测试流式响应 SSE 格式"""

    def test_sse_data_format(self):
        """测试 SSE 数据格式"""
        import json
        
        data = {
            "type": "text",
            "content": "你好！",
            "finished": False
        }
        
        sse_line = f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
        
        self.assertTrue(sse_line.startswith("data: "))
        self.assertTrue(sse_line.endswith("\n\n"))
        
        parsed_data = json.loads(sse_line.replace("data: ", "").replace("\n\n", ""))
        self.assertEqual(parsed_data["type"], "text")
        self.assertEqual(parsed_data["content"], "你好！")
        self.assertEqual(parsed_data["finished"], False)

    def test_sse_end_format(self):
        """测试 SSE 结束标记格式"""
        import json
        
        end_data = {"type": "end"}
        sse_line = f"data: {json.dumps(end_data, ensure_ascii=False)}\n\n"
        
        parsed_data = json.loads(sse_line.replace("data: ", "").replace("\n\n", ""))
        self.assertEqual(parsed_data["type"], "end")

    def test_sse_error_format(self):
        """测试 SSE 错误格式"""
        import json
        
        error_data = {
            "type": "error",
            "message": "服务错误"
        }
        sse_line = f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
        
        parsed_data = json.loads(sse_line.replace("data: ", "").replace("\n\n", ""))
        self.assertEqual(parsed_data["type"], "error")
        self.assertEqual(parsed_data["message"], "服务错误")

    def test_sse_multiple_chunks_format(self):
        """测试多块 SSE 格式"""
        import json
        
        chunks = [
            {"type": "text", "content": "今天", "finished": False},
            {"type": "text", "content": "天气", "finished": False},
            {"type": "text", "content": "很好！", "finished": True},
            {"type": "end"}
        ]
        
        sse_output = ""
        for chunk in chunks:
            sse_output += f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        
        lines = sse_output.split('\n')
        data_lines = [line for line in lines if line.startswith('data: ')]
        
        self.assertEqual(len(data_lines), 4)
        
        for i, data_line in enumerate(data_lines):
            parsed = json.loads(data_line.replace('data: ', ''))
            self.assertEqual(parsed, chunks[i])


if __name__ == "__main__":
    unittest.main()
