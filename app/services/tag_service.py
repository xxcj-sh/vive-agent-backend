"""
标签服务层
处理标签相关的业务逻辑
创建时间: 2025-01-28
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from sqlalchemy.sql import func
from app.models.tag import Tag, UserTagRel, TagType, TagStatus, UserTagRelStatus
from app.models.schemas import BaseResponse
import math


class TagService:
    """标签服务类"""
    
    MAX_TAGS_PER_USER = 10  # 单个用户最多创建的标签数量
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_tag(
        self,
        user_id: str,
        name: str,
        tag_type: str = "user_community",
        desc: str = "",
        icon: str = "",
        max_members: Optional[int] = None,
        is_public: int = 1
    ) -> Dict[str, Any]:
        """
        创建标签
        
        Args:
            user_id: 创建用户ID
            name: 标签名称
            tag_type: 标签类型
            desc: 标签描述
            icon: 标签图标
            max_members: 最大成员数
            is_public: 是否公开
            
        Returns:
            创建结果
        """
        try:
            # 检查用户创建的标签数量
            tag_count = self.db.query(Tag).filter(
                and_(
                    Tag.create_user_id == user_id,
                    Tag.status == TagStatus.ACTIVE,
                    Tag.tag_type == TagType(tag_type)
                )
            ).count()
            
            if tag_count >= self.MAX_TAGS_PER_USER:
                return {
                    "code": 400,
                    "message": f"单个用户最多创建 {self.MAX_TAGS_PER_USER} 个标签",
                    "data": None
                }
            
            # 检查标签名称是否重复（同一类型下）
            existing_tag = self.db.query(Tag).filter(
                and_(
                    Tag.name == name,
                    Tag.tag_type == TagType(tag_type),
                    Tag.status == TagStatus.ACTIVE
                )
            ).first()
            
            if existing_tag:
                return {
                    "code": 400,
                    "message": f"标签名称 '{name}' 已存在",
                    "data": None
                }
            
            # 创建标签
            tag = Tag(
                name=name,
                desc=desc,
                icon=icon,
                tag_type=TagType(tag_type),
                create_user_id=user_id,
                max_members=max_members,
                is_public=is_public
            )
            
            self.db.add(tag)
            self.db.commit()
            self.db.refresh(tag)
            
            return {
                "code": 0,
                "message": "标签创建成功",
                "data": self._format_tag(tag)
            }
            
        except Exception as e:
            self.db.rollback()
            print(f"创建标签失败: {str(e)}")
            return {
                "code": 500,
                "message": f"创建标签失败: {str(e)}",
                "data": None
            }
    
    def get_tag(self, tag_id: int) -> Optional[Tag]:
        """获取标签详情"""
        return self.db.query(Tag).filter(
            and_(
                Tag.id == tag_id,
                Tag.status == TagStatus.ACTIVE
            )
        ).first()
    
    def get_tags(
        self,
        tag_type: Optional[str] = None,
        user_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        is_public: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        获取标签列表
        
        Args:
            tag_type: 标签类型筛选
            user_id: 创建者用户ID筛选
            page: 页码
            page_size: 每页数量
            is_public: 是否公开筛选
            
        Returns:
            标签列表和分页信息
        """
        query = self.db.query(Tag).filter(Tag.status == TagStatus.ACTIVE)
        
        if tag_type:
            query = query.filter(Tag.tag_type == TagType(tag_type))
        
        if user_id:
            query = query.filter(Tag.create_user_id == user_id)
        
        if is_public is not None:
            query = query.filter(Tag.is_public == is_public)
        
        # 获取总数
        total = query.count()
        
        # 分页
        offset = (page - 1) * page_size
        tags = query.order_by(Tag.created_at.desc()).offset(offset).limit(page_size).all()
        
        return {
            "items": [self._format_tag(tag) for tag in tags],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 0
        }
    
    def get_user_created_tags(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        获取用户创建的标签列表
        
        Args:
            user_id: 用户ID
            page: 页码
            page_size: 每页数量
            
        Returns:
            标签列表和分页信息
        """
        return self.get_tags(
            user_id=user_id,
            page=page,
            page_size=page_size
        )
    
    def update_tag(
        self,
        tag_id: int,
        user_id: str,
        name: Optional[str] = None,
        desc: Optional[str] = None,
        icon: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        更新标签（仅创建者可操作）
        
        Args:
            tag_id: 标签ID
            user_id: 当前用户ID
            name: 新名称
            desc: 新描述
            icon: 新图标
            
        Returns:
            更新结果
        """
        try:
            tag = self.get_tag(tag_id)
            
            if not tag:
                return {
                    "code": 404,
                    "message": "标签不存在",
                    "data": None
                }
            
            # 检查权限
            if tag.create_user_id != user_id:
                return {
                    "code": 403,
                    "message": "只有标签创建者可以编辑标签",
                    "data": None
                }
            
            # 更新字段
            if name is not None:
                # 检查名称是否重复
                existing = self.db.query(Tag).filter(
                    and_(
                        Tag.name == name,
                        Tag.tag_type == tag.tag_type,
                        Tag.status == TagStatus.ACTIVE,
                        Tag.id != tag_id
                    )
                ).first()
                
                if existing:
                    return {
                        "code": 400,
                        "message": f"标签名称 '{name}' 已存在",
                        "data": None
                    }
                
                tag.name = name
            
            if desc is not None:
                tag.desc = desc
            
            if icon is not None:
                tag.icon = icon
            
            self.db.commit()
            self.db.refresh(tag)
            
            return {
                "code": 0,
                "message": "标签更新成功",
                "data": self._format_tag(tag)
            }
            
        except Exception as e:
            self.db.rollback()
            print(f"更新标签失败: {str(e)}")
            return {
                "code": 500,
                "message": f"更新标签失败: {str(e)}",
                "data": None
            }
    
    def delete_tag(self, tag_id: int, user_id: str) -> Dict[str, Any]:
        """
        删除标签（软删除，仅创建者可操作）
        
        Args:
            tag_id: 标签ID
            user_id: 当前用户ID
            
        Returns:
            删除结果
        """
        try:
            tag = self.get_tag(tag_id)
            
            if not tag:
                return {
                    "code": 404,
                    "message": "标签不存在",
                    "data": None
                }
            
            # 检查权限
            if tag.create_user_id != user_id:
                return {
                    "code": 403,
                    "message": "只有标签创建者可以删除标签",
                    "data": None
                }
            
            # 软删除标签
            tag.status = TagStatus.DELETED
            self.db.commit()
            
            # 同时软删除关联的用户标签关系
            self.db.query(UserTagRel).filter(
                and_(
                    UserTagRel.tag_id == tag_id,
                    UserTagRel.status == UserTagRelStatus.ACTIVE
                )
            ).update({"status": UserTagRelStatus.DELETED})
            self.db.commit()
            
            return {
                "code": 0,
                "message": "标签删除成功",
                "data": {"tag_id": tag_id}
            }
            
        except Exception as e:
            self.db.rollback()
            print(f"删除标签失败: {str(e)}")
            return {
                "code": 500,
                "message": f"删除标签失败: {str(e)}",
                "data": None
            }
    
    def bind_tag_to_user(
        self,
        user_id: str,
        tag_id: int,
        granted_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        给用户绑定标签
        
        Args:
            user_id: 被绑定用户ID
            tag_id: 标签ID
            granted_by: 授予者用户ID
            
        Returns:
            绑定结果
        """
        try:
            tag = self.get_tag(tag_id)
            
            if not tag:
                return {
                    "code": 404,
                    "message": "标签不存在",
                    "data": None
                }
            
            if tag.status != TagStatus.ACTIVE:
                return {
                    "code": 400,
                    "message": "标签已删除",
                    "data": None
                }
            
            # 检查是否已绑定
            existing = self.db.query(UserTagRel).filter(
                and_(
                    UserTagRel.user_id == user_id,
                    UserTagRel.tag_id == tag_id,
                    UserTagRel.status == UserTagRelStatus.ACTIVE
                )
            ).first()
            
            if existing:
                return {
                    "code": 400,
                    "message": "用户已拥有该标签",
                    "data": None
                }
            
            # 检查成员数量限制
            if tag.max_members is not None:
                member_count = self.db.query(UserTagRel).filter(
                    and_(
                        UserTagRel.tag_id == tag_id,
                        UserTagRel.status == UserTagRelStatus.ACTIVE
                    )
                ).count()
                
                if member_count >= tag.max_members:
                    return {
                        "code": 400,
                        "message": f"标签成员数量已达上限 ({tag.max_members})",
                        "data": None
                    }
            
            # 创建关联
            user_tag_rel = UserTagRel(
                user_id=user_id,
                tag_id=tag_id,
                granted_by_user_id=granted_by
            )
            
            self.db.add(user_tag_rel)
            self.db.commit()
            self.db.refresh(user_tag_rel)
            
            return {
                "code": 0,
                "message": "标签绑定成功",
                "data": self._format_user_tag_rel(user_tag_rel)
            }
            
        except Exception as e:
            self.db.rollback()
            print(f"绑定标签失败: {str(e)}")
            return {
                "code": 500,
                "message": f"绑定标签失败: {str(e)}",
                "data": None
            }
    
    def unbind_tag_from_user(
        self,
        user_id: str,
        tag_id: int,
        operator_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        解绑用户标签
        
        Args:
            user_id: 被解绑用户ID
            tag_id: 标签ID
            operator_id: 操作者用户ID
            
        Returns:
            解绑结果
        """
        try:
            tag = self.get_tag(tag_id)
            
            if not tag:
                return {
                    "code": 404,
                    "message": "标签不存在",
                    "data": None
                }
            
            # 检查关联是否存在
            user_tag_rel = self.db.query(UserTagRel).filter(
                and_(
                    UserTagRel.user_id == user_id,
                    UserTagRel.tag_id == tag_id,
                    UserTagRel.status == UserTagRelStatus.ACTIVE
                )
            ).first()
            
            if not user_tag_rel:
                return {
                    "code": 404,
                    "message": "用户未拥有该标签",
                    "data": None
                }
            
            # 权限检查：用户本人或标签创建者可解绑
            if user_id != operator_id and tag.create_user_id != operator_id:
                return {
                    "code": 403,
                    "message": "无权解绑该标签",
                    "data": None
                }
            
            # 软删除关联
            user_tag_rel.status = UserTagRelStatus.DELETED
            self.db.commit()
            
            return {
                "code": 0,
                "message": "标签解绑成功",
                "data": {"user_id": user_id, "tag_id": tag_id}
            }
            
        except Exception as e:
            self.db.rollback()
            print(f"解绑标签失败: {str(e)}")
            return {
                "code": 500,
                "message": f"解绑标签失败: {str(e)}",
                "data": None
            }
    
    def get_user_tags(self, user_id: str) -> List[Dict[str, Any]]:
        """
        获取用户的所有标签
        
        Args:
            user_id: 用户ID
            
        Returns:
            标签列表
        """
        user_tag_rels = self.db.query(UserTagRel).filter(
            and_(
                UserTagRel.user_id == user_id,
                UserTagRel.status == UserTagRelStatus.ACTIVE
            )
        ).all()
        
        tags = []
        for rel in user_tag_rels:
            tag = self.get_tag(rel.tag_id)
            if tag and tag.status == TagStatus.ACTIVE:
                tag_data = self._format_tag(tag)
                tag_data['granted_by_user_id'] = rel.granted_by_user_id
                tag_data['bound_at'] = rel.created_at.isoformat() if rel.created_at else None
                tags.append(tag_data)
        
        return tags
    
    def get_tag_users(
        self,
        tag_id: int,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取标签下的用户列表
        
        Args:
            tag_id: 标签ID
            page: 页码
            page_size: 每页数量
            keyword: 搜索关键词
            
        Returns:
            用户列表和分页信息
        """
        from app.models.user import User
        
        tag = self.get_tag(tag_id)
        
        if not tag:
            return {
                "code": 404,
                "message": "标签不存在",
                "data": None
            }
        
        # 查询关联的用户
        query = self.db.query(UserTagRel).filter(
            and_(
                UserTagRel.tag_id == tag_id,
                UserTagRel.status == UserTagRelStatus.ACTIVE
            )
        )
        
        # 如果有关键词，关联用户表搜索
        if keyword:
            query = query.join(User, UserTagRel.user_id == User.id).filter(
                and_(
                    User.is_active == True,
                    or_(
                        User.nick_name.ilike(f'%{keyword}%'),
                        User.bio.ilike(f'%{keyword}%')
                    )
                )
            )
        
        total = query.count()
        offset = (page - 1) * page_size
        user_rels = query.order_by(UserTagRel.created_at.desc()).offset(offset).limit(page_size).all()
        
        users = []
        for rel in user_rels:
            user = self.db.query(User).filter(
                and_(
                    User.id == rel.user_id,
                    User.is_active == True
                )
            ).first()
            
            if user:
                users.append({
                    "user_id": user.id,
                    "nick_name": user.nick_name,
                    "avatar_url": user.avatar_url,
                    "bio": user.bio,
                    "bound_at": rel.created_at.isoformat() if rel.created_at else None
                })
        
        return {
            "code": 0,
            "message": "success",
            "data": {
                "tag": self._format_tag(tag),
                "users": users,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total": total,
                    "total_pages": math.ceil(total / page_size) if total > 0 else 0
                }
            }
        }
    
    def _format_tag(self, tag: Tag) -> Dict[str, Any]:
        """格式化标签数据"""
        return {
            "id": tag.id,
            "name": tag.name,
            "desc": tag.desc,
            "icon": tag.icon,
            "tag_type": tag.tag_type.value if tag.tag_type else None,
            "create_user_id": tag.create_user_id,
            "max_members": tag.max_members,
            "is_public": tag.is_public,
            "created_at": tag.created_at.isoformat() if tag.created_at else None,
            "updated_at": tag.updated_at.isoformat() if tag.updated_at else None
        }
    
    def _format_user_tag_rel(self, rel: UserTagRel) -> Dict[str, Any]:
        """格式化用户标签关联数据"""
        return {
            "id": rel.id,
            "user_id": rel.user_id,
            "tag_id": rel.tag_id,
            "granted_by_user_id": rel.granted_by_user_id,
            "created_at": rel.created_at.isoformat() if rel.created_at else None
        }
