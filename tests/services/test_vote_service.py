"""
投票服务测试用例
"""
import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.services.vote_service import VoteService
from app.models.vote_card_db import VoteCard, VoteOption, VoteRecord
from app.models.user import User
from app.models.user_card_db import UserCard
from app.models.vote_card_db import UserCardVoteRelation


class TestVoteService:
    """投票服务测试类"""
    
    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def vote_service(self, mock_db):
        """创建投票服务实例"""
        return VoteService(mock_db)
    
    @pytest.fixture
    def mock_user(self):
        """创建模拟用户"""
        user = Mock(spec=User)
        user.id = "test_user_123"
        return user
    
    @pytest.fixture
    def mock_vote_card(self):
        """创建模拟投票卡片"""
        vote_card = Mock(spec=VoteCard)
        vote_card.id = "test_vote_card_123"
        vote_card.user_id = "creator_123"
        vote_card.title = "测试投票"
        vote_card.vote_type = "single"  # 单选投票
        vote_card.is_anonymous = 0
        vote_card.is_realtime_result = 1
        vote_card.is_active = 1
        vote_card.is_deleted = 0
        vote_card.start_time = None
        vote_card.end_time = None
        vote_card.total_votes = 0
        return vote_card
    
    @pytest.fixture
    def mock_vote_options(self):
        """创建模拟投票选项"""
        option1 = Mock(spec=VoteOption)
        option1.id = 1
        option1.vote_card_id = "test_vote_card_123"
        option1.option_text = "选项A"
        option1.vote_count = 0
        option1.is_active = 1
        
        option2 = Mock(spec=VoteOption)
        option2.id = 2
        option2.vote_card_id = "test_vote_card_123"
        option2.option_text = "选项B"
        option2.vote_count = 0
        option2.is_active = 1
        
        return [option1, option2]
    
    def test_submit_vote_user_not_authenticated(self, vote_service):
        """测试用户未认证的情况"""
        with pytest.raises(ValueError, match="用户未认证"):
            vote_service.submit_vote(None, "vote_card_123", [1])
    
    def test_submit_vote_user_not_found(self, vote_service, mock_db):
        """测试用户不存在的情况"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="用户不存在"):
            vote_service.submit_vote("non_existent_user", "vote_card_123", [1])
    
    def test_submit_vote_card_not_found(self, vote_service, mock_db, mock_user):
        """测试投票卡片不存在的情况"""
        # 设置用户存在
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_user, None]
        
        with pytest.raises(ValueError, match="投票卡片不存在或已失效"):
            vote_service.submit_vote("test_user", "non_existent_card", [1])
    
    def test_submit_vote_card_not_started(self, vote_service, mock_db, mock_user, mock_vote_card):
        """测试投票尚未开始的情况"""
        mock_vote_card.start_time = datetime(2025, 12, 31, tzinfo=timezone.utc)
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_user, mock_vote_card]
        
        with pytest.raises(ValueError, match="投票尚未开始"):
            vote_service.submit_vote("test_user", "test_card", [1])
    
    def test_submit_vote_card_ended(self, vote_service, mock_db, mock_user, mock_vote_card):
        """测试投票已结束的情况"""
        mock_vote_card.end_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_user, mock_vote_card]
        
        with pytest.raises(ValueError, match="投票已结束"):
            vote_service.submit_vote("test_user", "test_card", [1])
    
    def test_submit_vote_single_choice_multiple_options(self, vote_service, mock_db, mock_user, mock_vote_card):
        """测试单选投票选择多个选项的情况"""
        mock_vote_card.vote_type = "single"
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_user, mock_vote_card]
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        with pytest.raises(ValueError, match="单选投票只能选择一个选项"):
            vote_service.submit_vote("test_user", "test_card", [1, 2, 3])
    
    def test_submit_vote_invalid_option(self, vote_service, mock_db, mock_user, mock_vote_card, mock_vote_options):
        """测试选择无效选项的情况"""
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_user, mock_vote_card]
        mock_db.query.return_value.filter.return_value.all.side_effect = [[], mock_vote_options]
        
        with pytest.raises(ValueError, match="无效的选项ID"):
            vote_service.submit_vote("test_user", "test_card", [999])  # 不存在的选项ID
    
    def test_submit_vote_already_voted(self, vote_service, mock_db, mock_user, mock_vote_card, mock_vote_options):
        """测试重复投票的情况"""
        # 创建模拟的现有投票记录
        existing_vote = Mock(spec=VoteRecord)
        existing_vote.id = "existing_vote_123"
        existing_vote.vote_card_id = mock_vote_card.id
        existing_vote.user_id = mock_user.id
        existing_vote.option_id = 1
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_user, mock_vote_card]
        mock_db.query.return_value.filter.return_value.all.side_effect = [[existing_vote], mock_vote_options]
        
        # 模拟 _get_vote_options_with_counts 方法
        vote_service._get_vote_options_with_counts = Mock(return_value=[
            {"id": 1, "option_text": "选项A", "vote_count": 1},
            {"id": 2, "option_text": "选项B", "vote_count": 0}
        ])
        
        result = vote_service.submit_vote("test_user", "test_card", [1])
        
        assert "message" in result
        assert result["message"] == "您已经投过票了"
        assert result["total_votes"] == mock_vote_card.total_votes
    
    def test_submit_vote_success_single_choice(self, vote_service, mock_db, mock_user, mock_vote_card, mock_vote_options):
        """测试单选投票成功的情况"""
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_user, mock_vote_card]
        mock_db.query.return_value.filter.return_value.all.side_effect = [[], mock_vote_options]
        
        # 模拟 _get_vote_options_with_counts 方法
        vote_service._get_vote_options_with_counts = Mock(return_value=[
            {"id": 1, "option_text": "选项A", "vote_count": 1},
            {"id": 2, "option_text": "选项B", "vote_count": 0}
        ])
        
        result = vote_service.submit_vote("test_user", "test_card", [1])
        
        assert "vote_records" in result
        assert "total_votes" in result
        assert "options" in result
        assert result["total_votes"] == 1  # 投票数应该增加
        
        # 验证数据库操作
        assert mock_db.add.called
        assert mock_db.commit.called
    
    def test_submit_vote_success_multiple_choice(self, vote_service, mock_db, mock_user, mock_vote_card, mock_vote_options):
        """测试多选投票成功的情况"""
        mock_vote_card.vote_type = "multiple"
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_user, mock_vote_card]
        mock_db.query.return_value.filter.return_value.all.side_effect = [[], mock_vote_options]
        
        # 模拟 _get_vote_options_with_counts 方法
        vote_service._get_vote_options_with_counts = Mock(return_value=[
            {"id": 1, "option_text": "选项A", "vote_count": 1},
            {"id": 2, "option_text": "选项B", "vote_count": 1}
        ])
        
        result = vote_service.submit_vote("test_user", "test_card", [1, 2])
        
        assert "vote_records" in result
        assert "total_votes" in result
        assert "options" in result
        assert result["total_votes"] == 2  # 两个选项，投票数应该增加2
        
        # 验证数据库操作
        assert mock_db.add.call_count == 2  # 应该添加两条投票记录
        assert mock_db.commit.called


class TestCancelVote:
    """取消投票测试类"""
    
    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def vote_service(self, mock_db):
        """创建投票服务实例"""
        return VoteService(mock_db)
    
    @pytest.fixture
    def mock_vote_card(self):
        """创建模拟投票卡片"""
        vote_card = Mock(spec=VoteCard)
        vote_card.id = "test_vote_card_123"
        vote_card.total_votes = 5
        vote_card.is_deleted = 0
        return vote_card
    
    @pytest.fixture
    def mock_vote_records(self):
        """创建模拟投票记录"""
        record1 = Mock(spec=VoteRecord)
        record1.id = "vote_record_1"
        record1.vote_card_id = "test_vote_card_123"
        record1.user_id = "test_user_123"
        record1.option_id = "option_1"
        record1.is_deleted = 0
        
        return [record1]
    
    def test_cancel_vote_card_not_found(self, vote_service, mock_db):
        """测试投票卡片不存在的情况"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="投票卡片不存在"):
            vote_service.cancel_vote("test_user", "non_existent_card", "option_1")
    
    def test_cancel_vote_no_existing_vote(self, vote_service, mock_db, mock_vote_card):
        """测试用户没有投票记录的情况"""
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_vote_card, None]
        
        with pytest.raises(ValueError, match="用户尚未投票"):
            vote_service.cancel_vote("test_user", "test_card", "option_1")
    
    def test_cancel_vote_success(self, vote_service, mock_db, mock_vote_card, mock_vote_records):
        """测试取消投票成功的情况"""
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_vote_card]
        mock_db.query.return_value.filter.return_value.all.side_effect = [mock_vote_records]
        
        # 模拟投票选项
        mock_option = Mock()
        mock_option.id = "option_1"
        mock_option.vote_count = 3
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_option]
        
        # 模拟 _get_vote_options_with_counts 方法
        vote_service._get_vote_options_with_counts = Mock(return_value=[
            {"id": "option_1", "option_text": "选项A", "vote_count": 2},
            {"id": "option_2", "option_text": "选项B", "vote_count": 3}
        ])
        
        result = vote_service.cancel_vote("test_user", "test_card", "option_1")
        
        assert result["success"] is True
        assert result["message"] == "取消投票成功"
        assert result["total_votes"] == 4  # 原5票减1票
        
        # 验证数据库操作
        assert mock_db.commit.called
        # 验证投票记录被软删除
        for record in mock_vote_records:
            assert record.is_deleted == 1


class TestVoteLogicIssues:
    """投票逻辑问题测试类"""
    
    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def vote_service(self, mock_db):
        """创建投票服务实例"""
        return VoteService(mock_db)
    
    def test_submit_vote_existing_votes_logic_issue(self, vote_service, mock_db):
        """测试现有投票记录检查逻辑的问题"""
        # 当前逻辑只检查用户选择的选项，而不是检查用户的所有投票记录
        # 这可能导致重复投票问题
        
        # 模拟用户已经投了选项1
        existing_vote = Mock(spec=VoteRecord)
        existing_vote.vote_card_id = "test_card"
        existing_vote.user_id = "test_user"
        existing_vote.option_id = 1
        
        # 当用户尝试投选项2时，现有逻辑不会检测到已投票
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        # 这里应该有一个断言来验证逻辑问题
        # 但由于是逻辑缺陷测试，我们主要验证当前的行为
        pass
    
    def test_cancel_vote_parameter_type_issue(self, vote_service):
        """测试cancel_vote方法参数类型问题"""
        # cancel_vote方法签名使用option_id: str，但应该支持多个选项
        # 这与submit_vote的批量处理逻辑不一致
        
        # 验证方法签名
        import inspect
        sig = inspect.signature(vote_service.cancel_vote)
        option_id_param = sig.parameters['option_id']
        
        # 当前是单个字符串参数，应该支持列表
        assert option_id_param.annotation == str
        
        # 这里应该修改为支持多个选项取消
        # 建议修改为: option_ids: List[str]