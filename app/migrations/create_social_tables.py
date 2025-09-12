"""
社交场景数据库表创建脚本
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import sys

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.config import settings

Base = declarative_base()

class SocialPreference(Base):
    __tablename__ = 'social_preferences'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, nullable=False, index=True)
    social_purpose = Column(JSON, default=list)  # List[SocialPurpose]
    social_interests = Column(JSON, default=list)  # List[SocialInterest]
    experience_level_preference = Column(JSON, default=list)  # List[ProfessionalLevel]
    company_size_preference = Column(JSON, default=list)  # List[str]
    target_industries = Column(JSON, default=list)  # List[str]
    preferred_locations = Column(JSON, default=list)  # List[str]
    skills_to_learn = Column(JSON, default=list)  # List[str]
    skills_to_share = Column(JSON, default=list)  # List[str]
    remote_preference = Column(Boolean, default=True)
    activity_types = Column(JSON, default=list)  # List[SocialActivity]
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SocialProfile(Base):
    __tablename__ = 'social_profiles'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, nullable=False, index=True)
    headline = Column(String(200), nullable=False)
    summary = Column(Text, nullable=False)
    current_role = Column(String(100), nullable=False)
    current_company = Column(String(100), nullable=False)
    industry = Column(String(50), nullable=False)
    professional_level = Column(String(20), nullable=False)
    company_size = Column(String(20), nullable=False)
    years_of_experience = Column(Integer, nullable=False)
    skills = Column(JSON, default=list)  # List[str]
    expertise_areas = Column(JSON, default=list)  # List[str]
    social_interests = Column(JSON, default=list)  # List[SocialInterest]
    value_offerings = Column(JSON, default=list)  # List[str]
    seeking_opportunities = Column(JSON, default=list)  # List[str]
    activity_level = Column(String(20), default="medium")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SocialMatchCriteria(Base):
    __tablename__ = 'social_match_criteria'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, nullable=False, index=True)
    min_experience_level = Column(String(20), nullable=True)
    max_experience_level = Column(String(20), nullable=True)
    preferred_company_sizes = Column(JSON, default=list)  # List[str]
    must_have_skills = Column(JSON, default=list)  # List[str]
    preferred_industries = Column(JSON, default=list)  # List[str]
    location_radius_km = Column(Integer, default=50)
    min_mutual_connections = Column(Integer, default=0)
    activity_level_threshold = Column(String(20), default="medium")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def create_tables():
    """创建社交场景相关数据库表"""
    
    # 创建数据库引擎
    engine = create_engine(settings.DATABASE_URL)
    
    # 创建所有表
    Base.metadata.create_all(engine)
    
    print("✅ 社交场景数据库表创建成功!")
    print("创建的数据表:")
    print("- social_preferences: 社交偏好设置")
    print("- social_profiles: 社交档案")
    print("- social_match_criteria: 社交匹配标准")

if __name__ == "__main__":
    create_tables()