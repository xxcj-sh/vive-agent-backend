import pytest
import uuid
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime

from app.services.llm_service import LLMService
from app.models.enums import LLMProvider, LLMModel
from app.models.llm_request import LLMRequest, LLMResponse


class TestLLMService:
    """LLM服务测试类"""
    
    @pytest.fixture
    def mock_config(self):
        """创建模拟配置"""
        return {
            'volcengine': {
                'api_key': 'test_volc_key',
                'api_secret': 'test_volc_secret',
                'endpoint': 'https://test.volcengine.com'
            },
            'openai': {
                'api_key': 'test_openai_key',
                'base_url': 'https://api.openai.com'
            },
            'default_provider': LLMProvider.VOLCENGINE,
            'default_model': LLMModel.GPT_4
        }
    
    @pytest.fixture
    def mock_volcengine_client(self):
        """创建模拟火山引擎客户端"""
        client = AsyncMock()
        
        # 模拟成功的响应
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="测试回复内容"))]
        mock_response.usage = Mock(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        mock_response.model = "gpt-4"
        
        client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        return client
    
    @pytest.fixture
    def mock_openai_client(self):
        """创建模拟OpenAI客户端"""
        client = AsyncMock()
        
        # 模拟成功的响应
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="OpenAI测试回复"))]
        mock_response.usage = Mock(prompt_tokens=15, completion_tokens=25, total_tokens=40)
        mock_response.model = "gpt-4"
        
        client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        return client
    
    @pytest.fixture
    def sample_llm_request(self):
        """示例LLM请求"""
        return LLMRequest(
            id=uuid.uuid4(),
            user_id=12345,
            session_id="test_session_123",
            provider=LLMProvider.VOLCENGINE,
            model=LLMModel.GPT_4,
            messages=[
                {"role": "user", "content": "你好，请介绍一下自己"}
            ],
            temperature=0.7,
            max_tokens=1000,
            request_time=datetime.now()
        )
    
    @pytest.fixture
    def sample_llm_response(self):
        """示例LLM响应"""
        return LLMResponse(
            id=uuid.uuid4(),
            request_id=uuid.uuid4(),
            response_content="你好！我是一个AI助手，很高兴为你服务。",
            usage_tokens=50,
            prompt_tokens=20,
            completion_tokens=30,
            response_time=datetime.now()
        )
    
    def test_init_with_config(self, mock_config, mock_volcengine_client, mock_openai_client):
        """测试使用配置初始化服务"""
        with patch('app.services.llm_service.AsyncOpenAI', return_value=mock_openai_client):
            service = LLMService(mock_config)
            
            # 验证配置设置
            assert service.config == mock_config
            assert service.default_provider == LLMProvider.VOLCENGINE
            assert service.default_model == LLMModel.GPT_4
    
    def test_init_without_config(self):
        """测试无配置初始化服务"""
        service = LLMService()
        
        # 验证默认配置
        assert service.config is not None
        assert 'default_provider' in service.config
        assert 'default_model' in service.config
    
    def test_init_clients_volcengine(self, mock_config, mock_volcengine_client):
        """测试初始化火山引擎客户端"""
        with patch('app.services.llm_service.AsyncOpenAI', return_value=mock_volcengine_client):
            service = LLMService(mock_config)
            
            # 验证客户端初始化
            assert hasattr(service, 'clients')
            assert LLMProvider.VOLCENGINE in service.clients
    
    def test_init_clients_openai(self, mock_config, mock_openai_client):
        """测试初始化OpenAI客户端"""
        with patch('app.services.llm_service.AsyncOpenAI', return_value=mock_openai_client):
            service = LLMService(mock_config)
            
            # 验证客户端初始化
            assert hasattr(service, 'clients')
            assert LLMProvider.OPENAI in service.clients
    
    @pytest.mark.asyncio
    async def test_call_llm_api_volcengine_success(self, mock_config, mock_volcengine_client, sample_llm_request):
        """测试调用火山引擎API成功"""
        with patch('app.services.llm_service.AsyncOpenAI', return_value=mock_volcengine_client):
            service = LLMService(mock_config)
            
            # 调用API
            result = await service.call_llm_api(sample_llm_request)
            
            # 验证结果
            assert result is not None
            assert isinstance(result, LLMResponse)
            assert result.response_content == "测试回复内容"
            assert result.prompt_tokens == 10
            assert result.completion_tokens == 20
            assert result.usage_tokens == 30
            assert result.model == "gpt-4"
            
            # 验证客户端调用
            mock_volcengine_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_call_llm_api_openai_success(self, mock_config, mock_openai_client, sample_llm_request):
        """测试调用OpenAI API成功"""
        # 修改请求使用OpenAI
        sample_llm_request.provider = LLMProvider.OPENAI
        
        with patch('app.services.llm_service.AsyncOpenAI', return_value=mock_openai_client):
            service = LLMService(mock_config)
            
            # 调用API
            result = await service.call_llm_api(sample_llm_request)
            
            # 验证结果
            assert result is not None
            assert isinstance(result, LLMResponse)
            assert result.response_content == "OpenAI测试回复"
            assert result.prompt_tokens == 15
            assert result.completion_tokens == 25
            assert result.usage_tokens == 40
            
            # 验证客户端调用
            mock_openai_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_call_llm_api_mock_provider(self, mock_config, sample_llm_request):
        """测试调用模拟API提供商"""
        # 修改请求使用模拟提供商
        sample_llm_request.provider = LLMProvider.MOCK
        
        service = LLMService(mock_config)
        
        # 调用API
        result = await service.call_llm_api(sample_llm_request)
        
        # 验证结果
        assert result is not None
        assert isinstance(result, LLMResponse)
        assert result.response_content == "这是一个模拟的AI回复"
        assert result.prompt_tokens == 10
        assert result.completion_tokens == 15
        assert result.usage_tokens == 25
    
    @pytest.mark.asyncio
    async def test_call_llm_api_invalid_provider(self, mock_config, sample_llm_request):
        """测试调用无效的API提供商"""
        # 修改请求使用无效的提供商
        sample_llm_request.provider = "invalid_provider"
        
        with patch('app.services.llm_service.AsyncOpenAI'):
            service = LLMService(mock_config)
            
            # 调用API应该返回None
            result = await service.call_llm_api(sample_llm_request)
            
            # 验证结果
            assert result is None
    
    @pytest.mark.asyncio
    async def test_call_llm_api_client_error(self, mock_config, mock_volcengine_client, sample_llm_request):
        """测试调用API客户端错误"""
        # 模拟客户端错误
        mock_volcengine_client.chat.completions.create = AsyncMock(
            side_effect=Exception("Client error")
        )
        
        with patch('app.services.llm_service.AsyncOpenAI', return_value=mock_volcengine_client):
            service = LLMService(mock_config)
            
            # 调用API应该返回None
            result = await service.call_llm_api(sample_llm_request)
            
            # 验证结果
            assert result is None
    
    @pytest.mark.asyncio
    async def test_call_llm_api_network_error(self, mock_config, mock_volcengine_client, sample_llm_request):
        """测试调用API网络错误"""
        # 模拟网络错误
        mock_volcengine_client.chat.completions.create = AsyncMock(
            side_effect=ConnectionError("Network error")
        )
        
        with patch('app.services.llm_service.AsyncOpenAI', return_value=mock_volcengine_client):
            service = LLMService(mock_config)
            
            # 调用API应该返回None
            result = await service.call_llm_api(sample_llm_request)
            
            # 验证结果
            assert result is None
    
    @pytest.mark.asyncio
    async def test_call_llm_api_timeout_error(self, mock_config, mock_volcengine_client, sample_llm_request):
        """测试调用API超时错误"""
        # 模拟超时错误
        mock_volcengine_client.chat.completions.create = AsyncMock(
            side_effect=TimeoutError("Request timeout")
        )
        
        with patch('app.services.llm_service.AsyncOpenAI', return_value=mock_volcengine_client):
            service = LLMService(mock_config)
            
            # 调用API应该返回None
            result = await service.call_llm_api(sample_llm_request)
            
            # 验证结果
            assert result is None
    
    @pytest.mark.asyncio
    async def test_call_llm_api_empty_response(self, mock_config, mock_volcengine_client, sample_llm_request):
        """测试调用API空响应"""
        # 模拟空响应
        mock_response = Mock()
        mock_response.choices = []
        mock_response.usage = Mock(prompt_tokens=0, completion_tokens=0, total_tokens=0)
        mock_response.model = "gpt-4"
        
        mock_volcengine_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        with patch('app.services.llm_service.AsyncOpenAI', return_value=mock_volcengine_client):
            service = LLMService(mock_config)
            
            # 调用API
            result = await service.call_llm_api(sample_llm_request)
            
            # 验证结果
            assert result is not None
            assert result.response_content == ""  # 空内容
            assert result.usage_tokens == 0
    
    @pytest.mark.asyncio
    async def test_call_llm_api_large_response(self, mock_config, mock_volcengine_client, sample_llm_request):
        """测试调用API大响应"""
        # 模拟大响应
        large_content = "这是一个很长的回复内容。" * 100  # 长内容
        
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content=large_content))]
        mock_response.usage = Mock(prompt_tokens=100, completion_tokens=500, total_tokens=600)
        mock_response.model = "gpt-4"
        
        mock_volcengine_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        with patch('app.services.llm_service.AsyncOpenAI', return_value=mock_volcengine_client):
            service = LLMService(mock_config)
            
            # 调用API
            result = await service.call_llm_api(sample_llm_request)
            
            # 验证结果
            assert result is not None
            assert result.response_content == large_content
            assert result.usage_tokens == 600
    
    @pytest.mark.asyncio
    async def test_call_llm_api_different_models(self, mock_config, mock_volcengine_client, sample_llm_request):
        """测试调用不同模型"""
        # 测试不同的模型
        models = [LLMModel.GPT_4, LLMModel.GPT_3_5_TURBO, LLMModel.CLAUDE_3]
        
        with patch('app.services.llm_service.AsyncOpenAI', return_value=mock_volcengine_client):
            service = LLMService(mock_config)
            
            for model in models:
                sample_llm_request.model = model
                
                # 调用API
                result = await service.call_llm_api(sample_llm_request)
                
                # 验证结果
                assert result is not None
                assert result.model == "gpt-4"  # 模拟响应总是返回gpt-4
    
    @pytest.mark.asyncio
    async def test_call_llm_api_different_temperatures(self, mock_config, mock_volcengine_client, sample_llm_request):
        """测试调用不同温度参数"""
        # 测试不同的温度参数
        temperatures = [0.1, 0.5, 0.9, 1.0]
        
        with patch('app.services.llm_service.AsyncOpenAI', return_value=mock_volcengine_client):
            service = LLMService(mock_config)
            
            for temp in temperatures:
                sample_llm_request.temperature = temp
                
                # 调用API
                result = await service.call_llm_api(sample_llm_request)
                
                # 验证结果
                assert result is not None
                assert result.response_content == "测试回复内容"
    
    @pytest.mark.asyncio
    async def test_call_llm_api_different_max_tokens(self, mock_config, mock_volcengine_client, sample_llm_request):
        """测试调用不同最大token参数"""
        # 测试不同的max_tokens参数
        max_tokens_values = [100, 500, 1000, 2000]
        
        with patch('app.services.llm_service.AsyncOpenAI', return_value=mock_volcengine_client):
            service = LLMService(mock_config)
            
            for max_tokens in max_tokens_values:
                sample_llm_request.max_tokens = max_tokens
                
                # 调用API
                result = await service.call_llm_api(sample_llm_request)
                
                # 验证结果
                assert result is not None
                assert result.completion_tokens == 20  # 模拟响应总是返回20个完成token
    
    @pytest.mark.asyncio
    async def test_call_llm_api_complex_messages(self, mock_config, mock_volcengine_client, sample_llm_request):
        """测试调用复杂消息"""
        # 创建复杂的消息历史
        sample_llm_request.messages = [
            {"role": "system", "content": "你是一个专业的AI助手。"},
            {"role": "user", "content": "请介绍一下人工智能的发展历史。"},
            {"role": "assistant", "content": "人工智能的发展可以追溯到20世纪50年代..."},
            {"role": "user", "content": "那么深度学习的突破点是什么？"}
        ]
        
        with patch('app.services.llm_service.AsyncOpenAI', return_value=mock_volcengine_client):
            service = LLMService(mock_config)
            
            # 调用API
            result = await service.call_llm_api(sample_llm_request)
            
            # 验证结果
            assert result is not None
            assert result.response_content == "测试回复内容"
    
    @pytest.mark.asyncio
    async def test_call_llm_api_rate_limit_error(self, mock_config, mock_volcengine_client, sample_llm_request):
        """测试调用API速率限制错误"""
        # 模拟速率限制错误
        mock_volcengine_client.chat.completions.create = AsyncMock(
            side_effect=Exception("Rate limit exceeded")
        )
        
        with patch('app.services.llm_service.AsyncOpenAI', return_value=mock_volcengine_client):
            service = LLMService(mock_config)
            
            # 调用API应该返回None
            result = await service.call_llm_api(sample_llm_request)
            
            # 验证结果
            assert result is None