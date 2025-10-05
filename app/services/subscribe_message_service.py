"""
订阅消息服务
处理微信订阅消息的发送和管理
"""

import json
import httpx
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime

from app.models.subscribe_message import SubscribeMessage, UserSubscribeSetting
from app.models.schemas_models.subscribe_message import (
    SubscribeMessageCreate,
    UserSubscribeSettingCreate,
    WechatSubscribeMessageRequest,
    CheckSubscriptionResponse
)
from app.config import settings


class SubscribeMessageService:
    """订阅消息服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def send_subscribe_message(self, message_data: SubscribeMessageCreate) -> Dict[str, Any]:
        """
        发送订阅消息
        
        Args:
            message_data: 订阅消息数据
            
        Returns:
            发送结果
        """
        try:
            # 1. 检查用户是否已订阅
            user_setting = self.get_user_subscribe_setting(message_data.user_id, message_data.template_id)
            if not user_setting or not user_setting.is_enabled or not user_setting.is_subscribed:
                return {
                    "success": False,
                    "message": "用户未订阅该消息模板",
                    "status": "denied"
                }
            
            # 2. 获取微信access_token
            access_token = await self._get_wechat_access_token()
            if not access_token:
                return {
                    "success": False,
                    "message": "获取微信access_token失败",
                    "status": "failed"
                }
            
            # 3. 获取用户的openid
            user_openid = await self._get_user_openid(message_data.user_id)
            if not user_openid:
                return {
                    "success": False,
                    "message": "获取用户openid失败",
                    "status": "failed"
                }
            
            # 4. 构建微信订阅消息请求
            wechat_request = WechatSubscribeMessageRequest(
                touser=user_openid,
                template_id=message_data.template_id,
                data=message_data.message_data
            )
            
            # 5. 调用微信订阅消息API
            result = await self._call_wechat_subscribe_api(access_token, wechat_request)
            
            # 6. 保存订阅消息记录
            subscribe_message = SubscribeMessage(
                user_id=message_data.user_id,
                template_id=message_data.template_id,
                template_name=message_data.template_name,
                status="sent" if result.get("errcode") == 0 else "failed",
                message_data=json.dumps(message_data.message_data, ensure_ascii=False),
                send_result=json.dumps(result, ensure_ascii=False),
                error_message=result.get("errmsg") if result.get("errcode") != 0 else None
            )
            
            self.db.add(subscribe_message)
            self.db.commit()
            
            if result.get("errcode") == 0:
                return {
                    "success": True,
                    "message": "订阅消息发送成功",
                    "status": "sent"
                }
            else:
                return {
                    "success": False,
                    "message": f"订阅消息发送失败: {result.get('errmsg')}",
                    "status": "failed"
                }
                
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "message": f"发送订阅消息异常: {str(e)}",
                "status": "failed"
            }
    
    def create_user_subscribe_setting(self, setting_data: UserSubscribeSettingCreate) -> UserSubscribeSetting:
        """
        创建用户订阅设置
        
        Args:
            setting_data: 用户订阅设置数据
            
        Returns:
            用户订阅设置对象
        """
        # 检查是否已存在
        existing_setting = self.db.query(UserSubscribeSetting).filter(
            UserSubscribeSetting.user_id == setting_data.user_id,
            UserSubscribeSetting.template_id == setting_data.template_id
        ).first()
        
        if existing_setting:
            # 更新现有设置
            existing_setting.is_enabled = setting_data.is_enabled
            existing_setting.updated_at = datetime.utcnow()
        else:
            # 创建新设置
            existing_setting = UserSubscribeSetting(
                user_id=setting_data.user_id,
                template_id=setting_data.template_id,
                is_enabled=setting_data.is_enabled,
                is_subscribed=False  # 默认未订阅，需要用户授权
            )
            self.db.add(existing_setting)
        
        self.db.commit()
        return existing_setting
    
    def get_user_subscribe_setting(self, user_id: str, template_id: str) -> Optional[UserSubscribeSetting]:
        """
        获取用户订阅设置
        
        Args:
            user_id: 用户ID
            template_id: 模板ID
            
        Returns:
            用户订阅设置对象或None
        """
        return self.db.query(UserSubscribeSetting).filter(
            UserSubscribeSetting.user_id == user_id,
            UserSubscribeSetting.template_id == template_id
        ).first()
    
    def check_user_subscription(self, user_id: str, template_id: str) -> CheckSubscriptionResponse:
        """
        检查用户订阅状态
        
        Args:
            user_id: 用户ID
            template_id: 模板ID
            
        Returns:
            订阅状态响应
        """
        user_setting = self.get_user_subscribe_setting(user_id, template_id)
        
        if not user_setting:
            return CheckSubscriptionResponse(
                user_id=user_id,
                template_id=template_id,
                is_enabled=False,
                is_subscribed=False,
                status="unchecked"
            )
        
        if not user_setting.is_enabled:
            return CheckSubscriptionResponse(
                user_id=user_id,
                template_id=template_id,
                is_enabled=False,
                is_subscribed=user_setting.is_subscribed,
                status="denied"
            )
        
        if not user_setting.is_subscribed:
            return CheckSubscriptionResponse(
                user_id=user_id,
                template_id=template_id,
                is_enabled=True,
                is_subscribed=False,
                status="denied"
            )
        
        return CheckSubscriptionResponse(
            user_id=user_id,
            template_id=template_id,
            is_enabled=True,
            is_subscribed=True,
            status="granted"
        )
    
    async def _get_wechat_access_token(self) -> Optional[str]:
        """获取微信access_token"""
        try:
            url = "https://api.weixin.qq.com/cgi-bin/token"
            params = {
                "grant_type": "client_credential",
                "appid": settings.WECHAT_APP_ID,
                "secret": settings.WECHAT_APP_SECRET
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10)
                response.raise_for_status()
                
                result = response.json()
                if "access_token" in result:
                    return result["access_token"]
                else:
                    print(f"获取微信access_token失败: {result}")
                    return None
                    
        except Exception as e:
            print(f"获取微信access_token异常: {str(e)}")
            return None
    
    async def _get_user_openid(self, user_id: str) -> Optional[str]:
        """
        获取用户的openid
        
        TODO: 需要根据实际用户表结构实现
        目前返回模拟的openid
        """
        try:
            # 这里需要根据user_id查询用户的openid
            # 暂时返回模拟数据
            return f"mock_openid_{user_id}"
        except Exception as e:
            print(f"获取用户openid异常: {str(e)}")
            return None
    
    async def _call_wechat_subscribe_api(self, access_token: str, request: WechatSubscribeMessageRequest) -> Dict[str, Any]:
        """调用微信订阅消息API"""
        try:
            url = f"https://api.weixin.qq.com/cgi-bin/message/subscribe/send?access_token={access_token}"
            
            # 构建请求数据
            request_data = {
                "touser": request.touser,
                "template_id": request.template_id,
                "data": request.data
            }
            
            if request.page:
                request_data["page"] = request.page
            if request.miniprogram_state:
                request_data["miniprogram_state"] = request.miniprogram_state
            if request.lang:
                request_data["lang"] = request.lang
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=request_data, timeout=10)
                response.raise_for_status()
                
                return response.json()
                
        except Exception as e:
            print(f"调用微信订阅消息API异常: {str(e)}")
            return {"errcode": -1, "errmsg": str(e)}