from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional, Dict, Any
from app.models.user_card_db import UserCard
from app.models.user import User
from app.models.user_card import (
    CardCreate, CardUpdate, Card as CardSchema,
    CardsResponse, AllCardsResponse, CardsByScene
)
import uuid
import json
from datetime import datetime
from sqlalchemy.orm import Session

class UserCardService:
    """用户角色卡片服务"""
    
    @staticmethod
    def create_card(db: Session, user_id: str, card_data: CardCreate) -> UserCard:
        """创建用户角色卡片"""
        card_id = f"card_{card_data.scene_type}_{card_data.role_type}_{uuid.uuid4().hex[:8]}"
        
        # 处理 JSON 字段，确保正确序列化
        profile_data = card_data.profile_data
        if profile_data is not None and isinstance(profile_data, dict):
            profile_data = json.dumps(profile_data, ensure_ascii=False)
        else:
            profile_data = json.dumps({}, ensure_ascii=False)
            
        preferences = card_data.preferences
        if preferences is not None and isinstance(preferences, dict):
            preferences = json.dumps(preferences, ensure_ascii=False)
        else:
            preferences = json.dumps({}, ensure_ascii=False)
        
        db_card = UserCard(
            id=card_id,
            user_id=user_id,
            role_type=card_data.role_type,
            scene_type=card_data.scene_type,
            display_name=card_data.display_name,
            avatar_url=card_data.avatar_url,
            bio=card_data.bio,
            profile_data=profile_data,
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
        print(f"get_card_by_id: {card_id}")
        return db.query(UserCard).filter(UserCard.id == card_id).first()
    
    @staticmethod
    def get_user_card_by_role(db: Session, user_id: str, scene_type: str, role_type: str) -> Optional[Dict[str, Any]]:
        """获取用户在特定场景和角色下的卡片，包含基础用户信息"""
        
        # 获取用户卡片
        card = db.query(UserCard).filter(
            and_(
                UserCard.user_id == user_id,
                UserCard.scene_type == scene_type,
                UserCard.role_type == role_type,
                UserCard.is_deleted == 0
            )
        ).first()
        
        if not card:
            return None
            
        # 获取基础用户信息
        user = db.query(User).filter(User.id == user_id).first()
        
        # 构建基础card信息
        # 解析 JSON 字符串
        try:
            profile_data = json.loads(card.profile_data) if card.profile_data else {}
        except (json.JSONDecodeError, TypeError):
            profile_data = {}
            
        try:
            preferences = json.loads(card.preferences) if card.preferences else {}
        except (json.JSONDecodeError, TypeError):
            preferences = {}
        
        result = {
            "id": card.id,
            "user_id": card.user_id,
            "role_type": card.role_type,
            "scene_type": card.scene_type,
            "display_name": card.display_name,
            "avatar_url": card.avatar_url,
            "bio": card.bio or "",
            "profile_data": profile_data,
            "preferences": preferences,
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
                "age": user.age,
                "gender": user.gender,
                "occupation": getattr(user, 'occupation', None),  # 使用getattr处理可能不存在的字段
                "location": getattr(user, 'location', None),
                "phone": user.phone,
                "education": getattr(user, 'education', None),
                "interests": getattr(user, 'interests', []) or []
            })
        
        return result
    
    @staticmethod
    def get_cards_by_scene(db: Session, user_id: str, scene_type: str) -> List[UserCard]:
        """获取用户在特定场景下的所有角色卡片"""
        return db.query(UserCard).filter(
            and_(
                UserCard.user_id == user_id,
                UserCard.scene_type == scene_type
            )
        ).order_by(UserCard.created_at.desc()).all()
    
    @staticmethod
    def update_card(db: Session, card_id: str, update_data: Dict[str, Any]) -> Optional[UserCard]:
        """更新角色卡片"""
        card = db.query(UserCard).filter(UserCard.id == card_id).first()
        if not card:
            return None
            
        # 更新允许修改的字段
        for field, value in update_data.items():
            if field in ["bio", "profile_data", "preferences", "visibility", "search_code", "avatar_url", "display_name"]:
                # 对 JSON 字段进行序列化
                if field in ["profile_data", "preferences"]:
                    if value is not None:
                        if isinstance(value, dict):
                            value = json.dumps(value, ensure_ascii=False)
                            print(f"更新{field}后:", value)
                        else:
                            # 如果不是预期的类型，使用默认值
                            value = json.dumps({}, ensure_ascii=False)
                    else:
                        # 空值使用默认值
                        value = json.dumps({}, ensure_ascii=False)
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
        all_cards = UserCardService.get_user_cards(db, user_id)
        active_cards = [c for c in all_cards if c.is_deleted == 0]
        
        # 按场景分组
        scenes_dict = {}
        for card in active_cards:
            scene = card.scene_type
            if scene not in scenes_dict:
                scenes_dict[scene] = []
            scenes_dict[scene].append(card)
        
        # 处理卡片数据，确保字段类型正确
        processed_cards = []
        for card in active_cards:
            # 确保 JSON 字段正确解析
            if isinstance(card.profile_data, str):
                try:
                    card.profile_data = json.loads(card.profile_data)
                except (json.JSONDecodeError, TypeError):
                    card.profile_data = {}
            
            if isinstance(card.preferences, str):
                try:
                    card.preferences = json.loads(card.preferences)
                except (json.JSONDecodeError, TypeError):
                    card.preferences = {}
            
            processed_cards.append(card)
        
        # 重新按场景分组处理后的卡片
        scenes_dict_processed = {}
        for card in processed_cards:
            scene = card.scene_type
            if scene not in scenes_dict_processed:
                scenes_dict_processed[scene] = []
            scenes_dict_processed[scene].append(card)
        
        by_scene = [
            CardsByScene(scene_type=scene, profiles=cards)
            for scene, cards in scenes_dict_processed.items()
        ]
        
        return AllCardsResponse(
            user_id=user_id,
            total_count=len(processed_cards),
            active_count=len([c for c in processed_cards if c.is_deleted == 0]),
            by_scene=by_scene,
            all_cards=processed_cards
        )
    
    @staticmethod
    def get_available_roles_for_scene(scene_type: str) -> List[str]:
        """获取特定场景下可用的角色类型"""
        role_mapping = {
            "housing": ["housing_seeker", "housing_provider"],
            "dating": ["dating_seeker"],
            "activity": ["activity_organizer", "activity_participant"]
        }
        return role_mapping.get(scene_type, [])
    
    @staticmethod
    def get_public_cards(db: Session, page: int = 1, page_size: int = 10, scene_type: str = None) -> Dict[str, Any]:
        """获取公开的卡片列表"""
        from app.models.user_card_db import VISIBILITY_PUBLIC, VISIBILITY_PRIVATE

        # 构建查询条件 - 只查询公开卡片
        query = db.query(UserCard).filter(
            UserCard.visibility == VISIBILITY_PUBLIC,  # 只返回公开卡片
            UserCard.is_deleted == 0,  # 排除已删除的卡片
            UserCard.is_active == 1    # 只查询激活状态的卡片
        )
        
        # 如果提供了场景类型，则添加场景类型过滤
        if scene_type:
            query = query.filter(UserCard.scene_type == scene_type)
        
        # 获取总记录数
        total_count = query.count()
        
        # 计算偏移量并添加分页
        offset = (page - 1) * page_size
        cards = query.order_by(UserCard.created_at.desc()).offset(offset).limit(page_size).all()
        
        # 处理卡片数据
        processed_cards = []
        for card in cards:
            # 解析JSON字段
            try:
                profile_data = json.loads(card.profile_data) if card.profile_data else {}
            except (json.JSONDecodeError, TypeError):
                profile_data = {}
            
            try:
                preferences = json.loads(card.preferences) if card.preferences else {}
            except (json.JSONDecodeError, TypeError):
                preferences = {}
            
            # 获取用户基础信息
            user = db.query(User).filter(User.id == card.user_id).first()
            user_info = {}
            if user:
                user_info = {
                    "nick_name": user.nick_name if user else None,
                    "age": user.age if user else None,
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
                "scene_type": card.scene_type,
                "display_name": card.display_name,
                "avatar_url": card.avatar_url,
                "bio": card.bio,
                "profile_data": profile_data,
                "preferences": preferences,
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
    def get_card_template(scene_type: str, role_type: str) -> Dict[str, Any]:
        """获取特定场景和角色的卡片模板"""
        templates = {
            "housing": {
                "housing_seeker": {
                    "profile_data": {
                        "budget_range": [0, 0],
                        "preferred_areas": [],
                        "room_type": "",
                        "move_in_date": "",
                        "lease_duration": "",
                        "lifestyle": "",
                        "work_schedule": "",
                        "pets": False,
                        "smoking": False,
                        "occupation": "",
                        "company_location": ""
                    },
                    "preferences": {
                        "roommate_gender": "any",
                        "roommate_age_range": [18, 60],
                        "shared_facilities": [],
                        "transportation": [],
                        "nearby_facilities": []
                    }
                },
                "housing_provider": {
                    "profile_data": {
                        "properties": [],
                        "landlord_type": "individual",
                        "response_time": "within_24_hours",
                        "viewing_available": True,
                        "lease_terms": []
                    },
                    "preferences": {
                        "tenant_requirements": {
                            "stable_income": True,
                            "no_pets": False,
                            "no_smoking": False,
                            "quiet_lifestyle": False
                        },
                        "payment_methods": []
                    }
                }
            },
            "dating": {
                "dating_seeker": {
                    "profile_data": {
                        "age": 0,
                        "height": 0,
                        "education": "",
                        "occupation": "",
                        "income_range": "",
                        "relationship_status": "single",
                        "looking_for": "",
                        "hobbies": [],
                        "personality": [],
                        "lifestyle": {}
                    },
                    "preferences": {
                        "age_range": [18, 60],
                        "height_range": [150, 200],
                        "education_level": [],
                        "personality_preferences": [],
                        "lifestyle_preferences": {},
                        "relationship_goals": ""
                    }
                }
            },
            "activity": {
                "activity_organizer": {
                    "profile_data": {
                        "organizing_experience": "",
                        "specialties": [],
                        "group_size_preference": "",
                        "frequency": "",
                        "locations": [],
                        "past_activities": [],
                        "contact_info": {}
                    },
                    "preferences": {
                        "participant_requirements": {},
                        "activity_types": [],
                        "weather_dependency": "flexible"
                    }
                },
                "activity_participant": {
                    "profile_data": {
                        "interests": [],
                        "availability": {},
                        "experience_level": {},
                        "transportation": [],
                        "budget_range": {}
                    },
                    "preferences": {
                        "activity_types": [],
                        "group_size": "",
                        "duration": "",
                        "difficulty_level": [],
                        "location_preference": ""
                    }
                }
            }
        }
        
        return templates.get(scene_type, {}).get(role_type, {
            "profile_data": {},
            "preferences": {}
        })

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
            ).order_by(desc(TopicOpinionSummary.created_at)).all()
            for opinion_summary in opinion_summary_list:
                # 构建响应数据
                topic_info = {}
                # 如果有观点总结，添加相关信息
                if opinion_summary:
                    topic_info["opinion_summary"] = opinion_summary.opinion_summary
                    topic_info["key_points"] = opinion_summary.key_points
                    topic_info["sentiment"] = opinion_summary.sentiment
                    topic_info["confidence_score"] = opinion_summary.confidence_score
                    topic_info["is_anonymous"] = bool(opinion_summary.is_anonymous)  
                results.append(topic_info)
            print("results", results)
            return results
        except Exception as e:
            print(f"获取用户最近话题失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return []