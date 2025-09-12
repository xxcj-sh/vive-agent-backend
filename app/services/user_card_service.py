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

class UserCardService:
    """用户角色卡片服务"""
    
    @staticmethod
    def create_card(db: Session, user_id: str, card_data: CardCreate) -> UserCard:
        """创建用户角色卡片"""
        card_id = f"card_{card_data.scene_type}_{card_data.role_type}_{uuid.uuid4().hex[:8]}"
        
        db_card = UserCard(
            id=card_id,
            user_id=user_id,
            role_type=card_data.role_type,
            scene_type=card_data.scene_type,
            display_name=card_data.display_name,
            avatar_url=card_data.avatar_url,
            bio=card_data.bio,
            profile_data=card_data.profile_data,
            preferences=card_data.preferences,
            visibility=card_data.visibility or "public"
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
            query = query.filter(UserCard.is_active == 1)
            
        return query.order_by(UserCard.created_at.desc()).all()
    
    @staticmethod
    def get_card_by_id(db: Session, card_id: str) -> Optional[UserCard]:
        """根据卡片ID获取角色卡片"""
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
                UserCard.is_active == 1
            )
        ).first()
        
        if not card:
            return None
            
        # 获取基础用户信息
        user = db.query(User).filter(User.id == user_id).first()
        
        # 构建基础card信息
        result = {
            "id": card.id,
            "user_id": card.user_id,
            "role_type": card.role_type,
            "scene_type": card.scene_type,
            "display_name": card.display_name,
            "avatar_url": card.avatar_url,
            "profile_data": card.profile_data or {},
            "preferences": card.preferences or {},
            "visibility": card.visibility,
            "is_active": card.is_active,
            "created_at": card.created_at,
            "updated_at": card.updated_at,
            "bio": card.bio or ""
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
                "interests": getattr(user, 'interests', []) or [],

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
            if field in ["bio", "profile_data", "preferences", "visibility"]:
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
            
        card.is_active = 0
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
        active_cards = [c for c in all_cards if c.is_active == 1]
        
        # 按场景分组
        scenes_dict = {}
        for card in all_cards:
            scene = card.scene_type
            if scene not in scenes_dict:
                scenes_dict[scene] = []
            scenes_dict[scene].append(card)
        
        by_scene = [
            CardsByScene(scene_type=scene, profiles=cards)
            for scene, cards in scenes_dict.items()
        ]
        
        return AllCardsResponse(
            user_id=user_id,
            total_count=len(all_cards),
            active_count=len(active_cards),
            by_scene=by_scene,
            all_cards=all_cards
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