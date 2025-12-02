"""
话题邀请路由
提供话题邀请功能API
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid

from app.database import get_db
from app.models.topic_invitation import (
    TopicInvitation, TopicInvitationCreate, TopicInvitationResponse,
    TopicInvitationUpdate, TopicInvitationListResponse,
    InvitationStatus, InvitationType
)
from app.models.user import User
from app.dependencies import get_current_user
from app.core.response import BaseResponse
from app.utils.logger import logger

router = APIRouter()

@router.post("/topic-cards/invitations", response_model=BaseResponse)
async def create_topic_invitation(
    invitation_data: TopicInvitationCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建话题邀请"""
    try:
        user_id = str(current_user.get("id"))
        if not user_id:
            raise HTTPException(status_code=401, detail="用户未认证")
        
        # 检查被邀请人是否存在
        invitee = db.query(User).filter(User.id == invitation_data.invitee_id).first()
        if not invitee:
            raise HTTPException(status_code=404, detail="被邀请用户不存在")
        
        # 检查话题是否存在且属于邀请人
        from app.models.topic_card_db import TopicCard
        topic = db.query(TopicCard).filter(
            TopicCard.id == invitation_data.topic_id,
            TopicCard.user_id == user_id
        ).first()
        
        if not topic:
            raise HTTPException(status_code=404, detail="话题不存在或无权限")
        
        # 检查是否已存在相同的邀请
        existing_invitation = db.query(TopicInvitation).filter(
            TopicInvitation.topic_id == invitation_data.topic_id,
            TopicInvitation.inviter_id == user_id,
            TopicInvitation.invitee_id == invitation_data.invitee_id,
            TopicInvitation.status == InvitationStatus.PENDING
        ).first()
        
        if existing_invitation:
            raise HTTPException(status_code=400, detail="已存在待处理的邀请")
        
        # 创建邀请
        new_invitation = TopicInvitation(
            id=str(uuid.uuid4()),
            topic_id=invitation_data.topic_id,
            inviter_id=user_id,
            invitee_id=invitation_data.invitee_id,
            invitation_type=invitation_data.invitation_type,
            is_anonymous=invitation_data.is_anonymous,
            inviter_role=invitation_data.inviter_role,
            invite_mode=invitation_data.invite_mode,
            message=invitation_data.message,
            status=InvitationStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db.add(new_invitation)
        db.commit()
        db.refresh(new_invitation)
        
        # 发送通知
        await send_topic_invitation_notification(db, new_invitation, invitee, current_user)
        
        return BaseResponse(
            code=0,
            message="话题邀请发送成功",
            data={"invitation_id": new_invitation.id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建话题邀请失败: {str(e)}")
        db.rollback()
        return BaseResponse(
            code=500,
            message=f"创建话题邀请失败: {str(e)}",
            data=None
        )

@router.get("/topic-cards/invitations/my", response_model=TopicInvitationListResponse)
async def get_my_topic_invitations(
    status: Optional[str] = None,
    invitation_type: Optional[str] = "received",  # received: 收到的邀请, sent: 发出的邀请
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取我的话题邀请列表"""
    try:
        user_id = str(current_user.get("id"))
        if not user_id:
            raise HTTPException(status_code=401, detail="用户未认证")
        
        # 根据类型查询邀请列表
        if invitation_type == "sent":
            # 查询我发出的邀请
            query = db.query(TopicInvitation).filter(
                TopicInvitation.inviter_id == user_id
            )
        else:
            # 默认查询我收到的邀请
            query = db.query(TopicInvitation).filter(
                TopicInvitation.invitee_id == user_id
            )
        
        # 按状态筛选
        if status:
            query = query.filter(TopicInvitation.status == status)
        
        # 按创建时间倒序排列
        invitations = query.order_by(TopicInvitation.created_at.desc()).all()
        
        # 转换为响应格式
        invitation_list = []
        for invitation in invitations:
            # 获取相关用户信息
            if invitation_type == "sent":
                # 对于发出的邀请，获取被邀请人信息
                other_user = db.query(User).filter(User.id == invitation.invitee_id).first()
                other_user_name = other_user.nick_name or other_user.name if other_user else "未知用户"
                other_user_avatar = other_user.avatar_url if other_user else None
            else:
                # 对于收到的邀请，获取邀请人信息
                other_user = db.query(User).filter(User.id == invitation.inviter_id).first()
                other_user_name = "匿名用户" if invitation.is_anonymous else (other_user.nick_name or other_user.name if other_user else "未知用户")
                other_user_avatar = other_user.avatar_url if other_user and not invitation.is_anonymous else None
            
            # 获取话题信息
            from app.models.topic_card_db import TopicCard
            topic = db.query(TopicCard).filter(TopicCard.id == invitation.topic_id).first()
            
            invitation_list.append({
                "id": invitation.id,
                "topic_id": invitation.topic_id,
                "topic_title": topic.title if topic else "未知话题",
                "topic_cover": topic.cover_image if topic else None,
                "inviter_id": invitation.inviter_id,
                "inviter_name": "匿名用户" if invitation.is_anonymous and invitation_type != "sent" else (other_user_name if invitation_type == "sent" else (other_user.nick_name or other_user.name if other_user else "未知用户")),
                "inviter_avatar": other_user_avatar if invitation_type != "sent" else (other_user.avatar_url if other_user else None),
                "invitee_id": invitation.invitee_id,
                "invitee_name": other_user_name if invitation_type == "sent" else (other_user.nick_name or other_user.name if other_user else "未知用户"),
                "invitation_type": invitation.invitation_type,
                "is_anonymous": invitation.is_anonymous,
                "inviter_role": invitation.inviter_role,
                "invite_mode": invitation.invite_mode,
                "message": invitation.message,
                "status": invitation.status,
                "created_at": invitation.created_at,
                "updated_at": invitation.updated_at,
                "expired_at": invitation.expired_at
            })
        
        # 统计不同状态的邀请数量
        total_count = len(invitation_list)
        pending_count = len([inv for inv in invitations if inv.status == InvitationStatus.PENDING])
        accepted_count = len([inv for inv in invitations if inv.status == InvitationStatus.ACCEPTED])
        rejected_count = len([inv for inv in invitations if inv.status == InvitationStatus.REJECTED])
        expired_count = len([inv for inv in invitations if inv.status == InvitationStatus.EXPIRED])
        
        return TopicInvitationListResponse(
            invitations=invitation_list,
            total_count=total_count,
            pending_count=pending_count,
            accepted_count=accepted_count,
            rejected_count=rejected_count,
            expired_count=expired_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取话题邀请列表失败: {str(e)}")
        return BaseResponse(
            code=500,
            message=f"获取话题邀请列表失败: {str(e)}",
            data=None
        )

@router.get("/topic-cards/invitations/{invitation_id}", response_model=BaseResponse)
async def get_topic_invitation_detail(
    invitation_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取话题邀请详情"""
    try:
        user_id = str(current_user.get("id"))
        if not user_id:
            raise HTTPException(status_code=401, detail="用户未认证")
        
        # 查找邀请（邀请人或受邀人都可以查看）
        invitation = db.query(TopicInvitation).filter(
            TopicInvitation.id == invitation_id,
            (TopicInvitation.inviter_id == user_id) | (TopicInvitation.invitee_id == user_id)
        ).first()
        
        if not invitation:
            raise HTTPException(status_code=404, detail="邀请不存在")
        
        # 获取邀请人信息
        inviter = db.query(User).filter(User.id == invitation.inviter_id).first()
        # 获取被邀请人信息
        invitee = db.query(User).filter(User.id == invitation.invitee_id).first()
        # 获取话题信息
        from app.models.topic_card_db import TopicCard
        topic = db.query(TopicCard).filter(TopicCard.id == invitation.topic_id).first()
        
        invitation_detail = {
            "id": invitation.id,
            "topic_id": invitation.topic_id,
            "topic_title": topic.title if topic else "未知话题",
            "topic_cover": topic.cover_image if topic else None,
            "inviter_id": invitation.inviter_id,
            "inviter_name": inviter.nick_name or inviter.name if inviter else "未知用户",
            "inviter_avatar": inviter.avatar_url if inviter else None,
            "invitee_id": invitation.invitee_id,
            "invitee_name": invitee.nick_name or invitee.name if invitee else "未知用户",
            "invitation_type": invitation.invitation_type,
            "is_anonymous": invitation.is_anonymous,
            "inviter_role": invitation.inviter_role,
            "invite_mode": invitation.invite_mode,
            "message": invitation.message,
            "status": invitation.status,
            "created_at": invitation.created_at,
            "updated_at": invitation.updated_at,
            "expired_at": invitation.expired_at
        }
        
        return BaseResponse(
            code=0,
            message="获取邀请详情成功",
            data=invitation_detail
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取话题邀请详情失败: {str(e)}")
        return BaseResponse(
            code=500,
            message=f"获取话题邀请详情失败: {str(e)}",
            data=None
        )

@router.post("/topic-cards/invitations/{invitation_id}/respond", response_model=BaseResponse)
async def respond_to_topic_invitation(
    invitation_id: str,
    response_data: dict,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """响应话题邀请"""
    try:
        user_id = str(current_user.get("id"))
        if not user_id:
            raise HTTPException(status_code=401, detail="用户未认证")
        
        # 查找邀请
        invitation = db.query(TopicInvitation).filter(
            TopicInvitation.id == invitation_id,
            TopicInvitation.invitee_id == user_id
        ).first()
        
        if not invitation:
            raise HTTPException(status_code=404, detail="邀请不存在")
        
        if invitation.status != InvitationStatus.PENDING:
            raise HTTPException(status_code=400, detail="邀请已处理")
        
        # 更新邀请状态
        response_status = response_data.get("status")
        if response_status not in [InvitationStatus.ACCEPTED, InvitationStatus.REJECTED]:
            raise HTTPException(status_code=400, detail="无效的响应状态")
        
        invitation.status = response_status
        invitation.updated_at = datetime.now()
        
        db.commit()
        
        # 如果接受邀请，创建话题参与记录
        if response_status == InvitationStatus.ACCEPTED:
            await create_topic_participation(db, invitation)
        
        # 发送通知给邀请人
        await send_invitation_response_notification(db, invitation, current_user)
        
        return BaseResponse(
            code=0,
            message=f"邀请已{response_status}",
            data={"success": True}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"响应话题邀请失败: {str(e)}")
        db.rollback()
        return BaseResponse(
            code=500,
            message=f"响应话题邀请失败: {str(e)}",
            data=None
        )

async def send_topic_invitation_notification(db: Session, invitation: TopicInvitation, invitee: User, inviter: dict):
    """发送话题邀请通知"""
    try:
        # 获取邀请人信息
        inviter_user = db.query(User).filter(User.id == invitation.inviter_id).first()
        
        # 获取话题信息
        from app.models.topic_card_db import TopicCard
        topic = db.query(TopicCard).filter(TopicCard.id == invitation.topic_id).first()
        
        if not inviter_user or not topic:
            return
        
        # 构建通知内容
        inviter_name = "匿名用户" if invitation.is_anonymous else (inviter_user.nick_name or inviter_user.name or "未知用户")
        notification_data = {
            "user_id": invitation.invitee_id,
            "type": "topic_invitation",
            "title": "话题邀请",
            "content": f"{inviter_name} 邀请您参与话题讨论：{topic.title}",
            "data": {
                "invitation_id": invitation.id,
                "topic_id": invitation.topic_id,
                "inviter_id": invitation.inviter_id,
                "inviter_name": inviter_name,
                "invitation_type": invitation.invitation_type,
                "is_anonymous": invitation.is_anonymous,
                "invite_mode": invitation.invite_mode,
                "message": invitation.message,
                "topic_title": topic.title,
                "topic_cover": topic.cover_image
            }
        }
        
        # 这里可以调用通知服务发送通知
        # 例如：await notification_service.send_notification(notification_data)
        logger.info(f"话题邀请通知已准备: {notification_data}")
        
    except Exception as e:
        logger.error(f"发送话题邀请通知失败: {str(e)}")

async def create_topic_participation(db: Session, invitation: TopicInvitation):
    """创建话题参与记录"""
    try:
        # 这里可以实现话题参与记录的创建逻辑
        # 例如：创建话题讨论记录、更新话题参与人数等
        pass
    except Exception as e:
        logger.error(f"创建话题参与记录失败: {str(e)}")

async def send_invitation_response_notification(db: Session, invitation: TopicInvitation, responder: dict):
    """发送邀请响应通知"""
    try:
        # 获取邀请人信息
        inviter = db.query(User).filter(User.id == invitation.inviter_id).first()
        
        # 获取话题信息
        from app.models.topic_card_db import TopicCard
        topic = db.query(TopicCard).filter(TopicCard.id == invitation.topic_id).first()
        
        if not inviter or not topic:
            return
        
        # 构建通知内容
        status_text = "接受了" if invitation.status == InvitationStatus.ACCEPTED else "拒绝了"
        responder_name = responder.get('nick_name') or responder.get('name') or "未知用户"
        notification_data = {
            "user_id": invitation.inviter_id,
            "type": "invitation_response",
            "title": "邀请响应",
            "content": f"{responder_name} {status_text}您的话题邀请：{topic.title}",
            "data": {
                "invitation_id": invitation.id,
                "topic_id": invitation.topic_id,
                "responder_id": invitation.invitee_id,
                "responder_name": responder_name,
                "status": invitation.status,
                "topic_title": topic.title
            }
        }
        
        # 这里可以调用通知服务发送通知
        # 例如：await notification_service.send_notification(notification_data)
        logger.info(f"邀请响应通知已准备: {notification_data}")
        
    except Exception as e:
        logger.error(f"发送邀请响应通知失败: {str(e)}")