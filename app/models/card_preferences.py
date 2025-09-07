from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime

# 用于填充不同类型 Card 的 preferences 字段
class ActivityOrganizerPreferences(BaseModel):
    """活动组织者匹配偏好"""
    
    # 参与者筛选条件
    preferred_participant_age_range: Optional[List[int]] = Field(None, description="期望参与者年龄范围 [min, max]")
    preferred_participant_count: Optional[Dict[str, int]] = Field(None, description="期望参与人数范围 {'min': int, 'max': int}")
    
    # 活动匹配偏好
    preferred_activity_types: Optional[List[str]] = Field(None, description="偏好的活动类型")
    preferred_locations: Optional[List[str]] = Field(None, description="偏好的活动区域")
    budget_preference: Optional[Dict[str, Any]] = Field(None, description="预算偏好 {'flexible': bool, 'max_budget': int}")
    
    # 时间偏好
    preferred_days: Optional[List[str]] = Field(None, description="偏好的活动日期 ['weekday', 'weekend', 'any']")
    preferred_time_slots: Optional[List[str]] = Field(None, description="偏好的时间段 ['morning', 'afternoon', 'evening']")
    
    # 参与者质量要求
    min_participation_history: Optional[int] = Field(0, description="要求参与者最低历史参与次数")
    require_verification: Optional[bool] = Field(False, description="是否要求参与者身份验证")
    
    # 匹配强度设置
    match_strictness: Optional[Literal['loose', 'medium', 'strict']] = Field('medium', description="匹配严格程度")


class ActivityParticipantPreferences(BaseModel):
    """活动参与者匹配偏好"""
    
    # 组织者筛选条件
    preferred_organizer_experience: Optional[str] = Field(None, description="期望组织者经验级别 ['beginner', 'intermediate', 'expert']")
    organizer_rating_threshold: Optional[float] = Field(None, description="组织者最低评分要求")
    
    # 活动筛选条件
    preferred_activity_types: Optional[List[str]] = Field(None, description="偏好的活动类型")
    preferred_locations: Optional[List[str]] = Field(None, description="偏好的活动区域")
    max_commute_time: Optional[int] = Field(None, description="最大通勤时间(分钟)")
    
    # 预算限制
    budget_range: Optional[Dict[str, int]] = Field(None, description="预算范围 {'min': int, 'max': int}")
    cost_sharing_preference: Optional[Literal['equal', 'proportional', 'organizer_pays']] = Field('equal', description="费用分摊偏好")
    
    # 时间偏好
    availability_schedule: Optional[Dict[str, Any]] = Field(None, description="可用时间配置")
    notice_period_days: Optional[int] = Field(3, description="提前通知天数要求")
    
    # 活动规模偏好
    group_size_preference: Optional[Dict[str, int]] = Field(None, description="期望团队规模 {'min': int, 'max': int}")
    
    # 参与者匹配设置
    allow_co_participants: Optional[bool] = Field(True, description="是否允许与认识的人一起参与")
    match_strictness: Optional[Literal['loose', 'medium', 'strict']] = Field('medium', description="匹配严格程度")


class HouseSeekerPreferences(BaseModel):
    """找房者匹配偏好"""
    
    # 房源筛选条件
    preferred_house_types: Optional[List[str]] = Field(None, description="偏好的房屋类型")
    budget_flexibility: Optional[Dict[str, Any]] = Field(None, description="预算灵活性 {'flexible': bool, 'max_increase_percent': int}")
    
    # 地理位置偏好
    preferred_districts: Optional[List[str]] = Field(None, description="偏好的区域")
    max_commute_time: Optional[int] = Field(None, description="最大通勤时间(分钟)")
    nearby_requirements: Optional[List[str]] = Field(None, description="周边设施要求")
    
    # 房屋配置要求
    required_facilities: Optional[List[str]] = Field(None, description="必需设施")
    furniture_preference: Optional[Literal['fully_furnished', 'partially_furnished', 'unfurnished']] = Field(None, description="家具偏好")
    
    # 室友匹配偏好
    roommate_preferences: Optional[Dict[str, Any]] = Field(None, description="室友偏好")
    lifestyle_compatibility: Optional[List[str]] = Field(None, description="生活方式兼容性要求")
    
    # 租约灵活性
    lease_flexibility: Optional[bool] = Field(True, description="是否接受租约条款协商")
    move_in_flexibility_days: Optional[int] = Field(7, description="入住时间灵活性(天)")
    
    # 房东偏好
    preferred_landlord_type: Optional[List[str]] = Field(None, description="偏好的房东类型")
    require_verification: Optional[bool] = Field(True, description="是否要求房源验证")
    
    # 匹配设置
    match_strictness: Optional[Literal['loose', 'medium', 'strict']] = Field('medium', description="匹配严格程度")


class HousePreferences(BaseModel):
    """房源匹配偏好"""
    
    # 租客筛选条件
    preferred_occupation: Optional[List[str]] = Field(None, description="偏好的租客职业")
    preferred_age_range: Optional[List[int]] = Field(None, description="期望租客年龄范围")
    
    # 租客质量要求
    min_income_ratio: Optional[float] = Field(None, description="最低收入与租金比例")
    employment_verification: Optional[bool] = Field(True, description="是否要求工作验证")
    reference_check: Optional[bool] = Field(True, description="是否要求推荐信")
    
    # 租客行为偏好
    smoking_policy: Optional[Literal['no_preference', 'non_smoking_only', 'smoking_allowed']] = Field('no_preference', description="吸烟政策")
    pet_policy: Optional[Literal['no_preference', 'no_pets', 'pets_allowed']] = Field('no_preference', description="宠物政策")
    
    # 租约条款
    lease_term_preference: Optional[List[str]] = Field(None, description="偏好的租期")
    payment_frequency_preference: Optional[List[str]] = Field(None, description="偏好的付款频率")
    
    # 入住时间偏好
    preferred_move_in_period: Optional[Dict[str, str]] = Field(None, description="期望入住时间段")
    
    # 匹配设置
    match_strictness: Optional[Literal['loose', 'medium', 'strict']] = Field('medium', description="匹配严格程度")
    auto_approval: Optional[bool] = Field(False, description="是否自动批准符合条件的租客")


class DatingPreferences(BaseModel):
    """约会交友匹配偏好"""
    
    # 基本筛选条件
    preferred_age_range: Optional[List[int]] = Field(None, description="期望年龄范围 [min, max]")
    preferred_height_range: Optional[List[int]] = Field(None, description="期望身高范围 [min, max] (cm)")
    
    # 教育和职业偏好
    preferred_education_levels: Optional[List[str]] = Field(None, description="期望教育程度")
    preferred_occupations: Optional[List[str]] = Field(None, description="期望职业")
    income_preference: Optional[Dict[str, Any]] = Field(None, description="收入要求 {'min': str, 'flexible': bool}")
    
    # 关系状态偏好
    preferred_relationship_status: Optional[List[str]] = Field(None, description="期望感情状态")
    looking_for_match: Optional[List[str]] = Field(None, description="寻找关系类型匹配")
    
    # 兴趣和性格匹配
    shared_interests_weight: Optional[float] = Field(0.3, description="共同兴趣权重 0-1")
    personality_compatibility: Optional[List[str]] = Field(None, description="期望性格特征")
    lifestyle_compatibility: Optional[List[str]] = Field(None, description="生活方式兼容性")
    
    # 地理位置偏好
    preferred_locations: Optional[List[str]] = Field(None, description="偏好的地理位置")
    max_distance_km: Optional[int] = Field(None, description="最大距离限制(公里)")
    
    # 外观和生活方式
    appearance_preferences: Optional[Dict[str, Any]] = Field(None, description="外观偏好")
    lifestyle_requirements: Optional[Dict[str, Any]] = Field(None, description="生活方式要求")
    
    # 匹配设置
    match_strictness: Optional[Literal['loose', 'medium', 'strict']] = Field('medium', description="匹配严格程度")
    allow_different_intentions: Optional[bool] = Field(False, description="是否允许不同交友目的")
    
    # 安全和验证
    require_verification: Optional[bool] = Field(True, description="是否要求身份验证")
    allow_social_media_verification: Optional[bool] = Field(True, description="是否接受社交媒体验证")


# 统一的偏好设置包装类
class CardPreferences(BaseModel):
    """卡片偏好设置统一模型"""
    
    activity_organizer: Optional[ActivityOrganizerPreferences] = Field(None, description="活动组织者偏好")
    activity_participant: Optional[ActivityParticipantPreferences] = Field(None, description="活动参与者偏好")
    house_seeker: Optional[HouseSeekerPreferences] = Field(None, description="找房者偏好")
    house: Optional[HousePreferences] = Field(None, description="房源偏好")
    dating: Optional[DatingPreferences] = Field(None, description="约会交友偏好")
    
    # 通用设置
    notification_settings: Optional[Dict[str, bool]] = Field(
        default_factory=lambda: {
            "email": True,
            "push": True,
            "sms": False
        },
        description="通知设置"
    )
    
    privacy_settings: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {
            "show_profile_to_public": True,
            "allow_direct_message": True,
            "show_online_status": False
        },
        description="隐私设置"
    )
    
    def get_preferences_by_type(self, card_type: str) -> Optional[BaseModel]:
        """根据卡片类型获取对应的偏好设置"""
        preference_map = {
            "activity_organizer": self.activity_organizer,
            "activity_participant": self.activity_participant,
            "house_seeker": self.house_seeker,
            "house": self.house,
            "dating": self.dating
        }
        return preference_map.get(card_type)
    
    def set_preferences_by_type(self, card_type: str, preferences: BaseModel) -> None:
        """根据卡片类型设置对应的偏好设置"""
        if card_type == "activity_organizer" or card_type == "activity_provider":
            self.activity_organizer = preferences
        elif card_type == "activity_participant" or card_type == "activity_seeker":
            self.activity_participant = preferences
        elif card_type == "house_seeker":
            self.house_seeker = preferences
        elif card_type == "house":
            self.house = preferences
        elif card_type == "dating":
            self.dating = preferences