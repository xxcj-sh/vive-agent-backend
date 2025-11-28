from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid
import enum

# 关系类型枚举
class ConnectionType(str, enum.Enum):
    FOLLOW = "follow"  # 关注关系
    VISIT = "visit"  # 曾经访问过对方的主页
    VIEW = "view"  # 曾经浏览过对方的主页

# 关系状态枚举
class ConnectionStatus(str, enum.Enum):
    PENDING = "pending"  # 待确认
    ACCEPTED = "accepted"  # 已接受
    REJECTED = "rejected"  # 已拒绝
    BLOCKED = "blocked"  # 已拉黑

class UserConnection(Base):
    __tablename__ = "user_connections"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # 关系双方的用户ID
    from_user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    to_user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 关系类型和状态
    connection_type = Column(SQLEnum(ConnectionType), default=ConnectionType.FRIEND, nullable=False)
    status = Column(SQLEnum(ConnectionStatus), default=ConnectionStatus.PENDING, nullable=False)
    
    # 添加时间和更新时间
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # 备注信息
    remark = Column(Text, nullable=True)
    
    # 唯一约束，确保两个用户之间不会有重复的连接请求
    __table_args__ = (
        {'extend_existing': True},
    )
    
    # 关系定义
    from_user = relationship("User", foreign_keys=[from_user_id], backref="sent_connections")
    to_user = relationship("User", foreign_keys=[to_user_id], backref="received_connections")

# Pydantic 模型用于API
def generate_user_connection_id() -> str:
    return str(uuid.uuid4())

class UserConnectionBase(BaseModel):
    to_user_id: str
    connection_type: ConnectionType = Field(default=ConnectionType.FRIEND)
    remark: Optional[str] = None

class UserConnectionCreate(UserConnectionBase):
    pass

class UserConnectionUpdate(BaseModel):
    status: ConnectionStatus
    remark: Optional[str] = None

class UserConnectionResponse(BaseModel):
    id: str
    from_user_id: str
    to_user_id: str
    connection_type: ConnectionType
    status: ConnectionStatus
    remark: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserConnectionWithUserInfoResponse(UserConnectionResponse):
    # 包含对方用户的基本信息
    target_user: dict  # 存储对方用户的基本信息，如id、nick_name、avatar_url等
