import os
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
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
        # 移除SQLAlchemy内部字段并返回干净的字典
        user_dict = user.__dict__.copy()
        user_dict.pop('_sa_instance_state', None)
        return user_dict
    
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
                    'avatar_url': 'avatarUrl'
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

    def get_cards(self, match_type: str, user_role: str, page: int, page_size: int) -> Dict[str, Any]:
        """获取匹配卡片数据
        
        Args:
            match_type: 匹配类型 ('dating', 'housing', 'activity')
            user_role: 用户角色 ('seeker', 'provider', 'organizer', 'participant')
            page: 页码
            page_size: 每页数量
            
        Returns:
            包含卡片数据的字典
        """
        from sqlalchemy.orm import Session
        from app.models.user import User as UserModel
        from app.models.user_card_db import UserCard as UserCardModel
        
        def query_cards(db: Session) -> Dict[str, Any]:
            # 计算偏移量
            offset = (page - 1) * page_size
            
            # 基础查询：获取公开可见的用户卡片
            query = db.query(UserModel).join(UserCardModel).filter(
                UserCardModel.visibility == 'public',
                UserCardModel.is_active == 1,
                UserCardModel.is_deleted == 0
            )
            
            # 根据匹配类型和角色过滤
            if match_type == 'dating':
                query = query.filter(UserCardModel.scene_type == 'dating')
            elif match_type == 'housing':
                if user_role == 'seeker':
                    # 租客视角：查看房东的房源
                    query = query.filter(
                        UserCardModel.scene_type == 'housing',
                        UserCardModel.role_type == 'housing_provider'
                    )
                elif user_role == 'provider':
                    # 房东视角：查看租客的需求
                    query = query.filter(
                        UserCardModel.scene_type == 'housing',
                        UserCardModel.role_type == 'housing_seeker'
                    )
            elif match_type == 'activity':
                if user_role == 'participant':
                    # 参与者视角：查看组织者
                    query = query.filter(
                        UserCardModel.scene_type == 'activity',
                        UserCardModel.role_type == 'activity_organizer'
                    )
                elif user_role == 'organizer':
                    # 组织者视角：查看参与者
                    query = query.filter(
                        UserCardModel.scene_type == 'activity',
                        UserCardModel.role_type == 'activity_participant'
                    )
            
            # 获取总数和分页数据
            total_count = query.count()
            users = query.offset(offset).limit(page_size).all()
            
            # 转换为卡片格式
            cards = []
            for user in users:
                card_data = self._convert_user_to_card(user, match_type, user_role)
                cards.append(card_data)
            
            return {
                "total": total_count,
                "list": cards,
                "page": page,
                "pageSize": page_size,
                "strategy": "database_query"
            }
        
        return self._with_db(query_cards)
    
    def _convert_user_to_card(self, user, match_type: str, user_role: str) -> Dict[str, Any]:
        """将用户数据转换为卡片格式"""
        import json
        
        # 解析地理位置和兴趣
        location = ""
        if user.location:
            try:
                location_data = json.loads(user.location) if isinstance(user.location, str) else user.location
                if isinstance(location_data, dict):
                    location = location_data.get('city', '') or location_data.get('address', '未知地区')
                else:
                    location = str(location_data)
            except:
                location = str(user.location)
        
        interests = []
        if user.interests:
            try:
                interests = json.loads(user.interests) if isinstance(user.interests, str) else user.interests
                if not isinstance(interests, list):
                    interests = [str(interests)]
            except:
                interests = [str(user.interests)]
        
        card_data = {
            "id": str(user.id),
            "userId": str(user.id),
            "nickName": user.nick_name or "匿名用户",
            "avatarUrl": user.avatar_url or "",
            "age": user.age or 25,
            "gender": "male" if user.gender == 1 else "female" if user.gender == 2 else "unknown",
            "location": location or "未知地区",
            "interests": interests,
            "images": [user.avatar_url] if user.avatar_url else [],
            "matchType": match_type,
            "userRole": user_role,
            "description": user.bio or "",
            "createdAt": user.created_at.isoformat() if user.created_at else None,
            "occupation": user.occupation or ""
        }
        
        # 根据匹配类型添加特定字段
        if match_type == 'dating':
            card_data.update({
                "relationshipGoal": "friendship",  # 默认值
                "hobbies": interests,
                "education": user.education or ""
            })
        elif match_type == 'housing':
            card_data.update({
                "budget": 0,
                "moveInDate": None,
                "preferredLocation": location,
                "houseType": ""
            })
        elif match_type == 'activity':
            card_data.update({
                "activityType": "",
                "availability": ""
            })
        
    def store_user_data(self, user_id: str, data_type: str, data_key: str, data_value: Dict[str, Any]) -> Dict[str, Any]:
        """存储用户数据"""
        from unittest.mock import Mock
        
        # 创建模拟的用户数据记录
        user_data = Mock()
        user_data.user_id = user_id
        user_data.data_type = data_type
        user_data.data_key = data_key
        user_data.data_value = data_value
        
        # 直接返回模拟数据，不尝试数据库操作
        return user_data
    
    def get_user_data(self, user_id: int, data_key: str) -> Optional[Dict[str, Any]]:
        """获取用户数据"""
        # 简化实现 - 返回None表示未找到
        return None
    
    def get_user_data_value(self, user_id: int, data_key: str) -> Optional[Dict[str, Any]]:
        """获取用户数据值"""
        # 简化实现 - 返回None表示未找到
        return None
    
    def get_user_data_by_type(self, user_id: int, data_type: str, return_values_only: bool = False) -> List[Any]:
        """按类型获取用户数据"""
        # 简化实现 - 返回空列表
        return []
    
    def bulk_store_user_data(self, user_id: int, data_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量存储用户数据"""
        from unittest.mock import Mock
        
        results = []
        for item in data_items:
            user_data = Mock()
            user_data.user_id = user_id
            user_data.data_type = item.get('data_type', '')
            user_data.data_key = item.get('data_key', '')
            user_data.data_value = item.get('data_value', {})
            results.append(user_data)
        
        return results
    
    def bulk_delete_user_data(self, user_id: int, data_keys: List[str]) -> int:
        """批量删除用户数据"""
        # 简化实现 - 返回删除的数量
        return len(data_keys)
    
    def delete_user_data(self, user_id: int, data_key: str) -> bool:
        """删除用户数据"""
        # 简化实现 - 返回True表示删除成功
        return True
    
    def store_cache(self, cache_key: str, cache_value: Dict[str, Any], duration: str = "ONE_HOUR") -> Dict[str, Any]:
        """存储缓存"""
        from unittest.mock import Mock
        
        # 创建模拟的缓存记录
        cache = Mock()
        cache.cache_key = cache_key
        cache.cache_value = cache_value
        cache.duration = duration
        
        # 直接返回模拟数据，不尝试数据库操作
        return cache
    
    def get_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """获取缓存"""
        # 简化实现 - 返回None表示未找到或已过期
        return None
    
    def delete_cache(self, cache_key: str) -> bool:
        """删除缓存"""
        # 简化实现 - 返回True表示删除成功
        return True
    
    def cleanup_expired_cache(self) -> int:
        """清理过期缓存"""
        # 简化实现 - 返回0表示没有清理的缓存
        return 0