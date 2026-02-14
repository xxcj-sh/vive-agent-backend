from __future__ import annotations
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime

# 基础响应模型
class BaseResponse(BaseModel):
    code: int = Field(0, description="状态码，0表示成功，非0表示失败")
    message: str = Field("success", description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")

# 认证相关模型
class UserInfo(BaseModel):
    nick_name: Optional[str] = Field(None, description="用户昵称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    gender: Optional[int] = Field(None, description="性别，0-未知，1-男，2-女")

class LoginRequest(BaseModel):
    code: str = Field(..., description="登录凭证code")
    user_info: Optional[UserInfo] = Field(None, description="用户信息")
    
    @field_validator('code')
    @classmethod
    def code_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('code不能为空')
        return v

class LoginResponse(BaseModel):
    token: str = Field(..., description="用户token")
    expires_in: int = Field(..., description="token过期时间(秒)")
    user_info: Dict[str, Any] = Field(..., description="用户信息")

# 用户相关模型
class User(BaseModel):
    id: str = Field(..., description="用户ID")
    nick_name: str = Field(..., description="用户昵称")
    avatar_url: str = Field(..., description="头像URL")
    gender: int = Field(..., description="性别")
    age: Optional[int] = Field(None, description="年龄")
    occupation: Optional[str] = Field(None, description="职业")
    location: Optional[str] = Field(None, description="位置信息(JSON格式)")
    education: Optional[str] = Field(None, description="教育背景")
    interests: Optional[str] = Field(None, description="兴趣爱好(JSON格式)")
    wechat: Optional[str] = Field(None, description="微信号")
    email: Optional[str] = Field(None, description="邮箱")
    status: Optional[str] = Field(None, description="用户状态")
    level: Optional[int] = Field(None, description="用户等级")
    points: Optional[int] = Field(None, description="积分")
    last_login: Optional[datetime] = Field(None, description="最后登录时间")
    bio: Optional[str] = Field(None, description="个人简介")
    match_type: Optional[str] = Field(None, description="匹配类型: housing, activity, dating")
    user_role: Optional[str] = Field(None, description="用户角色: seeker, provider")

# 分页模型
class Pagination(BaseModel):
    page: int = Field(1, description="页码，从1开始")
    page_size: int = Field(10, description="每页数量")
    total: int = Field(0, description="总数量")





# 个人资料相关模型
class Card(BaseModel):
    id: str = Field(..., description="用户ID")
    nick_name: str = Field(..., description="昵称")
    avatar_url: str = Field(..., description="头像URL")
    age: Optional[int] = Field(None, description="年龄")
    occupation: Optional[str] = Field(None, description="职业")
    location: Optional[List[str]] = Field(None, description="位置，按[省, 市, 区/县]顺序存储")
    bio: Optional[str] = Field(None, description="个人简介")
    interests: Optional[List[str]] = Field(None, description="兴趣爱好")
    preferences: Optional[Dict[str, Any]] = Field(None, description="偏好设置")
    tenant_info: Optional[Dict[str, Any]] = Field(None, description="租户信息")

class CardUpdateRequest(BaseModel):
    nick_name: Optional[str] = Field(None, description="昵称")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    age: Optional[int] = Field(None, description="年龄")
    occupation: Optional[str] = Field(None, description="职业")
    location: Optional[List[str]] = Field(None, description="位置，按[省, 市, 区/县]顺序存储")
    bio: Optional[str] = Field(None, description="个人简介")
    interests: Optional[List[str]] = Field(None, description="兴趣爱好")
    preferences: Optional[Dict[str, Any]] = Field(None, description="偏好设置")
    tenant_info: Optional[Dict[str, Any]] = Field(None, description="租户信息")

# 文件上传响应
class FileUploadResponse(BaseModel):
    url: str = Field(..., description="文件URL")

# 场景配置相关模型
class SceneRole(BaseModel):
    key: str = Field(..., description="角色标识")
    label: str = Field(..., description="角色名称")
    description: str = Field(..., description="角色描述")

class SceneConfig(BaseModel):
    key: str = Field(..., description="场景标识")
    label: str = Field(..., description="场景名称")
    icon: str = Field(..., description="图标路径")
    iconActive: str = Field(..., description="激活时图标路径")
    description: str = Field(..., description="场景描述")
    roles: Dict[str, SceneRole] = Field(..., description="角色配置")
    CardFields: List[str] = Field(..., description="个人资料字段")
    tags: List[str] = Field(..., description="标签列表")

class SceneConfigResponse(BaseModel):
    scenes: Dict[str, SceneConfig] = Field(..., description="场景配置字典")


# 聊天相关模型
class ChatMessageResponse(BaseModel):
    id: str = Field(..., description="消息ID")
    content: str = Field(..., description="消息内容")
    type: str = Field(..., description="消息类型，如text、image等")
    sender: str = Field(..., description="发送者类型，如user、assistant等")
    created_at: str = Field(..., description="创建时间，ISO格式")
    is_anonymous: bool = Field(False, description="是否为匿名消息")


class ChatMessageCreate(BaseModel):
    user_id: Optional[str] = Field(None, description="用户ID")
    content: str = Field(..., description="消息内容")
    type: Optional[str] = Field("text", description="消息类型，如text、image等")
    is_anonymous: Optional[bool] = Field(False, description="是否为匿名消息")
    session_id: Optional[str] = Field(None, description="用户会话链接 ID")
    card_id: Optional[str] = Field(None, description="卡片ID")
    
    @field_validator('content')
    @classmethod
    def content_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('消息内容不能为空')
        return v


class ChatListResponse(BaseModel):
    chats: List[Dict[str, Any]] = Field(..., description="聊天会话列表")
    total: int = Field(..., description="总数")


# 聊天总结相关模型
class ChatSummaryResponse(BaseModel):
    id: str = Field(..., description="总结ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    card_id: Optional[str] = Field(None, description="卡片ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    summary_type: str = Field("chat", description="总结类型: chat, opinion, analysis")
    summary_content: str = Field(..., description="总结内容")
    chat_messages_count: Optional[str] = Field(None, description="聊天消息数量")
    summary_language: str = Field("zh", description="总结语言: zh, en")
    is_read: bool = Field(False, description="是否已读")
    read_at: Optional[str] = Field(None, description="阅读时间，ISO格式")
    created_at: Optional[str] = Field(None, description="创建时间，ISO格式")
    updated_at: Optional[str] = Field(None, description="更新时间，ISO格式")


class ChatSummaryCreate(BaseModel):
    user_id: Optional[str] = Field(None, description="用户ID")
    card_id: Optional[str] = Field(None, description="卡片ID")
    session_id: Optional[str] = Field(None, description="会话ID")
    summary_type: Optional[str] = Field("chat", description="总结类型: chat, opinion, analysis")
    chat_messages_count: Optional[str] = Field(None, description="聊天消息数量")
    summary_language: Optional[str] = Field("zh", description="总结语言: zh, en")
    is_read: Optional[bool] = Field(False, description="是否已读")
    user_messages: List[str] = Field(..., description="用户消息列表，用于LLM生成总结")
    
    @field_validator('user_messages')
    @classmethod
    def user_messages_must_not_be_empty(cls, v):
        if not v or len(v) == 0:
            raise ValueError('用户消息列表不能为空')
        return v