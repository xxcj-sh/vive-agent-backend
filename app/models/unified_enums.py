"""
统一的枚举定义，解决match_type和role_type命名混乱问题
"""

from enum import Enum

class SceneType(str, Enum):
    """场景类型枚举 - 统一所有场景定义"""
    HOUSING = "housing"
    DATING = "dating"
    ACTIVITY = "activity"
    BUSINESS = "business"

class UserRoleType(str, Enum):
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

class SimplifiedRole(str, Enum):
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
        SceneType.BUSINESS: [UserRoleType.BUSINESS_SEEKER, UserRoleType.BUSINESS_PROVIDER]
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