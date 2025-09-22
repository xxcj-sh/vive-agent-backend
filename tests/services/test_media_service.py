import pytest
import uuid
import os
from unittest.mock import Mock, MagicMock, patch, mock_open
from datetime import datetime

from app.services.media_service import MediaService
# Media type is string-based in media_service, not an enum
# Media data is returned as dict, not a model


class TestMediaService:
    """媒体服务测试类"""
    
    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return Mock()
    
    @pytest.fixture
    def mock_file_system(self):
        """创建模拟文件系统"""
        with patch('os.path.exists') as mock_exists, \
             patch('os.makedirs') as mock_makedirs, \
             patch('os.listdir') as mock_listdir, \
             patch('os.path.isfile') as mock_isfile, \
             patch('os.path.getsize') as mock_getsize, \
             patch('os.path.getmtime') as mock_getmtime, \
             patch('builtins.open', mock_open(read_data=b'fake_image_data')):
            
            mock_exists.return_value = True
            mock_makedirs.return_value = None
            mock_listdir.return_value = ['avatar_12345.jpg', 'image_67890.png']
            mock_isfile.return_value = True
            mock_getsize.return_value = 1024
            mock_getmtime.return_value = 1234567890
            
            yield {
                'exists': mock_exists,
                'makedirs': mock_makedirs,
                'listdir': mock_listdir,
                'isfile': mock_isfile,
                'getsize': mock_getsize,
                'getmtime': mock_getmtime
            }
    
    @pytest.fixture
    def sample_user_id(self):
        """示例用户ID"""
        return 12345
    
    @pytest.fixture
    def sample_media_data(self):
        """示例媒体数据"""
        return [
            Mock(spec=UserMedia, id=1, user_id=12345, media_type=MediaType.AVATAR, 
                 file_path='avatars/avatar_12345.jpg', file_size=1024, 
                 upload_time=datetime(2024, 1, 1, 10, 0, 0)),
            Mock(spec=UserMedia, id=2, user_id=12345, media_type=MediaType.IMAGE,
                 file_path='images/image_67890.png', file_size=2048,
                 upload_time=datetime(2024, 1, 2, 11, 0, 0))
        ]
    
    def test_get_user_media_success(self, mock_db, sample_user_id, sample_media_data):
        """测试获取用户媒体成功"""
        # 创建服务实例
        service = MediaService(mock_db)
        
        # 模拟数据库查询
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_media_data
        mock_db.query.return_value = mock_query
        
        # 获取用户媒体
        result = service.get_user_media(sample_user_id)
        
        # 验证结果
        assert len(result) == 2
        assert result[0]['id'] == 1
        assert result[0]['media_type'] == 'avatar'
        assert result[0]['file_path'] == 'avatars/avatar_12345.jpg'
        assert result[0]['file_size'] == 1024
        assert result[1]['id'] == 2
        assert result[1]['media_type'] == 'image'
    
    def test_get_user_media_no_data(self, mock_db, sample_user_id):
        """测试获取用户媒体（无数据）"""
        # 创建服务实例
        service = MediaService(mock_db)
        
        # 模拟数据库查询返回空结果
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query
        
        # 获取用户媒体
        result = service.get_user_media(sample_user_id)
        
        # 验证结果
        assert result == []
    
    def test_scan_user_media_files_success(self, mock_db, sample_user_id, mock_file_system):
        """测试扫描用户媒体文件成功"""
        # 创建服务实例
        service = MediaService(mock_db)
        
        # 扫描媒体文件
        result = service._scan_user_media_files(sample_user_id)
        
        # 验证结果
        assert len(result) == 2
        assert result[0]['file_name'] == 'avatar_12345.jpg'
        assert result[0]['file_size'] == 1024
        assert result[0]['media_type'] == 'avatar'
        assert result[1]['file_name'] == 'image_67890.png'
        assert result[1]['file_size'] == 2048
        assert result[1]['media_type'] == 'image'
    
    def test_scan_user_media_files_empty_directory(self, mock_db, sample_user_id, mock_file_system):
        """测试扫描用户媒体文件（空目录）"""
        # 修改模拟返回空目录
        mock_file_system['listdir'].return_value = []
        
        # 创建服务实例
        service = MediaService(mock_db)
        
        # 扫描媒体文件
        result = service._scan_user_media_files(sample_user_id)
        
        # 验证结果
        assert result == []
    
    def test_scan_user_media_files_non_media_files(self, mock_db, sample_user_id, mock_file_system):
        """测试扫描用户媒体文件（非媒体文件）"""
        # 修改模拟返回非媒体文件
        mock_file_system['listdir'].return_value = ['document.pdf', 'data.json', 'script.py']
        
        # 创建服务实例
        service = MediaService(mock_db)
        
        # 扫描媒体文件
        result = service._scan_user_media_files(sample_user_id)
        
        # 验证结果（应该过滤掉非媒体文件）
        assert result == []
    
    def test_generate_default_media_data_avatar(self, mock_db, sample_user_id):
        """测试生成默认媒体数据（头像）"""
        # 创建服务实例
        service = MediaService(mock_db)
        
        # 生成头像数据
        result = service._generate_default_media_data(sample_user_id, MediaType.AVATAR)
        
        # 验证结果
        assert result['user_id'] == sample_user_id
        assert result['media_type'] == MediaType.AVATAR
        assert result['file_path'].startswith('avatars/')
        assert result['file_path'].endswith('.jpg')
        assert result['file_size'] == 0
        assert result['file_format'] == 'image/jpeg'
    
    def test_generate_default_media_data_image(self, mock_db, sample_user_id):
        """测试生成默认媒体数据（图片）"""
        # 创建服务实例
        service = MediaService(mock_db)
        
        # 生成图片数据
        result = service._generate_default_media_data(sample_user_id, MediaType.IMAGE)
        
        # 验证结果
        assert result['user_id'] == sample_user_id
        assert result['media_type'] == MediaType.IMAGE
        assert result['file_path'].startswith('images/')
        assert result['file_path'].endswith('.png')
        assert result['file_size'] == 0
        assert result['file_format'] == 'image/png'
    
    def test_generate_default_media_data_video(self, mock_db, sample_user_id):
        """测试生成默认媒体数据（视频）"""
        # 创建服务实例
        service = MediaService(mock_db)
        
        # 生成视频数据
        result = service._generate_default_media_data(sample_user_id, MediaType.VIDEO)
        
        # 验证结果
        assert result['user_id'] == sample_user_id
        assert result['media_type'] == MediaType.VIDEO
        assert result['file_path'].startswith('videos/')
        assert result['file_path'].endswith('.mp4')
        assert result['file_size'] == 0
        assert result['file_format'] == 'video/mp4'
    
    def test_upload_media_file_success(self, mock_db, sample_user_id, mock_file_system):
        """测试上传媒体文件成功"""
        # 创建服务实例
        service = MediaService(mock_db)
        
        # 模拟文件数据
        file_data = b'fake_image_data'
        file_name = 'test_image.jpg'
        file_size = len(file_data)
        
        # 上传文件
        result = service.upload_media_file(sample_user_id, file_data, file_name, MediaType.IMAGE)
        
        # 验证数据库操作
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        
        # 验证结果类型
        assert isinstance(result, UserMedia)
    
    def test_upload_media_file_creates_directory(self, mock_db, sample_user_id, mock_file_system):
        """测试上传媒体文件（创建目录）"""
        # 修改模拟目录不存在
        mock_file_system['exists'].return_value = False
        
        # 创建服务实例
        service = MediaService(mock_db)
        
        # 模拟文件数据
        file_data = b'fake_image_data'
        file_name = 'test_image.jpg'
        
        # 上传文件
        result = service.upload_media_file(sample_user_id, file_data, file_name, MediaType.IMAGE)
        
        # 验证创建目录
        mock_file_system['makedirs'].assert_called_once()
        
        # 验证数据库操作
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_upload_media_file_write_error(self, mock_db, sample_user_id, mock_file_system):
        """测试上传媒体文件（写入错误）"""
        # 创建服务实例
        service = MediaService(mock_db)
        
        # 模拟文件写入错误
        with patch('builtins.open', side_effect=IOError("Write error")):
            # 上传文件
            result = service.upload_media_file(sample_user_id, b'data', 'test.jpg', MediaType.IMAGE)
            
            # 验证返回None
            assert result is None
    
    def test_delete_media_file_success(self, mock_db, sample_user_id, sample_media_data):
        """测试删除媒体文件成功"""
        # 创建服务实例
        service = MediaService(mock_db)
        
        # 模拟数据库查询
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_media_data[0]
        mock_db.query.return_value = mock_query
        
        # 模拟文件删除
        with patch('os.remove') as mock_remove:
            mock_remove.return_value = None
            
            # 删除文件
            result = service.delete_media_file(sample_media_data[0].id, sample_user_id)
            
            # 验证文件删除
            mock_remove.assert_called_once_with(sample_media_data[0].file_path)
            
            # 验证数据库操作
            mock_db.delete.assert_called_once()
            mock_db.commit.assert_called_once()
            
            # 验证结果
            assert result is True
    
    def test_delete_media_file_not_found(self, mock_db, sample_user_id):
        """测试删除媒体文件（文件不存在）"""
        # 创建服务实例
        service = MediaService(mock_db)
        
        # 模拟数据库查询返回None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # 删除文件
        result = service.delete_media_file(999, sample_user_id)
        
        # 验证结果
        assert result is False
        
        # 验证没有数据库删除操作
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()
    
    def test_delete_media_file_permission_denied(self, mock_db, sample_user_id, sample_media_data):
        """测试删除媒体文件（权限拒绝）"""
        # 创建服务实例
        service = MediaService(mock_db)
        
        # 模拟数据库查询
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_media_data[0]
        mock_db.query.return_value = mock_query
        
        # 模拟权限错误
        with patch('os.remove', side_effect=PermissionError("Permission denied")):
            # 删除文件
            result = service.delete_media_file(sample_media_data[0].id, sample_user_id)
            
            # 验证结果
            assert result is False
    
    def test_get_media_file_info_success(self, mock_db, sample_user_id, sample_media_data):
        """测试获取媒体文件信息成功"""
        # 创建服务实例
        service = MediaService(mock_db)
        
        # 模拟数据库查询
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_media_data[0]
        mock_db.query.return_value = mock_query
        
        # 获取文件信息
        result = service.get_media_file_info(sample_media_data[0].id, sample_user_id)
        
        # 验证结果
        assert result is not None
        assert result['id'] == sample_media_data[0].id
        assert result['media_type'] == 'avatar'
        assert result['file_path'] == 'avatars/avatar_12345.jpg'
        assert result['file_size'] == 1024
        assert 'upload_time' in result
        assert 'file_url' in result
    
    def test_get_media_file_info_not_found(self, mock_db, sample_user_id):
        """测试获取媒体文件信息（文件不存在）"""
        # 创建服务实例
        service = MediaService(mock_db)
        
        # 模拟数据库查询返回None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # 获取文件信息
        result = service.get_media_file_info(999, sample_user_id)
        
        # 验证结果
        assert result is None
    
    def test_get_media_file_info_wrong_user(self, mock_db, sample_user_id, sample_media_data):
        """测试获取媒体文件信息（用户不匹配）"""
        # 创建服务实例
        service = MediaService(mock_db)
        
        # 模拟数据库查询返回其他用户的文件
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_media_data[0]  # 其他用户的文件
        mock_db.query.return_value = mock_query
        
        # 获取文件信息（使用不同的用户ID）
        result = service.get_media_file_info(sample_media_data[0].id, 99999)
        
        # 验证结果
        assert result is None
    
    def test_get_user_media_by_type(self, mock_db, sample_user_id, sample_media_data):
        """测试按类型获取用户媒体"""
        # 创建服务实例
        service = MediaService(mock_db)
        
        # 模拟数据库查询（只返回头像）
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [sample_media_data[0]]
        mock_db.query.return_value = mock_query
        
        # 获取头像
        result = service.get_user_media(sample_user_id, MediaType.AVATAR)
        
        # 验证结果
        assert len(result) == 1
        assert result[0]['media_type'] == 'avatar'
        assert result[0]['id'] == 1
    
    def test_get_user_media_total_size(self, mock_db, sample_user_id, sample_media_data):
        """测试获取用户媒体总大小"""
        # 创建服务实例
        service = MediaService(mock_db)
        
        # 模拟数据库查询
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = sample_media_data
        mock_db.query.return_value = mock_query
        
        # 获取用户媒体
        result = service.get_user_media(sample_user_id)
        
        # 计算总大小
        total_size = sum(item['file_size'] for item in result)
        
        # 验证总大小
        assert total_size == 3072  # 1024 + 2048