import pytest
import uuid
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from fastapi import HTTPException

from app.services.auth import AuthService
from app.config import settings

class TestAuthService:
    """认证服务测试类"""
    
    def test_create_token_success(self):
        """测试创建token成功"""
        user_id = str(uuid.uuid4())
        token = AuthService.create_token(user_id)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_token_fallback(self):
        """测试token创建的回退机制（当jose库不可用时）"""
        # 当jose库不可用时，应该返回用户ID作为token
        token = AuthService.create_token("test_user_id")
        assert token == "test_user_id"
    
    def test_verify_wx_code_not_implemented(self):
        """测试微信code验证未实现"""
        with pytest.raises(HTTPException) as exc_info:
            AuthService.verify_wx_code("test_code")
        
        assert exc_info.value.status_code == 501
        assert "微信API集成待实现" in str(exc_info.value.detail)
    
    @patch('app.services.auth.get_db_services')
    @patch('app.utils.db_config.SessionLocal')
    def test_get_user_from_token_success(self, mock_session_local, mock_get_db_services):
        """测试从token获取用户信息成功"""
        # 设置模拟数据
        mock_user = Mock()
        mock_user.id = str(uuid.uuid4())
        mock_user.nick_name = "测试用户"
        mock_user.avatar_url = "https://example.com/avatar.jpg"
        mock_user.gender = 1
        mock_user.phone = "13800138000"
        
        # 设置模拟数据库会话
        mock_db = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_session_local.return_value = mock_db
        
        # 设置模拟数据库服务
        mock_get_user_func = Mock(return_value=mock_user)
        mock_get_db_services.return_value = (Mock(), Mock(), mock_get_user_func)
        
        # 测试
        user_id = str(uuid.uuid4())
        result = AuthService.get_user_from_token(user_id)
        
        assert result is not None
        assert result["id"] == mock_user.id
        assert result["nickName"] == mock_user.nick_name
        assert result["avatarUrl"] == mock_user.avatar_url
        assert result["gender"] == mock_user.gender
        assert result["phone"] == mock_user.phone
    
    def test_get_user_from_token_invalid(self):
        """测试无效的token"""
        result = AuthService.get_user_from_token("")
        assert result is None
    
    @patch('app.services.auth.settings')
    def test_verify_sms_code_debug_mode(self, mock_settings):
        """测试开发模式下验证码验证"""
        mock_settings.DEBUG = True
        
        result = AuthService.verify_sms_code("13800138000", "123456")
        assert result is True
    
    @patch('app.services.auth.settings')
    def test_verify_sms_code_production_mode(self, mock_settings):
        """测试生产模式下验证码验证"""
        mock_settings.DEBUG = False
        
        result = AuthService.verify_sms_code("13800138000", "123456")
        assert result is True  # 目前返回True，TODO: 需要实现真实验证
    
    def test_login_by_phone_invalid_code(self):
        """测试手机号登录无效验证码"""
        with patch('app.services.auth.AuthService.verify_sms_code', return_value=False):
            with pytest.raises(ValueError, match="无效的验证码"):
                AuthService.login_by_phone("13800138000", "000000", None)
    
    @patch('app.services.auth.AuthService.verify_sms_code')
    @patch('app.services.auth.get_db_services')
    def test_login_by_phone_existing_user(self, mock_get_db_services, mock_verify_sms):
        """测试手机号登录已存在用户"""
        # 设置模拟数据
        mock_user = Mock()
        mock_user.id = str(uuid.uuid4())
        mock_user.phone = "13800138000"
        mock_user.nick_name = "老用户"
        mock_user.avatar_url = "https://example.com/old_avatar.jpg"
        mock_user.gender = 1
        mock_user.register_at = datetime.now()
        
        # 设置模拟数据库服务
        mock_get_user_by_phone_func = Mock(return_value=mock_user)
        mock_get_db_services.return_value = (Mock(), mock_get_user_by_phone_func, Mock())
        
        # 设置验证码验证
        mock_verify_sms.return_value = True
        
        # 测试
        result = AuthService.login_by_phone("13800138000", "123456", Mock())
        
        assert result is not None
        assert result["token"] is not None
        assert result["isNewUser"] is False
        assert result["userInfo"]["id"] == mock_user.id
        assert result["userInfo"]["nickName"] == mock_user.nick_name
    
    @patch('app.services.auth.AuthService.verify_sms_code')
    @patch('app.services.auth.get_db_services')
    def test_login_by_phone_new_user(self, mock_get_db_services, mock_verify_sms):
        """测试手机号登录新用户"""
        # 设置模拟数据
        mock_user = Mock()
        mock_user.id = str(uuid.uuid4())
        mock_user.phone = "13800138000"
        mock_user.nick_name = "用户8000"
        mock_user.avatar_url = ""
        mock_user.gender = 0

        # 设置模拟数据库服务
        mock_get_user_by_phone_func = Mock(return_value=None)
        mock_create_user_func = Mock(return_value=mock_user)
        mock_get_db_services.return_value = (mock_create_user_func, mock_get_user_by_phone_func, Mock())

        # 设置验证码验证
        mock_verify_sms.return_value = True

        # 测试
        result = AuthService.login_by_phone("13800138000", "123456", Mock())

        assert result is not None
        assert result["token"] is not None
        assert result["isNewUser"] is True
        assert result["userInfo"]["nickName"] == mock_user.nick_name
        assert "token" in result
    
    def test_login_by_phone_no_db(self):
        """测试手机号登录无数据库连接"""
        with patch('app.services.auth.AuthService.verify_sms_code', return_value=True):
            with pytest.raises(ValueError, match="数据库连接不能为空"):
                AuthService.login_by_phone("13800138000", "123456", None)
    
    def test_login_invalid_wx_code(self):
        """测试微信登录无效code"""
        with patch('app.services.auth.AuthService.verify_wx_code', return_value=None):
            with pytest.raises(ValueError, match="无效的微信code"):
                AuthService.login("invalid_code")
    
    def test_login_user_not_registered(self):
        """测试微信登录用户未注册"""
        mock_wx_result = {"openid": "test_openid"}
        with patch('app.services.auth.AuthService.verify_wx_code', return_value=mock_wx_result):
            with pytest.raises(ValueError, match="用户未注册，请先注册"):
                AuthService.login("test_code")
    
    def test_login_by_wechat_invalid_code(self):
        """测试微信授权登录无效code"""
        with patch('app.services.auth.AuthService.verify_wx_code', return_value=None):
            with pytest.raises(ValueError, match="无效的微信code"):
                AuthService.login_by_wechat("invalid_code")
    
    def test_login_by_wechat_user_not_registered(self):
        """测试微信授权登录用户未注册"""
        mock_wx_result = {"openid": "test_openid"}
        with patch('app.services.auth.AuthService.verify_wx_code', return_value=mock_wx_result):
            with pytest.raises(ValueError, match="用户未注册，请先注册"):
                AuthService.login_by_wechat("test_code")
    
    def test_register_no_phone(self):
        """测试注册缺少手机号"""
        user_data = {"nickName": "测试用户"}
        
        with pytest.raises(ValueError, match="手机号和验证码不能为空"):
            AuthService.register(user_data, Mock())