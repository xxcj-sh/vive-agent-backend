from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
from pydantic import BaseModel
from typing import Optional
import enum
import uuid
from datetime import datetime

# 人脉关系状态枚举
class ConnectionStatus(str, enum.Enum):
    PENDING = "pending"      # 待确认
    ACCEPTED = "accepted"    # 已接受
    REJECTED = "rejected"    # 已拒绝
    BLOCKED = "blocked"      # 已拉黑
    CANCELLED = "cancelled"  # 已取消

# 人脉关系模型
class PersonConnection(Base):
    __tablename__ = "person_connections"
    
    id = Column(String(36), primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    from_user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    to_user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    connection_type = Column(String(50), nullable=True)  # 使用ConnectionType枚举的值
    status = Column(SQLEnum(ConnectionStatus), default=ConnectionStatus.PENDING, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    
    # 关系定义
    from_user = relationship("User", foreign_keys=[from_user_id], backref="sent_connections")
    to_user = relationship("User", foreign_keys=[to_user_id], backref="received_connections")

# Pydantic模型用于API输入输出
class PersonConnectionBase(BaseModel):
    to_user_id: str
    connection_type: Optional[str] = None
    notes: Optional[str] = None

class PersonConnectionCreate(PersonConnectionBase):
    pass

class PersonConnectionUpdate(BaseModel):
    status: ConnectionStatus
    notes: Optional[str] = None

class PersonConnectionResponse(BaseModel):
    id: str
    from_user_id: str
    to_user_id: str
    connection_type: Optional[str] = None
    status: ConnectionStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True

class PersonConnectionWithUsersResponse(PersonConnectionResponse):
    from_user: Optional[dict] = None  # 包含用户基本信息
    to_user: Optional[dict] = None    # 包含用户基本信息

class ConnectionListResponse(BaseModel):
    connections: list[PersonConnectionWithUsersResponse]
    total: int
    page: int
    page_size: int