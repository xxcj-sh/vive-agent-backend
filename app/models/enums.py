"""
枚举值定义模块
根据产品设计的枚举值列表定义所有枚举类
"""

import enum
from typing import List

# 1. 通用基础枚举

class Region(str, enum.Enum):
    """地区枚举"""
    BEIJING = "北京"
    SHANGHAI = "上海"
    GUANGZHOU = "广州"
    SHENZHEN = "深圳"
    HANGZHOU = "杭州"
    CHENGDU = "成都"
    WUHAN = "武汉"
    XIAN = "西安"
    NANJING = "南京"
    SUZHOU = "苏州"
    TIANJIN = "天津"
    CHONGQING = "重庆"
    QINGDAO = "青岛"
    DALIAN = "大连"
    XIAMEN = "厦门"
    CHANGSHA = "长沙"
    OTHER = "其他"

class Interest(str, enum.Enum):
    """兴趣爱好枚举"""
    DINING = "聚餐"
    MOVIE = "电影"
    TRAVEL = "旅行"
    READING = "阅读"
    MUSIC = "音乐"
    GAMING = "游戏"
    SPORTS = "运动"
    PHOTOGRAPHY = "摄影"
    FOOD = "美食"
    PETS = "宠物"
    PAINTING = "绘画"
    DANCING = "舞蹈"
    YOGA = "瑜伽"
    FITNESS = "健身"
    BASKETBALL = "篮球"
    FOOTBALL = "足球"
    BADMINTON = "羽毛球"
    SWIMMING = "游泳"

class Personality(str, enum.Enum):
    """性格特质枚举"""
    CHEERFUL = "开朗"
    INTROVERTED = "内向"
    EASYGOING = "随和"
    RIGOROUS = "严谨"
    CREATIVE = "创意"
    RATIONAL = "理性"
    EMOTIONAL = "感性"
    HUMOROUS = "幽默"
    CAREFUL = "细心"
    STEADY = "稳重"
    ENTHUSIASTIC = "热情"
    CALM = "冷静"
    OPTIMISTIC = "乐观"
    CAUTIOUS = "谨慎"
    INDEPENDENT = "独立"
    SOCIABLE = "合群"
    OPINIONATED = "有主见"
    UNDERSTANDING = "善解人意"

class Lifestyle(str, enum.Enum):
    """生活方式枚举"""
    EARLY_BIRD = "早睡早起"
    NIGHT_OWL = "夜猫子"
    FITNESS_ENTHUSIAST = "健身达人"
    HOMEBODY = "宅家一族"
    SOCIAL_ACTIVE = "社交活跃"
    QUIET_INTROVERTED = "安静内敛"
    FOODIE = "美食爱好者"
    WORK_FROM_HOME = "居家办公"
    STUDENT = "学生党"
    WORKAHOLIC = "工作狂"
    ARTSY = "文艺青年"

class CommunicationStyle(str, enum.Enum):
    """沟通风格枚举"""
    DIRECT = "直接"
    TACTFUL = "委婉"
    EASYGOING = "随和"
    FORMAL = "正式"

class CleanlinessLevel(str, enum.Enum):
    """整洁程度枚举"""
    GERMAPHOBE = "洁癖"
    CLEAN = "整洁"
    AVERAGE = "一般"
    CASUAL = "随意"

class NoiseTolerance(str, enum.Enum):
    """噪音容忍度枚举"""
    HIGH = "高"
    MEDIUM = "中等"
    LOW = "低"

# 2. 住房场景枚举

class HouseType(str, enum.Enum):
    """房屋类型枚举"""
    WHOLE_RENT = "整租"
    SHARED_RENT = "合租"
    MASTER_ROOM = "主卧"
    SECOND_ROOM = "次卧"
    APARTMENT = "公寓"
    VILLA = "别墅"
    ORDINARY = "普通住宅"
    DUPLEX = "复式"
    HOTEL_APARTMENT = "酒店式公寓"
    COMMERCIAL = "商住两用"

class Orientation(str, enum.Enum):
    """房屋朝向枚举"""
    EAST = "东"
    SOUTH = "南"
    WEST = "西"
    NORTH = "北"
    SOUTHEAST = "东南"
    NORTHEAST = "东北"
    SOUTHWEST = "西南"
    NORTHWEST = "西北"

class DecorationLevel(str, enum.Enum):
    """装修程度枚举"""
    LUXURY = "精装修"
    SIMPLE = "简装修"
    ROUGH = "毛坯房"

class FloorLevel(str, enum.Enum):
    """楼层范围枚举"""
    LOW = "低楼层(1-5层)"
    MIDDLE = "中楼层(6-15层)"
    HIGH = "高楼层(16层及以上)"

class ElevatorStatus(str, enum.Enum):
    """电梯情况枚举"""
    WITH_ELEVATOR = "有电梯"
    WITHOUT_ELEVATOR = "无电梯"

class Facility(str, enum.Enum):
    """房屋设施枚举"""
    AIR_CONDITIONING = "空调"
    WASHING_MACHINE = "洗衣机"
    REFRIGERATOR = "冰箱"
    WATER_HEATER = "热水器"
    WIFI = "WiFi"
    TV = "电视"
    KITCHEN = "厨房"
    BALCONY = "阳台"
    ELEVATOR = "电梯"
    PARKING = "停车位"
    HEATING = "暖气"
    PRIVATE_BATHROOM = "独立卫浴"
    DESK = "书桌"
    WARDROBE = "衣柜"

class BudgetRange(str, enum.Enum):
    """租客预算枚举"""
    RANGE_1000_2000 = "1000-2000元"
    RANGE_2000_3000 = "2000-3000元"
    RANGE_3000_5000 = "3000-5000元"
    RANGE_5000_8000 = "5000-8000元"
    RANGE_8000_PLUS = "8000元以上"

class PropertyType(str, enum.Enum):
    """房源类型枚举"""
    APARTMENT = "公寓"
    ORDINARY = "普通住宅"
    VILLA = "别墅"
    COMMERCIAL = "商住两用"
    LOFT = "loft"
    DUPLEX = "复式"

class Transportation(str, enum.Enum):
    """交通方式枚举"""
    WALKING = "步行"
    BICYCLE = "自行车"
    SUBWAY = "地铁"
    BUS = "公交"
    DRIVING = "自驾"
    RIDE_HAILING = "网约车"

class ManagementService(str, enum.Enum):
    """管理服务枚举"""
    MAINTENANCE = "维修服务"
    CLEANING = "清洁服务"

class NearbyAmenity(str, enum.Enum):
    """周边配套枚举"""
    SUBWAY = "地铁"

class UserStatus(str, enum.Enum):
    """用户状态枚举"""
    PENDING = "pending"      # 待激活
    ACTIVE = "active"        # 正常
    SUSPENDED = "suspended"  # 暂停
    DELETED = "deleted"      # 已删除
    BUS_STOP = "公交站"
    SUPERMARKET = "超市"
    MALL = "商场"
    HOSPITAL = "医院"
    SCHOOL = "学校"
    PARK = "公园"
    GYM = "健身房"
    RESTAURANT = "餐厅"
    BANK = "银行"

class HouseRule(str, enum.Enum):
    """房屋规则枚举"""
    PETS_ALLOWED = "允许宠物"
    SMOKING_ALLOWED = "允许吸烟"
    COOKING_ALLOWED = "允许做饭"
    VISITORS_ALLOWED = "允许访客"

# 3. 活动场景枚举

class SkillLevel(str, enum.Enum):
    """技能水平枚举"""
    BEGINNER = "新手"
    ELEMENTARY = "初级"
    INTERMEDIATE = "中级"
    ADVANCED = "高级"
    EXPERT = "专家"

class ActivityType(str, enum.Enum):
    """活动类型枚举"""
    SPORTS_FITNESS = "运动健身"
    CULTURE_ART = "文化艺术"
    OUTDOOR_ADVENTURE = "户外探险"
    FOOD_TASTING = "美食品鉴"
    LEARNING_EXCHANGE = "学习交流"
    ENTERTAINMENT = "娱乐休闲"
    OTHER = "其他"

class Experience(str, enum.Enum):
    """经验水平枚举"""
    NO_EXPERIENCE = "无经验"
    WITHIN_1_YEAR = "1年以内"
    ONE_TO_THREE_YEARS = "1-3年"
    THREE_TO_FIVE_YEARS = "3-5年"
    OVER_FIVE_YEARS = "5年以上"

class GroupSize(str, enum.Enum):
    """团队规模枚举"""
    SIZE_1_2 = "1-2人"
    SIZE_3_5 = "3-5人"
    SIZE_5_10 = "5-10人"
    SIZE_10_PLUS = "10人以上"

class ActivityBudget(str, enum.Enum):
    """活动预算枚举"""
    FREE = "免费"
    RANGE_0_100 = "0-100元"
    RANGE_100_300 = "100-300元"
    RANGE_300_500 = "300-500元"
    RANGE_500_1000 = "500-1000元"
    RANGE_1000_PLUS = "1000元以上"

class Frequency(str, enum.Enum):
    """活动频率枚举"""
    DAILY = "每天"
    TWO_THREE_TIMES_WEEK = "每周2-3次"
    ONCE_WEEK = "每周1次"
    TWO_THREE_TIMES_MONTH = "每月2-3次"
    ONCE_MONTH = "每月1次"
    OCCASIONALLY = "偶尔"

class Duration(str, enum.Enum):
    """活动时长枚举"""
    WITHIN_1_HOUR = "1小时以内"
    ONE_TO_TWO_HOURS = "1-2小时"
    TWO_TO_FOUR_HOURS = "2-4小时"
    HALF_DAY = "半天"
    FULL_DAY = "全天"
    MULTIPLE_DAYS = "多天"

class Intensity(str, enum.Enum):
    """活动强度枚举"""
    RELAXED = "轻松"
    MODERATE = "适中"
    HIGH_INTENSITY = "高强度"
    EXTREME = "极限"

class AvailableTime(str, enum.Enum):
    """可用时间枚举"""
    WEEKDAY_MORNING = "工作日早上"
    WEEKDAY_NOON = "工作日中午"
    WEEKDAY_EVENING = "工作日晚间"
    WEEKEND_MORNING = "周末上午"
    WEEKEND_AFTERNOON = "周末下午"
    WEEKEND_EVENING = "周末晚上"

class PreferredTime(str, enum.Enum):
    """偏好时间枚举"""
    EARLY_MORNING = "早上(6-9点)"
    MORNING = "上午(9-12点)"
    NOON = "中午(12-14点)"
    AFTERNOON = "下午(14-18点)"
    EVENING = "晚上(18-22点)"
    LATE_NIGHT = "深夜(22点后)"

class Equipment(str, enum.Enum):
    """所需设备枚举"""
    SPORTS_EQUIPMENT = "运动装备"
    PHOTOGRAPHY_EQUIPMENT = "摄影器材"
    LEARNING_SUPPLIES = "学习用品"
    ENTERTAINMENT_EQUIPMENT = "娱乐设备"
    OTHER = "其他"

# 4. 恋爱交友场景枚举

class Education(str, enum.Enum):
    """教育程度枚举"""
    HIGH_SCHOOL = "高中"
    COLLEGE = "大专"
    BACHELOR = "本科"
    MASTER = "硕士"
    DOCTOR = "博士"
    OTHER = "其他"

class IncomeRange(str, enum.Enum):
    """收入范围枚举"""
    UNDER_50K = "5万以下"
    RANGE_50K_100K = "5-10万"
    RANGE_100K_200K = "10-20万"
    RANGE_200K_300K = "20-30万"
    RANGE_300K_500K = "30-50万"
    OVER_500K = "50万以上"

class MaritalStatus(str, enum.Enum):
    """婚姻状况枚举"""
    SINGLE = "未婚"
    DIVORCED = "离异"
    MARRIED = "已婚"
    WIDOWED = "丧偶"

class HeightRange(str, enum.Enum):
    """身高范围枚举"""
    RANGE_150_155 = "150-155"
    RANGE_155_160 = "155-160"
    RANGE_160_165 = "160-165"
    RANGE_165_170 = "165-170"
    RANGE_170_175 = "170-175"
    RANGE_175_180 = "175-180"
    RANGE_180_185 = "180-185"
    RANGE_185_190 = "185-190"

class DatingLifestyle(str, enum.Enum):
    """交友生活方式枚举"""
    HOMEBODY = "宅家"
    SOCIAL_BUTTERFLY = "社交达人"
    FITNESS_ENTHUSIAST = "运动健身"
    ARTSY = "文艺青年"
    FOODIE = "美食探索"
    TRAVEL_LOVER = "旅行爱好者"
    WORKAHOLIC = "工作狂"
    LEARNING_FOCUSED = "学习提升"

class DatingInterest(str, enum.Enum):
    """交友兴趣爱好枚举"""
    FOOD = "美食"
    TRAVEL = "旅行"
    MOVIE = "电影"
    MUSIC = "音乐"
    READING = "阅读"
    SPORTS = "运动"
    PHOTOGRAPHY = "摄影"
    GAMING = "游戏"
    SHOPPING = "购物"
    PETS = "宠物"
    HANDICRAFT = "手工"
    DANCING = "舞蹈"
    YOGA = "瑜伽"
    FITNESS = "健身"

class WorkIndustry(str, enum.Enum):
    """工作行业枚举"""
    INTERNET = "互联网"
    FINANCE = "金融"
    EDUCATION = "教育"
    HEALTHCARE = "医疗"
    MANUFACTURING = "制造业"
    SERVICE = "服务业"
    CIVIL_SERVANT = "公务员"
    FREELANCE = "自由职业"
    STUDENT = "学生"
    OTHER = "其他"

# 7. 社交场景专用枚举

class SocialPurpose(str, enum.Enum):
    """社交目的枚举"""
    BUSINESS_NETWORKING = "商务拓展"
    CAREER_DEVELOPMENT = "职业发展"
    SKILL_EXCHANGE = "技能交换"
    HOBBY_SHARING = "兴趣分享"
    FRIENDSHIP = "结交朋友"
    MENTORSHIP = "导师指导"
    COLLABORATION = "项目合作"
    KNOWLEDGE_SHARING = "知识分享"

class SocialActivity(str, enum.Enum):
    """社交活动类型枚举"""
    COFFEE_CHAT = "咖啡聊天"
    BUSINESS_MEETUP = "商务聚会"
    WORKSHOP = "工作坊"
    SEMINAR = "研讨会"
    NETWORKING_EVENT = "社交活动"
    ONLINE_DISCUSSION = "线上讨论"
    STUDY_GROUP = "学习小组"
    PROJECT_COLLABORATION = "项目合作"

class SocialInterest(str, enum.Enum):
    """社交兴趣枚举"""
    TECHNOLOGY = "科技"
    FINANCE = "金融"
    STARTUP = "创业"
    MARKETING = "市场营销"
    DESIGN = "设计"
    PRODUCT = "产品"
    DATA_SCIENCE = "数据科学"
    AI_ML = "人工智能"
    BLOCKCHAIN = "区块链"
    E_COMMERCE = "电商"
    CONSULTING = "咨询"
    INVESTMENT = "投资"

class ProfessionalLevel(str, enum.Enum):
    """职业水平枚举"""
    STUDENT = "学生"
    ENTRY_LEVEL = "初级"
    MID_LEVEL = "中级"
    SENIOR_LEVEL = "高级"
    EXECUTIVE = "高管"
    ENTREPRENEUR = "创业者"
    EXPERT = "专家"

class CompanySize(str, enum.Enum):
    """公司规模枚举"""
    STARTUP = "初创公司"
    SMALL = "小型公司(1-50人)"
    MEDIUM = "中型公司(50-200人)"
    LARGE = "大型公司(200-1000人)"
    ENTERPRISE = "大型企业(1000人以上)"
    FREELANCE = "自由职业"

class ConnectionType(str, enum.Enum):
    """连接类型枚举"""
    MENTOR = "导师"
    PEER = "同行"
    MENTEE = "学生"
    PARTNER = "合作伙伴"
    INVESTOR = "投资人"
    ADVISOR = "顾问"

# 5. 系统枚举

# 8. 匹配系统枚举

class MatchActionType(str, enum.Enum):
    """匹配操作类型枚举"""
    LIKE = "like"              # 喜欢
    DISLIKE = "dislike"        # 不喜欢
    SUPER_LIKE = "super_like"  # 超级喜欢
    PASS = "pass"              # 跳过
    AI_RECOMMEND_BY_SYSTEM = "ai_recommend_by_system"  # 系统主动 AI 引荐
    AI_RECOMMEND_AFTER_USER_CHAT = "ai_recommend_after_user_chat"  # 用户聊天后AI引荐
    COLLECTION = "collection"  # 收藏卡片
    FOLLOW = "follow"          # 关注
    FOLLOW_AFTER_TRIGGER_IN_CHAT = "follow_after_trigger_in_chat"  # 触发后在聊天中关注

class MatchResultStatus(str, enum.Enum):
    """匹配结果状态枚举"""
    PENDING = "pending"        # 等待对方操作
    MATCHED = "matched"        # 双向匹配成功
    UNMATCHED = "unmatched"    # 未匹配
    EXPIRED = "expired"        # 已过期
    BLOCKED = "blocked"        # 已屏蔽

class MatchStatus(str, enum.Enum):
    """匹配状态枚举"""
    PENDING = "pending"         # 待处理
    ACCEPTED = "accepted"       # 已接受
    REJECTED = "rejected"       # 已拒绝
    EXPIRED = "expired"         # 已过期
    CANCELLED = "cancelled"     # 已取消    # 双重角色

class Gender(int, enum.Enum):
    """性别枚举"""
    UNKNOWN = 0                # 未知
    MALE = 1                   # 男性
    FEMALE = 2                 # 女性

# 6. 统一场景和角色管理枚举

class SceneType(str, enum.Enum):
    """场景类型枚举 - 统一所有场景定义"""
    HOUSING = "housing"
    DATING = "dating"
    ACTIVITY = "activity"
    BUSINESS = "business"
    SOCIAL = "social"

class UserRoleType(str, enum.Enum):
    """用户角色类型枚举 - 完整格式"""
    # 房源场景
    HOUSING_SEEKER = "housing_seeker"
    HOUSING_PROVIDER = "housing_provider"
    
    # 交友场景
    DATING_SEEKER = "dating_seeker"
    DATING_PROVIDER = "dating_provider"
    
    # 活动场景
    ACTIVITY_ORGANIZER = "activity_organizer"
    ACTIVITY_PARTICIPANT = "activity_participant"
    
    # 商务场景
    BUSINESS_SEEKER = "business_seeker"
    BUSINESS_PROVIDER = "business_provider"

    # 社交场景
    SOCIAL_BUSINESS = "social_business"
    SOCIAL_CAREER = "social_career"
    SOCIAL_INTEREST = "social_interest"
    SOCIAL_DATING = "social_dating"
    SOCIAL_BASIC = "social_basic"
    

class SimplifiedRole(str, enum.Enum):
    """简化角色枚举 - 用于前端交互"""
    SEEKER = "seeker"
    PROVIDER = "provider"
    ORGANIZER = "organizer"
    PARTICIPANT = "participant"

class RoleMapping:
    """角色映射工具类"""
    
    # 场景到角色的映射
    SCENE_ROLES = {
        SceneType.HOUSING: [UserRoleType.HOUSING_SEEKER, UserRoleType.HOUSING_PROVIDER],
        SceneType.DATING: [UserRoleType.DATING_SEEKER, UserRoleType.DATING_PROVIDER],
        SceneType.ACTIVITY: [UserRoleType.ACTIVITY_ORGANIZER, UserRoleType.ACTIVITY_PARTICIPANT],
        SceneType.BUSINESS: [UserRoleType.BUSINESS_SEEKER, UserRoleType.BUSINESS_PROVIDER],
        SceneType.SOCIAL: [UserRoleType.SOCIAL_BUSINESS, UserRoleType.SOCIAL_CAREER, UserRoleType.SOCIAL_INTEREST, UserRoleType.SOCIAL_DATING]
    }
    
    # 简化角色到完整角色的映射
    SIMPLIFIED_TO_FULL = {
        (SceneType.HOUSING, SimplifiedRole.SEEKER): UserRoleType.HOUSING_SEEKER,
        (SceneType.HOUSING, SimplifiedRole.PROVIDER): UserRoleType.HOUSING_PROVIDER,
        (SceneType.DATING, SimplifiedRole.SEEKER): UserRoleType.DATING_SEEKER,
        (SceneType.DATING, SimplifiedRole.PROVIDER): UserRoleType.DATING_PROVIDER,
        (SceneType.ACTIVITY, SimplifiedRole.ORGANIZER): UserRoleType.ACTIVITY_ORGANIZER,
        (SceneType.ACTIVITY, SimplifiedRole.PARTICIPANT): UserRoleType.ACTIVITY_PARTICIPANT,
        (SceneType.BUSINESS, SimplifiedRole.SEEKER): UserRoleType.BUSINESS_SEEKER,
        (SceneType.BUSINESS, SimplifiedRole.PROVIDER): UserRoleType.BUSINESS_PROVIDER,
    }
    
    # 反向映射
    FULL_TO_SIMPLIFIED = {v: k[1] for k, v in SIMPLIFIED_TO_FULL.items()}
    
    @classmethod
    def get_full_role(cls, scene_type: str, simplified_role: str) -> str:
        """根据场景和简化角色获取完整角色"""
        return cls.SIMPLIFIED_TO_FULL.get((scene_type, simplified_role), simplified_role)
    
    @classmethod
    def get_simplified_role(cls, full_role: str) -> str:
        """根据完整角色获取简化角色"""
        return cls.FULL_TO_SIMPLIFIED.get(full_role, full_role)
    
    @classmethod
    def get_available_roles(cls, scene_type: str) -> list[str]:
        """获取场景可用的完整角色列表"""
        return [role.value for role in cls.SCENE_ROLES.get(scene_type, [])]
    
    @classmethod
    def get_target_role(cls, current_role: str) -> str:
        """根据当前角色获取匹配目标角色"""
        role_mapping = {
            UserRoleType.HOUSING_SEEKER: UserRoleType.HOUSING_PROVIDER,
            UserRoleType.HOUSING_PROVIDER: UserRoleType.HOUSING_SEEKER,
            UserRoleType.DATING_SEEKER: UserRoleType.DATING_PROVIDER,
            UserRoleType.DATING_PROVIDER: UserRoleType.DATING_SEEKER,
            UserRoleType.ACTIVITY_ORGANIZER: UserRoleType.ACTIVITY_PARTICIPANT,
            UserRoleType.ACTIVITY_PARTICIPANT: UserRoleType.ACTIVITY_ORGANIZER,
            UserRoleType.BUSINESS_SEEKER: UserRoleType.BUSINESS_PROVIDER,
            UserRoleType.BUSINESS_PROVIDER: UserRoleType.BUSINESS_SEEKER,
        }
        return role_mapping.get(current_role, current_role)

# 枚举值获取工具函数

def get_enum_values(enum_class) -> List[str]:
    """获取枚举类的所有值"""
    return [item.value for item in enum_class]

def get_enum_choices(enum_class) -> List[tuple]:
    """获取枚举类的选择项（用于表单）"""
    return [(item.value, item.value) for item in enum_class]

# 枚举值验证函数

def validate_enum_value(value: str, enum_class) -> bool:
    """验证值是否在枚举范围内"""
    return value in get_enum_values(enum_class)

def validate_enum_list(values: List[str], enum_class) -> bool:
    """验证值列表是否都在枚举范围内"""
    enum_values = get_enum_values(enum_class)
    return all(value in enum_values for value in values)