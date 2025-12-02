from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.topic_card_db import TopicCard, TopicDiscussion
from app.models.topic_card import TopicCardCreate, TopicCardUpdate, TopicCardResponse, TopicDiscussionCreate, TopicDiscussionResponse
from app.models.user import User

class TopicCardService:
    """话题卡片服务类"""
    
    @staticmethod
    def create_topic_card(db: Session, user_id: str, card_data: TopicCardCreate) -> TopicCardResponse:
        """创建话题卡片"""
        try:
            # 创建话题卡片
            topic_card = TopicCard(
                user_id=user_id,
                title=card_data.title,
                description=card_data.description,
                discussion_goal=card_data.discussion_goal,
                category=card_data.category,
                tags=card_data.tags,
                cover_image=card_data.cover_image,
                visibility=card_data.visibility,
                is_active=1,
                is_deleted=0,
                is_anonymous=1 if card_data.is_anonymous else 0
            )
            
            db.add(topic_card)
            db.commit()
            db.refresh(topic_card)
            
            # 获取创建者信息
            creator = db.query(User).filter(User.id == user_id).first()
            
            # 构建响应数据
            return TopicCardResponse(
                id=topic_card.id,
                user_id=topic_card.user_id,
                title=topic_card.title,
                description=topic_card.description,
                discussion_goal=topic_card.discussion_goal,
                category=topic_card.category,
                tags=topic_card.tags or [],
                cover_image=topic_card.cover_image,
                visibility=topic_card.visibility,
                is_active=topic_card.is_active,
                is_anonymous=topic_card.is_anonymous,
                view_count=topic_card.view_count,
                like_count=topic_card.like_count,
                discussion_count=topic_card.discussion_count,
                created_at=topic_card.created_at,
                updated_at=topic_card.updated_at,
                # 返回创建者信息（前端会根据需要处理匿名显示）
                creator_nickname=creator.nick_name if creator else None,
                creator_avatar=creator.avatar_url if creator else None,
                trigger_conditions=[]  # 添加缺失的触发条件字段
            )
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def get_topic_cards(
        db: Session, 
        user_id: Optional[str] = None,
        page: int = 1, 
        page_size: int = 10,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取话题卡片列表"""
        try:
            # 构建查询条件
            query = db.query(TopicCard, User).join(User, TopicCard.user_id == User.id)
            
            # 只显示激活且未删除的卡片
            query = query.filter(
                TopicCard.is_active == 1,
                TopicCard.is_deleted == 0
            )
            
            # 分类筛选
            if category:
                query = query.filter(TopicCard.category == category)
            
            # 搜索筛选
            if search:
                query = query.filter(
                    or_(
                        TopicCard.title.contains(search),
                        TopicCard.description.contains(search),
                        TopicCard.tags.contains([search])
                    )
                )
            
            # 获取总数
            total = query.count()
            
            # 分页查询
            offset = (page - 1) * page_size
            results = query.order_by(TopicCard.created_at.desc()).offset(offset).limit(page_size).all()
            
            # 构建响应数据
            cards = []
            for topic_card, creator in results:
                card_response = TopicCardResponse(
                    id=topic_card.id,
                    user_id=topic_card.user_id,
                    title=topic_card.title,
                    description=topic_card.description,
                    discussion_goal=topic_card.discussion_goal,
                    category=topic_card.category,
                    tags=topic_card.tags or [],
                    cover_image=topic_card.cover_image,
                    visibility=topic_card.visibility,
                    is_active=topic_card.is_active,
                    is_anonymous=topic_card.is_anonymous,
                    view_count=topic_card.view_count,
                    like_count=topic_card.like_count,
                    discussion_count=topic_card.discussion_count,
                    created_at=topic_card.created_at,
                    updated_at=topic_card.updated_at,
                    # 返回创建者信息（前端会根据需要处理匿名显示）
                    creator_nickname=creator.nick_name if creator else None,
                    creator_avatar=creator.avatar_url if creator else None,
                    trigger_conditions=[]  # 添加缺失的触发条件字段
                )
                cards.append(card_response)
            
            total_pages = (total + page_size - 1) // page_size
            return {
                "total": total,
                "items": cards,
                "page": page,
                "pageSize": page_size,
                "totalPages": total_pages
            }
        except Exception as e:
            raise e
    
    @staticmethod
    def get_topic_card_detail(db: Session, card_id: str, user_id: Optional[str] = None, invitation_id: Optional[str] = None) -> Optional[TopicCardResponse]:
        """获取话题卡片详情"""
        try:
            # 查询话题卡片和创建者信息
            result = db.query(TopicCard, User).join(User, TopicCard.user_id == User.id).filter(
                TopicCard.id == card_id,
                TopicCard.is_deleted == 0
            ).first()
            
            if not result:
                return None
            
            topic_card, creator = result
            
            # 检查可见性权限
            if topic_card.visibility == "private" and topic_card.user_id != user_id:
                return None
            
            # 增加浏览次数
            topic_card.view_count += 1
            db.commit()
            
            # 初始化邀请者信息
            inviter_nickname = None
            inviter_avatar = None
            is_invited = False
            
            # 如果有邀请ID，获取邀请者信息
            if invitation_id and user_id:
                from app.models.topic_invitation import TopicInvitation
                invitation = db.query(TopicInvitation).filter(
                    TopicInvitation.id == invitation_id,
                    TopicInvitation.topic_id == card_id,
                    TopicInvitation.invitee_id == user_id,
                    TopicInvitation.status == "accepted"
                ).first()
                
                if invitation:
                    is_invited = True
                    # 如果邀请不是匿名，获取邀请者信息
                    if not invitation.is_anonymous:
                        inviter = db.query(User).filter(User.id == invitation.inviter_id).first()
                        if inviter:
                            inviter_nickname = inviter.nick_name
                            inviter_avatar = inviter.avatar_url
                    else:
                        inviter_nickname = "匿名用户"
                        inviter_avatar = None
            
            return TopicCardResponse(
                id=topic_card.id,
                user_id=topic_card.user_id,
                title=topic_card.title,
                description=topic_card.description,
                discussion_goal=topic_card.discussion_goal,
                category=topic_card.category,
                tags=topic_card.tags or [],
                cover_image=topic_card.cover_image,
                visibility=topic_card.visibility,
                is_active=topic_card.is_active,
                is_anonymous=topic_card.is_anonymous,
                view_count=topic_card.view_count,
                like_count=topic_card.like_count,
                discussion_count=topic_card.discussion_count,
                created_at=topic_card.created_at,
                updated_at=topic_card.updated_at,
                # 返回创建者信息（前端会根据需要处理匿名显示）
                creator_nickname=creator.nick_name if creator else None,
                creator_avatar=creator.avatar_url if creator else None,
                # 返回邀请者信息
                inviter_nickname=inviter_nickname,
                inviter_avatar=inviter_avatar,
                is_invited=is_invited,
                trigger_conditions=[]  # 添加缺失的触发条件字段
            )
        except Exception as e:
            raise e
    
    @staticmethod
    def update_topic_card(db: Session, card_id: str, update_data: TopicCardUpdate) -> Optional[TopicCardResponse]:
        """更新话题卡片"""
        try:
            topic_card = db.query(TopicCard).filter(TopicCard.id == card_id).first()
            if not topic_card:
                return None
            
            # 更新字段
            update_dict = update_data.dict(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(topic_card, field, value)
            
            topic_card.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(topic_card)
            
            # 获取创建者信息
            creator = db.query(User).filter(User.id == topic_card.user_id).first()
            
            return TopicCardResponse(
                id=topic_card.id,
                user_id=topic_card.user_id,
                title=topic_card.title,
                description=topic_card.description,
                discussion_goal=topic_card.discussion_goal,
                category=topic_card.category,
                tags=topic_card.tags or [],
                cover_image=topic_card.cover_image,
                visibility=topic_card.visibility,
                is_active=topic_card.is_active,
                view_count=topic_card.view_count,
                like_count=topic_card.like_count,
                discussion_count=topic_card.discussion_count,
                created_at=topic_card.created_at,
                updated_at=topic_card.updated_at,
                creator_nickname=creator.nick_name if creator else None,
                creator_avatar=creator.avatar_url if creator else None,
                trigger_conditions=[]  # 添加缺失的触发条件字段
            )
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def delete_topic_card(db: Session, card_id: str) -> bool:
        """删除话题卡片"""
        try:
            topic_card = db.query(TopicCard).filter(TopicCard.id == card_id).first()
            if not topic_card:
                return False
            
            # 软删除
            topic_card.is_deleted = 1
            topic_card.updated_at = datetime.utcnow()
            db.commit()
            
            return True
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def create_topic_discussion(
        db: Session, 
        card_id: str, 
        participant_id: str, 
        discussion_data: TopicDiscussionCreate
    ) -> TopicDiscussionResponse:
        """创建话题讨论"""
        try:
            # 获取话题卡片信息
            topic_card = db.query(TopicCard).filter(TopicCard.id == card_id).first()
            if not topic_card:
                raise ValueError("话题卡片不存在")
            
            # 创建讨论记录
            discussion = TopicDiscussion(
                topic_card_id=card_id,
                participant_id=participant_id,
                host_id=topic_card.user_id,
                message=discussion_data.message,
                message_type=discussion_data.message_type,
                is_anonymous=discussion_data.is_anonymous,
                is_deleted=0
            )
            
            db.add(discussion)
            
            # 更新讨论次数
            topic_card.discussion_count += 1
            
            db.commit()
            db.refresh(discussion)
            
            # 获取参与者信息（非匿名时）
            participant = None
            if not discussion_data.is_anonymous:
                participant = db.query(User).filter(User.id == participant_id).first()
            
            return TopicDiscussionResponse(
                id=discussion.id,
                topic_card_id=discussion.topic_card_id,
                participant_id=discussion.participant_id,
                host_id=discussion.host_id,
                message=discussion.message,
                message_type=discussion.message_type,
                is_anonymous=discussion.is_anonymous,
                created_at=discussion.created_at,
                participant_nickname=participant.nick_name if participant else None,
                participant_avatar=participant.avatar_url if participant else None
            )
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def get_topic_discussions(
        db: Session, 
        card_id: str, 
        page: int = 1, 
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取话题讨论列表"""
        try:
            # 查询讨论记录和参与者信息
            query = db.query(TopicDiscussion, User).join(
                User, TopicDiscussion.participant_id == User.id
            ).filter(
                TopicDiscussion.topic_card_id == card_id,
                TopicDiscussion.is_deleted == 0
            )
            
            # 获取总数
            total = query.count()
            
            # 分页查询
            offset = (page - 1) * page_size
            results = query.order_by(TopicDiscussion.created_at.desc()).offset(offset).limit(page_size).all()
            
            # 构建响应数据
            discussions = []
            for discussion, participant in results:
                discussion_response = TopicDiscussionResponse(
                    id=discussion.id,
                    topic_card_id=discussion.topic_card_id,
                    participant_id=discussion.participant_id,
                    host_id=discussion.host_id,
                    message=discussion.message,
                    message_type=discussion.message_type,
                    is_anonymous=discussion.is_anonymous,
                    created_at=discussion.created_at,
                    participant_nickname=participant.nick_name if not discussion.is_anonymous else None,
                    participant_avatar=participant.avatar_url if not discussion.is_anonymous else None
                )
                discussions.append(discussion_response)
            
            return {
                "total": total,
                "list": discussions
            }
        except Exception as e:
            raise e
    
    @staticmethod
    def like_topic_card(db: Session, card_id: str, user_id: str) -> bool:
        """点赞话题卡片"""
        try:
            topic_card = db.query(TopicCard).filter(TopicCard.id == card_id).first()
            if not topic_card:
                return False
            
            # 增加点赞次数
            topic_card.like_count += 1
            db.commit()
            
            return True
        except Exception as e:
            db.rollback()
            raise e