"""
活动邀约路由
提供AI分身活动邀约功能API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import random
import string

from app.database import get_db
from app.models.activity_invitation import (
    ActivityInvitation, ActivityInvitationCreate, ActivityInvitationResponse,
    ActivityInvitationUpdate, ActivityInvitationListResponse,
    ActivityInvitationAction, InvitationStatus, ActivityType,
    ActivityParticipant, ActivityLocation,
    CoffeeRecommendationRequest, CoffeeRecommendationResponse, LocationRecommendation
)
from app.models.ai_skill import AISkill, UserCardSkill, AISkillResponse
from app.models.user_card_db import UserCard
from app.models.user import User
from app.utils.logger import logger
from app.services.llm_service import LLMService

router = APIRouter()


def generate_invitation_code() -> str:
    """生成8位邀约码"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


@router.post("/invitations", response_model=ActivityInvitationResponse)
async def create_activity_invitation(
    invitation: ActivityInvitationCreate,
    db: Session = Depends(get_db)
):
    """创建活动邀约"""
    try:
        # 验证用户卡片是否存在
        user_card = db.query(UserCard).filter(UserCard.id == invitation.user_card_id).first()
        if not user_card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AI分身不存在"
            )

        # 获取卡片主人信息
        card_owner = db.query(User).filter(User.id == user_card.user_id).first()
        if not card_owner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="卡片主人不存在"
            )

        # TODO: 获取当前登录用户信息（发起人）
        # 暂时使用模拟数据
        inviter_id = "current_user_id"
        inviter_name = "当前用户"
        inviter_avatar = None

        # 生成邀约码
        invitation_code = generate_invitation_code()

        # 设置过期时间（7天后）
        expires_at = datetime.now() + timedelta(days=7)

        # 创建邀约记录
        db_invitation = ActivityInvitation(
            invitation_code=invitation_code,
            inviter_id=inviter_id,
            inviter_name=inviter_name,
            inviter_avatar=inviter_avatar,
            user_card_id=invitation.user_card_id,
            card_owner_id=card_owner.id,
            activity_type=ActivityType(invitation.activity_type),
            activity_title=invitation.activity_title,
            activity_description=invitation.activity_description,
            proposed_time=invitation.proposed_time,
            proposed_location=invitation.proposed_location,
            location_details=invitation.location_details,
            estimated_duration=invitation.estimated_duration,
            invitation_message=invitation.invitation_message,
            expires_at=expires_at,
            llm_recommendations=invitation.llm_recommendations
        )

        db.add(db_invitation)
        db.commit()
        db.refresh(db_invitation)

        # 创建参与者记录
        # 发起人
        inviter_participant = ActivityParticipant(
            invitation_id=db_invitation.id,
            user_id=inviter_id,
            user_name=inviter_name,
            user_avatar=inviter_avatar,
            role="inviter",
            is_confirmed=True
        )
        db.add(inviter_participant)

        # 卡片主人
        owner_participant = ActivityParticipant(
            invitation_id=db_invitation.id,
            user_id=card_owner.id,
            user_name=card_owner.nickName or card_owner.phone or "用户",
            user_avatar=card_owner.avatarUrl,
            role="owner",
            is_confirmed=False
        )
        db.add(owner_participant)

        db.commit()

        logger.info(f"创建活动邀约成功: {db_invitation.id}")
        return db_invitation

    except Exception as e:
        db.rollback()
        logger.error(f"创建活动邀约失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建活动邀约失败: {str(e)}"
        )


@router.get("/invitations/{invitation_id}", response_model=ActivityInvitationResponse)
async def get_activity_invitation(
    invitation_id: str,
    db: Session = Depends(get_db)
):
    """获取活动邀约详情"""
    invitation = db.query(ActivityInvitation).filter(
        ActivityInvitation.id == invitation_id
    ).first()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="活动邀约不存在"
        )

    return invitation


@router.get("/invitations/code/{invitation_code}", response_model=ActivityInvitationResponse)
async def get_activity_invitation_by_code(
    invitation_code: str,
    db: Session = Depends(get_db)
):
    """通过邀约码获取活动邀约"""
    invitation = db.query(ActivityInvitation).filter(
        ActivityInvitation.invitation_code == invitation_code
    ).first()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="邀约码不存在"
        )

    # 检查是否过期
    if invitation.expires_at and invitation.expires_at < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邀约已过期"
        )

    return invitation


@router.get("/my/invitations", response_model=ActivityInvitationListResponse)
async def get_my_invitations(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取我的活动邀约列表"""
    # TODO: 获取当前登录用户ID
    current_user_id = "current_user_id"

    query = db.query(ActivityInvitation).filter(
        (ActivityInvitation.inviter_id == current_user_id) |
        (ActivityInvitation.card_owner_id == current_user_id)
    )

    if status_filter:
        query = query.filter(ActivityInvitation.status == status_filter)

    invitations = query.order_by(ActivityInvitation.created_at.desc()).all()

    # 统计信息
    total_count = len(invitations)
    pending_count = len([i for i in invitations if i.status == InvitationStatus.PENDING])
    accepted_count = len([i for i in invitations if i.status == InvitationStatus.ACCEPTED])

    return ActivityInvitationListResponse(
        invitations=invitations,
        total_count=total_count,
        pending_count=pending_count,
        accepted_count=accepted_count
    )


@router.post("/invitations/{invitation_id}/accept", response_model=ActivityInvitationResponse)
async def accept_invitation(
    invitation_id: str,
    action: ActivityInvitationAction,
    db: Session = Depends(get_db)
):
    """接受活动邀约"""
    # TODO: 获取当前登录用户ID
    current_user_id = "current_user_id"

    invitation = db.query(ActivityInvitation).filter(
        ActivityInvitation.id == invitation_id
    ).first()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="活动邀约不存在"
        )

    # 检查是否是卡片主人
    if invitation.card_owner_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有卡片主人可以接受邀约"
        )

    # 检查状态
    if invitation.status != InvitationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"邀约当前状态为{invitation.status}，无法接受"
        )

    # 更新状态
    invitation.status = InvitationStatus.ACCEPTED
    invitation.confirmed_time = datetime.now()
    invitation.response_message = action.response_message

    # 更新参与者确认状态
    owner_participant = db.query(ActivityParticipant).filter(
        ActivityParticipant.invitation_id == invitation_id,
        ActivityParticipant.role == "owner"
    ).first()
    if owner_participant:
        owner_participant.is_confirmed = True

    db.commit()
    db.refresh(invitation)

    logger.info(f"接受活动邀约成功: {invitation_id}")
    return invitation


@router.post("/invitations/{invitation_id}/decline", response_model=ActivityInvitationResponse)
async def decline_invitation(
    invitation_id: str,
    action: ActivityInvitationAction,
    db: Session = Depends(get_db)
):
    """拒绝活动邀约"""
    # TODO: 获取当前登录用户ID
    current_user_id = "current_user_id"

    invitation = db.query(ActivityInvitation).filter(
        ActivityInvitation.id == invitation_id
    ).first()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="活动邀约不存在"
        )

    # 检查是否是卡片主人
    if invitation.card_owner_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有卡片主人可以拒绝邀约"
        )

    # 更新状态
    invitation.status = InvitationStatus.DECLINED
    invitation.response_message = action.response_message

    db.commit()
    db.refresh(invitation)

    logger.info(f"拒绝活动邀约成功: {invitation_id}")
    return invitation


@router.post("/invitations/{invitation_id}/cancel", response_model=ActivityInvitationResponse)
async def cancel_invitation(
    invitation_id: str,
    db: Session = Depends(get_db)
):
    """取消活动邀约（发起人操作）"""
    # TODO: 获取当前登录用户ID
    current_user_id = "current_user_id"

    invitation = db.query(ActivityInvitation).filter(
        ActivityInvitation.id == invitation_id
    ).first()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="活动邀约不存在"
        )

    # 检查是否是发起人
    if invitation.inviter_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有发起人可以取消邀约"
        )

    # 检查状态
    if invitation.status != InvitationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"邀约当前状态为{invitation.status}，无法取消"
        )

    # 更新状态
    invitation.status = InvitationStatus.CANCELLED

    db.commit()
    db.refresh(invitation)

    logger.info(f"取消活动邀约成功: {invitation_id}")
    return invitation


@router.get("/coffee-recommendations", response_model=CoffeeRecommendationResponse)
async def get_coffee_recommendations(
    user_card_id: str,
    location: Optional[str] = None,
    coffee_type: Optional[str] = None,
    atmosphere: Optional[str] = None,
    budget_range: Optional[str] = None,
    rating_min: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """获取咖啡店推荐"""
    try:
        # 获取用户卡片信息
        user_card = db.query(UserCard).filter(UserCard.id == user_card_id).first()
        if not user_card:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户卡片不存在"
            )

        # 获取用户信息
        user = db.query(User).filter(User.id == user_card.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        # 构建推荐请求
        request_data = CoffeeRecommendationRequest(
            user_card_id=user_card_id,
            location=location,
            coffee_type=coffee_type,
            atmosphere=atmosphere,
            budget_range=budget_range,
            rating_min=rating_min or 4.0,  # 默认最低评分4.0
            user_preferences={
                "preferred_locations": user_card.location_preferences or [],
                "coffee_preferences": user_card.coffee_preferences or [],
                "atmosphere_preferences": user_card.atmosphere_preferences or []
            }
        )

        # 使用LLM服务生成推荐
        llm_service = LLMService()
        recommendations = await llm_service.generate_coffee_recommendation(request_data)

        logger.info(f"咖啡店推荐生成成功，用户卡片: {user_card_id}")
        return CoffeeRecommendationResponse(
            recommendations=recommendations,
            total_count=len(recommendations),
            user_card_id=user_card_id
        )

    except Exception as e:
        logger.error(f"咖啡店推荐生成失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"推荐生成失败: {str(e)}"
        )


@router.get("/invitations/{invitation_id}/share-info")
async def get_invitation_share_info(
    invitation_id: str,
    db: Session = Depends(get_db)
):
    """获取活动邀约分享信息"""
    try:
        # 获取邀约详情
        invitation = db.query(ActivityInvitation).filter(
            ActivityInvitation.id == invitation_id
        ).first()

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="活动邀约不存在"
            )

        # 获取发起人信息
        inviter = db.query(User).filter(User.id == invitation.inviter_id).first()
        
        # 获取卡片信息
        user_card = db.query(UserCard).filter(UserCard.id == invitation.user_card_id).first()
        
        # 构建分享信息
        share_info = {
            "invitation_id": invitation.id,
            "invitation_code": invitation.invitation_code,
            "activity_type": invitation.activity_type.value,
            "activity_title": invitation.activity_title,
            "activity_description": invitation.activity_description,
            "proposed_time": invitation.proposed_time,
            "proposed_location": invitation.proposed_location,
            "invitation_message": invitation.invitation_message,
            "status": invitation.status.value,
            "expires_at": invitation.expires_at,
            "created_at": invitation.created_at,
            "inviter_info": {
                "id": inviter.id if inviter else None,
                "name": inviter.nickName if inviter else invitation.inviter_name,
                "avatar": inviter.avatarUrl if inviter else invitation.inviter_avatar
            },
            "card_info": {
                "id": user_card.id if user_card else None,
                "name": user_card.name if user_card else "AI分身",
                "avatar": user_card.avatar_url if user_card else None
            },
            "share_title": f"{invitation.activity_title} - 来自{inviter.nickName if inviter else invitation.inviter_name}的邀约",
            "share_description": invitation.activity_description or f"一起{invitation.activity_type.value}吧！",
            "share_image": user_card.avatar_url if user_card else "/images/icon-invitation.svg",
            "share_path": f"/pages/activity-invitation/activity-invitation?code={invitation.invitation_code}"
        }

        return share_info

    except Exception as e:
        logger.error(f"获取邀约分享信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取分享信息失败: {str(e)}"
        )


@router.post("/invitations/{invitation_id}/poster")
async def generate_invitation_poster(
    invitation_id: str,
    db: Session = Depends(get_db)
):
    """生成活动邀约分享海报"""
    try:
        # 获取邀约详情
        invitation = db.query(ActivityInvitation).filter(
            ActivityInvitation.id == invitation_id
        ).first()

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="活动邀约不存在"
            )

        # 获取分享信息
        share_info = await get_invitation_share_info(invitation_id, db)
        
        # 这里可以集成图片生成服务（如Pillow、Pillow等）
        # 暂时返回一个模拟的海报URL
        poster_url = f"/images/posters/invitation_{invitation_id}.jpg"
        
        # 模拟海报生成过程
        import time
        time.sleep(1)  # 模拟生成时间

        return {
            "poster_url": poster_url,
            "invitation_id": invitation_id,
            "expires_at": invitation.expires_at,
            "generated_at": datetime.now()
        }

    except Exception as e:
        logger.error(f"生成邀约海报失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成海报失败: {str(e)}"
        )
