"""
订阅消息路由
处理订阅消息相关的API请求
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import get_db
from app.services.subscribe_message_service import SubscribeMessageService
from app.models.schemas_models.subscribe_message import (
    SendSubscribeMessageRequest,
    CheckSubscriptionRequest,
    UserSubscribeSettingCreate
)
from app.models.schemas import BaseResponse

router = APIRouter(prefix="/subscribe-messages", tags=["订阅消息"])


@router.post("/send", response_model=BaseResponse)
async def send_subscribe_message(
    request: SendSubscribeMessageRequest,
    db: Session = Depends(get_db)
):
    """
    发送订阅消息
    
    Args:
        request: 发送订阅消息请求
        
    Returns:
        发送结果
    """
    try:
        service = SubscribeMessageService(db)
        
        # 构建订阅消息数据
        message_data = {
            "user_id": request.user_id,
            "template_id": request.template_id,
            "template_name": request.template_name,
            "message_data": request.message_data
        }
        
        result = await service.send_subscribe_message(message_data)
        
        return BaseResponse(
            code=0 if result["success"] else 1,
            message=result["message"],
            data={"status": result["status"]}
        )
        
    except Exception as e:
        return BaseResponse(
            code=1,
            message=f"发送订阅消息失败: {str(e)}",
            data={}
        )


@router.get("/check/{user_id}", response_model=BaseResponse)
def check_subscription_status(
    user_id: str,
    template_id: str = "5r-EhMIVK3yoUEo-TDkO36xwZvjzFuVAGETnKf5N36E",
    db: Session = Depends(get_db)
):
    """
    检查用户订阅状态
    
    Args:
        user_id: 用户ID
        template_id: 模板ID
        
    Returns:
        订阅状态
    """
    try:
        service = SubscribeMessageService(db)
        result = service.check_user_subscription(user_id, template_id)
        
        return BaseResponse(
            code=0,
            message="success",
            data={
                "status": result.status,
                "is_enabled": result.is_enabled,
                "is_subscribed": result.is_subscribed
            }
        )
        
    except Exception as e:
        return BaseResponse(
            code=1,
            message=f"检查订阅状态失败: {str(e)}",
            data={}
        )


@router.post("/settings", response_model=BaseResponse)
def create_user_subscribe_setting(
    request: UserSubscribeSettingCreate,
    db: Session = Depends(get_db)
):
    """
    创建或更新用户订阅设置
    
    Args:
        request: 用户订阅设置请求
        
    Returns:
        操作结果
    """
    try:
        service = SubscribeMessageService(db)
        setting = service.create_user_subscribe_setting(request)
        
        return BaseResponse(
            code=0,
            message="success",
            data={
                "id": setting.id,
                "user_id": setting.user_id,
                "template_id": setting.template_id,
                "is_enabled": setting.is_enabled,
                "is_subscribed": setting.is_subscribed
            }
        )
        
    except Exception as e:
        return BaseResponse(
            code=1,
            message=f"创建订阅设置失败: {str(e)}",
            data={}
        )


@router.post("/trigger-notification", response_model=BaseResponse)
async def send_trigger_notification(
    request: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """
    发送触发对话通知
    
    Args:
        request: 触发通知请求
            - trigger_user_id: 触发对话的用户ID
            - target_user_id: 目标用户ID（卡片所有者）
            - card_id: 卡片ID
            - role_type: 角色类型
            - trigger_content: 触发内容
            
    Returns:
        发送结果
    """
    try:
        service = SubscribeMessageService(db)
        
        # 提取请求参数
        trigger_user_id = request.get("trigger_user_id")
        target_user_id = request.get("target_user_id")
        card_id = request.get("card_id")
        role_type = request.get("role_type")
        trigger_content = request.get("trigger_content", "")
        
        if not all([trigger_user_id, target_user_id, card_id, role_type]):
            return BaseResponse(
                code=1,
                message="缺少必要参数",
                data={}
            )
        
        # 构建订阅消息数据
        message_data = {
            "user_id": target_user_id,  # 发送给卡片所有者
            "template_id": "5r-EhMIVK3yoUEo-TDkO36xwZvjzFuVAGETnKf5N36E",
            "template_name": "用户关注通知",
            "message_data": {
                "thing1": {"value": "有人触发了您的对话规则"},
                "thing2": {"value": trigger_content[:20] + "..." if len(trigger_content) > 20 else trigger_content},
                "thing3": {"value": role_type},
                "time4": {"value": "刚刚"}
            }
        }
        
        result = await service.send_subscribe_message(message_data)
        
        return BaseResponse(
            code=0 if result["success"] else 1,
            message=result["message"],
            data={
                "status": result["status"],
                "trigger_user_id": trigger_user_id,
                "target_user_id": target_user_id
            }
        )
        
    except Exception as e:
        return BaseResponse(
            code=1,
            message=f"发送触发通知失败: {str(e)}",
            data={}
        )