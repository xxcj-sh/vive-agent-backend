from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

# 用户角色卡片相关模型
class CardBase(BaseModel):
    """用户角色卡片基础模型"""
    id: str = Field(..., description="卡片ID")
    user_id: str = Field(..., description="用户ID")
    is_active: int = Field(..., description="是否激活")
    is_deleted: int = Field(..., description="是否删除")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

class CardCreate(BaseModel):
    """创建用户角色卡片模型"""
    role_type: str = Field(..., description="角色类型")
    display_name: str = Field(..., description="显示名称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    bio: Optional[str] = Field(None, description="个人简介")

    profile_data: Optional[Dict[str, Any]] = Field(None, description="角色特定数据")
    preferences: Optional[Dict[str, Any]] = Field(None, description="偏好设置")
    visibility: Optional[str] = Field("public", description="可见性")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    search_code: Optional[str] = Field(None, description="搜索代码")

class CardUpdate(BaseModel):
    """更新用户角色卡片模型"""
    display_name: Optional[str] = Field(None, description="显示名称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    bio: Optional[str] = Field(None, description="个人简介")

    profile_data: Optional[Dict[str, Any]] = Field(None, description="卡片描述数据")
    preferences: Optional[Dict[str, Any]] = Field(None, description="收卡人条件偏好")
    visibility: Optional[str] = Field(None, description="可见性")
    is_active: Optional[int] = Field(None, description="是否激活")
    search_code: Optional[str] = Field(None, description="搜索代码")

class Card(CardBase):
    """用户角色卡片响应模型"""
    role_type: str = Field(..., description="角色类型")
    display_name: str = Field(..., description="显示名称")
    avatar_url: Optional[str] = Field(None, description="卡片封面 URL")
    bio: Optional[str] = Field(None, description="卡片简介")

    profile_data: Optional[Dict[str, Any]] = Field(None, description="卡片特定数据")
    preferences: Optional[Dict[str, Any]] = Field(None, description="卡片匹配偏好")
    visibility: Optional[str] = Field("public", description="可见性")
    is_active: Optional[int] = Field(None, description="是否激活")
    search_code: Optional[str] = Field(None, description="搜索代码")
    
    @validator('profile_data', pre=True)
    def validate_profile_data(cls, v):
        """验证profile_data字段"""
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                return parsed if isinstance(parsed, dict) else {}
            except (json.JSONDecodeError, TypeError):
                return {}
        return v if isinstance(v, dict) else {}
    
    @validator('preferences', pre=True)
    def validate_preferences(cls, v):
        """验证preferences字段"""
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                return parsed if isinstance(parsed, dict) else {}
            except (json.JSONDecodeError, TypeError):
                return {}
        return v if isinstance(v, dict) else {}

    class Config:
        from_attributes = True

class CardsResponse(BaseModel):
    """用户多角色卡片响应模型"""
    user_id: str = Field(..., description="用户ID")
    profiles: List[Card] = Field(..., description="角色卡片列表")
    active_profiles: List[Card] = Field(..., description="激活的角色卡片列表")
    
class CardsByScene(BaseModel):
    """按场景分组的用户角色卡片"""
    profiles: List[Card] = Field(..., description="该场景下的卡片信息")

class AllCardsResponse(BaseModel):
    """用户所有角色卡片响应模型"""
    user_id: str = Field(..., description="用户ID")
    total_count: int = Field(..., description="总卡片数")
    active_count: int = Field(..., description="激活卡片数")
    by_scene: List[CardsByScene] = Field(..., description="按场景分组的卡片")
    all_cards: List[Card] = Field(..., description="所有卡片信息列表")