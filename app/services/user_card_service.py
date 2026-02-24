from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional, Dict, Any
from app.models.user_card_db import UserCard
from app.models.user import User
from app.models.user_card import (
    CardCreate, CardUpdate, Card,
    CardsResponse, AllCardsResponse, CardsByScene
)
from app.services.points_service import PointsService
import uuid
import json
from datetime import datetime

class UserCardService:
    """用户角色卡片服务"""
    
    @staticmethod
    def create_card(db: Session, user_id: str, card_data: CardCreate) -> UserCard:
        """创建用户角色卡片"""
        # 检查并扣除积分
        points_service = PointsService(db)
        consume_result = points_service.consume_create_card(user_id, 'user_card')
        
        if not consume_result['success']:
            raise ValueError(f"积分不足：当前积分 {consume_result['current_points']}，需要积分 {consume_result['required_points']}")
        
        card_id = f"card_{card_data.role_type}_{uuid.uuid4().hex[:8]}"

        # preferences 是纯字符串字段，直接使用传入的值，None 或空字符串则设为空对象字符串
        preferences = card_data.preferences if card_data.preferences else ''
        # 如果是字典类型，转换为 JSON 字符串（兼容旧数据）
        if isinstance(preferences, dict):
            preferences = json.dumps(preferences, ensure_ascii=False)

        db_card = UserCard(
            id=card_id,
            user_id=user_id,
            role_type=card_data.role_type,
            display_name=card_data.display_name,
            avatar_url=card_data.avatar_url,
            bio=card_data.bio,
            preferences=preferences,
            visibility=card_data.visibility or "public",
            search_code=card_data.search_code
        )
        
        db.add(db_card)
        db.commit()
        db.refresh(db_card)
        return db_card
    
    @staticmethod
    def get_user_cards(db: Session, user_id: str, active_only: bool = False) -> List[UserCard]:
        """获取用户的所有角色卡片"""
        query = db.query(UserCard).filter(UserCard.user_id == user_id)
        
        if active_only:
            query = query.filter(UserCard.is_deleted == 0)
            
        return query.order_by(UserCard.created_at.desc()).all()
    
    @staticmethod
    def get_card_by_id(db: Session, card_id: str) -> Optional[UserCard]:
        """根据卡片ID获取角色卡片"""
        return db.query(UserCard).filter(UserCard.id == card_id).first()
    
    @staticmethod
    def get_user_card_by_role(db: Session, user_id: str, role_type: str) -> Optional[Dict[str, Any]]:
        """获取用户在特定角色下的卡片，包含基础用户信息"""
        
        # 获取用户卡片
        card = db.query(UserCard).filter(
            and_(
                UserCard.user_id == user_id,
                UserCard.role_type == role_type,
                UserCard.is_deleted == 0
            )
        ).first()
        
        if not card:
            return None
            
        # 获取基础用户信息
        user = db.query(User).filter(User.id == user_id).first()
        
        result = {
            "id": card.id,
            "user_id": card.user_id,
            "role_type": card.role_type,
            "display_name": card.display_name,
            "avatar_url": card.avatar_url,
            "bio": card.bio or "",
            "preferences": card.preferences,
            "visibility": card.visibility,
            "is_active": card.is_active,
            "search_code": card.search_code,
            "created_at": card.created_at,
            "updated_at": card.updated_at
        }
        
        # 添加基础用户信息
        if user:
            result.update({
                "username": user.nick_name or user.phone,  # 使用昵称或手机号作为用户名
                "email": None,  # 用户模型中没有邮箱字段
                "nick_name": user.nick_name,
                "gender": user.gender,
                "occupation": getattr(user, 'occupation', None),  # 使用getattr处理可能不存在的字段
                "location": getattr(user, 'location', None),
                "phone": user.phone,
                "education": getattr(user, 'education', None),
                "interests": getattr(user, 'interests', []) or []
            })
        
        return result
    
    @staticmethod
    def get_cards_by_scene(db: Session, user_id: str) -> List[UserCard]:
        """获取用户的所有角色卡片"""
        return db.query(UserCard).filter(
            UserCard.user_id == user_id
        ).order_by(UserCard.created_at.desc()).all()
    
    @staticmethod
    def update_card(db: Session, card_id: str, update_data: Dict[str, Any]) -> Optional[UserCard]:
        """更新角色卡片"""
        card = db.query(UserCard).filter(UserCard.id == card_id).first()
        if not card:
            return None
            
        # 更新允许修改的字段
        for field, value in update_data.items():
            if field in ["bio", "preferences", "visibility", "search_code", "avatar_url", "display_name"]:
                # preferences 是纯字符串字段，None 或空字符串则设为空对象字符串
                if field == "preferences":
                    value = value if value else ''
                    # 如果是字典类型，转换为 JSON 字符串（兼容旧数据）
                setattr(card, field, value)
                
        card.updated_at = datetime.now()
        db.commit()
        db.refresh(card)
        
        return card
    
    @staticmethod
    def delete_card(db: Session, card_id: str) -> bool:
        """删除角色卡片（软删除）"""
        card = db.query(UserCard).filter(UserCard.id == card_id).first()
        if not card:
            return False
            
        card.is_deleted = 1
        card.updated_at = datetime.now()
        db.commit()
        
        return True
    
    @staticmethod
    def toggle_card_status(db: Session, card_id: str, is_active: int) -> Optional[UserCard]:
        """切换卡片激活状态"""
        db_card = db.query(UserCard).filter(UserCard.id == card_id).first()
        
        if not db_card:
            return None
        
        db_card.is_active = is_active
        db.commit()
        db.refresh(db_card)
        return db_card
    
    @staticmethod
    def get_user_all_cards_response(db: Session, user_id: str) -> AllCardsResponse:
        """获取用户所有角色卡片的完整响应"""
        try:
            all_cards = UserCardService.get_user_cards(db, user_id)
            active_cards = [c for c in all_cards if c.is_deleted == 0]
            
            # 处理卡片数据，确保字段类型正确 - 不直接修改 ORM 对象，而是创建字典副本
            processed_card_dicts = []
            for card in active_cards:
                card_dict = {
                    "id": card.id,
                    "user_id": card.user_id,
                    "role_type": card.role_type,
                    "display_name": card.display_name,
                    "avatar_url": card.avatar_url,
                    "bio": card.bio,
                    "preferences": card.preferences or "",
                    "visibility": card.visibility,
                    "is_active": card.is_active,
                    "is_deleted": card.is_deleted,
                    "search_code": card.search_code,
                    "created_at": card.created_at,
                    "updated_at": card.updated_at
                }
                
                processed_card_dicts.append(card_dict)
            
            # 按场景分组处理后的卡片
            scenes_dict_processed = {}
            for card_dict in processed_card_dicts:
                scene = "default"
                if scene not in scenes_dict_processed:
                    scenes_dict_processed[scene] = []
                scenes_dict_processed[scene].append(card_dict)
            
            # 转换为 Card 模型实例
            processed_cards = [Card(**card_dict) for card_dict in processed_card_dicts]
            
            by_scene = []
            for scene, cards in scenes_dict_processed.items():
                profiles = [Card(**card_dict) for card_dict in cards]
                by_scene.append(CardsByScene(profiles=profiles))
            
            return AllCardsResponse(
                user_id=user_id,
                total_count=len(processed_cards),
                active_count=len(processed_cards),
                by_scene=by_scene,
                all_cards=processed_cards
            )
        except Exception as e:
            print(f"获取用户卡片响应时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            # 返回空的响应
            return AllCardsResponse(
                user_id=user_id,
                total_count=0,
                active_count=0,
                by_scene=[],
                all_cards=[]
            )
    
    @staticmethod
    def get_available_roles_for_scene() -> List[str]:
        """获取可用的角色类型"""
        return ["housing_seeker", "housing_provider", "dating_seeker", "activity_organizer", "activity_participant"]
    
    @staticmethod
    def get_public_cards(db: Session, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """获取公开的卡片列表"""
        from app.models.user_card_db import VISIBILITY_PUBLIC, VISIBILITY_PRIVATE

        # 构建查询条件 - 只查询公开卡片
        query = db.query(UserCard).filter(
            UserCard.visibility == VISIBILITY_PUBLIC,  # 只返回公开卡片
            UserCard.is_deleted == 0,  # 排除已删除的卡片
            UserCard.is_active == 1    # 只查询激活状态的卡片
        )
        
        # 获取总记录数
        total_count = query.count()
        
        # 计算偏移量并添加分页
        offset = (page - 1) * page_size
        cards = query.order_by(UserCard.created_at.desc()).offset(offset).limit(page_size).all()
        
        # 处理卡片数据
        processed_cards = []
        for card in cards:
            # 获取用户基础信息
            user = db.query(User).filter(User.id == card.user_id).first()
            user_info = {}
            if user:
                user_info = {
                    "nick_name": user.nick_name if user else None,
                    "gender": user.gender if user else None,
                    "occupation": getattr(user, 'occupation', None) if user else None,
                    "location": getattr(user, 'location', None) if user else None,
                    "education": getattr(user, 'education', None) if user else None,
                    "interests": getattr(user, 'interests', []) if user else [],
                    "avatar_url": user.avatar_url if user else None
                }

            # 处理卡片数据
            processed_card = {
                "id": card.id,
                "user_id": card.user_id,
                "role_type": card.role_type,
                "display_name": card.display_name,
                "avatar_url": card.avatar_url,
                "bio": card.bio,
                "preferences": card.preferences,
                "visibility": card.visibility,
                "created_at": card.created_at,
                "updated_at": card.updated_at,
                "user_info": user_info
            }

            processed_cards.append(processed_card)
        
        # 计算总页数
        total_pages = (total_count + page_size - 1) // page_size
        
        return {
            "list": processed_cards,
            "total_count": total_count,
            "total_pages": total_pages,
            "current_page": page,
            "page_size": page_size
        }

    @staticmethod
    def get_user_recent_topics_with_opinion_summaries(
        db: Session, 
        user_id: str, 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取用户最近参与讨论的话题信息，包括标题和观点总结"""
        try:
            from app.models.topic_card_db import TopicCard, TopicDiscussion, TopicOpinionSummary
            from sqlalchemy import desc
            # 获取话题卡片信息和用户的观点总结
            results = []        
            # 获取用户对该话题的观点总结
            opinion_summary_list = db.query(TopicOpinionSummary).filter(
                TopicOpinionSummary.user_id == user_id,
                TopicOpinionSummary.is_deleted == 0
            ).order_by(desc(TopicOpinionSummary.created_at)).limit(limit).all()
            
            for opinion_summary in opinion_summary_list:
                # 构建响应数据
                topic_info = {}
                
                # 通过topic_card_id获取对应的话题卡片信息
                topic_card = db.query(TopicCard).filter(
                    TopicCard.id == opinion_summary.topic_card_id,
                    TopicCard.is_deleted == 0
                ).first()
                
                # 如果有话题卡片信息，添加基本信息
                if topic_card:
                    topic_info["card_id"] = topic_card.id
                    topic_info["title"] = topic_card.title
                    topic_info["description"] = topic_card.description
                    topic_info["category"] = topic_card.category
                    topic_info["tags"] = topic_card.tags
                    topic_info["cover_image"] = topic_card.cover_image
                    topic_info["view_count"] = topic_card.view_count
                    topic_info["like_count"] = topic_card.like_count
                    topic_info["discussion_count"] = topic_card.discussion_count
                    topic_info["created_at"] = topic_card.created_at.isoformat() if topic_card.created_at else None
                
                # 添加观点总结信息
                if opinion_summary:
                    topic_info["opinion_summary"] = opinion_summary.opinion_summary
                    topic_info["key_points"] = opinion_summary.key_points
                    topic_info["sentiment"] = opinion_summary.sentiment
                    topic_info["confidence_score"] = opinion_summary.confidence_score
                    topic_info["is_anonymous"] = bool(opinion_summary.is_anonymous)
                    topic_info["summary_created_at"] = opinion_summary.created_at.isoformat() if opinion_summary.created_at else None
                
                results.append(topic_info)
            
            return results
        except Exception as e:
            print(f"获取用户最近话题失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return []