from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.database import get_db
from app.models.user import User
from app.models.topic_card_db import TopicCard, TopicDiscussion, TopicTriggerCondition
from app.models.topic_card import (
    TopicCardCreate, TopicCardUpdate, TopicCardResponse, TopicCardListResponse,
    TopicDiscussionCreate, TopicDiscussionResponse, TopicDiscussionListResponse,
    TriggerCondition, TriggerConditionResponse, TriggerConditionListResponse
)
from app.dependencies import get_current_user
from app.core.response import BaseResponse
from app.services.topic_card_service import TopicCardService
import uuid

router = APIRouter(prefix="", tags=["话题卡片"])

@router.post("", response_model=TopicCardResponse)
async def create_topic_card(
    card_data: TopicCardCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建话题卡片"""
    try:
        user_id = str(current_user.get("id"))
        if not user_id:
            raise HTTPException(status_code=401, detail="用户未认证")
        
        # 创建话题卡片
        topic_card = TopicCardService.create_topic_card(db, user_id, card_data)
        
        return topic_card
    except HTTPException:
        raise
    except Exception as e:
        print(f"创建话题卡片异常: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"创建话题卡片失败: {str(e)}")

@router.get("", response_model=TopicCardListResponse)
async def get_topic_cards(
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=50, description="每页数量"),
    category: Optional[str] = Query(None, description="话题分类"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取话题卡片列表"""
    try:
        user_id = str(current_user.get("id")) if current_user else None
        
        result = TopicCardService.get_topic_cards(
            db, 
            user_id=user_id,
            page=page, 
            page_size=pageSize,
            category=category,
            search=search
        )
        
        return result
    except Exception as e:
        print(f"获取话题卡片列表异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return BaseResponse(
            code=500,
            message=f"获取话题卡片列表失败: {str(e)}",
            data=None
        )

@router.get("/{card_id}", response_model=TopicCardResponse)
async def get_topic_card_detail(
    card_id: str,
    invitation_id: Optional[str] = Query(None, description="邀请ID，用于显示邀请者信息"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取话题卡片详情"""
    try:
        user_id = str(current_user.get("id")) if current_user else None
        
        card_detail = TopicCardService.get_topic_card_detail(db, card_id, user_id, invitation_id)
        if not card_detail:
            raise HTTPException(status_code=404, detail="话题卡片不存在")
        
        return card_detail
    except HTTPException:
        raise
    except Exception as e:
        print(f"获取话题卡片详情异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return BaseResponse(
            code=500,
            message=f"获取话题卡片详情失败: {str(e)}",
            data=None
        )

@router.put("/{card_id}", response_model=TopicCardResponse)
async def update_topic_card(
    card_id: str,
    update_data: TopicCardUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新话题卡片"""
    try:
        user_id = str(current_user.get("id"))
        if not user_id:
            raise HTTPException(status_code=401, detail="用户未认证")
        
        # 验证卡片所有权
        card = db.query(TopicCard).filter(TopicCard.id == card_id).first()
        if not card:
            raise HTTPException(status_code=404, detail="话题卡片不存在")
        
        # 调试日志：检查用户ID比较
        print(f"🔍 调试信息 - 权限验证:")
        print(f"   当前用户ID: '{user_id}' (类型: {type(user_id)})")
        print(f"   话题创建者ID: '{card.user_id}' (类型: {type(card.user_id)})")
        print(f"   比较结果: {card.user_id != user_id}")
        print(f"   相等结果: {card.user_id == user_id}")
        print(f"   长度比较: len('{user_id}')={len(user_id)}, len('{card.user_id}')={len(card.user_id)}")
        
        if card.user_id != user_id:
            raise HTTPException(
                status_code=403, 
                detail=f"无权限修改此话题卡片 (当前用户: {user_id}, 创建者: {card.user_id})"
            )
        
        # 更新话题卡片
        updated_card = TopicCardService.update_topic_card(db, card_id, update_data)
        
        return BaseResponse(
            code=0,
            message="话题卡片更新成功",
            data=updated_card
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"更新话题卡片异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return BaseResponse(
            code=500,
            message=f"更新话题卡片失败: {str(e)}",
            data=None
        )

@router.delete("/{card_id}")
async def delete_topic_card(
    card_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除话题卡片"""
    try:
        user_id = str(current_user.get("id"))
        if not user_id:
            raise HTTPException(status_code=401, detail="用户未认证")
        
        # 验证卡片所有权
        card = db.query(TopicCard).filter(TopicCard.id == card_id).first()
        if not card:
            raise HTTPException(status_code=404, detail="话题卡片不存在")
        
        if card.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权限删除此话题卡片")
        
        # 删除话题卡片
        success = TopicCardService.delete_topic_card(db, card_id)
        
        return BaseResponse(
            code=0,
            message="话题卡片删除成功",
            data={"success": success}
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"删除话题卡片异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return BaseResponse(
            code=500,
            message=f"删除话题卡片失败: {str(e)}",
            data=None
        )

@router.post("/{card_id}/discussions", response_model=TopicDiscussionResponse)
async def create_topic_discussion(
    card_id: str,
    discussion_data: TopicDiscussionCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建话题讨论"""
    try:
        user_id = str(current_user.get("id"))
        if not user_id:
            raise HTTPException(status_code=401, detail="用户未认证")
        
        # 验证话题卡片存在且可访问
        card = db.query(TopicCard).filter(TopicCard.id == card_id).first()
        if not card:
            raise HTTPException(status_code=404, detail="话题卡片不存在")
        
        if card.visibility == "private" and card.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权限访问此话题卡片")
        
        # 创建讨论记录
        discussion = TopicCardService.create_topic_discussion(
            db, card_id, user_id, discussion_data
        )
        
        return BaseResponse(
            code=0,
            message="讨论发表成功",
            data=discussion
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"创建话题讨论异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return BaseResponse(
            code=500,
            message=f"发表讨论失败: {str(e)}",
            data=None
        )

@router.get("/{card_id}/discussions", response_model=TopicDiscussionListResponse)
async def get_topic_discussions(
    card_id: str,
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取话题讨论列表"""
    try:
        user_id = str(current_user.get("id")) if current_user else None
        
        # 验证话题卡片存在且可访问
        card = db.query(TopicCard).filter(TopicCard.id == card_id).first()
        if not card:
            raise HTTPException(status_code=404, detail="话题卡片不存在")
        
        if card.visibility == "private" and (not user_id or card.user_id != user_id):
            raise HTTPException(status_code=403, detail="无权限访问此话题卡片")
        
        result = TopicCardService.get_topic_discussions(
            db, card_id, page=page, page_size=pageSize
        )
        
        return BaseResponse(
            code=0,
            message="success",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"获取话题讨论列表异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return BaseResponse(
            code=500,
            message=f"获取讨论列表失败: {str(e)}",
            data=None
        )

@router.post("/{card_id}/like")
async def like_topic_card(
    card_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """点赞话题卡片"""
    try:
        user_id = str(current_user.get("id"))
        if not user_id:
            raise HTTPException(status_code=401, detail="用户未认证")
        
        # 验证话题卡片存在
        card = db.query(TopicCard).filter(TopicCard.id == card_id).first()
        if not card:
            raise HTTPException(status_code=404, detail="话题卡片不存在")
        
        # 点赞话题卡片
        success = TopicCardService.like_topic_card(db, card_id, user_id)
        
        return BaseResponse(
            code=0,
            message="点赞成功",
            data={"success": success}
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"点赞话题卡片异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return BaseResponse(
            code=500,
            message=f"点赞失败: {str(e)}",
            data=None
        )

# 触发条件相关API
@router.get("/{card_id}/trigger-conditions", response_model=TriggerConditionListResponse)
async def get_trigger_conditions(
    card_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取话题卡片的触发条件列表"""
    try:
        user_id = str(current_user.get("id"))
        if not user_id:
            raise HTTPException(status_code=401, detail="用户未认证")
        
        # 验证卡片所有权
        card = db.query(TopicCard).filter(TopicCard.id == card_id).first()
        if not card:
            raise HTTPException(status_code=404, detail="话题卡片不存在")
        
        if card.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权限访问此话题卡片")
        
        # 获取触发条件列表
        conditions = db.query(TopicTriggerCondition).filter(
            TopicTriggerCondition.topic_card_id == card_id
        ).order_by(TopicTriggerCondition.priority.desc()).all()
        
        # 转换为响应模型
        condition_responses = []
        for condition in conditions:
            condition_responses.append(TriggerConditionResponse(
                id=condition.id,
                topic_card_id=condition.topic_card_id,
                condition_type=condition.trigger_type,
                condition_value={
                    "trigger_content": condition.trigger_content,
                    "output_content": condition.output_content,
                    "confidence": condition.confidence,
                    "time_type": condition.time_type,
                    "start_time": condition.start_time,
                    "end_time": condition.end_time,
                    "location_type": condition.location_type,
                    "location_data": condition.location_data,
                    "frequency_limit": condition.frequency_limit,
                    "priority": condition.priority,
                    "extra_config": condition.extra_config
                },
                is_enabled=condition.is_active,
                created_at=condition.created_at,
                updated_at=condition.updated_at
            ))
        
        return BaseResponse(
            code=0,
            message="success",
            data=TriggerConditionListResponse(
                items=condition_responses,
                total=len(condition_responses)
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"获取触发条件列表异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return BaseResponse(
            code=500,
            message=f"获取触发条件列表失败: {str(e)}",
            data=None
        )

@router.post("/{card_id}/trigger-conditions", response_model=TriggerConditionResponse)
async def create_trigger_condition(
    card_id: str,
    condition_data: TriggerCondition,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建话题卡片的触发条件"""
    try:
        user_id = str(current_user.get("id"))
        if not user_id:
            raise HTTPException(status_code=401, detail="用户未认证")
        
        # 验证卡片所有权
        card = db.query(TopicCard).filter(TopicCard.id == card_id).first()
        if not card:
            raise HTTPException(status_code=404, detail="话题卡片不存在")
        
        if card.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权限修改此话题卡片")
        
        # 创建触发条件
        condition_value = condition_data.condition_value or {}
        
        new_condition = TopicTriggerCondition(
            id=str(uuid.uuid4()),
            topic_card_id=card_id,
            trigger_type=condition_data.condition_type,
            trigger_content=condition_value.get("trigger_content"),
            output_content=condition_value.get("output_content"),
            confidence=condition_value.get("confidence", "medium"),
            time_type=condition_value.get("time_type"),
            start_time=condition_value.get("start_time"),
            end_time=condition_value.get("end_time"),
            location_type=condition_value.get("location_type"),
            location_data=condition_value.get("location_data"),
            frequency_limit=condition_value.get("frequency_limit", 0),
            is_active=condition_data.is_enabled,
            priority=condition_value.get("priority", 1),
            extra_config=condition_value.get("extra_config")
        )
        
        db.add(new_condition)
        db.commit()
        db.refresh(new_condition)
        
        # 转换为响应模型
        response = TriggerConditionResponse(
            id=new_condition.id,
            topic_card_id=new_condition.topic_card_id,
            condition_type=new_condition.trigger_type,
            condition_value={
                "trigger_content": new_condition.trigger_content,
                "output_content": new_condition.output_content,
                "confidence": new_condition.confidence,
                "time_type": new_condition.time_type,
                "start_time": new_condition.start_time,
                "end_time": new_condition.end_time,
                "location_type": new_condition.location_type,
                "location_data": new_condition.location_data,
                "frequency_limit": new_condition.frequency_limit,
                "priority": new_condition.priority,
                "extra_config": new_condition.extra_config
            },
            is_enabled=new_condition.is_active,
            created_at=new_condition.created_at,
            updated_at=new_condition.updated_at
        )
        
        return BaseResponse(
            code=0,
            message="触发条件创建成功",
            data=response
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"创建触发条件异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return BaseResponse(
            code=500,
            message=f"创建触发条件失败: {str(e)}",
            data=None
        )

@router.put("/{card_id}/trigger-conditions/{condition_id}", response_model=TriggerConditionResponse)
async def update_trigger_condition(
    card_id: str,
    condition_id: str,
    condition_data: TriggerCondition,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新话题卡片的触发条件"""
    try:
        user_id = str(current_user.get("id"))
        if not user_id:
            raise HTTPException(status_code=401, detail="用户未认证")
        
        # 验证卡片所有权
        card = db.query(TopicCard).filter(TopicCard.id == card_id).first()
        if not card:
            raise HTTPException(status_code=404, detail="话题卡片不存在")
        
        if card.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权限修改此话题卡片")
        
        # 查找触发条件
        condition = db.query(TopicTriggerCondition).filter(
            TopicTriggerCondition.id == condition_id,
            TopicTriggerCondition.topic_card_id == card_id
        ).first()
        
        if not condition:
            raise HTTPException(status_code=404, detail="触发条件不存在")
        
        # 更新触发条件
        condition_value = condition_data.condition_value or {}
        
        condition.trigger_type = condition_data.condition_type
        condition.trigger_content = condition_value.get("trigger_content", condition.trigger_content)
        condition.output_content = condition_value.get("output_content", condition.output_content)
        condition.confidence = condition_value.get("confidence", condition.confidence)
        condition.time_type = condition_value.get("time_type", condition.time_type)
        condition.start_time = condition_value.get("start_time", condition.start_time)
        condition.end_time = condition_value.get("end_time", condition.end_time)
        condition.location_type = condition_value.get("location_type", condition.location_type)
        condition.location_data = condition_value.get("location_data", condition.location_data)
        condition.frequency_limit = condition_value.get("frequency_limit", condition.frequency_limit)
        condition.is_active = condition_data.is_enabled
        condition.priority = condition_value.get("priority", condition.priority)
        condition.extra_config = condition_value.get("extra_config", condition.extra_config)
        
        db.commit()
        db.refresh(condition)
        
        # 转换为响应模型
        response = TriggerConditionResponse(
            id=condition.id,
            topic_card_id=condition.topic_card_id,
            condition_type=condition.trigger_type,
            condition_value={
                "trigger_content": condition.trigger_content,
                "output_content": condition.output_content,
                "confidence": condition.confidence,
                "time_type": condition.time_type,
                "start_time": condition.start_time,
                "end_time": condition.end_time,
                "location_type": condition.location_type,
                "location_data": condition.location_data,
                "frequency_limit": condition.frequency_limit,
                "priority": condition.priority,
                "extra_config": condition.extra_config
            },
            is_enabled=condition.is_active,
            created_at=condition.created_at,
            updated_at=condition.updated_at
        )
        
        return BaseResponse(
            code=0,
            message="触发条件更新成功",
            data=response
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"更新触发条件异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return BaseResponse(
            code=500,
            message=f"更新触发条件失败: {str(e)}",
            data=None
        )

@router.delete("/{card_id}/trigger-conditions/{condition_id}")
async def delete_trigger_condition(
    card_id: str,
    condition_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除话题卡片的触发条件"""
    try:
        user_id = str(current_user.get("id"))
        if not user_id:
            raise HTTPException(status_code=401, detail="用户未认证")
        
        # 验证卡片所有权
        card = db.query(TopicCard).filter(TopicCard.id == card_id).first()
        if not card:
            raise HTTPException(status_code=404, detail="话题卡片不存在")
        
        if card.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权限修改此话题卡片")
        
        # 查找触发条件
        condition = db.query(TopicTriggerCondition).filter(
            TopicTriggerCondition.id == condition_id,
            TopicTriggerCondition.topic_card_id == card_id
        ).first()
        
        if not condition:
            raise HTTPException(status_code=404, detail="触发条件不存在")
        
        # 删除触发条件
        db.delete(condition)
        db.commit()
        
        return BaseResponse(
            code=0,
            message="触发条件删除成功",
            data={"success": True}
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"删除触发条件异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return BaseResponse(
            code=500,
            message=f"删除触发条件失败: {str(e)}",
            data=None
        )