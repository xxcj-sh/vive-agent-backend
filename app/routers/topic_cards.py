from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.database import get_db
from app.models.user import User
from app.models.topic_card_db import TopicCard, TopicDiscussion
from app.models.topic_card import (
    TopicCardCreate, TopicCardUpdate, TopicCardResponse, TopicCardListResponse,
    TopicDiscussionCreate, TopicDiscussionResponse, TopicDiscussionListResponse,
    TopicOpinionSummaryResponse, TopicOpinionSummaryListResponse
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

@router.get("/{card_id}/opinion-summaries")
async def get_topic_opinion_summaries(
    card_id: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取话题观点总结列表"""
    try:
        result = TopicCardService.get_topic_opinion_summaries(db, card_id, page, page_size)
        return BaseResponse(
            code=0,
            message="success",
            data=result
        )
    except Exception as e:
        print(f"获取话题观点总结失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return BaseResponse(
            code=500,
            message=f"获取观点总结失败: {str(e)}",
            data=None
        )