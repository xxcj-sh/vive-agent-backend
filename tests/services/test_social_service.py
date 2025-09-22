import pytest
import uuid
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from app.services.social_service import SocialService
from app.models.enums import SocialPurpose, SocialInterest, ProfessionalLevel
from app.models.social_preferences import SocialPreference, SocialProfile, SocialMatchCriteria


class TestSocialService:
    """社交服务测试类"""
    
    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return Mock()
    
    @pytest.fixture
    def sample_user_id(self):
        """示例用户ID"""
        return 12345
    
    @pytest.fixture
    def sample_social_preference_data(self):
        """示例社交偏好数据"""
        return {
            "social_purpose": [SocialPurpose.NETWORKING, SocialPurpose.CAREER_DEVELOPMENT],
            "social_interests": [SocialInterest.TECHNOLOGY, SocialInterest.BUSINESS],
            "target_industries": ["互联网", "金融"],
            "experience_level_preference": [ProfessionalLevel.SENIOR, ProfessionalLevel.EXPERT],
            "company_size_preference": ["startup", "large"],
            "preferred_locations": ["北京", "上海"],
            "skills_to_learn": ["AI/ML", "产品设计"],
            "value_offerings": ["技术咨询", "项目管理"]
        }
    
    @pytest.fixture
    def sample_social_profile_data(self):
        """示例社交档案数据"""
        return {
            "industry": "互联网",
            "company_size": "startup",
            "professional_level": ProfessionalLevel.SENIOR,
            "social_interests": [SocialInterest.TECHNOLOGY, SocialInterest.STARTUP],
            "skills": ["Python", "JavaScript", "产品设计"],
            "value_offerings": ["技术咨询", "代码审查"],
            "current_company": "北京",
            "years_of_experience": 5
        }
    
    @pytest.fixture
    def sample_social_preference(self):
        """示例社交偏好对象"""
        preference = Mock(spec=SocialPreference)
        preference.user_id = 12345
        preference.social_purpose = [SocialPurpose.NETWORKING]
        preference.social_interests = [SocialInterest.TECHNOLOGY]
        preference.target_industries = ["互联网"]
        preference.experience_level_preference = [ProfessionalLevel.SENIOR]
        preference.company_size_preference = ["startup"]
        preference.preferred_locations = ["北京"]
        preference.skills_to_learn = ["AI/ML"]
        preference.value_offerings = ["技术咨询"]
        return preference
    
    @pytest.fixture
    def sample_social_profile(self):
        """示例社交档案对象"""
        profile = Mock(spec=SocialProfile)
        profile.user_id = 12345
        profile.industry = "互联网"
        profile.company_size = "startup"
        profile.professional_level = ProfessionalLevel.SENIOR
        profile.social_interests = [SocialInterest.TECHNOLOGY]
        profile.skills = ["Python", "JavaScript"]
        profile.value_offerings = ["技术咨询"]
        profile.current_company = "北京"
        profile.years_of_experience = 5
        return profile
    
    def test_create_social_preference_success(self, mock_db, sample_user_id, sample_social_preference_data):
        """测试创建社交偏好成功"""
        # 创建服务实例
        service = SocialService(mock_db)
        
        # 创建偏好
        result = service.create_social_preference(sample_user_id, sample_social_preference_data)
        
        # 验证数据库操作
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        
        # 验证结果类型
        assert isinstance(result, SocialPreference)
    
    def test_update_social_preference_existing(self, mock_db, sample_user_id, sample_social_preference_data):
        """测试更新已存在的社交偏好"""
        # 创建服务实例
        service = SocialService(mock_db)
        
        # 模拟已存在的偏好
        existing_preference = Mock(spec=SocialPreference)
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = existing_preference
        mock_db.query.return_value = mock_query
        
        # 更新偏好
        result = service.update_social_preference(sample_user_id, sample_social_preference_data)
        
        # 验证数据库操作
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        
        # 验证结果
        assert result == existing_preference
    
    def test_update_social_preference_not_existing(self, mock_db, sample_user_id, sample_social_preference_data):
        """测试更新不存在的社交偏好（创建新的）"""
        # 创建服务实例
        service = SocialService(mock_db)
        
        # 模拟不存在的偏好
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # 更新偏好（会创建新的）
        result = service.update_social_preference(sample_user_id, sample_social_preference_data)
        
        # 验证创建新的偏好
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_twice()  # 一次是创建，一次是更新
        mock_db.refresh.assert_called_once()
    
    def test_create_social_profile_success(self, mock_db, sample_user_id, sample_social_profile_data):
        """测试创建社交档案成功"""
        # 创建服务实例
        service = SocialService(mock_db)
        
        # 创建档案
        result = service.create_social_profile(sample_user_id, sample_social_profile_data)
        
        # 验证数据库操作
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        
        # 验证结果类型
        assert isinstance(result, SocialProfile)
    
    def test_update_social_profile_existing(self, mock_db, sample_user_id, sample_social_profile_data):
        """测试更新已存在的社交档案"""
        # 创建服务实例
        service = SocialService(mock_db)
        
        # 模拟已存在的档案
        existing_profile = Mock(spec=SocialProfile)
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = existing_profile
        mock_db.query.return_value = mock_query
        
        # 更新档案
        result = service.update_social_profile(sample_user_id, sample_social_profile_data)
        
        # 验证数据库操作
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        
        # 验证结果
        assert result == existing_profile
    
    def test_create_match_criteria_success(self, mock_db, sample_user_id):
        """测试创建匹配标准成功"""
        # 创建服务实例
        service = SocialService(mock_db)
        
        # 匹配标准数据
        criteria_data = {
            "age_range": [25, 35],
            "location_radius": 50,
            "experience_years_range": [3, 10],
            "industry_preference": ["互联网", "金融"],
            "skill_match_weight": 0.7,
            "industry_match_weight": 0.3
        }
        
        # 创建标准
        result = service.create_match_criteria(sample_user_id, criteria_data)
        
        # 验证数据库操作
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        
        # 验证结果类型
        assert isinstance(result, SocialMatchCriteria)
    
    def test_get_social_matches_with_profile_and_preference(self, mock_db, sample_user_id, sample_social_profile, sample_social_preference):
        """测试获取社交匹配（有档案和偏好）"""
        # 创建服务实例
        service = SocialService(mock_db)
        
        # 模拟用户档案和偏好查询
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = [sample_social_profile, sample_social_preference, None]  # profile, preference, criteria
        mock_db.query.return_value = mock_query
        
        # 模拟匹配查询
        mock_matches_query = Mock()
        mock_matches_query.filter.return_value = mock_matches_query
        mock_matches_query.filter.return_value = mock_matches_query
        mock_matches_query.limit.return_value = []
        
        # 设置不同的查询返回
        mock_db.query.side_effect = [
            mock_query,  # profile query
            mock_query,  # preference query  
            mock_query,  # criteria query
            mock_matches_query  # matches query
        ]
        
        # 获取匹配
        result = service.get_social_matches(sample_user_id)
        
        # 验证结果
        assert result == []
    
    def test_get_social_matches_no_profile(self, mock_db, sample_user_id):
        """测试获取社交匹配（无档案）"""
        # 创建服务实例
        service = SocialService(mock_db)
        
        # 模拟无用户档案
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        # 获取匹配
        result = service.get_social_matches(sample_user_id)
        
        # 验证返回空列表
        assert result == []
    
    def test_get_social_matches_no_preference(self, mock_db, sample_user_id, sample_social_profile):
        """测试获取社交匹配（无偏好）"""
        # 创建服务实例
        service = SocialService(mock_db)
        
        # 模拟有档案但无偏好
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = [sample_social_profile, None]  # profile, no preference
        mock_db.query.return_value = mock_query
        
        # 获取匹配
        result = service.get_social_matches(sample_user_id)
        
        # 验证返回空列表
        assert result == []
    
    def test_calculate_social_match_score_perfect_match(self, mock_db):
        """测试计算社交匹配分数（完美匹配）"""
        # 创建服务实例
        service = SocialService(mock_db)
        
        # 创建用户档案和偏好
        user_profile = Mock()
        user_profile.industry = "互联网"
        user_profile.social_interests = [SocialInterest.TECHNOLOGY]
        user_profile.skills = ["Python", "JavaScript"]
        user_profile.professional_level = ProfessionalLevel.SENIOR
        user_profile.company_size = "startup"
        user_profile.current_company = "北京"
        user_profile.years_of_experience = 5
        
        user_preference = Mock()
        user_preference.target_industries = ["互联网"]
        user_preference.skills_to_learn = ["AI/ML"]
        user_preference.experience_level_preference = [ProfessionalLevel.SENIOR]
        user_preference.company_size_preference = ["startup"]
        user_preference.preferred_locations = ["北京"]
        
        # 创建候选档案（完美匹配）
        candidate = Mock()
        candidate.industry = "互联网"
        candidate.social_interests = [SocialInterest.TECHNOLOGY]
        candidate.skills = ["AI/ML", "Python"]
        candidate.value_offerings = ["AI/ML", "技术咨询"]
        candidate.professional_level = ProfessionalLevel.SENIOR
        candidate.company_size = "startup"
        candidate.current_company = "北京"
        candidate.years_of_experience = 7
        
        # 计算分数
        score = service._calculate_social_match_score(user_profile, user_preference, candidate)
        
        # 验证高分
        assert score > 80  # 应该接近满分
    
    def test_calculate_social_match_score_no_match(self, mock_db):
        """测试计算社交匹配分数（无匹配）"""
        # 创建服务实例
        service = SocialService(mock_db)
        
        # 创建用户档案和偏好
        user_profile = Mock()
        user_profile.industry = "互联网"
        user_profile.social_interests = [SocialInterest.TECHNOLOGY]
        user_profile.skills = ["Python"]
        user_profile.professional_level = ProfessionalLevel.SENIOR
        
        user_preference = Mock()
        user_preference.target_industries = ["互联网"]
        user_preference.skills_to_learn = ["AI/ML"]
        user_preference.experience_level_preference = [ProfessionalLevel.SENIOR]
        
        # 创建候选档案（完全不匹配）
        candidate = Mock()
        candidate.industry = "制造业"
        candidate.social_interests = [SocialInterest.ART]
        candidate.skills = ["机械设计"]
        candidate.value_offerings = ["机械维修"]
        candidate.professional_level = ProfessionalLevel.JUNIOR
        
        # 计算分数
        score = service._calculate_social_match_score(user_profile, user_preference, candidate)
        
        # 验证低分
        assert score < 30  # 应该很低
    
    def test_calculate_social_match_score_partial_match(self, mock_db):
        """测试计算社交匹配分数（部分匹配）"""
        # 创建服务实例
        service = SocialService(mock_db)
        
        # 创建用户档案和偏好
        user_profile = Mock()
        user_profile.industry = "互联网"
        user_profile.social_interests = [SocialInterest.TECHNOLOGY, SocialInterest.BUSINESS]
        user_profile.skills = ["Python", "JavaScript", "产品设计"]
        user_profile.professional_level = ProfessionalLevel.SENIOR
        
        user_preference = Mock()
        user_preference.target_industries = ["互联网", "金融"]
        user_preference.skills_to_learn = ["AI/ML", "数据分析"]
        user_preference.experience_level_preference = [ProfessionalLevel.SENIOR, ProfessionalLevel.MID]
        
        # 创建候选档案（部分匹配）
        candidate = Mock()
        candidate.industry = "金融"  # 匹配偏好
        candidate.social_interests = [SocialInterest.TECHNOLOGY]  # 部分匹配
        candidate.skills = ["数据分析", "R语言"]  # 匹配学习需求
        candidate.value_offerings = ["数据分析", "金融建模"]
        candidate.professional_level = ProfessionalLevel.MID  # 匹配偏好
        
        # 计算分数
        score = service._calculate_social_match_score(user_profile, user_preference, candidate)
        
        # 验证中等分数
        assert 40 <= score <= 80  # 应该在中等范围
    
    def test_get_social_matches_with_limit(self, mock_db, sample_user_id, sample_social_profile, sample_social_preference):
        """测试获取社交匹配带有限制数量"""
        # 创建服务实例
        service = SocialService(mock_db)
        
        # 模拟用户档案和偏好查询
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = [sample_social_profile, sample_social_preference, None]
        mock_db.query.return_value = mock_query
        
        # 模拟匹配结果
        mock_match_profile = Mock()
        mock_match_profile.user_id = 67890
        mock_match_profile.industry = "互联网"
        mock_match_profile.social_interests = [SocialInterest.TECHNOLOGY]
        mock_match_profile.skills = ["AI/ML"]
        mock_match_profile.value_offerings = ["技术咨询"]
        mock_match_profile.professional_level = ProfessionalLevel.SENIOR
        mock_match_profile.company_size = "startup"
        mock_match_profile.current_company = "北京"
        mock_match_profile.years_of_experience = 6
        
        # 模拟匹配查询返回结果
        mock_matches_query = Mock()
        mock_matches_query.filter.return_value = mock_matches_query
        mock_matches_query.filter.return_value = mock_matches_query
        mock_matches_query.limit.return_value = [mock_match_profile]
        
        mock_db.query.side_effect = [
            mock_query,  # profile query
            mock_query,  # preference query
            mock_query,  # criteria query
            mock_matches_query  # matches query
        ]
        
        # 获取匹配（限制5个）
        result = service.get_social_matches(sample_user_id, limit=5)
        
        # 验证结果
        assert len(result) == 1
        assert result[0]['profile'] == mock_match_profile
        assert 'score' in result[0]
        assert 'common_interests' in result[0]
        assert 'common_skills' in result[0]