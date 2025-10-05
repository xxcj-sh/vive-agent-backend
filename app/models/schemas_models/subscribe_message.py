"""
订阅消息相关的Pydantic模型
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class SubscribeMessageCreate(BaseModel):
    """创建订阅消息请求模型"""
    user_id: str
    template_id: str
    template_name: str
    message_data: Dict[str, Any]


class SubscribeMessageResponse(BaseModel):
    """订阅消息响应模型"""
    id: str
    user_id: str
    template_id: str
    template_name: str
    status: str
    message_data: Dict[str, Any]
    send_result: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class UserSubscribeSettingCreate(BaseModel):
    """创建用户订阅设置请求模型"""
    user_id: str
    template_id: str
    is_enabled: bool = True


class UserSubscribeSettingResponse(BaseModel):
    """用户订阅设置响应模型"""
    id: str
    user_id: str
    template_id: str
    is_enabled: bool
    is_subscribed: bool
    created_at: datetime
    updated_at: datetime


class SendSubscribeMessageRequest(BaseModel):
    """发送订阅消息请求模型"""
    user_id: str
    template_id: str = "5r-EhMIVK3yoUEo-TDkO36xwZvjzFuVAGETnKf5N36E"  # 用户关注通知模板ID
    template_name: str = "用户关注通知"
    message_data: Dict[str, Any]


class CheckSubscriptionRequest(BaseModel):
    """检查订阅状态请求模型"""
    user_id: str
    template_id: str = "5r-EhMIVK3yoUEo-TDkO36xwZvjzFuVAGETnKf5N36E"


class CheckSubscriptionResponse(BaseModel):
    """检查订阅状态响应模型"""
    user_id: str
    template_id: str
    is_enabled: bool
    is_subscribed: bool
    status: str  # granted, denied, unavailable, unchecked


class WechatSubscribeMessageRequest(BaseModel):
    """微信订阅消息请求模型"""
    touser: str  # 接收者（用户）的 openid
    template_id: str  # 所需下发的订阅模板id
    page: Optional[str] = None  # 点击模板卡片后的跳转页面
    data: Dict[str, Any]  # 模板内容
    miniprogram_state: Optional[str] = None  # 跳转小程序类型
    lang: Optional[str] = None  # 语言类型


class WechatSubscribeMessageResponse(BaseModel):
    """微信订阅消息响应模型"""
    errcode: int
    errmsg: str