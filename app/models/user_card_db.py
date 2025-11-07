from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import uuid

# 可见性常量
VISIBILITY_PUBLIC = "public"
VISIBILITY_PRIVATE = "private"

class UserCard(Base):
    """用户角色资料数据库模型"""
    __tablename__ = "user_cards"

    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    role_type = Column(String(50), nullable=False)
    scene_type = Column(String(50), nullable=False)
    display_name = Column(String(100), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    trigger_and_output = Column(Text, nullable=True)
    profile_data = Column(JSON, nullable=True)
    preferences = Column(JSON, nullable=True)
    visibility = Column(String(20), default="public")  # public, private
    is_active = Column(Integer, default=1)
    is_deleted = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    search_code = Column(String(100), nullable=True, index=True)
    
    # 关系
    user = relationship("User", back_populates="cards")
    
    def to_dict(self, include_private=False):
        """转换为字典"""
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "role_type": self.role_type,
            "scene_type": self.scene_type,
            "visibility": self.visibility,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "search_code": self.search_code
        }

        # 私有模式处理
        if self.visibility == VISIBILITY_PRIVATE and not include_private:
            # 私有模式下不暴露详细信息
            data["display_name"] = "私有用户"
            data["avatar_url"] = ""
            data["bio"] = ""
            data["profile_data"] = {}
            data["preferences"] = {}
        else:
            data["display_name"] = self.display_name
            data["avatar_url"] = self.avatar_url
            data["bio"] = self.bio
            data["profile_data"] = self.profile_data or {}
            data["preferences"] = self.preferences or {}
            data["trigger_and_output"] = self.trigger_and_output or {}

        return data
