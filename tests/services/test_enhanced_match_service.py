import pytest
import uuid
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

from app.services.enhanced_match_service import EnhancedMatchService
from app.models.enums import MatchStatus, MatchType, UserRole, MatchScoreType
from app.models.match import Match
from app.models.user import User
from app.models.user_card import UserCard


class TestEnhancedMatchService:
    """增强匹配服务测试类"""
    
    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return Mock()
    
    @pytest.fixture
    def sample_user_id(self):
        """示例用户ID"""
        return 12345
    
    @pytest.fixture
    def sample_target_user_id(self):
        """示例目标用户ID"""
        return 67890
    
    @pytest.fixture
    def sample_match_data(self):
        """示例匹配数据"""
        return {
            "user_id": 12345,
            "target_user_id": 67890,
            "match_type": MatchType.SOCIAL,
            "status": MatchStatus.PENDING,
            "score": 85.5,
            "score_breakdown": {
                "industry_match": 90,
                "skill_match": 80,
                "experience_match": 85,
                "location_match": 95,
                "interest_match": 75
            },
            "metadata": {
                "match_reason": "行业和经验匹配",
                "common_skills": ["Python", "JavaScript"],
                "common_interests": ["技术", "创业"]
            }
        }
    
    @pytest.fixture
    def sample_user_data(self):
        """示例用户数据"""
        return {
            "id": 12345,
            "openid": "test_openid_12345",
            "phone": "13800138000",
            "nickname": "测试用户",
            "avatar_url": "https://example.com/avatar.jpg",
            "role": UserRole.USER,
            "status": "active",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
    
    @pytest.fixture
    def sample_match(self):
        """示例匹配对象"""
        match = Mock(spec=Match)
        match.id = uuid.uuid4()
        match.user_id = 12345
        match.target_user_id = 67890
        match.match_type = MatchType.SOCIAL
        match.status = MatchStatus.PENDING
        match.score = 85.5
        match.score_breakdown = {
            "industry_match": 90,
            "skill_match": 80,
            "experience_match": 85,
            "location_match": 95,
            "interest_match": 75
        }
        match.metadata = {
            "match_reason": "行业和经验匹配",
            "common_skills": ["Python", "JavaScript"],
            "common_interests": ["技术", "创业"]
        }
        match.created_at = datetime.now()
        match.updated_at = datetime.now()
        return match
    
    @pytest.fixture
    def sample_user(self):
        """示例用户对象"""
        user = Mock(spec=User)
        user.id = 12345
        user.openid = "test_openid_12345"
        user.phone = "13800138000"
        user.nickname = "测试用户"
        user.avatar_url = "https://example.com/avatar.jpg"
        user.role = UserRole.USER
        user.status = "active"
        user.created_at = datetime.now()
        user.updated_at = datetime.now()
        return user
    
    @pytest.fixture
    def sample_user_card(self):
        """示例用户卡片对象"""
        card = Mock(spec=UserCard)
        card.id = uuid.uuid4()
        card.user_id = 12345
        card.card_type = "professional"
        card.card_data = {
            "industry": "互联网",
            "skills": ["Python", "JavaScript", "机器学习"],
            "experience_years": 5,
            "location": "北京",
            "interests": ["技术", "创业", "产品设计"]
        }
        card.is_active = True
        card.created_at = datetime.now()
        card.updated_at = datetime.now()
        return card
    
    def test_create_enhanced_match_success(self, mock_db, sample_match_data):
        """测试创建增强匹配成功"""
        # 创建服务实例
        service = EnhancedMatchService(mock_db)
        
        # 创建匹配
        result = service.create_enhanced_match(**sample_match_data)
        
        # 验证数据库操作
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        
        # 验证结果类型
        assert isinstance(result, Match)
    
    def test_create_enhanced_match_with_detailed_scores(self, mock_db, sample_match_data):
        """测试创建带详细评分的增强匹配"""
        # 创建服务实例
        service = EnhancedMatchService(mock_db)
        
        # 添加详细的评分数据
        sample_match_data['score_breakdown'] = {
            "industry_match": 95,
            "skill_match": 88,
            "experience_match": 92,
            "location_match": 98,
            "interest_match": 85,
            "education_match": 90,
            "company_size_match": 87,
            "professional_level_match": 91
        }
        
        # 创建匹配
        result = service.create_enhanced_match(**sample_match_data)
        
        # 验证数据库操作
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    
    def test_get_match_by_id_success(self, mock_db, sample_match):
        """测试通过ID获取匹配成功"""
        # 创建服务实例
        service = EnhancedMatchService(mock_db)
        
        # 模拟数据库查询
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_match
        mock_db.query.return_value = mock_query
        
        # 获取匹配
        result = service.get_match_by_id(sample_match.id)
        
        # 验证结果
        assert result == sample_match
    
    def test_get_match_by_id_not_found(self, mock_db):
        """测试通过ID获取匹配（未找到）"""
        # 创建服务实例
        service = EnhancedMatchService(mock_db)
        
        # 模拟数据库查询返回None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # 获取匹配
        result = service.get_match_by_id(uuid.uuid4())
        
        # 验证结果
        assert result is None
    
    def test_get_user_matches_success(self, mock_db, sample_user_id, sample_match):
        """测试获取用户匹配成功"""
        # 创建服务实例
        service = EnhancedMatchService(mock_db)
        
        # 模拟数据库查询
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [sample_match]
        mock_db.query.return_value = mock_query
        
        # 获取用户匹配
        result = service.get_user_matches(sample_user_id)
        
        # 验证结果
        assert len(result) == 1
        assert result[0] == sample_match
    
    def test_get_user_matches_by_type(self, mock_db, sample_user_id, sample_match):
        """测试按类型获取用户匹配"""
        # 创建服务实例
        service = EnhancedMatchService(mock_db)
        
        # 模拟数据库查询
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [sample_match]
        mock_db.query.return_value = mock_query
        
        # 获取特定类型的匹配
        result = service.get_user_matches(sample_user_id, match_type=MatchType.SOCIAL)
        
        # 验证结果
        assert len(result) == 1
        assert result[0].match_type == MatchType.SOCIAL
    
    def test_get_user_matches_by_status(self, mock_db, sample_user_id, sample_match):
        """测试按状态获取用户匹配"""
        # 创建服务实例
        service = EnhancedMatchService(mock_db)
        
        # 模拟数据库查询
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [sample_match]
        mock_db.query.return_value = mock_query
        
        # 获取特定状态的匹配
        result = service.get_user_matches(sample_user_id, status=MatchStatus.PENDING)
        
        # 验证结果
        assert len(result) == 1
        assert result[0].status == MatchStatus.PENDING
    
    def test_get_user_matches_with_limit(self, mock_db, sample_user_id, sample_match):
        """测试获取用户匹配（限制数量）"""
        # 创建服务实例
        service = EnhancedMatchService(mock_db)
        
        # 模拟数据库查询
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_match]
        mock_db.query.return_value = mock_query
        
        # 获取有限数量的匹配
        result = service.get_user_matches(sample_user_id, limit=5)
        
        # 验证结果
        assert len(result) == 1
    
    def test_update_match_status_success(self, mock_db, sample_match):
        """测试更新匹配状态成功"""
        # 创建服务实例
        service = EnhancedMatchService(mock_db)
        
        # 模拟数据库查询
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_match
        mock_db.query.return_value = mock_query
        
        # 更新匹配状态
        result = service.update_match_status(sample_match.id, MatchStatus.ACCEPTED)
        
        # 验证数据库操作
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        
        # 验证状态更新
        assert sample_match.status == MatchStatus.ACCEPTED
        assert result == sample_match
    
    def test_update_match_status_not_found(self, mock_db):
        """测试更新匹配状态（未找到）"""
        # 创建服务实例
        service = EnhancedMatchService(mock_db)
        
        # 模拟数据库查询返回None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # 更新匹配状态
        result = service.update_match_status(uuid.uuid4(), MatchStatus.ACCEPTED)
        
        # 验证结果
        assert result is None
    
    def test_delete_match_success(self, mock_db, sample_match):
        """测试删除匹配成功"""
        # 创建服务实例
        service = EnhancedMatchService(mock_db)
        
        # 模拟数据库查询
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_match
        mock_db.query.return_value = mock_query
        
        # 删除匹配
        result = service.delete_match(sample_match.id)
        
        # 验证数据库操作
        mock_db.delete.assert_called_once()
        mock_db.commit.assert_called_once()
        
        # 验证结果
        assert result is True
    
    def test_delete_match_not_found(self, mock_db):
        """测试删除匹配（未找到）"""
        # 创建服务实例
        service = EnhancedMatchService(mock_db)
        
        # 模拟数据库查询返回None
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # 删除匹配
        result = service.delete_match(uuid.uuid4())
        
        # 验证结果
        assert result is False
    
    def test_calculate_match_score_perfect_match(self, mock_db, sample_user_id, sample_target_user_id):
        """测试计算匹配分数（完美匹配）"""
        # 创建服务实例
        service = EnhancedMatchService(mock_db)
        
        # 创建用户卡片数据
        user_card_data = {
            "industry": "互联网",
            "skills": ["Python", "JavaScript", "机器学习"],
            "experience_years": 5,
            "location": "北京",
            "interests": ["技术", "创业", "产品设计"],
            "education_level": "本科",
            "company_size": "startup",
            "professional_level": "senior"
        }
        
        target_card_data = {
            "industry": "互联网",
            "skills": ["Python", "JavaScript", "深度学习"],
            "experience_years": 6,
            "location": "北京",
            "interests": ["技术", "创业", "AI研究"],
            "education_level": "本科",
            "company_size": "startup",
            "professional_level": "senior"
        }
        
        # 计算匹配分数
        score, breakdown = service.calculate_match_score(user_card_data, target_card_data)
        
        # 验证高分
        assert score > 80  # 应该接近满分
        assert len(breakdown) > 0  # 应该有详细的评分
    
    def test_calculate_match_score_no_match(self, mock_db, sample_user_id, sample_target_user_id):
        """测试计算匹配分数（无匹配）"""
        # 创建服务实例
        service = EnhancedMatchService(mock_db)
        
        # 创建完全不匹配的用户卡片数据
        user_card_data = {
            "industry": "互联网",
            "skills": ["Python", "JavaScript"],
            "experience_years": 5,
            "location": "北京",
            "interests": ["技术", "创业"]
        }
        
        target_card_data = {
            "industry": "制造业",
            "skills": ["机械设计", "CAD"],
            "experience_years": 15,
            "location": "上海",
            "interests": ["机械", "制造"]
        }
        
        # 计算匹配分数
        score, breakdown = service.calculate_match_score(user_card_data, target_card_data)
        
        # 验证低分
        assert score < 30  # 应该很低
        assert len(breakdown) > 0  # 应该有详细的评分
    
    def test_calculate_match_score_partial_match(self, mock_db, sample_user_id, sample_target_user_id):
        """测试计算匹配分数（部分匹配）"""
        # 创建服务实例
        service = EnhancedMatchService(mock_db)
        
        # 创建部分匹配的用户卡片数据
        user_card_data = {
            "industry": "互联网",
            "skills": ["Python", "JavaScript", "数据分析"],
            "experience_years": 5,
            "location": "北京",
            "interests": ["技术", "创业", "数据分析"]
        }
        
        target_card_data = {
            "industry": "金融",
            "skills": ["数据分析", "R语言", "统计学"],
            "experience_years": 4,
            "location": "北京",
            "interests": ["数据分析", "金融", "统计学"]
        }
        
        # 计算匹配分数
        score, breakdown = service.calculate_match_score(user_card_data, target_card_data)
        
        # 验证中等分数
        assert 40 <= score <= 80  # 应该在中等范围
        assert len(breakdown) > 0  # 应该有详细的评分
    
    def test_find_best_matches_success(self, mock_db, sample_user_id, sample_user_card, sample_match):
        """测试查找最佳匹配成功"""
        # 创建服务实例
        service = EnhancedMatchService(mock_db)
        
        # 模拟用户卡片查询
        mock_card_query = Mock()
        mock_card_query.filter.return_value = mock_card_query
        mock_card_query.first.return_value = sample_user_card
        
        # 模拟匹配查询
        mock_match_query = Mock()
        mock_match_query.filter.return_value = mock_match_query
        mock_match_query.filter.return_value = mock_match_query
        mock_match_query.order_by.return_value = mock_match_query
        mock_match_query.limit.return_value = mock_match_query
        mock_match_query.all.return_value = [sample_match]
        
        # 设置不同的查询返回
        mock_db.query.side_effect = [
            mock_card_query,  # user card query
            mock_match_query  # matches query
        ]
        
        # 查找最佳匹配
        result = service.find_best_matches(sample_user_id, limit=5)
        
        # 验证结果
        assert len(result) == 1
        assert result[0] == sample_match
    
    def test_find_best_matches_no_user_card(self, mock_db, sample_user_id):
        """测试查找最佳匹配（无用户卡片）"""
        # 创建服务实例
        service = EnhancedMatchService(mock_db)
        
        # 模拟用户卡片查询返回None
        mock_card_query = Mock()
        mock_card_query.filter.return_value = mock_card_query
        mock_card_query.first.return_value = None
        mock_db.query.return_value = mock_card_query
        
        # 查找最佳匹配
        result = service.find_best_matches(sample_user_id, limit=5)
        
        # 验证结果
        assert result == []
    
    def test_find_best_matches_no_matches(self, mock_db, sample_user_id, sample_user_card):
        """测试查找最佳匹配（无匹配）"""
        # 创建服务实例
        service = EnhancedMatchService(mock_db)
        
        # 模拟用户卡片查询
        mock_card_query = Mock()
        mock_card_query.filter.return_value = mock_card_query
        mock_card_query.first.return_value = sample_user_card
        
        # 模拟匹配查询返回空结果
        mock_match_query = Mock()
        mock_match_query.filter.return_value = mock_match_query
        mock_match_query.filter.return_value = mock_match_query
        mock_match_query.order_by.return_value = mock_match_query
        mock_match_query.limit.return_value = mock_match_query
        mock_match_query.all.return_value = []
        
        # 设置不同的查询返回
        mock_db.query.side_effect = [
            mock_card_query,  # user card query
            mock_match_query  # matches query
        ]
        
        # 查找最佳匹配
        result = service.find_best_matches(sample_user_id, limit=5)
        
        # 验证结果
        assert result == []
    
    def test_get_match_statistics_success(self, mock_db, sample_user_id, sample_match):
        """测试获取匹配统计成功"""
        # 创建服务实例
        service = EnhancedMatchService(mock_db)
        
        # 模拟数据库查询
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 10  # 总匹配数
        mock_query.count.return_value = 5   # 待处理匹配数
        mock_query.count.return_value = 3   # 已接受匹配数
        mock_query.count.return_value = 2   # 已拒绝匹配数
        
        # 设置不同的查询返回
        mock_db.query.side_effect = [
            mock_query,  # total count
            mock_query,  # pending count
            mock_query,  # accepted count
            mock_query   # rejected count
        ]
        
        # 获取匹配统计
        result = service.get_match_statistics(sample_user_id)
        
        # 验证结果
        assert result['total_matches'] == 10
        assert result['pending_matches'] == 5
        assert result['accepted_matches'] == 3
        assert result['rejected_matches'] == 2
    
    def test_get_match_statistics_no_matches(self, mock_db, sample_user_id):
        """测试获取匹配统计（无匹配）"""
        # 创建服务实例
        service = EnhancedMatchService(mock_db)
        
        # 模拟数据库查询返回0
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        
        # 设置不同的查询返回
        mock_db.query.side_effect = [
            mock_query,  # total count
            mock_query,  # pending count
            mock_query,  # accepted count
            mock_query   # rejected count
        ]
        
        # 获取匹配统计
        result = service.get_match_statistics(sample_user_id)
        
        # 验证结果
        assert result['total_matches'] == 0
        assert result['pending_matches'] == 0
        assert result['accepted_matches'] == 0
        assert result['rejected_matches'] == 0
    
    def test_get_recent_matches_success(self, mock_db, sample_user_id, sample_match):
        """测试获取最近匹配成功"""
        # 创建服务实例
        service = EnhancedMatchService(mock_db)
        
        # 模拟数据库查询
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_match]
        mock_db.query.return_value = mock_query
        
        # 获取最近匹配
        result = service.get_recent_matches(sample_user_id, days=7, limit=10)
        
        # 验证结果
        assert len(result) == 1
        assert result[0] == sample_match
    
    def test_get_recent_matches_no_recent_matches(self, mock_db, sample_user_id):
        """测试获取最近匹配（无最近匹配）"""
        # 创建服务实例
        service = EnhancedMatchService(mock_db)
        
        # 模拟数据库查询返回空结果
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query
        
        # 获取最近匹配
        result = service.get_recent_matches(sample_user_id, days=7, limit=10)
        
        # 验证结果
        assert result == []