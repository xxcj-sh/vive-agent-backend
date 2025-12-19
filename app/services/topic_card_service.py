from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.topic_card_db import TopicCard, TopicDiscussion, TopicOpinionSummary
from app.models.topic_card import (
    TopicCardCreate, TopicCardUpdate, TopicCardResponse, TopicCardListResponse,
    TopicDiscussionCreate, TopicDiscussionResponse, TopicDiscussionListResponse,
    TopicOpinionSummaryResponse, TopicOpinionSummaryListResponse
)
from app.models.user import User
from app.utils.logger import logger

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
                creator_avatar=creator.avatar_url if creator else None
            )
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    async def generate_opinion_summary(
        db: Session,
        card_id: str,
        user_id: str,
        user_messages: List[Dict[str, str]],
        llm_service: Optional[Any] = None
    ) -> TopicOpinionSummaryResponse:
        """
        生成话题观点总结（AI自动生成）
        
        Args:
            db: 数据库会话
            card_id: 话题卡片ID
            user_id: 用户ID
            llm_service: LLM服务实例（可选）
            
        Returns:
            观点总结响应对象
        """
        try:
            # 验证用户是否存在
            from app.models.user import User
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.error(f"用户不存在: user_id={user_id}")
                raise ValueError("用户不存在，无法生成观点总结")
            
            logger.info(f"用户验证成功，开始生成观点总结: user_id={user_id}, card_id={card_id}")
            
            # 获取话题卡片信息
            topic_card = db.query(TopicCard).filter(
                TopicCard.id == card_id,
                TopicCard.is_deleted == 0
            ).first()
            
            if not topic_card:
                raise ValueError("话题卡片不存在")
            
            # 处理用户消息数据
            if not user_messages:
                # 如果没有讨论内容，返回默认总结
                return TopicCardService.save_topic_opinion_summary(
                    db=db,
                    card_id=card_id,
                    user_id=user_id,
                    opinion_summary="暂无用户观点数据",
                    key_points=["暂无讨论内容"],
                    sentiment="neutral",
                    confidence_score=0.0,
                    is_anonymous=True
                )
            
            # 构建对话历史 - 适配前端消息结构
            conversation_history = []
            for message in user_messages:
                # 前端消息结构: {id, content, sender, time, type}
                if message and message.get('content'):
                    conversation_history.append({
                        "role": "user",
                        "content": message['content'],
                        "timestamp": message.get('time', '')
                    })
            
            # 如果没有有效的用户消息，返回默认总结
            if not conversation_history:
                return TopicCardService.save_topic_opinion_summary(
                    db=db,
                    card_id=card_id,
                    user_id=user_id,
                    opinion_summary="暂无有效用户观点数据",
                    key_points=["暂无有效讨论内容"],
                    sentiment="neutral",
                    confidence_score=0.0,
                    is_anonymous=True
                )
            
            # 获取LLM服务实例
            if llm_service is None:
                from app.services.llm_service import LLMService
                llm_service = LLMService(db)
            
            # 调用LLM生成观点总结
            opinion_response = await llm_service.summarize_opinions(
                user_id=user_id,
                conversation_history=conversation_history,
                topic_title=topic_card.title,
                topic_description=topic_card.description or ""
            )
            
            # 保存观点总结
            return TopicCardService.save_topic_opinion_summary(
                db=db,
                card_id=card_id,
                user_id=user_id,
                opinion_summary=opinion_response.summary,
                key_points=opinion_response.key_points,
                sentiment=opinion_response.sentiment,
                confidence_score=opinion_response.confidence_score,
                is_anonymous=True  # AI生成的总结标记为匿名
            )
            
        except Exception as e:
            logger.error(f"生成话题观点总结失败: {str(e)}")
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
            
            # 只显示激活且未删除的卡片，且用户状态正常
            query = query.filter(
                TopicCard.is_active == 1,
                TopicCard.is_deleted == 0,
                User.is_active == True,
                User.status != 'deleted'
            )
            
            # 如果指定了用户ID，只返回该用户创建的话题卡片
            if user_id:
                query = query.filter(TopicCard.user_id == user_id)
            
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
                    creator_avatar=creator.avatar_url if creator else None
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
                is_invited=is_invited
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
                is_anonymous=topic_card.is_anonymous,
                view_count=topic_card.view_count,
                like_count=topic_card.like_count,
                discussion_count=topic_card.discussion_count,
                created_at=topic_card.created_at,
                updated_at=topic_card.updated_at,
                creator_nickname=creator.nick_name if creator else None,
                creator_avatar=creator.avatar_url if creator else None
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

    @staticmethod
    def get_topic_opinion_summaries(
        db: Session, 
        card_id: str, 
        page: int = 1, 
        page_size: int = 10
    ) -> Dict[str, Any]:
        """获取话题观点总结列表"""
        try:
            # 查询观点总结和用户信息
            query = db.query(TopicOpinionSummary, User).join(
                User, TopicOpinionSummary.user_id == User.id
            ).filter(
                TopicOpinionSummary.topic_card_id == card_id,
                TopicOpinionSummary.is_deleted == 0
            )
            
            # 获取总数
            total = query.count()
            
            # 分页查询
            offset = (page - 1) * page_size
            results = query.order_by(TopicOpinionSummary.created_at.desc()).offset(offset).limit(page_size).all()
            
            # 构建响应数据
            opinion_summaries = []
            for opinion_summary, user in results:
                opinion_response = TopicOpinionSummaryResponse(
                    id=opinion_summary.id,
                    topic_card_id=opinion_summary.topic_card_id,
                    user_id=opinion_summary.user_id,
                    opinion_summary=opinion_summary.opinion_summary,
                    key_points=opinion_summary.key_points,
                    sentiment=opinion_summary.sentiment,
                    confidence_score=opinion_summary.confidence_score,
                    is_anonymous=opinion_summary.is_anonymous,
                    created_at=opinion_summary.created_at,
                    updated_at=opinion_summary.updated_at,
                    # 用户信息（匿名时不显示）
                    user_nickname=user.nick_name if not opinion_summary.is_anonymous else None,
                    user_avatar=user.avatar_url if not opinion_summary.is_anonymous else None
                )
                opinion_summaries.append(opinion_response)
            
            return {
                "total": total,
                "list": opinion_summaries,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        except Exception as e:
            raise e

    @staticmethod
    def save_topic_opinion_summary(
        db: Session,
        card_id: str,
        user_id: str,
        opinion_summary: str,
        key_points: List[str],
        sentiment: str,
        confidence_score: float,
        is_anonymous: bool = False
    ) -> TopicOpinionSummaryResponse:
        """保存话题观点总结"""
        try:
            # 检查是否已存在该用户的观点总结
            existing_summary = db.query(TopicOpinionSummary).filter(
                TopicOpinionSummary.topic_card_id == card_id,
                TopicOpinionSummary.user_id == user_id,
                TopicOpinionSummary.is_deleted == 0
            ).first()
            
            if existing_summary:
                # 更新现有总结
                existing_summary.opinion_summary = opinion_summary
                existing_summary.key_points = key_points
                existing_summary.sentiment = sentiment
                existing_summary.confidence_score = confidence_score
                existing_summary.is_anonymous = is_anonymous
                existing_summary.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(existing_summary)
                opinion_summary_obj = existing_summary
            else:
                # 创建新的观点总结
                new_summary = TopicOpinionSummary(
                    topic_card_id=card_id,
                    user_id=user_id,
                    opinion_summary=opinion_summary,
                    key_points=key_points,
                    sentiment=sentiment,
                    confidence_score=confidence_score,
                    is_anonymous=is_anonymous,
                    is_deleted=0
                )
                db.add(new_summary)
                db.commit()
                db.refresh(new_summary)
                opinion_summary_obj = new_summary
            
            # 获取用户信息
            user = db.query(User).filter(User.id == user_id).first()
            
            return TopicOpinionSummaryResponse(
                id=opinion_summary_obj.id,
                topic_card_id=opinion_summary_obj.topic_card_id,
                user_id=opinion_summary_obj.user_id,
                opinion_summary=opinion_summary_obj.opinion_summary,
                key_points=opinion_summary_obj.key_points,
                sentiment=opinion_summary_obj.sentiment,
                confidence_score=opinion_summary_obj.confidence_score,
                is_anonymous=opinion_summary_obj.is_anonymous,
                created_at=opinion_summary_obj.created_at,
                updated_at=opinion_summary_obj.updated_at,
                # 用户信息（匿名时不显示）
                user_nickname=user.nick_name if not is_anonymous else None,
                user_avatar=user.avatar_url if not is_anonymous else None
            )
        except Exception as e:
            db.rollback()
            raise e