import pytest
import uuid
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.db_service import (
    create_user, get_user, get_user_by_email, get_user_by_phone,
    get_users, update_user, delete_user,
    create_match, get_match, get_matches, update_match, delete_match,
    add_match_detail, get_match_details,
    create_match_action, get_match_action, get_user_match_actions, check_existing_action,
    create_match_result, get_match_result, get_user_match_results, check_mutual_match,
    update_match_result_activity
)
from app.models.user import User
from app.models.match import Match, MatchDetail
from app.models.match_action import MatchAction, MatchResult

class TestDBService:
    """数据库服务测试类"""
    
    def test_create_user_success(self, mock_db):
        """测试创建用户成功"""
        # 设置模拟数据
        user_data = {
            "phone": "13800138000",
            "nick_name": "测试用户",
            "avatar_url": "https://example.com/avatar.jpg",
            "gender": 1
        }
        
        # 设置模拟用户对象
        mock_user = Mock(spec=User)
        mock_user.id = str(uuid.uuid4())
        mock_user.phone = user_data["phone"]
        mock_user.nick_name = user_data["nick_name"]
        mock_user.avatar_url = user_data["avatar_url"]
        mock_user.gender = user_data["gender"]
        
        # 设置数据库操作
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        # 模拟User类
        with patch('app.services.db_service.User') as mock_user_class:
            mock_user_class.return_value = mock_user
            
            result = create_user(mock_db, user_data)
            
            assert result == mock_user
            mock_db.add.assert_called_once_with(mock_user)
            mock_db.commit.assert_called_once()
            mock_db.refresh.assert_called_once_with(mock_user)
    
    def test_create_user_with_id(self, mock_db):
        """测试创建用户时提供ID"""
        user_id = str(uuid.uuid4())
        user_data = {
            "id": user_id,
            "phone": "13800138000",
            "nick_name": "测试用户"
        }
        
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        with patch('app.services.db_service.User') as mock_user_class:
            mock_user_class.return_value = mock_user
            
            result = create_user(mock_db, user_data)
            
            assert result.id == user_id
            mock_user_class.assert_called_once_with(**user_data)
    
    def test_create_user_rollback_on_error(self, mock_db):
        """测试创建用户失败时回滚"""
        user_data = {"phone": "13800138000", "nick_name": "测试用户"}
        
        # 设置异常
        mock_db.add.side_effect = Exception("数据库错误")
        
        with patch('app.services.db_service.User') as mock_user_class:
            mock_user_class.return_value = Mock(spec=User)
            
            with pytest.raises(Exception):
                create_user(mock_db, user_data)
            
            mock_db.rollback.assert_called_once()
    
    def test_get_user_success(self, mock_db):
        """测试获取用户成功"""
        user_id = str(uuid.uuid4())
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value = mock_query
        
        result = get_user(mock_db, user_id)
        
        assert result == mock_user
        mock_db.query.assert_called_once_with(User)
    
    def test_get_user_not_found(self, mock_db):
        """测试获取用户不存在"""
        user_id = str(uuid.uuid4())
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        result = get_user(mock_db, user_id)
        
        assert result is None
    
    def test_get_user_by_phone_success(self, mock_db):
        """测试根据手机号获取用户成功"""
        phone = "13800138000"
        mock_user = Mock(spec=User)
        mock_user.phone = phone
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value = mock_query
        
        result = get_user_by_phone(mock_db, phone)
        
        assert result == mock_user
        mock_db.query.assert_called_once_with(User)
    
    def test_update_user_success(self, mock_db):
        """测试更新用户成功"""
        user_id = str(uuid.uuid4())
        user_data = {
            "nickName": "新昵称",
            "avatarUrl": "https://example.com/new_avatar.jpg"
        }
        
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_user.nick_name = "旧昵称"
        mock_user.avatar_url = "https://example.com/old_avatar.jpg"
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value = mock_query
        
        result = update_user(mock_db, user_id, user_data)
        
        assert result == mock_user
        assert mock_user.nick_name == "新昵称"
        assert mock_user.avatar_url == "https://example.com/new_avatar.jpg"
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_user)
    
    def test_update_user_with_json_fields(self, mock_db):
        """测试更新用户JSON字段"""
        user_id = str(uuid.uuid4())
        user_data = {
            "location": ["北京", "上海"],
            "interests": {"运动": ["篮球", "足球"]}
        }
        
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_user.location = None
        mock_user.interests = None
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value = mock_query
        
        result = update_user(mock_db, user_id, user_data)
        
        assert result == mock_user
        # 验证JSON字段被正确序列化
        assert hasattr(mock_user, 'location')
        assert hasattr(mock_user, 'interests')
    
    def test_delete_user_success(self, mock_db):
        """测试删除用户成功"""
        user_id = str(uuid.uuid4())
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value = mock_query
        
        result = delete_user(mock_db, user_id)
        
        assert result is True
        mock_db.delete.assert_called_once_with(mock_user)
        mock_db.commit.assert_called_once()
    
    def test_delete_user_not_found(self, mock_db):
        """测试删除用户不存在"""
        user_id = str(uuid.uuid4())
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        result = delete_user(mock_db, user_id)
        
        assert result is False
        mock_db.delete.assert_not_called()
    
    def test_create_match_success(self, mock_db):
        """测试创建匹配成功"""
        match_data = {
            "user_id": str(uuid.uuid4()),
            "match_type": "dating",
            "status": "active",
            "score": 85.5
        }
        
        mock_match = Mock(spec=Match)
        mock_match.id = str(uuid.uuid4())
        mock_match.user_id = match_data["user_id"]
        
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        with patch('app.services.db_service.Match') as mock_match_class:
            mock_match_class.return_value = mock_match
            
            result = create_match(mock_db, match_data)
            
            assert result == mock_match
            mock_db.add.assert_called_once_with(mock_match)
            mock_db.commit.assert_called_once()
    
    def test_create_match_with_details(self, mock_db):
        """测试创建匹配带详情"""
        match_data = {"user_id": str(uuid.uuid4()), "match_type": "dating"}
        details = [
            {"user_id": str(uuid.uuid4()), "score": 90},
            {"user_id": str(uuid.uuid4()), "score": 80}
        ]
        
        mock_match = Mock(spec=Match)
        mock_match.id = str(uuid.uuid4())
        
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        with patch('app.services.db_service.Match') as mock_match_class:
            with patch('app.services.db_service.MatchDetail') as mock_detail_class:
                mock_match_class.return_value = mock_match
                mock_detail_class.return_value = Mock(spec=MatchDetail)
                
                result = create_match(mock_db, match_data, details)
                
                assert result == mock_match
                # 验证详情被创建
                assert mock_db.add.call_count == 3  # 1个匹配 + 2个详情
    
    def test_get_match_success(self, mock_db):
        """测试获取匹配成功"""
        match_id = str(uuid.uuid4())
        mock_match = Mock(spec=Match)
        mock_match.id = match_id
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_match
        mock_db.query.return_value = mock_query
        
        result = get_match(mock_db, match_id)
        
        assert result == mock_match
    
    def test_get_matches_with_user_filter(self, mock_db):
        """测试获取用户匹配列表"""
        user_id = str(uuid.uuid4())
        mock_matches = [Mock(spec=Match), Mock(spec=Match)]
        
        mock_query = Mock()
        mock_query.filter.return_value.offset.return_value.limit.return_value.all.return_value = mock_matches
        mock_db.query.return_value = mock_query
        
        result = get_matches(mock_db, user_id=user_id, skip=0, limit=10)
        
        assert result == mock_matches
        mock_query.filter.assert_called_once()
    
    def test_update_match_success(self, mock_db):
        """测试更新匹配成功"""
        match_id = str(uuid.uuid4())
        match_data = {"status": "completed", "score": 95}
        
        mock_match = Mock(spec=Match)
        mock_match.id = match_id
        mock_match.status = "active"
        mock_match.score = 85
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_match
        mock_db.query.return_value = mock_query
        
        result = update_match(mock_db, match_id, match_data)
        
        assert result == mock_match
        assert mock_match.status == "completed"
        assert mock_match.score == 95
        mock_db.commit.assert_called_once()
    
    def test_delete_match_with_details(self, mock_db):
        """测试删除匹配及关联详情"""
        match_id = str(uuid.uuid4())
        mock_match = Mock(spec=Match)
        mock_match.id = match_id
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_match
        mock_db.query.return_value = mock_query
        
        result = delete_match(mock_db, match_id)
        
        assert result is True
        # 验证匹配详情被删除
        mock_db.query.return_value.filter.return_value.delete.assert_called_once()
        mock_db.delete.assert_called_once_with(mock_match)
        mock_db.commit.assert_called_once()
    
    def test_add_match_detail_success(self, mock_db):
        """测试添加匹配详情成功"""
        match_id = str(uuid.uuid4())
        detail_data = {"user_id": str(uuid.uuid4()), "score": 90}
        
        mock_detail = Mock(spec=MatchDetail)
        mock_detail.id = str(uuid.uuid4())
        mock_detail.match_id = match_id
        
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        with patch('app.services.db_service.MatchDetail') as mock_detail_class:
            mock_detail_class.return_value = mock_detail
            
            result = add_match_detail(mock_db, match_id, detail_data)
            
            assert result == mock_detail
            assert result.match_id == match_id
            mock_detail_class.assert_called_once_with(**detail_data, match_id=match_id)
    
    def test_get_match_details_success(self, mock_db):
        """测试获取匹配详情成功"""
        match_id = str(uuid.uuid4())
        mock_details = [Mock(spec=MatchDetail), Mock(spec=MatchDetail)]
        
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = mock_details
        mock_db.query.return_value = mock_query
        
        result = get_match_details(mock_db, match_id)
        
        assert result == mock_details
    
    def test_create_match_action_success(self, mock_db):
        """测试创建匹配操作成功"""
        action_data = {
            "user_id": str(uuid.uuid4()),
            "target_user_id": str(uuid.uuid4()),
            "target_card_id": str(uuid.uuid4()),
            "action_type": "like",
            "match_type": "dating"
        }
        
        mock_action = Mock(spec=MatchAction)
        mock_action.id = str(uuid.uuid4())
        
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        with patch('app.services.db_service.MatchAction') as mock_action_class:
            mock_action_class.return_value = mock_action
            
            result = create_match_action(mock_db, action_data)
            
            assert result == mock_action
            mock_action_class.assert_called_once_with(**action_data)
    
    def test_create_match_action_rollback_on_error(self, mock_db):
        """测试创建匹配操作失败时回滚"""
        action_data = {"user_id": str(uuid.uuid4()), "action_type": "like"}
        
        mock_db.add.side_effect = Exception("数据库错误")
        
        with patch('app.services.db_service.MatchAction') as mock_action_class:
            mock_action_class.return_value = Mock(spec=MatchAction)
            
            with pytest.raises(Exception):
                create_match_action(mock_db, action_data)
            
            mock_db.rollback.assert_called_once()
    
    def test_get_match_action_success(self, mock_db):
        """测试获取匹配操作成功"""
        action_id = str(uuid.uuid4())
        mock_action = Mock(spec=MatchAction)
        mock_action.id = action_id
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_action
        mock_db.query.return_value = mock_query
        
        result = get_match_action(mock_db, action_id)
        
        assert result == mock_action
    
    def test_get_user_match_actions_with_filter(self, mock_db):
        """测试获取用户匹配操作列表带过滤"""
        user_id = str(uuid.uuid4())
        match_type = "dating"
        mock_actions = [Mock(spec=MatchAction), Mock(spec=MatchAction)]
        
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_actions
        mock_db.query.return_value = mock_query
        
        result = get_user_match_actions(mock_db, user_id, match_type=match_type)
        
        assert result == mock_actions
        # 验证调用了两次filter（用户ID和匹配类型）
        assert mock_query.filter.call_count == 2
    
    def test_check_existing_action_found(self, mock_db):
        """测试检查已存在匹配操作找到"""
        user_id = str(uuid.uuid4())
        target_user_id = str(uuid.uuid4())
        target_card_id = str(uuid.uuid4())
        match_type = "dating"
        
        mock_action = Mock(spec=MatchAction)
        
        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.filter.return_value.first.return_value = mock_action
        mock_db.query.return_value = mock_query
        
        result = check_existing_action(mock_db, user_id, target_user_id, target_card_id, match_type)
        
        assert result == mock_action
    
    def test_check_existing_action_not_found(self, mock_db):
        """测试检查已存在匹配操作未找到"""
        user_id = str(uuid.uuid4())
        target_user_id = str(uuid.uuid4())
        target_card_id = str(uuid.uuid4())
        match_type = "dating"
        
        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query
        
        result = check_existing_action(mock_db, user_id, target_user_id, target_card_id, match_type)
        
        assert result is None
    
    def test_create_match_result_success(self, mock_db):
        """测试创建匹配结果成功"""
        result_data = {
            "user1_id": str(uuid.uuid4()),
            "user2_id": str(uuid.uuid4()),
            "match_type": "dating",
            "status": "pending"
        }
        
        mock_result = Mock(spec=MatchResult)
        mock_result.id = str(uuid.uuid4())
        
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        mock_db.refresh.return_value = None
        
        with patch('app.services.db_service.MatchResult') as mock_result_class:
            mock_result_class.return_value = mock_result
            
            result = create_match_result(mock_db, result_data)
            
            assert result == mock_result
            mock_result_class.assert_called_once_with(**result_data)
    
    def test_get_user_match_results_with_status_filter(self, mock_db):
        """测试获取用户匹配结果带状态过滤"""
        user_id = str(uuid.uuid4())
        status = "matched"
        mock_results = [Mock(spec=MatchResult), Mock(spec=MatchResult)]
        
        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_results
        mock_db.query.return_value = mock_query
        
        result = get_user_match_results(mock_db, user_id, status=status)
        
        assert result == mock_results
        # 验证调用了filter两次（用户ID和状态）
        assert mock_query.filter.call_count == 2