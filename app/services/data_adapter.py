import os
from typing import Any, Dict, List, Optional
# 使用数据库服务
from app.services.db_service import (
    create_user, get_user, get_user_by_email, get_users, update_user, delete_user,
    create_match, get_match, get_matches, update_match, delete_match,
    add_match_detail, get_match_details
)
from sqlalchemy.orm import Session
from app.utils.db_config import get_db

class DataService:
    """数据服务适配器 - 始终使用数据库"""
    
    def __init__(self):
        """初始化数据服务"""
        # 移除环境判断和mock服务相关代码
        pass
    
    def _get_db(self):
        """获取数据库会话生成器"""
        return get_db()
    
    def _with_db(self, func, *args, **kwargs):
        """使用数据库会话执行函数"""
        db_gen = self._get_db()
        db = next(db_gen)
        try:
            return func(db, *args, **kwargs)
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass
    
    # 用户相关方法
    def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """创建用户"""
        user = self._with_db(create_user, user_data)
        return user.__dict__
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取用户"""
        try:
            user = self._with_db(get_user, user_id)
            if user:
                # 将数据库字段映射回前端字段
                user_dict = user.__dict__.copy()
                # 移除SQLAlchemy内部字段
                user_dict.pop('_sa_instance_state', None)
                
                # 字段映射：数据库字段名 -> 前端字段名
                reverse_mapping = {
                    'nick_name': 'nickName',
                    'avatar_url': 'avatarUrl',
                    'match_type': 'matchType',
                    'user_role': 'userRole',
                    'join_date': 'joinDate'
                }
                
                # 应用反向映射
                mapped_dict = {}
                for db_field, value in user_dict.items():
                    frontend_field = reverse_mapping.get(db_field, db_field)
                    mapped_dict[frontend_field] = value
                
                return mapped_dict
            return None
        except Exception as e:
            print(f"获取用户失败: {str(e)}")
            return None
    
    def get_user_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        """根据token获取用户信息"""
        # 从数据库获取用户（通过token作为用户ID）
        try:
            user = self._with_db(get_user, token)  # token就是用户ID
            if user:
                # 将数据库字段映射回前端字段
                user_dict = user.__dict__.copy()
                # 移除SQLAlchemy内部字段
                user_dict.pop('_sa_instance_state', None)
                
                # 字段映射：数据库字段名 -> 前端字段名
                reverse_mapping = {
                    'nick_name': 'nickName',
                    'avatar_url': 'avatarUrl',
                    'match_type': 'matchType',
                    'user_role': 'userRole',
                    'join_date': 'joinDate'
                }
                
                # 应用反向映射
                mapped_dict = {}
                for db_field, value in user_dict.items():
                    frontend_field = reverse_mapping.get(db_field, db_field)
                    mapped_dict[frontend_field] = value
                
                return mapped_dict
        except Exception as e:
            print(f"通过token获取用户失败: {str(e)}")
        
        return None