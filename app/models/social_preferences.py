"""
社交场景偏好设置模型
"""

from sqlalchemy import Column, Integer, String, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from typing import Optional, List, Dict
import json

Base = declarative_base()

class SocialPreference(Base):
    """社交场景用户偏好设置"""
    
    __tablename__ = "social_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    
    # 社交目的
    social_purposes = Column(JSON, default=list)  # List[SocialPurpose]
    
    # 专业背景
    current_industry = Column(String(50), nullable=True)
    target_industries = Column(JSON, default=list)  # List[str]
    professional_level = Column(String(20), nullable=True)
    company_size_preference = Column(JSON, default=list)  # List[CompanySize]
    
    # 兴趣领域
    social_interests = Column(JSON, default=list)  # List[SocialInterest]
    skills_to_offer = Column(JSON, default=list)  # List[str]
    skills_to_learn = Column(JSON, default=list)  # List[str]
    
    # 活动偏好
    preferred_activities = Column(JSON, default=list)  # List[SocialActivity]
    preferred_meeting_formats = Column(JSON, default=list)  # ['online', 'offline', 'hybrid']
    
    # 连接偏好
    preferred_connection_types = Column(JSON, default=list)  # List[ConnectionType]
    experience_level_preference = Column(JSON, default=list)  # List[ProfessionalLevel]
    
    # 时间和频率
    available_time_slots = Column(JSON, default=list)  # List[str]
    preferred_frequency = Column(String(20), nullable=True)  # 'weekly', 'monthly', 'flexible'
    
    # 地理位置
    preferred_locations = Column(JSON, default=list)  # List[str]
    remote_preference = Column(Boolean, default=True)
    
    # 语言偏好
    languages = Column(JSON, default=list)  # List[str]
    
    # 其他偏好
    group_size_preference = Column(String(20), nullable=True)  # '1-1', 'small_group', 'large_group'
    budget_range = Column(String(50), nullable=True)
    
    def __repr__(self):
        return f"<SocialPreference(user_id={self.user_id})>"

class SocialProfile(Base):
    """社交场景用户档案"""
    
    __tablename__ = "social_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)
    
    # 基本信息
    headline = Column(String(200), nullable=True)
    summary = Column(Text, nullable=True)
    
    # 专业信息
    current_role = Column(String(100), nullable=True)
    current_company = Column(String(100), nullable=True)
    company_size = Column(String(20), nullable=True)
    industry = Column(String(50), nullable=True)
    professional_level = Column(String(20), nullable=True)
    years_experience = Column(Integer, nullable=True)
    
    # 技能和专长
    skills = Column(JSON, default=list)  # List[str]
    expertise_areas = Column(JSON, default=list)  # List[str]
    
    # 社交信息
    social_interests = Column(JSON, default=list)  # List[SocialInterest]
    social_purposes = Column(JSON, default=list)  # List[SocialPurpose]
    
    # 可提供的价值
    value_offerings = Column(JSON, default=list)  # List[str]
    mentorship_areas = Column(JSON, default=list)  # List[str]
    
    # 学习需求
    learning_goals = Column(JSON, default=list)  # List[str]
    skill_gaps = Column(JSON, default=list)  # List[str]
    
    # 联系方式偏好
    preferred_contact_methods = Column(JSON, default=list)  # ['email', 'wechat', 'linkedin']
    
    # 活跃度
    activity_level = Column(String(20), default='moderate')  # 'low', 'moderate', 'high'
    
    def __repr__(self):
        return f"<SocialProfile(user_id={self.user_id}, role={self.current_role})>"

class SocialMatchCriteria(Base):
    """社交匹配标准"""
    
    __tablename__ = "social_match_criteria"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)
    
    # 匹配权重
    industry_weight = Column(Integer, default=3)  # 1-5
    experience_weight = Column(Integer, default=3)
    skills_weight = Column(Integer, default=4)
    interests_weight = Column(Integer, default=3)
    location_weight = Column(Integer, default=2)
    
    # 匹配偏好
    min_experience_gap = Column(Integer, default=0)
    max_experience_gap = Column(Integer, default=10)
    
    # 排除条件
    exclude_competitors = Column(Boolean, default=False)
    exclude_same_company = Column(Boolean, default=False)
    
    # 连接类型偏好
    preferred_connection_types = Column(JSON, default=list)  # List[ConnectionType]
    
    def __repr__(self):
        return f"<SocialMatchCriteria(user_id={self.user_id})>"