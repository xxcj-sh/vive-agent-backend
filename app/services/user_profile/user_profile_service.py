"""
用户画像服务
提供用户画像的CRUD操作和历史记录管理
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.user_profile import UserProfile, UserProfileCreate, UserProfileUpdate
from app.models.user_profile_history import UserProfileHistory, UserProfileHistoryCreate
from app.utils.logger import logger


class UserProfileService:
    """用户画像服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """获取用户的画像"""
        return self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    
    def get_user_profile_by_id(self, profile_id: str) -> Optional[UserProfile]:
        """根据ID获取画像"""
        return self.db.query(UserProfile).filter(UserProfile.id == profile_id).first()
    
    def create_user_profile(self, profile_data: UserProfileCreate) -> UserProfile:
        """创建用户画像"""
        # 检查是否已存在
        existing = self.get_user_profile(profile_data.user_id)
        if existing:
            logger.info(f"用户 {profile_data.user_id} 的用户画像已存在，将更新现有画像")
            return self.update_user_profile(existing.id, UserProfileUpdate(**profile_data.dict()))
        
        # 创建新画像
        db_profile = UserProfile(**profile_data.dict())
        self.db.add(db_profile)
        self.db.commit()
        self.db.refresh(db_profile)
        
        # 创建历史记录
        self._create_history_record(db_profile, "create", "system", "初始创建")
        
        logger.info(f"创建用户画像成功: user_id={profile_data.user_id}")
        return db_profile
    
    def update_user_profile(self, profile_id: str, profile_update: UserProfileUpdate) -> Optional[UserProfile]:
        """更新用户画像"""
        db_profile = self.get_user_profile_by_id(profile_id)
        if not db_profile:
            return None
        
        # 记录更新前的数据
        old_data = db_profile.raw_profile
        
        # 更新字段
        update_data = profile_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_profile, field, value)
        
        self.db.commit()
        self.db.refresh(db_profile)
        
        # 创建历史记录
        change_reason = profile_update.update_reason or "用户更新"
        self._create_history_record(db_profile, "update", "user", change_reason)
        
        logger.info(f"更新用户画像成功: profile_id={profile_id}")
        return db_profile
    
    def update_profile(self, user_id: str, profile_update: UserProfileUpdate, change_source: str = "user") -> UserProfile:
        """通过用户ID更新用户画像（API路由使用）"""
        # 首先获取用户画像
        db_profile = self.get_user_profile(user_id)
        if not db_profile:
            # 如果画像不存在，创建新的
            create_data = UserProfileCreate(
                user_id=user_id,
                raw_profile=profile_update.raw_profile,
                update_reason=profile_update.update_reason or "自动创建"
            )
            return self.create_user_profile(create_data)
        
        # 记录更新前的数据
        old_data = db_profile.raw_profile
        
        # 更新字段
        update_data = profile_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:  # 只更新非空值
                setattr(db_profile, field, value)
        
        self.db.commit()
        self.db.refresh(db_profile)
        
        # 创建历史记录
        change_reason = profile_update.update_reason or "用户更新"
        self._create_history_record(db_profile, "update", change_source, change_reason)
        
        logger.info(f"更新用户画像成功: user_id={user_id}")
        return db_profile
    
    def delete_user_profile(self, profile_id: str) -> bool:
        """删除用户画像"""
        db_profile = self.get_user_profile_by_id(profile_id)
        if not db_profile:
            return False
        
        self.db.delete(db_profile)
        self.db.commit()
        
        logger.info(f"删除用户画像成功: profile_id={profile_id}")
        return True
    
    def get_profile_history(self, user_id: str, limit: int = 10) -> List[UserProfileHistory]:
        """获取用户画像历史记录"""
        return self.db.query(UserProfileHistory).filter(
            UserProfileHistory.user_id == user_id
        ).order_by(desc(UserProfileHistory.created_at)).limit(limit).all()
    
    def _create_history_record(self, profile: UserProfile, change_type: str, 
                              change_source: str, change_reason: str) -> UserProfileHistory:
        """创建历史记录"""
        # 获取下一个版本号
        last_history = self.db.query(UserProfileHistory).filter(
            UserProfileHistory.profile_id == profile.id
        ).order_by(desc(UserProfileHistory.version)).first()
        
        next_version = (last_history.version + 1) if last_history else 1
        
        history_record = UserProfileHistory(
            profile_id=profile.id,
            user_id=profile.user_id,
            version=next_version,
            change_type=change_type,
            change_source=change_source,
            change_reason=change_reason,
            current_raw_profile=profile.raw_profile
        )
        
        self.db.add(history_record)
        self.db.commit()
        self.db.refresh(history_record)
        
        logger.info(f"创建画像历史记录成功: profile_id={profile.id}, version={next_version}")
        return history_record
    
    def get_or_create_profile(self, user_id: str) -> UserProfile:
        """获取或创建用户画像"""
        profile = self.get_user_profile(user_id)
        if not profile:
            # 创建默认画像
            profile_data = UserProfileCreate(
                user_id=user_id,
                raw_profile=None,
                update_reason="自动创建默认画像"
            )
            profile = self.create_user_profile(profile_data)
        
        return profile