"""
角色类型转换工具
用于统一处理前端简化角色与后端完整角色之间的转换
"""

from typing import Optional
from app.models.unified_enums import RoleMapping, SceneType

class RoleConverter:
    """角色转换工具类"""
    
    @staticmethod
    def to_full_role(scene_type: str, simplified_role: str) -> str:
        """
        将前端简化角色转换为后端完整角色
        
        Args:
            scene_type: 场景类型 (housing/dating/activity/business)
            simplified_role: 简化角色 (seeker/provider/organizer/participant)
            
        Returns:
            完整角色类型字符串
        """
        return RoleMapping.get_full_role(scene_type, simplified_role)
    
    @staticmethod
    def to_simplified_role(full_role: str) -> str:
        """
        将后端完整角色转换为前端简化角色
        
        Args:
            full_role: 完整角色类型字符串
            
        Returns:
            简化角色字符串
        """
        return RoleMapping.get_simplified_role(full_role)
    
    @staticmethod
    def get_available_roles(scene_type: str) -> list[str]:
        """
        获取指定场景下可用的完整角色列表
        
        Args:
            scene_type: 场景类型
            
        Returns:
            完整角色类型列表
        """
        return RoleMapping.get_available_roles(scene_type)
    
    @staticmethod
    def get_target_role(current_role: str) -> Optional[str]:
        """
        根据当前角色获取匹配目标角色
        
        Args:
            current_role: 当前用户的完整角色类型
            
        Returns:
            目标角色类型，如果没有对应映射则返回None
        """
        try:
            return RoleMapping.get_target_role(current_role)
        except Exception:
            return None
    
    @staticmethod
    def validate_role_pair(scene_type: str, role_type: str) -> bool:
        """
        验证场景和角色的组合是否有效
        
        Args:
            scene_type: 场景类型
            role_type: 完整角色类型
            
        Returns:
            是否有效的布尔值
        """
        available_roles = RoleMapping.get_available_roles(scene_type)
        return role_type in available_roles
    
    @staticmethod
    def extract_scene_from_role(full_role: str) -> Optional[str]:
        """
        从完整角色中提取场景类型
        
        Args:
            full_role: 完整角色类型字符串
            
        Returns:
            场景类型字符串，如果无法提取则返回None
        """
        if "_" in full_role:
            scene = full_role.split("_")[0]
            # 验证场景是否有效
            if scene in ["housing", "dating", "activity", "business"]:
                return scene
        return None