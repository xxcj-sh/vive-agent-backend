"""
社交场景API路由
"""

from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database import get_db
from app.services.social_service import SocialService
from app.models.enums import (
    SocialPurpose, SocialInterest, ProfessionalLevel, 
    ConnectionType, SocialActivity
)

router = APIRouter(prefix="/api/social", tags=["social"])

# Pydantic模型定义
class SocialPreferenceCreate(BaseModel):
    social_purpose: List[SocialPurpose] = Field(..., description="社交目的")
    social_interests: List[SocialInterest] = Field(..., description="社交兴趣")
    experience_level_preference: List[ProfessionalLevel] = Field(default=[], description="经验水平偏好")
    company_size_preference: List[str] = Field(default=[], description="公司规模偏好")
    target_industries: List[str] = Field(default=[], description="目标行业")
    preferred_locations: List[str] = Field(default=[], description="偏好地点")
    skills_to_learn: List[str] = Field(default=[], description="想学习的技能")
    skills_to_share: List[str] = Field(default=[], description="可分享的技能")
    remote_preference: bool = Field(default=True, description="是否接受远程")
    activity_types: List[SocialActivity] = Field(default=[], description="活动类型")

class SocialPreferenceUpdate(BaseModel):
    social_purpose: Optional[List[SocialPurpose]] = None
    social_interests: Optional[List[SocialInterest]] = None
    experience_level_preference: Optional[List[ProfessionalLevel]] = None
    company_size_preference: Optional[List[str]] = None
    target_industries: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    skills_to_learn: Optional[List[str]] = None
    skills_to_share: Optional[List[str]] = None
    remote_preference: Optional[bool] = None
    activity_types: Optional[List[SocialActivity]] = None

class SocialProfileCreate(BaseModel):
    headline: str = Field(..., description="个人简介")
    summary: str = Field(..., description="详细描述")
    current_role: str = Field(..., description="当前职位")
    current_company: str = Field(..., description="当前公司")
    industry: str = Field(..., description="所在行业")
    professional_level: ProfessionalLevel = Field(..., description="职业水平")
    company_size: str = Field(..., description="公司规模")
    years_of_experience: int = Field(..., ge=0, description="工作经验年数")
    skills: List[str] = Field(..., description="技能列表")
    expertise_areas: List[str] = Field(default=[], description="专业领域")
    social_interests: List[SocialInterest] = Field(default=[], description="社交兴趣")
    value_offerings: List[str] = Field(default=[], description="可提供的价值")
    seeking_opportunities: List[str] = Field(default=[], description="寻求的机会")
    activity_level: str = Field(default="medium", description="活跃度")

class SocialProfileUpdate(BaseModel):
    headline: Optional[str] = None
    summary: Optional[str] = None
    current_role: Optional[str] = None
    current_company: Optional[str] = None
    industry: Optional[str] = None
    professional_level: Optional[ProfessionalLevel] = None
    company_size: Optional[str] = None
    years_of_experience: Optional[int] = None
    skills: Optional[List[str]] = None
    expertise_areas: Optional[List[str]] = None
    social_interests: Optional[List[SocialInterest]] = None
    value_offerings: Optional[List[str]] = None
    seeking_opportunities: Optional[List[str]] = None
    activity_level: Optional[str] = None

class SocialMatchCriteriaCreate(BaseModel):
    min_experience_level: Optional[ProfessionalLevel] = None
    max_experience_level: Optional[ProfessionalLevel] = None
    preferred_company_sizes: List[str] = Field(default=[], description="偏好公司规模")
    must_have_skills: List[str] = Field(default=[], description="必备技能")
    preferred_industries: List[str] = Field(default=[], description="偏好行业")
    location_radius_km: Optional[int] = Field(default=50, description="地理位置半径(公里)")
    min_mutual_connections: int = Field(default=0, description="最小共同连接数")
    activity_level_threshold: str = Field(default="medium", description="活跃度阈值")

class SocialMatchResponse(BaseModel):
    user_id: int
    headline: str
    current_role: str
    current_company: str
    industry: str
    professional_level: str
    skills: List[str]
    social_interests: List[str]
    score: float
    common_interests: List[str]
    common_skills: List[str]

class SocialAnalyticsResponse(BaseModel):
    profile_completeness: float
    skills: List[str]
    expertise_areas: List[str]
    industry_distribution: Dict[str, int]
    total_network_size: int
    activity_level: str

# API路由
@router.post("/preferences", response_model=dict)
async def create_social_preference(
    user_id: int,
    preference: SocialPreferenceCreate,
    db: Session = Depends(get_db)
):
    """创建社交偏好设置"""
    service = SocialService(db)
    result = service.create_social_preference(user_id, preference.dict())
    return {"success": True, "data": result}

@router.put("/preferences", response_model=dict)
async def update_social_preference(
    user_id: int,
    preference: SocialPreferenceUpdate,
    db: Session = Depends(get_db)
):
    """更新社交偏好设置"""
    service = SocialService(db)
    update_data = {k: v for k, v in preference.dict().items() if v is not None}
    result = service.update_social_preference(user_id, update_data)
    return {"success": True, "data": result}

@router.get("/preferences", response_model=dict)
async def get_social_preference(
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取社交偏好设置"""
    from app.models.social_preferences import SocialPreference
    
    preference = db.query(SocialPreference).filter(
        SocialPreference.user_id == user_id
    ).first()
    
    if not preference:
        raise HTTPException(status_code=404, detail="Preference not found")
    
    return {"success": True, "data": preference}

@router.post("/profile", response_model=dict)
async def create_social_profile(
    user_id: int,
    profile: SocialProfileCreate,
    db: Session = Depends(get_db)
):
    """创建社交档案"""
    service = SocialService(db)
    result = service.create_social_profile(user_id, profile.dict())
    return {"success": True, "data": result}

@router.put("/profile", response_model=dict)
async def update_social_profile(
    user_id: int,
    profile: SocialProfileUpdate,
    db: Session = Depends(get_db)
):
    """更新社交档案"""
    service = SocialService(db)
    update_data = {k: v for k, v in profile.dict().items() if v is not None}
    result = service.update_social_profile(user_id, update_data)
    return {"success": True, "data": result}

@router.get("/profile", response_model=dict)
async def get_social_profile(
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取社交档案"""
    from app.models.social_preferences import SocialProfile
    
    profile = db.query(SocialProfile).filter(
        SocialProfile.user_id == user_id
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return {"success": True, "data": profile}

@router.post("/match-criteria", response_model=dict)
async def create_match_criteria(
    user_id: int,
    criteria: SocialMatchCriteriaCreate,
    db: Session = Depends(get_db)
):
    """创建匹配标准"""
    service = SocialService(db)
    result = service.create_match_criteria(user_id, criteria.dict())
    return {"success": True, "data": result}

@router.get("/matches", response_model=dict)
async def get_social_matches(
    user_id: int,
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """获取社交匹配推荐"""
    service = SocialService(db)
    matches = service.get_social_matches(user_id, limit)
    
    # 格式化响应
    formatted_matches = []
    for match in matches:
        profile = match['profile']
        formatted_matches.append(SocialMatchResponse(
            user_id=profile.user_id,
            headline=profile.headline,
            current_role=profile.current_role,
            current_company=profile.current_company,
            industry=profile.industry,
            professional_level=profile.professional_level,
            skills=profile.skills or [],
            social_interests=profile.social_interests or [],
            score=match['score'],
            common_interests=match['common_interests'],
            common_skills=match['common_skills']
        ))
    
    return {"success": True, "data": formatted_matches}

@router.get("/analytics", response_model=dict)
async def get_social_analytics(
    user_id: int,
    db: Session = Depends(get_db)
):
    """获取社交分析数据"""
    service = SocialService(db)
    analytics = service.get_social_analytics(user_id)
    
    if not analytics:
        raise HTTPException(status_code=404, detail="Analytics not available")
    
    return {"success": True, "data": SocialAnalyticsResponse(**analytics)}

@router.get("/enums", response_model=dict)
async def get_social_enums():
    """获取社交场景相关枚举值"""
    return {
        "social_purpose": [e.value for e in SocialPurpose],
        "social_interest": [e.value for e in SocialInterest],
        "professional_level": [e.value for e in ProfessionalLevel],
        "connection_type": [e.value for e in ConnectionType],
        "social_activity": [e.value for e in SocialActivity]
    }

@router.get("/search", response_model=dict)
async def search_social_profiles(
    keyword: str = Query(..., min_length=2),
    industry: Optional[str] = None,
    location: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """搜索社交档案"""
    from app.models.social_preferences import SocialProfile
    from sqlalchemy import or_
    
    query = db.query(SocialProfile)
    
    # 关键词搜索
    keyword_filter = or_(
        SocialProfile.headline.contains(keyword),
        SocialProfile.summary.contains(keyword),
        SocialProfile.current_role.contains(keyword),
        SocialProfile.current_company.contains(keyword),
        SocialProfile.skills.contains(keyword)
    )
    query = query.filter(keyword_filter)
    
    # 行业过滤
    if industry:
        query = query.filter(SocialProfile.industry == industry)
    
    # 地点过滤
    if location:
        query = query.filter(SocialProfile.current_company.contains(location))
    
    profiles = query.limit(limit).all()
    
    return {
        "success": True,
        "data": profiles,
        "total": len(profiles)
    }