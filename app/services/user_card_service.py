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
            if field in ["bio", "profile_data", "preferences", "visibility", "avatar_url", "display_name"]:
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
            all_profiles=all_cards
        )
    
    @staticmethod
    def get_available_roles_for_scene(scene_type: str) -> List[str]:
        """获取特定场景下可用的角色类型"""
        from app.utils.role_converter import RoleConverter
        return RoleConverter.get_available_roles(scene_type)
    
    @staticmethod
    def get_card_template(scene_type: str, role_type: str) -> Dict[str, Any]:
        """获取特定场景和角色的卡片模板"""
        templates = {
            "housing": {
                "house_seeker": {
                    "profile_data": {
                        "budget_range": [1000, 3000],
                        "room_type": "master_bedroom",
                        "move_in_date": "",
                        "lease_duration": "1_year",
                        "lifestyle": "quiet",
                        "work_schedule": "9_to_5",
                        "pets": False,
                        "smoking": False,
                        "occupation": "",
                        "company_location": "",
                        "preferred_areas": [],
                        "amenities": []
                    },
                    "preferences": {
                        "preferred_house_types": ["apartment", "condo"],
                        "budget_flexibility": { "flexible": True, "max_increase_percent": 10 },
                        "preferred_districts": [],
                        "max_commute_time": 60,
                        "nearby_requirements": ["subway", "supermarket"],
                        "required_facilities": ["wifi", "kitchen"],
                        "furniture_preference": "partially_furnished",
                        "roommate_preferences": {
                            "gender_preference": "no_preference",
                            "age_range": [20, 35],
                            "occupation_types": ["professional", "student"]
                        },
                        "lifestyle_compatibility": ["quiet", "clean"],
                        "lease_flexibility": True,
                        "move_in_flexibility_days": 7,
                        "preferred_landlord_type": ["individual", "agent"],
                        "require_verification": True,
                        "match_strictness": "medium"
                    }
                },
                "house": {
                    "profile_data": {
                        "properties": [{
                            "type": "apartment",
                            "area": 80,
                            "rooms": 2,
                            "floor": 5,
                            "total_floors": 20,
                            "address": "",
                            "subway_distance": 500,
                            "facilities": ["elevator", "parking"],
                            "photos": [],
                            "virtual_tour_url": "",
                            "description": ""
                        }],
                        "landlord_type": "individual",
                        "response_time": "within_24_hours",
                        "viewing_available": True,
                        "lease_terms": ["1_year", "2_years"]
                    },
                    "preferences": {
                        "preferred_tenant_type": ["professional", "student"],
                        "preferred_gender": ["不限"],
                        "preferred_age_range": [18, 60],
                        "preferred_occupation": [],
                        "smoking_policy": "prefer_no_smoking",
                        "pet_policy": "small_pets_allowed",
                        "max_tenants": 2,
                        "require_verification": True,
                        "match_strictness": "medium",
                        "house_rules": [],
                        "payment_methods": []
                    }
                }
            },
            "dating": {
                "dating": {
                    "profile_data": {
                        "age": 25,
                        "height": 170,
                        "education": "本科",
                        "occupation": "",
                        "income_range": "",
                        "relationship_status": "single",
                        "looking_for": "dating",
                        "hobbies": [],
                        "personality": [],
                        "lifestyle": {
                            "smoking": False,
                            "drinking": "occasionally",
                            "exercise": "regularly",
                            "diet": "balanced"
                        },
                        "languages": [],
                        "children": 0,
                        "religion": ""
                    },
                    "preferences": {
                        "preferred_age_range": [20, 35],
                        "preferred_height_range": [160, 180],
                        "preferred_education_levels": ["本科", "硕士"],
                        "preferred_occupations": [],
                        "income_preference": { "min": "不限", "flexible": True },
                        "preferred_relationship_status": ["single"],
                        "looking_for_match": ["dating", "relationship"],
                        "shared_interests_weight": 0.5,
                        "personality_compatibility": [],
                        "lifestyle_compatibility": [],
                        "preferred_locations": [],
                        "max_distance_km": 50,
                        "appearance_preferences": {},
                        "lifestyle_requirements": {
                            "smoking": "no_preference",
                            "drinking": "no_preference",
                            "exercise": "no_preference"
                        },
                        "match_strictness": "medium",
                        "allow_different_intentions": False,
                        "require_verification": True,
                        "allow_social_media_verification": True
                    }
                }
            },
            "activity": {
                "activity_organizer": {
                    "profile_data": {
                        "activity_start_time": "",
                        "activity_end_time": "",
                        "activity_cost": "免费",
                        "activity_city": "",
                        "activity_location": "",
                        "activity_max_participants": 10,
                        "activity_min_participants": 2,
                        "activity_types": [],
                        "organizing_experience": 0,
                        "specialties": [],
                        "locations": [],
                        "past_activities": [],
                        "contact_info": {}
                    },
                    "preferences": {
                        "preferred_participant_age_range": [18, 60],
                        "preferred_participant_count": { "min": 2, "max": 20 },
                        "preferred_activity_types": [],
                        "preferred_locations": [],
                        "budget_preference": { "flexible": True, "max_budget": 100 },
                        "preferred_days": ["weekend"],
                        "preferred_time_slots": ["afternoon"],
                        "min_participation_history": 0,
                        "require_verification": False,
                        "match_strictness": "medium",
                        "participant_requirements": {},
                        "weather_dependency": "flexible"
                    }
                },
                "activity_participant": {
                    "profile_data": {
                        "interests": [],
                        "availability": {
                            "weekdays": ["evening"],
                            "weekends": ["afternoon", "evening"]
                        },
                        "experience_level": {
                            "beginner": True,
                            "intermediate": False,
                            "advanced": False
                        },
                        "transportation": [],
                        "budget_range": { "min": 0, "max": 100 },
                        "skill_levels": []
                    },
                    "preferences": {
                        "preferred_activity_types": [],
                        "preferred_locations": [],
                        "preferred_time_slots": ["evening", "weekend"],
                        "budget_range": { "min": 0, "max": 100 },
                        "group_size_preference": "small",
                        "match_strictness": "medium",
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