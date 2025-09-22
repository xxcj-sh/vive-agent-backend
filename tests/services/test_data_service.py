import pytest
import uuid
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

from app.services.data_service import DataService
from app.models.enums import DataType, CacheDuration
from app.models.user_data import UserData
from app.models.cache import Cache


class TestDataService:
    """数据服务测试类"""
    
    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return Mock()
    
    @pytest.fixture
    def sample_user_id(self):
        """示例用户ID"""
        return 12345
    
    @pytest.fixture
    def sample_data_key(self):
        """示例数据键"""
        return "user_preferences_12345"
    
    @pytest.fixture
    def sample_data_value(self):
        """示例数据值"""
        return {
            "theme": "dark",
            "language": "zh-CN",
            "notifications": True,
            "privacy_level": "high"
        }
    
    @pytest.fixture
    def sample_user_data(self):
        """示例用户数据对象"""
        user_data = Mock(spec=UserData)
        user_data.id = uuid.uuid4()
        user_data.user_id = 12345
        user_data.data_type = DataType.USER_PREFERENCE
        user_data.data_key = "user_preferences_12345"
        user_data.data_value = {
            "theme": "dark",
            "language": "zh-CN",
            "notifications": True,
            "privacy_level": "high"
        }
        user_data.created_at = datetime.now()
        user_data.updated_at = datetime.now()
        return user_data
    
    @pytest.fixture
    def sample_cache_data(self):
        """示例缓存数据对象"""
        cache = Mock(spec=Cache)
        cache.id = uuid.uuid4()
        cache.cache_key = "cache_user_12345_profile"
        cache.cache_value = {
            "nickname": "测试用户",
            "avatar_url": "https://example.com/avatar.jpg",
            "bio": "这是一个测试用户"
        }
        cache.duration = CacheDuration.ONE_HOUR
        cache.created_at = datetime.now()
        cache.expires_at = datetime.now() + timedelta(hours=1)
        return cache
    
    def test_store_user_data_success(self, mock_db, sample_user_id, sample_data_key, sample_data_value):
        """测试存储用户数据成功"""
        # 创建服务实例
        service = DataService(mock_db)
        
        # 存储数据
        result = service.store_user_data(
            user_id=sample_user_id,
            data_type=DataType.USER_PREFERENCE,
            data_key=sample_data_key,
            data_value=sample_data_value
        )
        
        # 验证数据库操作
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        
        # 验证结果类型
        assert isinstance(result, UserData)
    
    def test_store_user_data_update_existing(self, mock_db, sample_user_id, sample_data_key, sample_data_value, sample_user_data):
        """测试更新已存在的用户数据"""
        # 创建服务实例
        service = DataService(mock_db)
        
        # 模拟已存在的数据
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_user_data
        mock_db.query.return_value = mock_query
        
        # 更新数据
        new_value = {"theme": "light", "language": "en-US"}
        result = service.store_user_data(
            user_id=sample_user_id,
            data_type=DataType.USER_PREFERENCE,
            data_key=sample_data_key,
            data_value=new_value
        )
        
        # 验证数据库操作
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        
        # 验证数据更新
        assert result.data_value == new_value
    
    def test_store_user_data_create_new(self, mock_db, sample_user_id, sample_data_key, sample_data_value):
        """测试创建新的用户数据"""
        # 创建服务实例
        service = DataService(mock_db)
        
        # 模拟数据不存在
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # 存储数据
        result = service.store_user_data(
            user_id=sample_user_id,
            data_type=DataType.USER_PREFERENCE,
            data_key=sample_data_key,
            data_value=sample_data_value
        )
        
        # 验证数据库操作
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_get_user_data_success(self, mock_db, sample_user_id, sample_data_key, sample_user_data):
        """测试获取用户数据成功"""
        # 创建服务实例
        service = DataService(mock_db)
        
        # 模拟数据库查询
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_user_data
        mock_db.query.return_value = mock_query
        
        # 获取数据
        result = service.get_user_data(sample_user_id, sample_data_key)
        
        # 验证结果
        assert result == sample_user_data
    
    def test_get_user_data_not_found(self, mock_db, sample_user_id, sample_data_key):
        """测试获取用户数据（未找到）"""
        # 创建服务实例
        service = DataService(mock_db)
        
        # 模拟数据库查询返回None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # 获取数据
        result = service.get_user_data(sample_user_id, sample_data_key)
        
        # 验证结果
        assert result is None
    
    def test_get_user_data_by_type_success(self, mock_db, sample_user_id, sample_user_data):
        """测试按类型获取用户数据成功"""
        # 创建服务实例
        service = DataService(mock_db)
        
        # 模拟数据库查询
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [sample_user_data]
        mock_db.query.return_value = mock_query
        
        # 获取数据
        result = service.get_user_data_by_type(sample_user_id, DataType.USER_PREFERENCE)
        
        # 验证结果
        assert len(result) == 1
        assert result[0] == sample_user_data
    
    def test_get_user_data_by_type_no_data(self, mock_db, sample_user_id):
        """测试按类型获取用户数据（无数据）"""
        # 创建服务实例
        service = DataService(mock_db)
        
        # 模拟数据库查询返回空结果
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query
        
        # 获取数据
        result = service.get_user_data_by_type(sample_user_id, DataType.USER_PREFERENCE)
        
        # 验证结果
        assert result == []
    
    def test_delete_user_data_success(self, mock_db, sample_user_id, sample_data_key, sample_user_data):
        """测试删除用户数据成功"""
        # 创建服务实例
        service = DataService(mock_db)
        
        # 模拟数据库查询
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_user_data
        mock_db.query.return_value = mock_query
        
        # 删除数据
        result = service.delete_user_data(sample_user_id, sample_data_key)
        
        # 验证数据库操作
        mock_db.delete.assert_called_once()
        mock_db.commit.assert_called_once()
        
        # 验证结果
        assert result is True
    
    def test_delete_user_data_not_found(self, mock_db, sample_user_id, sample_data_key):
        """测试删除用户数据（未找到）"""
        # 创建服务实例
        service = DataService(mock_db)
        
        # 模拟数据库查询返回None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # 删除数据
        result = service.delete_user_data(sample_user_id, sample_data_key)
        
        # 验证结果
        assert result is False
    
    def test_store_cache_success(self, mock_db, sample_cache_data):
        """测试存储缓存成功"""
        # 创建服务实例
        service = DataService(mock_db)
        
        # 存储缓存
        result = service.store_cache(
            cache_key=sample_cache_data.cache_key,
            cache_value=sample_cache_data.cache_value,
            duration=CacheDuration.ONE_HOUR
        )
        
        # 验证数据库操作
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        
        # 验证结果类型
        assert isinstance(result, Cache)
    
    def test_store_cache_update_existing(self, mock_db, sample_cache_data):
        """测试更新已存在的缓存"""
        # 创建服务实例
        service = DataService(mock_db)
        
        # 模拟已存在的缓存
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_cache_data
        mock_db.query.return_value = mock_query
        
        # 更新缓存
        new_value = {"nickname": "新昵称", "avatar_url": "https://example.com/new_avatar.jpg"}
        result = service.store_cache(
            cache_key=sample_cache_data.cache_key,
            cache_value=new_value,
            duration=CacheDuration.ONE_HOUR
        )
        
        # 验证数据库操作
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        
        # 验证数据更新
        assert result.cache_value == new_value
    
    def test_get_cache_success(self, mock_db, sample_cache_data):
        """测试获取缓存成功"""
        # 创建服务实例
        service = DataService(mock_db)
        
        # 模拟数据库查询
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_cache_data
        mock_db.query.return_value = mock_query
        
        # 获取缓存
        result = service.get_cache(sample_cache_data.cache_key)
        
        # 验证结果
        assert result == sample_cache_data
    
    def test_get_cache_expired(self, mock_db, sample_cache_data):
        """测试获取缓存（已过期）"""
        # 创建服务实例
        service = DataService(mock_db)
        
        # 修改缓存数据为已过期
        sample_cache_data.expires_at = datetime.now() - timedelta(hours=1)
        
        # 模拟数据库查询
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_cache_data
        mock_db.query.return_value = mock_query
        
        # 获取缓存
        result = service.get_cache(sample_cache_data.cache_key)
        
        # 验证结果（应该返回None，因为已过期）
        assert result is None
    
    def test_get_cache_not_found(self, mock_db):
        """测试获取缓存（未找到）"""
        # 创建服务实例
        service = DataService(mock_db)
        
        # 模拟数据库查询返回None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # 获取缓存
        result = service.get_cache("non_existent_key")
        
        # 验证结果
        assert result is None
    
    def test_delete_cache_success(self, mock_db, sample_cache_data):
        """测试删除缓存成功"""
        # 创建服务实例
        service = DataService(mock_db)
        
        # 模拟数据库查询
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_cache_data
        mock_db.query.return_value = mock_query
        
        # 删除缓存
        result = service.delete_cache(sample_cache_data.cache_key)
        
        # 验证数据库操作
        mock_db.delete.assert_called_once()
        mock_db.commit.assert_called_once()
        
        # 验证结果
        assert result is True
    
    def test_delete_cache_not_found(self, mock_db):
        """测试删除缓存（未找到）"""
        # 创建服务实例
        service = DataService(mock_db)
        
        # 模拟数据库查询返回None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # 删除缓存
        result = service.delete_cache("non_existent_key")
        
        # 验证结果
        assert result is False
    
    def test_cleanup_expired_cache_success(self, mock_db):
        """测试清理过期缓存成功"""
        # 创建服务实例
        service = DataService(mock_db)
        
        # 模拟过期缓存查询
        expired_cache = Mock(spec=Cache)
        expired_cache.id = uuid.uuid4()
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [expired_cache]
        mock_db.query.return_value = mock_query
        
        # 清理过期缓存
        result = service.cleanup_expired_cache()
        
        # 验证数据库操作
        mock_db.delete.assert_called_once()
        mock_db.commit.assert_called_once()
        
        # 验证结果
        assert result == 1  # 清理了1个过期缓存
    
    def test_cleanup_expired_cache_no_expired(self, mock_db):
        """测试清理过期缓存（无过期缓存）"""
        # 创建服务实例
        service = DataService(mock_db)
        
        # 模拟无过期缓存
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query
        
        # 清理过期缓存
        result = service.cleanup_expired_cache()
        
        # 验证结果
        assert result == 0  # 没有清理任何缓存
    
    def test_get_user_data_value_success(self, mock_db, sample_user_id, sample_data_key, sample_user_data):
        """测试获取用户数据值成功"""
        # 创建服务实例
        service = DataService(mock_db)
        
        # 模拟数据库查询
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_user_data
        mock_db.query.return_value = mock_query
        
        # 获取数据值
        result = service.get_user_data_value(sample_user_id, sample_data_key)
        
        # 验证结果
        assert result == sample_user_data.data_value
    
    def test_get_user_data_value_not_found(self, mock_db, sample_user_id, sample_data_key):
        """测试获取用户数据值（未找到）"""
        # 创建服务实例
        service = DataService(mock_db)
        
        # 模拟数据库查询返回None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # 获取数据值
        result = service.get_user_data_value(sample_user_id, sample_data_key)
        
        # 验证结果
        assert result is None
    
    def test_get_user_data_by_type_with_values(self, mock_db, sample_user_id, sample_user_data):
        """测试按类型获取用户数据（只返回值）"""
        # 创建服务实例
        service = DataService(mock_db)
        
        # 模拟数据库查询
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [sample_user_data]
        mock_db.query.return_value = mock_query
        
        # 获取数据值
        result = service.get_user_data_by_type(sample_user_id, DataType.USER_PREFERENCE, return_values_only=True)
        
        # 验证结果
        assert len(result) == 1
        assert result[0] == sample_user_data.data_value
    
    def test_bulk_store_user_data_success(self, mock_db, sample_user_id):
        """测试批量存储用户数据成功"""
        # 创建服务实例
        service = DataService(mock_db)
        
        # 创建批量数据
        data_items = [
            {"data_type": DataType.USER_PREFERENCE, "data_key": "theme", "data_value": {"value": "dark"}},
            {"data_type": DataType.USER_PREFERENCE, "data_key": "language", "data_value": {"value": "zh-CN"}},
            {"data_type": DataType.USER_SETTING, "data_key": "notifications", "data_value": {"enabled": True}}
        ]
        
        # 批量存储数据
        result = service.bulk_store_user_data(sample_user_id, data_items)
        
        # 验证数据库操作
        assert mock_db.add.call_count == 3  # 添加了3个数据项
        mock_db.commit.assert_called_once()
        
        # 验证结果
        assert len(result) == 3
        assert all(isinstance(item, UserData) for item in result)
    
    def test_bulk_delete_user_data_success(self, mock_db, sample_user_id):
        """测试批量删除用户数据成功"""
        # 创建服务实例
        service = DataService(mock_db)
        
        # 创建要删除的数据键列表
        data_keys = ["theme", "language", "notifications"]
        
        # 模拟数据存在
        mock_data = Mock(spec=UserData)
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_data] * 3  # 返回3个数据项
        mock_db.query.return_value = mock_query
        
        # 批量删除数据
        result = service.bulk_delete_user_data(sample_user_id, data_keys)
        
        # 验证数据库操作
        assert mock_db.delete.call_count == 3  # 删除了3个数据项
        mock_db.commit.assert_called_once()
        
        # 验证结果
        assert result == 3  # 删除了3个数据项