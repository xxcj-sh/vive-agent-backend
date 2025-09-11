from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ActivityOrganizerProfile(BaseModel):
    """活动组织者卡片"""
    # 必填字段
    activity_start_date: Optional[datetime] = Field(None, description="活动开始日期")
    activity_start_time: Optional[datetime] = Field(None, description="活动开始时间")
    activity_cost: Optional[str] = Field(None, description="活动费用")
    activity_city: Optional[str] = Field(None, description="活动城市，默认为用户所在城市")

    # 可选字段
    activity_types: Optional[List[str]] = Field(None, description="活动类型列表")
    activity_end_time: Optional[datetime] = Field(None, description="活动结束时间")
    activity_location: Optional[str] = Field(None, description="活动地点")
    activity_max_participants: Optional[int] = Field(None, description="活动最多人数")
    activity_min_participants: Optional[int] = Field(None, description="活动最少人数")

    # 原有字段保留
    organizing_experience: Optional[str] = Field(None, description="组织经验")
    specialties: Optional[List[str]] = Field(None, description="专长领域")
    frequency: Optional[str] = Field(None, description="活动频率")
    locations: Optional[List[str]] = Field(None, description="活动地点")
    past_activities: Optional[List[Dict[str, Any]]] = Field(None, description="过往活动")


class ActivityParticipantProfile(BaseModel):
    """活动参与者卡片"""
    interests: List[str] = Field(..., description="兴趣领域")
    availability: Dict[str, str] = Field(..., description="可参与时间")
    experience_level: Dict[str, str] = Field(..., description="经验水平")
    budget_range: Dict[str, int] = Field(..., description="预算范围")


class HouseSeekerProfile(BaseModel):
    """找房者卡片"""
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


class HouseProfile(BaseModel):
    """房源卡片"""
    # 基本信息
    title: str = Field(..., description="房源标题")
    house_type: str = Field(..., description="房屋类型(整租/合租/单间)")
    room_count: int = Field(..., description="房间数量")
    area: float = Field(..., description="房屋面积(平方米)")
    floor: int = Field(..., description="楼层")
    total_floors: int = Field(..., description="总楼层")
    orientation: str = Field(..., description="房屋朝向")
    
    # 位置信息
    community_name: str = Field(..., description="小区名称")
    district: str = Field(..., description="区域")
    address: str = Field(..., description="详细地址")
    nearby_stations: List[str] = Field(default_factory=list, description="附近地铁站")
    
    # 租金信息
    monthly_rent: int = Field(..., description="月租金(元)")
    deposit: int = Field(..., description="押金(元)")
    payment_method: str = Field(..., description="付款方式")
    
    # 房屋配置
    furniture: List[str] = Field(default_factory=list, description="家具配置")
    appliances: List[str] = Field(default_factory=list, description="家电配置")
    facilities: List[str] = Field(default_factory=list, description="房屋设施")
    
    # 房东信息
    landlord_type: str = Field(..., description="房东类型(个人/中介)")
    response_time: str = Field(..., description="响应时间")
    viewing_available: bool = Field(..., description="是否可看房")
    
    # 房源特色
    tags: List[str] = Field(default_factory=list, description="房源标签")
    highlights: List[str] = Field(default_factory=list, description="房源亮点")
    
    # 图片信息
    images: List[str] = Field(default_factory=list, description="房源图片URLs")
    
    # 其他信息
    description: str = Field(..., description="房源描述")
    available_date: str = Field(..., description="可入住日期")
    lease_term: str = Field(..., description="租赁期限")
    pet_allowed: bool = Field(default=False, description="是否允许宠物")
    smoking_allowed: bool = Field(default=False, description="是否允许吸烟")
    
    # 时间戳
    created_at: Optional[datetime] = Field(None, description="发布时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


class DatingProfile(BaseModel):
    """约会交友卡片"""
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