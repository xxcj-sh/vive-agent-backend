"""
卡片偏好设置使用示例

这个文件展示了如何为不同类型的卡片创建和使用偏好设置
"""

from datetime import datetime
from .card_preferences import (
    CardPreferences,
    ActivityOrganizerPreferences,
    ActivityParticipantPreferences,
    HouseSeekerPreferences,
    HousePreferences,
    DatingPreferences
)

def create_activity_organizer_preferences() -> ActivityOrganizerPreferences:
    """创建活动组织者的偏好设置示例"""
    return ActivityOrganizerPreferences(
        preferred_participant_age_range=[20, 45],
        preferred_participant_count={'min': 5, 'max': 20},
        preferred_activity_types=['outdoor', 'cultural', 'networking'],
        preferred_locations=['朝阳区', '海淀区', '西城区'],
        budget_preference={'flexible': True, 'max_budget': 500},
        preferred_days=['weekend'],
        preferred_time_slots=['afternoon', 'evening'],
        min_participation_history=2,
        require_verification=True,
        match_strictness='medium'
    )

def create_activity_participant_preferences() -> ActivityParticipantPreferences:
    """创建活动参与者的偏好设置示例"""
    return ActivityParticipantPreferences(
        preferred_organizer_experience='intermediate',
        organizer_rating_threshold=4.0,
        preferred_activity_types=['sports', 'art', 'food'],
        preferred_locations=['朝阳区', '海淀区'],
        max_commute_time=60,
        budget_range={'min': 50, 'max': 300},
        cost_sharing_preference='equal',
        notice_period_days=5,
        group_size_preference={'min': 3, 'max': 15},
        allow_co_participants=True,
        match_strictness='loose'
    )

def create_house_seeker_preferences() -> HouseSeekerPreferences:
    """创建找房者的偏好设置示例"""
    return HouseSeekerPreferences(
        preferred_house_types=['合租', '单间'],
        budget_flexibility={'flexible': True, 'max_increase_percent': 10},
        preferred_districts=['海淀区', '朝阳区', '西城区'],
        max_commute_time=45,
        nearby_requirements=['地铁', '超市', '医院'],
        required_facilities=['空调', '洗衣机', '热水器'],
        furniture_preference='partially_furnished',
        roommate_preferences={
            'gender_preference': 'no_preference',
            'age_range': [20, 35],
            'occupation_type': ['tech', 'finance', 'education']
        },
        lifestyle_compatibility=['安静', '整洁', '不吸烟'],
        lease_flexibility=True,
        move_in_flexibility_days=14,
        preferred_landlord_type=['个人'],
        require_verification=True,
        match_strictness='strict'
    )

def create_house_preferences() -> HousePreferences:
    """创建房源的偏好设置示例"""
    return HousePreferences(
        preferred_occupation=['tech', 'finance', 'education'],
        preferred_age_range=[22, 40],
        min_income_ratio=3.0,
        employment_verification=True,
        reference_check=True,
        smoking_policy='non_smoking_only',
        pet_policy='no_pets',
        lease_term_preference=['1年', '6个月'],
        payment_frequency_preference=['月付', '季付'],
        preferred_move_in_period={
            'start_date': '2024-02-01',
            'end_date': '2024-03-31'
        },
        match_strictness='medium',
        auto_approval=False
    )

def create_dating_preferences() -> DatingPreferences:
    """创建约会交友的偏好设置示例"""
    return DatingPreferences(
        preferred_age_range=[25, 35],
        preferred_height_range=[160, 180],
        preferred_education_levels=['本科', '硕士', '博士'],
        preferred_occupations=['tech', 'finance', 'art', 'education'],
        income_preference={'min': '15k', 'flexible': True},
        preferred_relationship_status=['单身'],
        looking_for_match=['长期关系', '结婚'],
        shared_interests_weight=0.4,
        personality_compatibility=['善良', '幽默', '上进'],
        lifestyle_compatibility=['健康', '积极', '稳定'],
        preferred_locations=['北京', '上海'],
        max_distance_km=50,
        appearance_preferences={
            'style': ['休闲', '商务'],
            'body_type': ['匀称', '偏瘦', '运动']
        },
        lifestyle_requirements={
            'smoking': False,
            'drinking': 'social',
            'exercise': 'regular'
        },
        match_strictness='strict',
        allow_different_intentions=False,
        require_verification=True,
        allow_social_media_verification=True
    )

def create_card_preferences_example() -> CardPreferences:
    """创建完整的卡片偏好设置示例"""
    preferences = CardPreferences()
    
    # 为每种卡片类型设置偏好
    preferences.activity_organizer = create_activity_organizer_preferences()
    preferences.activity_participant = create_activity_participant_preferences()
    preferences.house_seeker = create_house_seeker_preferences()
    preferences.house = create_house_preferences()
    preferences.dating = create_dating_preferences()
    
    return preferences

def demonstrate_usage():
    """演示如何使用偏好设置"""
    # 创建偏好设置
    card_prefs = create_card_preferences_example()
    
    # 获取特定类型的偏好
    organizer_prefs = card_prefs.get_preferences_by_type('activity_organizer')
    if organizer_prefs:
        print(f"活动组织者年龄偏好: {organizer_prefs.preferred_participant_age_range}")
    
    # 创建新的偏好设置
    new_dating_prefs = DatingPreferences(
        preferred_age_range=[28, 38],
        match_strictness='loose'
    )
    card_prefs.set_preferences_by_type('dating', new_dating_prefs)
    
    # 转换为字典用于存储
    prefs_dict = card_prefs.dict()
    print("偏好设置已保存为字典格式")
    
    return prefs_dict

if __name__ == "__main__":
    demonstrate_usage()