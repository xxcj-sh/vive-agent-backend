"""
标签服务层
处理标签相关的业务逻辑
创建时间: 2025-01-28
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from sqlalchemy.sql import func
from app.models.tag import Tag, UserTagRel, TagType, TagStatus, UserTagRelStatus
from app.models.schemas import BaseResponse
from app.models.tag_content import TagContent, ContentType, ContentStatus, ContentTagInteraction
from app.models.user_profile import UserProfile
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
            # 先检查 ACTIVE 状态的标签
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
            
            # 检查是否有已删除的同名标签（同一类型、同一创建者），如果有则恢复
            deleted_tag = self.db.query(Tag).filter(
                and_(
                    Tag.name == name,
                    Tag.tag_type == TagType(tag_type),
                    Tag.create_user_id == user_id,
                    Tag.status == TagStatus.DELETED
                )
            ).first()
            
            if deleted_tag:
                # 恢复已删除的标签
                deleted_tag.status = TagStatus.ACTIVE
                deleted_tag.desc = desc
                deleted_tag.icon = icon
                deleted_tag.max_members = max_members
                deleted_tag.is_public = is_public
                self.db.commit()
                self.db.refresh(deleted_tag)
                print(f"[TagService] 标签已恢复: tag.id={deleted_tag.id}, create_user_id={user_id}")
                
                # 恢复创建者的标签关系
                self.db.query(UserTagRel).filter(
                    and_(
                        UserTagRel.tag_id == deleted_tag.id,
                        UserTagRel.user_id == user_id,
                        UserTagRel.status == UserTagRelStatus.DELETED
                    )
                ).update({"status": UserTagRelStatus.ACTIVE})
                self.db.commit()
                
                return {
                    "code": 0,
                    "message": "标签已恢复",
                    "data": self._format_tag(deleted_tag)
                }
            
            # 创建新标签
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
            print(f"[TagService] 标签创建成功: tag.id={tag.id}, create_user_id={user_id}")
            
            # 自动将创建者加入标签
            user_tag_rel = UserTagRel(
                user_id=user_id,
                tag_id=tag.id,
                granted_by_user_id=user_id,
                status=UserTagRelStatus.ACTIVE
            )
            self.db.add(user_tag_rel)
            self.db.commit()
            print(f"[TagService] 创建者加入标签成功: user_id={user_id}, tag_id={tag.id}")
            
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
    
    def _update_tag_member_count(self, tag_id: int):
        """更新标签的成员数量"""
        try:
            member_count = self.db.query(UserTagRel).filter(
                and_(
                    UserTagRel.tag_id == tag_id,
                    UserTagRel.status == UserTagRelStatus.ACTIVE
                )
            ).count()
            
            self.db.query(Tag).filter(Tag.id == tag_id).update({
                Tag.member_count: member_count
            })
            
            self.db.commit()
            print(f"[TagService] 更新标签 {tag_id} 的成员数量为 {member_count}")
        except Exception as e:
            self.db.rollback()
            print(f"[TagService] 更新成员数量失败: {str(e)}")
    
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
            
            self._update_tag_member_count(tag_id)
            
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
            
            self._update_tag_member_count(tag_id)
            
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
        print(f"[TagService] get_user_tags: user_id={user_id}")
        
        # 使用原始SQL查询避免枚举转换问题
        from sqlalchemy import text
        result = self.db.execute(text("""
            SELECT tag_id, granted_by_user_id, created_at 
            FROM user_tag_rel 
            WHERE user_id = :user_id AND status = 'active'
        """), {"user_id": user_id})
        user_tag_rels = result.fetchall()
        
        print(f"[TagService] get_user_tags: 查询到 {len(user_tag_rels)} 条 UserTagRel 记录")
        
        tags = []
        for rel in user_tag_rels:
            tag_id, granted_by_user_id, created_at = rel
            tag = self.get_tag(tag_id)
            print(f"[TagService] get_user_tags: rel.tag_id={tag_id}, tag={tag}")
            if tag and tag.status == TagStatus.ACTIVE:
                tag_data = self._format_tag(tag)
                tag_data['granted_by_user_id'] = granted_by_user_id
                tag_data['bound_at'] = created_at.isoformat() if created_at else None
                tags.append(tag_data)
        
        print(f"[TagService] get_user_tags: 返回 {len(tags)} 个标签")
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
        
        query = self.db.query(UserTagRel).filter(
            and_(
                UserTagRel.tag_id == tag_id,
                UserTagRel.status == UserTagRelStatus.ACTIVE
            )
        )
        
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
            user_profile = self.db.query(UserProfile).filter(
                UserProfile.user_id == rel.user_id
            ).first()
            
            user = self.db.query(User).filter(
                and_(
                    User.id == rel.user_id,
                    User.is_active == True
                )
            ).first()
            
            user_info = {
                "user_id": rel.user_id,
                "avatar_url": user.avatar_url if user else None,
                "profile_summary": user_profile.profile_summary if user_profile else None,
                "bound_at": rel.created_at.isoformat() if rel.created_at else None,
                "nick_name": user.nick_name if user else None,
            }
            
            users.append(user_info)
        
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
            "member_count": tag.member_count or 0,
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

    # ==================== 标签内容推送功能 ====================
    
    def create_tag_content(
        self,
        title: str,
        content: str,
        content_type: str,
        tag_ids: List[int],
        cover_image: str = "",
        priority: int = 0,
        created_by: str = ""
    ) -> Dict[str, Any]:
        """创建标签推送内容
        
        Args:
            title: 内容标题
            content: 内容详情
            content_type: 内容类型
            tag_ids: 关联标签ID列表
            cover_image: 封面图
            priority: 优先级
            created_by: 创建者用户ID
            
        Returns:
            创建结果
        """
        try:
            for tag_id in tag_ids:
                tag = self.get_tag(tag_id)
                if not tag:
                    return {
                        "code": 404,
                        "message": f"标签ID {tag_id} 不存在",
                        "data": None
                    }
            
            tag_content = TagContent(
                title=title,
                content=content,
                content_type=ContentType(content_type),
                tag_ids=tag_ids,
                cover_image=cover_image,
                priority=priority,
                status=ContentStatus.DRAFT,
                created_by=created_by
            )
            
            self.db.add(tag_content)
            self.db.commit()
            self.db.refresh(tag_content)
            
            return {
                "code": 0,
                "message": "内容创建成功",
                "data": self._format_tag_content(tag_content)
            }
            
        except Exception as e:
            self.db.rollback()
            print(f"创建内容失败: {str(e)}")
            return {
                "code": 500,
                "message": f"创建内容失败: {str(e)}",
                "data": None
            }
    
    def publish_tag_content(
        self,
        content_id: int,
        user_id: str
    ) -> Dict[str, Any]:
        """发布标签内容
        
        Args:
            content_id: 内容ID
            user_id: 当前用户ID
            
        Returns:
            发布结果
        """
        try:
            tag_content = self.db.query(TagContent).filter(TagContent.id == content_id).first()
            
            if not tag_content:
                return {
                    "code": 404,
                    "message": "内容不存在",
                    "data": None
                }
            
            if tag_content.created_by != user_id:
                return {
                    "code": 403,
                    "message": "只有创建者可以发布内容",
                    "data": None
                }
            
            tag_content.status = ContentStatus.PUBLISHED
            tag_content.published_at = datetime.now()
            self.db.commit()
            self.db.refresh(tag_content)
            
            return {
                "code": 0,
                "message": "内容发布成功",
                "data": self._format_tag_content(tag_content)
            }
            
        except Exception as e:
            self.db.rollback()
            print(f"发布内容失败: {str(e)}")
            return {
                "code": 500,
                "message": f"发布内容失败: {str(e)}",
                "data": None
            }
    
    def get_tag_contents(
        self,
        tag_id: int,
        page: int = 1,
        page_size: int = 20,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取标签的内容列表
        
        Args:
            tag_id: 标签ID
            page: 页码
            page_size: 每页数量
            content_type: 内容类型筛选
            
        Returns:
            内容列表和分页信息
        """
        query = self.db.query(TagContent).filter(
            and_(
                TagContent.status == ContentStatus.PUBLISHED,
                TagContent.tag_ids.contains([tag_id])
            )
        )
        
        if content_type:
            query = query.filter(TagContent.content_type == ContentType(content_type))
        
        total = query.count()
        offset = (page - 1) * page_size
        contents = query.order_by(
            TagContent.priority.desc(),
            TagContent.published_at.desc()
        ).offset(offset).limit(page_size).all()
        
        return {
            "items": [self._format_tag_content(c) for c in contents],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 0
        }
    
    def get_contents_by_tags(
        self,
        tag_ids: List[int],
        page: int = 1,
        page_size: int = 20,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """根据标签列表获取内容（用于推荐）
        
        Args:
            tag_ids: 标签ID列表
            page: 页码
            page_size: 每页数量
            content_type: 内容类型筛选
            
        Returns:
            内容列表和分页信息
        """
        conditions = [
            TagContent.status == ContentStatus.PUBLISHED
        ]
        
        if tag_ids:
            conditions.append(
                or_(*[TagContent.tag_ids.contains([tag_id]) for tag_id in tag_ids])
            )
        
        query = self.db.query(TagContent).filter(and_(*conditions))
        
        if content_type:
            query = query.filter(TagContent.content_type == ContentType(content_type))
        
        total = query.count()
        offset = (page - 1) * page_size
        contents = query.order_by(
            TagContent.priority.desc(),
            TagContent.published_at.desc()
        ).offset(offset).limit(page_size).all()
        
        return {
            "items": [self._format_tag_content(c) for c in contents],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 0
        }
    
    def get_content_detail(self, content_id: int) -> Optional[TagContent]:
        """获取内容详情"""
        from app.models.tag_content import TagContent, ContentStatus
        return self.db.query(TagContent).filter(
            and_(
                TagContent.id == content_id,
                TagContent.status == ContentStatus.PUBLISHED
            )
        ).first()
    
    def interact_with_content(
        self,
        content_id: int,
        user_id: str,
        interaction_type: str
    ) -> Dict[str, Any]:
        """内容交互（浏览、点赞、分享）
        
        Args:
            content_id: 内容ID
            user_id: 用户ID
            interaction_type: 交互类型
            
        Returns:
            交互结果
        """
        try:
            tag_content = self.get_content_detail(content_id)
            
            if not tag_content:
                return {
                    "code": 404,
                    "message": "内容不存在",
                    "data": None
                }
            
            existing = self.db.query(ContentTagInteraction).filter(
                and_(
                    ContentTagInteraction.content_id == content_id,
                    ContentTagInteraction.user_id == user_id,
                    ContentTagInteraction.interaction_type == interaction_type
                )
            ).first()
            
            if existing:
                action_map = {"like": "点赞", "view": "浏览", "share": "分享"}
                action = action_map.get(interaction_type, "")
                return {
                    "code": 400,
                    "message": f"已{action}过该内容",
                    "data": None
                }
            
            interaction = ContentTagInteraction(
                content_id=content_id,
                user_id=user_id,
                interaction_type=interaction_type
            )
            self.db.add(interaction)
            
            if interaction_type == "view":
                tag_content.view_count += 1
            elif interaction_type == "like":
                tag_content.like_count += 1
            elif interaction_type == "share":
                tag_content.share_count += 1
            
            self.db.commit()
            
            return {
                "code": 0,
                "message": "操作成功",
                "data": {
                    "view_count": tag_content.view_count,
                    "like_count": tag_content.like_count,
                    "share_count": tag_content.share_count
                }
            }
            
        except Exception as e:
            self.db.rollback()
            print(f"内容交互失败: {str(e)}")
            return {
                "code": 500,
                "message": f"操作失败: {str(e)}",
                "data": None
            }
    
    def get_user_recommended_contents(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取用户的推荐内容（根据用户标签）
        
        Args:
            user_id: 用户ID
            page: 页码
            page_size: 每页数量
            content_type: 内容类型筛选
            
        Returns:
            推荐内容列表
        """
        user_tags = self.get_user_tags(user_id)
        tag_ids = [tag["id"] for tag in user_tags]
        
        if not tag_ids:
            return {
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "total_pages": 0
            }
        
        return self.get_contents_by_tags(
            tag_ids=tag_ids,
            page=page,
            page_size=page_size,
            content_type=content_type
        )
    
    def _format_tag_content(self, content: TagContent) -> Dict[str, Any]:
        """格式化内容数据"""
        tags = []
        for tag_id in content.tag_ids:
            tag = self.get_tag(tag_id)
            if tag:
                tags.append(self._format_tag(tag))
        
        return {
            "id": content.id,
            "title": content.title,
            "content": content.content,
            "content_type": content.content_type.value if content.content_type else None,
            "target_id": content.target_id,
            "cover_image": content.cover_image,
            "tags": tags,
            "priority": content.priority,
            "status": content.status.value if content.status else None,
            "view_count": content.view_count,
            "like_count": content.like_count,
            "share_count": content.share_count,
            "created_by": content.created_by,
            "created_at": content.created_at.isoformat() if content.created_at else None,
            "published_at": content.published_at.isoformat() if content.published_at else None
        }
