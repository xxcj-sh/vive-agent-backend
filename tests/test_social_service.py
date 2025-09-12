"""
社交场景服务测试
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.social_preferences import SocialPreference, SocialProfile, SocialMatchCriteria
from app.services.social_service import SocialService
from app.models.enums import (
    SocialPurpose, SocialInterest, ProfessionalLevel, 
    SocialActivity
)

# 测试数据库设置
@pytest.fixture
def db_session():
    """创建测试数据库会话"""
    engine = create_engine("sqlite:///:memory:")
    from app.models.social_preferences import Base
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture
def social_service(db_session):
    """创建社交服务实例"""
    return SocialService(db_session)

class TestSocialService:
    """社交场景服务测试类"""
    
    def test_create_social_preference(self, social_service):
        """测试创建社交偏好"""
        preference_data = {
            "social_purpose": [SocialPurpose.NETWORKING, SocialPurpose.MENTORSHIP],
            "social_interests": [SocialInterest.TECHNOLOGY, SocialInterest.FINANCE],
            "experience_level_preference": [ProfessionalLevel.MID_LEVEL, ProfessionalLevel.SENIOR_LEVEL],
            "target_industries": ["Technology", "Finance"],
            "skills_to_learn": ["Python", "Machine Learning"],
            "skills_to_share": ["JavaScript", "Web Development"]
        }
        
        result = social_service.create_social_preference(1, preference_data)
        
        assert result.user_id == 1
        assert SocialPurpose.NETWORKING in result.social_purpose
        assert SocialInterest.TECHNOLOGY in result.social_interests
    
    def test_update_social_preference(self, social_service):
        """测试更新社交偏好"""
        # 先创建
        preference_data = {
            "social_purpose": [SocialPurpose.NETWORKING],
            "social_interests": [SocialInterest.TECHNOLOGY]
        }
        social_service.create_social_preference(1, preference_data)
        
        # 再更新
        update_data = {
            "social_purpose": [SocialPurpose.NETWORKING, SocialPurpose.CAREER_ADVICE],
            "skills_to_learn": ["Data Science"]
        }
        
        result = social_service.update_social_preference(1, update_data)
        
        assert len(result.social_purpose) == 2
        assert "Data Science" in result.skills_to_learn
    
    def test_create_social_profile(self, social_service):
        """测试创建社交档案"""
        profile_data = {
            "headline": "Senior Software Engineer",
            "summary": "Experienced full-stack developer",
            "current_role": "Senior Software Engineer",
            "current_company": "Tech Corp",
            "industry": "Technology",
            "professional_level": ProfessionalLevel.SENIOR_LEVEL,
            "company_size": "Large",
            "years_of_experience": 8,
            "skills": ["Python", "JavaScript", "React"],
            "social_interests": [SocialInterest.TECHNOLOGY, SocialInterest.STARTUP],
            "value_offerings": ["Mentorship", "Technical Consulting"]
        }
        
        result = social_service.create_social_profile(1, profile_data)
        
        assert result.user_id == 1
        assert result.headline == "Senior Software Engineer"
        assert ProfessionalLevel.SENIOR_LEVEL == result.professional_level
    
    def test_update_social_profile(self, social_service):
        """测试更新社交档案"""
        # 先创建
        profile_data = {
            "headline": "Software Engineer",
            "summary": "Developer",
            "current_role": "Software Engineer",
            "current_company": "Company",
            "industry": "Tech",
            "professional_level": ProfessionalLevel.MID_LEVEL,
            "company_size": "Medium",
            "years_of_experience": 5,
            "skills": ["Python"]
        }
        social_service.create_social_profile(1, profile_data)
        
        # 再更新
        update_data = {
            "headline": "Senior Software Engineer",
            "skills": ["Python", "JavaScript"]
        }
        
        result = social_service.update_social_profile(1, update_data)
        
        assert result.headline == "Senior Software Engineer"
        assert len(result.skills) == 2
    
    def test_create_match_criteria(self, social_service):
        """测试创建匹配标准"""
        criteria_data = {
            "preferred_company_sizes": ["Large", "Medium"],
            "must_have_skills": ["Python", "JavaScript"],
            "preferred_industries": ["Technology", "Finance"],
            "min_mutual_connections": 2
        }
        
        result = social_service.create_match_criteria(1, criteria_data)
        
        assert result.user_id == 1
        assert "Python" in result.must_have_skills
    
    def test_calculate_social_match_score(self, social_service):
        """测试社交匹配分数计算"""
        # 创建用户档案
        user_profile_data = {
            "headline": "Senior Developer",
            "summary": "Tech lead",
            "current_role": "Tech Lead",
            "current_company": "Company A",
            "industry": "Technology",
            "professional_level": ProfessionalLevel.SENIOR_LEVEL,
            "company_size": "Large",
            "years_of_experience": 10,
            "skills": ["Python", "Leadership"],
            "social_interests": [SocialInterest.TECHNOLOGY]
        }
        
        candidate_data = {
            "headline": "Mid-level Developer",
            "summary": "Python specialist",
            "current_role": "Python Developer",
            "current_company": "Company B",
            "industry": "Technology",
            "professional_level": ProfessionalLevel.MID_LEVEL,
            "company_size": "Medium",
            "years_of_experience": 5,
            "skills": ["Python", "Django"],
            "social_interests": [SocialInterest.TECHNOLOGY]
        }
        
        user_profile = social_service.create_social_profile(1, user_profile_data)
        candidate = social_service.create_social_profile(2, candidate_data)
        
        # 创建用户偏好
        preference_data = {
            "social_purpose": [SocialPurpose.MENTORSHIP],
            "social_interests": [SocialInterest.TECHNOLOGY],
            "skills_to_learn": ["Django"],
            "skills_to_share": ["Leadership"]
        }
        user_preference = social_service.create_social_preference(1, preference_data)
        
        # 计算匹配分数
        score = social_service._calculate_social_match_score(
            user_profile, user_preference, candidate
        )
        
        assert 0 <= score <= 100
        assert score > 50  # 应该有较高的匹配度
    
    def test_get_social_analytics(self, social_service):
        """测试获取社交分析数据"""
        # 创建档案
        profile_data = {
            "headline": "Full Stack Developer",
            "summary": "Experienced developer",
            "current_role": "Full Stack Developer",
            "current_company": "Startup Inc",
            "industry": "Technology",
            "professional_level": ProfessionalLevel.MID_LEVEL,
            "company_size": "Startup",
            "years_of_experience": 6,
            "skills": ["Python", "JavaScript", "React"],
            "social_interests": [SocialInterest.TECHNOLOGY, SocialInterest.STARTUP]
        }
        
        social_service.create_social_profile(1, profile_data)
        
        analytics = social_service.get_social_analytics(1)
        
        assert "profile_completeness" in analytics
        assert "skills" in analytics
        assert isinstance(analytics["profile_completeness"], float)
    
    def test_profile_completeness_calculation(self, social_service):
        """测试档案完整度计算"""
        # 创建部分完成的档案
        profile_data = {
            "headline": "Developer",
            "summary": "Summary",
            "current_role": "Role",
            "current_company": "Company",
            "industry": "Tech",
            "professional_level": ProfessionalLevel.MID_LEVEL,
            "company_size": "Medium",
            "years_of_experience": 5,
            "skills": ["Python"]
        }
        
        profile = social_service.create_social_profile(1, profile_data)
        completeness = social_service._calculate_profile_completeness(profile)
        
        assert 0 <= completeness <= 100
        assert completeness > 50  # 至少完成了基本字段