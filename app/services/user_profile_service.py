from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional, Dict, Any
from app.models.user_profile import UserProfile
from app.models.user import User
from app.models.user_profile_schemas import (
    UserProfileCreate, UserProfileUpdate, UserProfile as UserProfileSchema,
    UserProfilesResponse, UserAllProfilesResponse, UserProfilesByScene
)
import uuid
import json

class UserProfileService:
    """用户角色资料服务"""
    
    @staticmethod
    def create_profile(db: Session, user_id: str, profile_data: UserProfileCreate) -> UserProfile:
        """创建用户角色资料"""
        profile_id = f"profile_{profile_data.scene_type}_{profile_data.role_type}_{uuid.uuid4().hex[:8]}"
        
        db_profile = UserProfile(
            id=profile_id,
            user_id=user_id,
            role_type=profile_data.role_type,
            scene_type=profile_data.scene_type,
            display_name=profile_data.display_name,
            avatar_url=profile_data.avatar_url,
            bio=profile_data.bio,
            profile_data=profile_data.profile_data,
            preferences=profile_data.preferences,
            tags=profile_data.tags,
            visibility=profile_data.visibility or "public"
        )
        
        db.add(db_profile)
        db.commit()
        db.refresh(db_profile)
        return db_profile
    
    @staticmethod
    def get_user_profiles(db: Session, user_id: str, active_only: bool = False) -> List[UserProfile]:
        """获取用户的所有角色资料"""
        query = db.query(UserProfile).filter(UserProfile.user_id == user_id)
        
        if active_only:
            query = query.filter(UserProfile.is_active == 1)
            
        return query.order_by(UserProfile.created_at.desc()).all()
    
    @staticmethod
    def get_profile_by_id(db: Session, profile_id: str) -> Optional[UserProfile]:
        """根据资料ID获取角色资料"""
        return db.query(UserProfile).filter(UserProfile.id == profile_id).first()
    
    @staticmethod
    def get_user_profile_by_role(db: Session, user_id: str, scene_type: str, role_type: str) -> Optional[Dict[str, Any]]:
        """获取用户在特定场景和角色下的资料，包含基础用户信息"""
        
        # 获取用户资料
        profile = db.query(UserProfile).filter(
            and_(
                UserProfile.user_id == user_id,
                UserProfile.scene_type == scene_type,
                UserProfile.role_type == role_type,
                UserProfile.is_active == 1
            )
        ).first()
        
        if not profile:
            return None
            
        # 获取基础用户信息
        user = db.query(User).filter(User.id == user_id).first()
        
        # 合并资料数据和基础用户信息
        result = {
            "id": profile.id,
            "user_id": profile.user_id,
            "role_type": profile.role_type,
            "scene_type": profile.scene_type,
            "display_name": profile.display_name,
            "avatar_url": profile.avatar_url,
            "bio": profile.bio,
            "profile_data": profile.profile_data or {},
            "preferences": profile.preferences or {},
            "tags": profile.tags or [],
            "visibility": profile.visibility,
            "is_active": profile.is_active,
            "created_at": profile.created_at,
            "updated_at": profile.updated_at,
        }
        
        # 添加基础用户信息
        if user:
            result.update({
                "username": user.username,
                "email": user.email,
                "nick_name": user.nick_name,
                "age": user.age,
                "gender": user.gender,
                "occupation": user.occupation,
                "location": user.location,
                "phone": user.phone,
                "education": user.education,
                "interests": user.interests or [],
                "user_bio": user.bio,  # 用户基础简介，区别于角色简介
            })
        
        return result
    
    @staticmethod
    def get_profiles_by_scene(db: Session, user_id: str, scene_type: str) -> List[UserProfile]:
        """获取用户在特定场景下的所有角色资料"""
        return db.query(UserProfile).filter(
            and_(
                UserProfile.user_id == user_id,
                UserProfile.scene_type == scene_type
            )
        ).order_by(UserProfile.created_at.desc()).all()
    
    @staticmethod
    def update_profile(db: Session, profile_id: str, update_data: UserProfileUpdate) -> Optional[UserProfile]:
        """更新用户角色资料"""
        db_profile = db.query(UserProfile).filter(UserProfile.id == profile_id).first()
        
        if not db_profile:
            return None
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(db_profile, field, value)
        
        db.commit()
        db.refresh(db_profile)
        return db_profile
    
    @staticmethod
    def delete_profile(db: Session, profile_id: str) -> bool:
        """删除用户角色资料"""
        db_profile = db.query(UserProfile).filter(UserProfile.id == profile_id).first()
        
        if not db_profile:
            return False
        
        db.delete(db_profile)
        db.commit()
        return True
    
    @staticmethod
    def toggle_profile_status(db: Session, profile_id: str, is_active: int) -> Optional[UserProfile]:
        """切换资料激活状态"""
        db_profile = db.query(UserProfile).filter(UserProfile.id == profile_id).first()
        
        if not db_profile:
            return None
        
        db_profile.is_active = is_active
        db.commit()
        db.refresh(db_profile)
        return db_profile
    
    @staticmethod
    def get_user_all_profiles_response(db: Session, user_id: str) -> UserAllProfilesResponse:
        """获取用户所有角色资料的完整响应"""
        all_profiles = UserProfileService.get_user_profiles(db, user_id)
        active_profiles = [p for p in all_profiles if p.is_active == 1]
        
        # 按场景分组
        scenes_dict = {}
        for profile in all_profiles:
            scene = profile.scene_type
            if scene not in scenes_dict:
                scenes_dict[scene] = []
            scenes_dict[scene].append(profile)
        
        by_scene = [
            UserProfilesByScene(scene_type=scene, profiles=profiles)
            for scene, profiles in scenes_dict.items()
        ]
        
        return UserAllProfilesResponse(
            user_id=user_id,
            total_count=len(all_profiles),
            active_count=len(active_profiles),
            by_scene=by_scene,
            all_profiles=all_profiles
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
    def get_profile_template(scene_type: str, role_type: str) -> Dict[str, Any]:
        """获取特定场景和角色的资料模板"""
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