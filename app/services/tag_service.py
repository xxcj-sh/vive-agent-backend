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
from app.models.community_invitation import CommunityInvitation, InvitationStatus, InvitationUsage
from app.models.tag_content import TagContent, ContentType, ContentStatus, ContentTagInteraction
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
    
    # ==================== 社群邀请功能 ====================
    
    def create_community_invitation(
        self,
        tag_id: int,
        inviter_user_id: str,
        description: str = "",
        max_uses: Optional[int] = None,
        expires_at: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """创建社群邀请码
        
        Args:
            tag_id: 社群标签ID
            inviter_user_id: 邀请人用户ID
            description: 邀请描述
            max_uses: 最大使用次数
            expires_at: 过期时间
            
        Returns:
            创建结果
        """
        try:
            tag = self.get_tag(tag_id)
            
            if not tag:
                return {
                    "code": 404,
                    "message": "标签不存在",
                    "data": None
                }
            
            if tag.tag_type.value != "user_community":
                return {
                    "code": 400,
                    "message": "仅社群标签可以创建邀请",
                    "data": None
                }
            
            if tag.create_user_id != inviter_user_id:
                return {
                    "code": 403,
                    "message": "只有标签创建者可以创建邀请",
                    "data": None
                }
            
            from app.models.community_invitation import create_invitation_code
            
            invitation = CommunityInvitation(
                code=create_invitation_code(),
                tag_id=tag_id,
                inviter_user_id=inviter_user_id,
                description=description,
                max_uses=max_uses,
                expires_at=expires_at,
                status=InvitationStatus.PENDING
            )
            
            self.db.add(invitation)
            self.db.commit()
            self.db.refresh(invitation)
            
            return {
                "code": 0,
                "message": "邀请码创建成功",
                "data": self._format_invitation(invitation)
            }
            
        except Exception as e:
            self.db.rollback()
            print(f"创建邀请码失败: {str(e)}")
            return {
                "code": 500,
                "message": f"创建邀请码失败: {str(e)}",
                "data": None
            }
    
    def get_invitation(self, invitation_id: int) -> Optional[CommunityInvitation]:
        """获取邀请详情"""
        return self.db.query(CommunityInvitation).filter(
            and_(
                CommunityInvitation.id == invitation_id,
                CommunityInvitation.status == InvitationStatus.PENDING
            )
        ).first()
    
    def get_invitation_by_code(self, code: str) -> Optional[CommunityInvitation]:
        """通过邀请码获取邀请"""
        return self.db.query(CommunityInvitation).filter(
            and_(
                CommunityInvitation.code == code,
                CommunityInvitation.status == InvitationStatus.PENDING
            )
        ).first()
    
    def redeem_invitation(
        self,
        code: str,
        user_id: str
    ) -> Dict[str, Any]:
        """使用邀请码加入社群
        
        Args:
            code: 邀请码
            user_id: 用户ID
            
        Returns:
            使用结果
        """
        try:
            invitation = self.get_invitation_by_code(code)
            
            if not invitation:
                return {
                    "code": 404,
                    "message": "邀请码不存在或已失效",
                    "data": None
                }
            
            if invitation.status != InvitationStatus.PENDING:
                return {
                    "code": 400,
                    "message": "邀请码已失效",
                    "data": None
                }
            
            if invitation.expires_at and invitation.expires_at < datetime.now():
                invitation.status = InvitationStatus.EXPIRED
                self.db.commit()
                return {
                    "code": 400,
                    "message": "邀请码已过期",
                    "data": None
                }
            
            if invitation.max_uses is not None and invitation.used_count >= invitation.max_uses:
                invitation.status = InvitationStatus.EXPIRED
                self.db.commit()
                return {
                    "code": 400,
                    "message": "邀请码已达使用上限",
                    "data": None
                }
            
            check_usage = self.db.query(InvitationUsage).filter(
                and_(
                    InvitationUsage.invitation_id == invitation.id,
                    InvitationUsage.invited_user_id == user_id
                )
            ).first()
            
            if check_usage:
                return {
                    "code": 400,
                    "message": "您已使用过该邀请码",
                    "data": None
                }
            
            result = self.bind_tag_to_user(
                user_id=user_id,
                tag_id=invitation.tag_id,
                granted_by=invitation.inviter_user_id
            )
            
            if result["code"] != 0:
                return result
            
            invitation.used_count += 1
            
            if invitation.max_uses is not None and invitation.used_count >= invitation.max_uses:
                invitation.status = InvitationStatus.USED
            
            usage_record = InvitationUsage(
                invitation_id=invitation.id,
                invited_user_id=user_id
            )
            self.db.add(usage_record)
            self.db.commit()
            
            tag = self.get_tag(invitation.tag_id)
            
            return {
                "code": 0,
                "message": "成功加入社群",
                "data": {
                    "invitation": self._format_invitation(invitation),
                    "tag": self._format_tag(tag) if tag else None
                }
            }
            
        except Exception as e:
            self.db.rollback()
            print(f"使用邀请码失败: {str(e)}")
            return {
                "code": 500,
                "message": f"使用邀请码失败: {str(e)}",
                "data": None
            }
    
    def get_user_invitations(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取用户创建的邀请列表
        
        Args:
            user_id: 用户ID
            page: 页码
            page_size: 每页数量
            
        Returns:
            邀请列表和分页信息
        """
        query = self.db.query(CommunityInvitation).filter(
            and_(
                CommunityInvitation.inviter_user_id == user_id,
                CommunityInvitation.status != InvitationStatus.CANCELLED
            )
        )
        
        total = query.count()
        offset = (page - 1) * page_size
        invitations = query.order_by(CommunityInvitation.created_at.desc()).offset(offset).limit(page_size).all()
        
        return {
            "items": [self._format_invitation(inv) for inv in invitations],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 0
        }
    
    def get_tag_invitations(
        self,
        tag_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取标签的邀请列表
        
        Args:
            tag_id: 标签ID
            page: 页码
            page_size: 每页数量
            
        Returns:
            邀请列表和分页信息
        """
        query = self.db.query(CommunityInvitation).filter(
            and_(
                CommunityInvitation.tag_id == tag_id,
                CommunityInvitation.status != InvitationStatus.CANCELLED
            )
        )
        
        total = query.count()
        offset = (page - 1) * page_size
        invitations = query.order_by(CommunityInvitation.created_at.desc()).offset(offset).limit(page_size).all()
        
        return {
            "items": [self._format_invitation(inv) for inv in invitations],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if total > 0 else 0
        }
    
    def cancel_invitation(
        self,
        invitation_id: int,
        user_id: str
    ) -> Dict[str, Any]:
        """取消邀请
        
        Args:
            invitation_id: 邀请ID
            user_id: 当前用户ID
            
        Returns:
            取消结果
        """
        try:
            invitation = self.db.query(CommunityInvitation).filter(
                and_(
                    CommunityInvitation.id == invitation_id,
                    CommunityInvitation.status == InvitationStatus.PENDING
                )
            ).first()
            
            if not invitation:
                return {
                    "code": 404,
                    "message": "邀请不存在",
                    "data": None
                }
            
            if invitation.inviter_user_id != user_id:
                return {
                    "code": 403,
                    "message": "只有邀请创建者可以取消邀请",
                    "data": None
                }
            
            invitation.status = InvitationStatus.CANCELLED
            self.db.commit()
            
            return {
                "code": 0,
                "message": "邀请已取消",
                "data": {"invitation_id": invitation_id}
            }
            
        except Exception as e:
            self.db.rollback()
            print(f"取消邀请失败: {str(e)}")
            return {
                "code": 500,
                "message": f"取消邀请失败: {str(e)}",
                "data": None
            }
    
    def _format_invitation(self, invitation: CommunityInvitation) -> Dict[str, Any]:
        """格式化邀请数据"""
        tag = self.get_tag(invitation.tag_id)
        return {
            "id": invitation.id,
            "code": invitation.code,
            "tag_id": invitation.tag_id,
            "tag_name": tag.name if tag else None,
            "inviter_user_id": invitation.inviter_user_id,
            "description": invitation.description,
            "max_uses": invitation.max_uses,
            "used_count": invitation.used_count,
            "remaining_uses": (invitation.max_uses - invitation.used_count) if invitation.max_uses else None,
            "expires_at": invitation.expires_at.isoformat() if invitation.expires_at else None,
            "status": invitation.status.value,
            "created_at": invitation.created_at.isoformat() if invitation.created_at else None
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
