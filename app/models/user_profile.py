from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

# 用户角色资料相关模型
class UserProfileBase(BaseModel):
    """用户角色资料基础模型"""
    role_type: str = Field(..., description="角色类型")
    scene_type: str = Field(..., description="场景类型")
    display_name: str = Field(..., description="显示名称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    bio: Optional[str] = Field(None, description="个人简介")
    profile_data: Optional[Dict[str, Any]] = Field(None, description="角色特定数据")
    preferences: Optional[Dict[str, Any]] = Field(None, description="偏好设置")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    visibility: Optional[str] = Field("public", description="可见性")

class UserProfileCreate(UserProfileBase):
    """创建用户角色资料模型"""
    pass

class UserProfileUpdate(BaseModel):
    """更新用户角色资料模型"""
    display_name: Optional[str] = Field(None, description="显示名称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    bio: Optional[str] = Field(None, description="个人简介")
    profile_data: Optional[Dict[str, Any]] = Field(None, description="角色特定数据")
    preferences: Optional[Dict[str, Any]] = Field(None, description="偏好设置")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    visibility: Optional[str] = Field(None, description="可见性")
    is_active: Optional[int] = Field(None, description="是否激活")

class UserProfile(UserProfileBase):
    """用户角色资料响应模型"""
    id: str = Field(..., description="资料ID")
    user_id: str = Field(..., description="用户ID")
    is_active: int = Field(..., description="是否激活")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

    class Config:
        from_attributes = True

class UserProfilesResponse(BaseModel):
    """用户多角色资料响应模型"""
    user_id: str = Field(..., description="用户ID")
    profiles: List[UserProfile] = Field(..., description="角色资料列表")
    active_profiles: List[UserProfile] = Field(..., description="激活的角色资料列表")
    
class UserProfilesByScene(BaseModel):
    """按场景分组的用户角色资料"""
    scene_type: str = Field(..., description="场景类型")
    profiles: List[UserProfile] = Field(..., description="该场景下的角色资料")

class UserAllProfilesResponse(BaseModel):
    """用户所有角色资料响应模型"""
    user_id: str = Field(..., description="用户ID")
    total_count: int = Field(..., description="总资料数")
    active_count: int = Field(..., description="激活资料数")
    by_scene: List[UserProfilesByScene] = Field(..., description="按场景分组的资料")
    all_profiles: List[UserProfile] = Field(..., description="所有资料列表")

# 特定场景的资料模型
class HousingSeekerProfile(BaseModel):
    """找房者资料"""
    budget_range: List[int] = Field(..., description="预算范围")
    preferred_areas: List[str] = Field(..., description="偏好区域")
    room_type: str = Field(..., description="房间类型")
    move_in_date: str = Field(..., description="入住日期")
    lease_duration: str = Field(..., description="租期")
    lifestyle: str = Field(..., description="生活方式")
    work_schedule: str = Field(..., description="工作时间")
    pets: bool = Field(..., description="是否有宠物")
    smoking: bool = Field(..., description="是否吸烟")
    occupation: str = Field(..., description="职业")
    company_location: str = Field(..., description="公司位置")

class HousingProviderProfile(BaseModel):
    """房源提供者资料"""
    properties: List[Dict[str, Any]] = Field(..., description="房源列表")
    landlord_type: str = Field(..., description="房东类型")
    response_time: str = Field(..., description="响应时间")
    viewing_available: bool = Field(..., description="是否可看房")
    lease_terms: List[str] = Field(..., description="租赁条款")

class DatingSeekerProfile(BaseModel):
    """交友者资料"""
    age: int = Field(..., description="年龄")
    height: int = Field(..., description="身高")
    education: str = Field(..., description="教育程度")
    occupation: str = Field(..., description="职业")
    income_range: str = Field(..., description="收入范围")
    relationship_status: str = Field(..., description="感情状态")
    looking_for: str = Field(..., description="寻找类型")
    hobbies: List[str] = Field(..., description="兴趣爱好")
    personality: List[str] = Field(..., description="性格特点")
    lifestyle: Dict[str, Any] = Field(..., description="生活方式")

class ActivityOrganizerProfile(BaseModel):
    """活动组织者资料"""
    # 必填字段
    activity_cover: str = Field(..., description="活动封面")
    activity_name: str = Field(..., description="活动名称")
    
    # 可选字段
    activity_types: Optional[List[str]] = Field(None, description="活动类型列表")
    activity_start_time: Optional[datetime] = Field(None, description="活动开始时间")
    activity_city: Optional[str] = Field(None, description="活动城市，默认为用户所在城市")
    activity_end_time: Optional[datetime] = Field(None, description="活动结束时间")
    activity_location: Optional[str] = Field(None, description="活动地点")
    activity_min_participants: Optional[int] = Field(None, description="活动最少人数")
    activity_max_participants: Optional[int] = Field(None, description="活动最多人数")
    activity_cost: Optional[str] = Field(None, description="活动费用")
    activity_description: Optional[str] = Field(None, description="活动描述")
    
    # 原有字段保留
    organizing_experience: Optional[str] = Field(None, description="组织经验")
    specialties: Optional[List[str]] = Field(None, description="专长领域")
    group_size_preference: Optional[str] = Field(None, description="偏好群体大小")
    frequency: Optional[str] = Field(None, description="活动频率")
    locations: Optional[List[str]] = Field(None, description="活动地点")
    past_activities: Optional[List[Dict[str, Any]]] = Field(None, description="过往活动")
    contact_info: Optional[Dict[str, Any]] = Field(None, description="联系方式")

class ActivityParticipantProfile(BaseModel):
    """活动参与者资料"""
    interests: List[str] = Field(..., description="兴趣领域")
    availability: Dict[str, str] = Field(..., description="可参与时间")
    experience_level: Dict[str, str] = Field(..., description="经验水平")
    transportation: List[str] = Field(..., description="交通方式")
    budget_range: Dict[str, int] = Field(..., description="预算范围")