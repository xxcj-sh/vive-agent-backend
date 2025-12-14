from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timezone
import logging

from app.models.vote_card_db import VoteCard, VoteOption, VoteRecord, VoteDiscussion, UserCardVoteRelation
from app.models.user import User
from app.models.user_card_db import UserCard
from app.database import get_db

logger = logging.getLogger(__name__)

class VoteService:
    """投票业务逻辑服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_vote_card(self, user_id: str, vote_data: Dict[str, Any]) -> VoteCard:
        """创建投票卡片"""
        # 创建投票卡片
        vote_card = VoteCard(
            user_id=user_id,
            title=vote_data.get("title"),
            description=vote_data.get("description"),
            category=vote_data.get("category"),
            tags=vote_data.get("tags", []),
            cover_image=vote_data.get("cover_image"),
            vote_type=vote_data.get("vote_type", "single"),
            is_anonymous=vote_data.get("is_anonymous_vote", False),
            is_realtime_result=vote_data.get("is_realtime_result", True),
            visibility=vote_data.get("visibility", "public"),
            start_time=vote_data.get("start_time"),
            end_time=vote_data.get("end_time")
        )
        
        self.db.add(vote_card)
        self.db.flush()
        
        # 创建投票选项
        options = vote_data.get("vote_options", [])
        for i, option_text in enumerate(options):
            if isinstance(option_text, dict):
                option = VoteOption(
                    vote_card_id=vote_card.id,
                    option_text=option_text.get("text", ""),
                    option_image=option_text.get("image"),
                    display_order=i
                )
            else:
                option = VoteOption(
                    vote_card_id=vote_card.id,
                    option_text=str(option_text),
                    display_order=i
                )
            self.db.add(option)
        
        # 创建用户卡片关联
        if vote_data.get("user_card_id"):
            relation = UserCardVoteRelation(
                user_card_id=vote_data["user_card_id"],
                vote_card_id=vote_card.id,
                relation_type="created"
            )
            self.db.add(relation)
        
        self.db.commit()
        return vote_card
    
    def get_vote_card(self, vote_card_id: str, include_options: bool = True) -> Optional[VoteCard]:
        """获取投票卡片详情"""
        query = self.db.query(VoteCard).filter(
            VoteCard.id == vote_card_id,
            VoteCard.is_deleted == 0
        )
        
        if include_options:
            query = query.join(VoteOption).filter(VoteOption.is_active == 1)
        
        return query.first()
    
    def get_vote_cards_by_user(self, user_id: str, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """获取用户的投票卡片列表"""
        offset = (page - 1) * page_size
        
        query = self.db.query(VoteCard).filter(
            VoteCard.user_id == user_id,
            VoteCard.is_deleted == 0
        ).order_by(VoteCard.created_at.desc())
        
        total = query.count()
        vote_cards = query.offset(offset).limit(page_size).all()
        
        return {
            "cards": vote_cards,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    def submit_vote(self, user_id: Optional[str], vote_card_id: str, option_ids: List[int], 
                   ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Dict[str, Any]:
        """提交投票"""
        # 验证用户是否存在
        if not user_id:
            raise ValueError("用户未认证")
            
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("用户不存在")
        
        # 检查投票卡片是否存在且有效
        vote_card = self.db.query(VoteCard).filter(
            VoteCard.id == vote_card_id,
            VoteCard.is_deleted == 0,
            VoteCard.is_active == 1
        ).first()
        
        if not vote_card:
            raise ValueError("投票卡片不存在或已失效")
        
        # 检查投票时间
        now = datetime.now(timezone.utc)
        if vote_card.start_time and now < vote_card.start_time:
            raise ValueError("投票尚未开始")
        if vote_card.end_time and now > vote_card.end_time:
            raise ValueError("投票已结束")
        
        # 检查是否存在现有投票记录（用于更新/覆盖）
        existing_votes = self.db.query(VoteRecord).filter(
            VoteRecord.vote_card_id == vote_card_id,
            VoteRecord.user_id == user_id,
            VoteRecord.option_id.in_(option_ids),
            VoteRecord.is_deleted == 0
        ).all()
        # 验证选项
        options = self.db.query(VoteOption).filter(
            VoteOption.vote_card_id == vote_card_id,
            VoteOption.is_active == 1
        ).all()
        
        if not options:
            raise ValueError("投票选项不存在")
        # 验证投票类型
        if vote_card.vote_type == "single" and len(option_ids) > 1:
            raise ValueError("单选投票只能选择一个选项")
        
        # 验证选项索引有效性
        for option_id in option_ids:
            if option_id not in [option.id for option in options]:
                raise ValueError(f"无效的选项ID: {option_id}")
        
        # 处理现有投票记录（如果存在）
        if existing_votes:
            logger.info(f"用户 {user_id} 正在更新投票卡片 {vote_card_id} 的投票记录，现有 {len(existing_votes)} 条记录将被软删除")
            
            # 获取现有投票的选项ID列表
            existing_option_ids = [record.option_id for record in existing_votes]
            
            # 软删除现有投票记录
            for record in existing_votes:
                record.is_deleted = 1
            
            # 减少投票卡片的总投票数（减去被删除的投票数）
            vote_card.total_votes = max(0, vote_card.total_votes - len(existing_votes))
            
            # 减少各个选项的投票数
            existing_options = self.db.query(VoteOption).filter(
                VoteOption.id.in_(existing_option_ids)
            ).all()
            
            for option in existing_options:
                option.vote_count = max(0, option.vote_count - 1)
                option.updated_at = datetime.now(timezone.utc)
        
        # 创建新的投票记录
        vote_records = []
        for option_id in option_ids:
            option = options[option_ids.index(option_id)]
            vote_record = VoteRecord(
                vote_card_id=vote_card_id,
                user_id=user_id,
                option_id=option_id,
                is_anonymous=vote_card.is_anonymous,
                ip_address=ip_address,
                user_agent=user_agent
            )
            self.db.add(vote_record)
            vote_records.append(vote_record)
            
            # 更新选项投票数
            option.vote_count += 1
            option.updated_at = datetime.now(timezone.utc)
        
        # 更新投票卡片总投票数（加上新的投票数）
        vote_card.total_votes += len(option_ids)
        
        # 创建用户卡片关联（如果存在用户卡片）
        user_card = self.db.query(UserCard).filter(
            UserCard.user_id == user_id,
            UserCard.is_deleted == 0
        ).first()
        
        if user_card:
            existing_relation = self.db.query(UserCardVoteRelation).filter(
                UserCardVoteRelation.user_card_id == user_card.id,
                UserCardVoteRelation.vote_card_id == vote_card_id
            ).first()
            
            if not existing_relation:
                relation = UserCardVoteRelation(
                    user_card_id=user_card.id,
                    vote_card_id=vote_card_id,
                    relation_type="participated"
                )
                self.db.add(relation)
        
        self.db.commit()
        return {
            "vote_records": vote_records,
            "total_votes": vote_card.total_votes,
            "options": self._get_vote_options_with_counts(vote_card_id)
        }
    
    def get_vote_results(self, vote_card_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """获取投票结果"""
        vote_card = self.db.query(VoteCard).filter(
            VoteCard.id == vote_card_id,
            VoteCard.is_deleted == 0
        ).first()
        
        if not vote_card:
            raise ValueError("投票卡片不存在")
        
        # 获取选项和投票数
        options = self._get_vote_options_with_counts(vote_card_id)
        
        # 获取用户投票记录
        user_votes = []
        has_voted = False
        if user_id:
            user_vote_records = self.db.query(VoteRecord).filter(
                VoteRecord.vote_card_id == vote_card_id,
                VoteRecord.user_id == user_id,
                VoteRecord.is_deleted == 0
            ).all()
            
            has_voted = len(user_vote_records) > 0
            user_votes = [record.option_id for record in user_vote_records]
        
        return {
            "vote_card": vote_card,
            "options": options,
            "total_votes": vote_card.total_votes,
            "has_voted": has_voted,
            "user_votes": user_votes,
            "show_realtime_result": vote_card.is_realtime_result
        }
    
    def get_user_vote_status(self, user_id: Optional[str], vote_card_id: str) -> Dict[str, Any]:
        """获取用户投票状态"""
        # 如果用户ID为None，表示未认证用户
        if not user_id:
            return {
                "has_voted": False,
                "user_votes": []
            }
        
        vote_records = self.db.query(VoteRecord).filter(
            VoteRecord.vote_card_id == vote_card_id,
            VoteRecord.user_id == user_id,
            VoteRecord.is_deleted == 0
        ).all()
        
        has_voted = len(vote_records) > 0
        user_votes = [record.option_id for record in vote_records]
        
        return {
            "has_voted": has_voted,
            "user_votes": user_votes
        }
    
    def get_voted_users(self, vote_card_id: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取已投票用户列表
        
        Args:
            vote_card_id: 投票卡片ID
            page: 页码
            page_size: 每页数量
            
        Returns:
            包含用户列表、总数、分页信息的字典
        """
        from sqlalchemy.orm import joinedload
        from app.models.user import User
        
        # 验证投票卡片是否存在
        vote_card = self.db.query(VoteCard).filter(
            VoteCard.id == vote_card_id,
            VoteCard.is_deleted == 0
        ).first()
        
        if not vote_card:
            raise ValueError("投票卡片不存在")
        
        offset = (page - 1) * page_size
        
        # 查询已投票的用户（去重）
        query = self.db.query(User).join(
            VoteRecord, User.id == VoteRecord.user_id
        ).filter(
            VoteRecord.vote_card_id == vote_card_id
        ).distinct()
        
        total = query.count()
        users = query.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()
        
        # 构建用户列表数据
        user_list = []
        for user in users:
            # 获取该用户的投票记录
            vote_records = self.db.query(VoteRecord).filter(
                VoteRecord.vote_card_id == vote_card_id,
                VoteRecord.user_id == user.id,
                VoteRecord.is_deleted == 0
            ).all()
            
            # 获取用户投票的选项
            voted_options = []
            for record in vote_records:
                option = self.db.query(VoteOption).filter(
                    VoteOption.id == record.option_id
                ).first()
                if option:
                    voted_options.append({
                        "option_id": option.id,
                        "option_text": option.option_text
                    })
            
            user_data = {
                "id": user.id,
                "nick_name": user.nick_name or "匿名用户",
                "avatar_url": user.avatar_url or "",
                "gender": user.gender,
                "age": user.age,
                "occupation": user.occupation,
                "education": user.education,
                "location": user.location,
                "voted_at": vote_records[0].created_at.isoformat() if vote_records else None,
                "voted_options": voted_options,
                "vote_count": len(vote_records)
            }
            user_list.append(user_data)
        
        return {
            "users": user_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    
    def increment_view_count(self, vote_card_id: str) -> bool:
        """增加浏览次数"""
        vote_card = self.db.query(VoteCard).filter(
            VoteCard.id == vote_card_id,
            VoteCard.is_deleted == 0
        ).first()
        
        if vote_card:
            vote_card.view_count += 1
            self.db.commit()
            return True
        
        return False
    
    def add_discussion(self, vote_card_id: str, participant_id: str, host_id: str, 
                      message: str, message_type: str = "text", is_anonymous: bool = True) -> VoteDiscussion:
        """添加投票讨论"""
        discussion = VoteDiscussion(
            vote_card_id=vote_card_id,
            participant_id=participant_id,
            host_id=host_id,
            message=message,
            message_type=message_type,
            is_anonymous=1 if is_anonymous else 0
        )
        
        self.db.add(discussion)
        
        # 更新讨论数
        vote_card = self.db.query(VoteCard).filter(VoteCard.id == vote_card_id).first()
        if vote_card:
            vote_card.discussion_count += 1
        
        self.db.commit()
        return discussion
    
    def get_discussions(self, vote_card_id: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取投票讨论列表"""
        offset = (page - 1) * page_size
        
        query = self.db.query(VoteDiscussion).filter(
            VoteDiscussion.vote_card_id == vote_card_id,
            VoteDiscussion.is_deleted == 0
        ).order_by(VoteDiscussion.created_at.desc())
        
        total = query.count()
        discussions = query.offset(offset).limit(page_size).all()
        
        return {
            "discussions": discussions,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    def _get_vote_options_with_counts(self, vote_card_id: str) -> List[Dict[str, Any]]:
        """获取带投票数的选项列表"""
        options = self.db.query(VoteOption).filter(
            VoteOption.vote_card_id == vote_card_id,
            VoteOption.is_active == 1
        ).order_by(VoteOption.display_order).all()
        
        result = []
        for option in options:
            result.append({
                "id": option.id,
                "option_text": option.option_text,
                "option_image": option.option_image,
                "vote_count": option.vote_count,
                "display_order": option.display_order
            })
        
        return result
    
    def get_recall_vote_cards(self, limit: int = 10, user_id: Optional[str] = None) -> List[VoteCard]:
        """获取召回的投票卡片
        
        Args:
            limit: 返回卡片数量限制
            user_id: 用户ID，如果提供则过滤掉该用户已参与投票的卡片
        """
        query = self.db.query(VoteCard).filter(
            VoteCard.is_deleted == 0,
            VoteCard.is_active == 1,
            VoteCard.visibility == "public"
        )
        
        # 如果提供了用户ID，过滤掉该用户已参与投票的卡片
        if user_id:
            # 子查询：获取用户已参与投票的卡片ID
            user_voted_card_ids = self.db.query(VoteRecord.vote_card_id).filter(
                VoteRecord.user_id == user_id,
                VoteRecord.is_deleted == 0
            ).distinct()
            
            # 排除这些卡片
            # TEST
            # query = query.filter(~VoteCard.id.in_(user_voted_card_ids))
        
        return query.order_by(
            VoteCard.total_votes.desc(),
            VoteCard.view_count.desc()
        ).limit(limit).all()
    
    def search_vote_cards(self, keyword: str, category: Optional[str] = None, 
                         page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """搜索投票卡片"""
        offset = (page - 1) * page_size
        
        query = self.db.query(VoteCard).filter(
            VoteCard.is_deleted == 0,
            VoteCard.is_active == 1,
            VoteCard.visibility == "public"
        )
        
        if keyword:
            query = query.filter(
                or_(
                    VoteCard.title.contains(keyword),
                    VoteCard.description.contains(keyword),
                    VoteCard.tags.contains(keyword)
                )
            )
        
        if category:
            query = query.filter(VoteCard.category == category)
        
        total = query.count()
        vote_cards = query.order_by(VoteCard.created_at.desc()).offset(offset).limit(page_size).all()
        
        return {
            "cards": vote_cards,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    def delete_vote_card(self, vote_card_id: str, user_id: str) -> bool:
        """删除投票卡片（软删除）"""
        try:
            # 获取投票卡片
            vote_card = self.db.query(VoteCard).filter(
                VoteCard.id == vote_card_id,
                VoteCard.is_deleted == 0
            ).first()
            
            if not vote_card:
                raise ValueError("投票卡片不存在")
            
            # 验证用户是否有权限删除（只有创建者可以删除）
            if vote_card.user_id != user_id:
                raise ValueError("没有权限删除此投票卡片")
            
            # 软删除投票卡片
            vote_card.is_deleted = 1
            
            # 软删除相关的投票选项
            vote_options = self.db.query(VoteOption).filter(
                VoteOption.vote_card_id == vote_card_id
            ).all()
            for option in vote_options:
                option.is_active = 0
            
            # 软删除相关的投票记录
            vote_records = self.db.query(VoteRecord).filter(
                VoteRecord.vote_card_id == vote_card_id
            ).all()
            for record in vote_records:
                record.is_deleted = 1
            
            # 软删除相关的讨论
            discussions = self.db.query(VoteDiscussion).filter(
                VoteDiscussion.vote_card_id == vote_card_id
            ).all()
            for discussion in discussions:
                discussion.is_deleted = 1
            
            # 删除用户卡片关联
            self.db.query(UserCardVoteRelation).filter(
                UserCardVoteRelation.vote_card_id == vote_card_id
            ).delete()
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    def cancel_user_vote(self, user_id: str, vote_card_id: str) -> Dict[str, Any]:
        """取消用户投票
        
        Args:
            user_id: 用户ID
            vote_card_id: 投票卡片ID
            
        Returns:
            包含操作结果的字典
        """
        try:
            # 验证投票卡片是否存在
            vote_card = self.db.query(VoteCard).filter(
                VoteCard.id == vote_card_id,
                VoteCard.is_deleted == 0
            ).first()
            
            if not vote_card:
                raise ValueError("投票卡片不存在")
            
            # 获取用户的投票记录
            vote_records = self.db.query(VoteRecord).filter(
                VoteRecord.vote_card_id == vote_card_id,
                VoteRecord.user_id == user_id,
                VoteRecord.is_deleted == 0
            ).all()
            
            if not vote_records:
                raise ValueError("用户尚未投票")
            
            # 获取用户投票的选项ID列表
            option_ids = [record.option_id for record in vote_records]
            
            # 软删除用户的投票记录
            for record in vote_records:
                record.is_deleted = 1
            
            # 减少投票卡片的总投票数
            vote_card.total_votes = max(0, vote_card.total_votes - len(vote_records))
            
            # 减少各个选项的投票数
            vote_options = self.db.query(VoteOption).filter(
                VoteOption.id.in_(option_ids)
            ).all()
            
            for option in vote_options:
                option.vote_count = max(0, option.vote_count - 1)
            
            self.db.commit()
            
            # 返回更新后的投票结果
            return {
                "success": True,
                "message": "取消投票成功",
                "total_votes": vote_card.total_votes,
                "options": self._get_vote_options_with_counts(vote_card_id)
            }
            
        except ValueError as e:
            self.db.rollback()
            raise e
        except Exception as e:
            self.db.rollback()
            raise e
