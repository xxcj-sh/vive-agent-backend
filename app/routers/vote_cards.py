from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any

from app.database import get_db
from app.services.vote_service import VoteService
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(tags=["votes"])

# Pydantic 模型
class VoteOptionCreate(BaseModel):
    text: str = Field(..., description="选项文本")
    image: Optional[str] = Field(None, description="选项图片URL")

class VoteCardCreate(BaseModel):
    title: str = Field(..., description="投票标题")
    description: Optional[str] = Field(None, description="投票描述")
    category: Optional[str] = Field(None, description="投票分类")
    tags: Optional[List[str]] = Field(default_factory=list, description="投票标签")
    cover_image: Optional[str] = Field(None, description="封面图片URL")
    vote_type: str = Field("single", description="投票类型: single(单选), multiple(多选)")
    is_anonymous_vote: bool = Field(False, description="是否匿名投票")
    is_realtime_result: bool = Field(True, description="是否实时显示结果")
    visibility: str = Field("public", description="可见性: public, private")
    start_time: Optional[datetime] = Field(None, description="投票开始时间")
    end_time: Optional[datetime] = Field(None, description="投票结束时间")
    vote_options: List[VoteOptionCreate] = Field(..., description="投票选项列表")
    user_card_id: Optional[str] = Field(None, description="用户卡片ID")

class VoteOptionResponse(BaseModel):
    id: str
    option_text: str
    option_image: Optional[str]
    vote_count: int
    display_order: int

class VoteCardResponse(BaseModel):
    id: str
    user_id: str
    title: str
    description: Optional[str]
    category: Optional[str]
    tags: Optional[List[str]]
    cover_image: Optional[str]
    vote_type: str
    is_anonymous: int
    is_realtime_result: int
    visibility: str
    view_count: int
    total_votes: int
    discussion_count: int
    share_count: int
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    vote_options: List[VoteOptionResponse]
    has_voted: bool = False
    user_votes: List[str] = []

class VoteSubmitRequest(BaseModel):
    topic_id: str = Field(..., description="投票卡片ID")
    option_ids: List[str] = Field(..., description="选择的选项ID列表")

class VoteSubmitResponse(BaseModel):
    success: bool
    message: str
    total_votes: int
    options: List[VoteOptionResponse]

class VoteDiscussionCreate(BaseModel):
    message: str = Field(..., description="讨论消息内容")
    message_type: str = Field("text", description="消息类型: text, image, voice")
    is_anonymous: bool = Field(True, description="是否匿名")

class VoteDiscussionResponse(BaseModel):
    id: str
    vote_card_id: str
    participant_id: str
    host_id: str
    message: str
    message_type: str
    is_anonymous: int
    created_at: datetime

class VoteCardsListResponse(BaseModel):
    cards: List[VoteCardResponse]
    total: int
    page: int
    page_size: int

# API 路由
@router.post("/create", response_model=VoteCardResponse)
async def create_vote_card(
    vote_data: VoteCardCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建投票卡片"""
    try:
        # 获取当前用户ID
        user_id = current_user.get("id") if current_user else None
        if not user_id:
            raise HTTPException(status_code=401, detail="用户未认证") if current_user else None
        if not user_id:
            raise HTTPException(status_code=401, detail="用户未认证") if current_user else None
        if not user_id:
            raise HTTPException(status_code=401, detail="用户未认证")
        
        print(f"收到投票创建请求，用户ID: {user_id}")
        print(f"投票数据: {vote_data.dict()}")
        
        vote_service = VoteService(db)
        vote_card = vote_service.create_vote_card(user_id, vote_data.dict())
        print(f"投票卡片创建成功，ID: {vote_card.id}")
        
        # 获取完整的投票卡片信息
        vote_results = vote_service.get_vote_results(vote_card.id, user_id)
        print(f"投票结果获取成功: {vote_results}")
        
        return VoteCardResponse(
            id=vote_card.id,
            user_id=vote_card.user_id,
            title=vote_card.title,
            description=vote_card.description,
            category=vote_card.category,
            tags=vote_card.tags,
            cover_image=vote_card.cover_image,
            vote_type=vote_card.vote_type,
            is_anonymous=vote_card.is_anonymous,
            is_realtime_result=vote_card.is_realtime_result,
            visibility=vote_card.visibility,
            view_count=vote_card.view_count,
            total_votes=vote_card.total_votes,
            discussion_count=vote_card.discussion_count,
            share_count=vote_card.share_count,
            start_time=vote_card.start_time,
            end_time=vote_card.end_time,
            created_at=vote_card.created_at,
            updated_at=vote_card.updated_at,
            vote_options=vote_results["options"],
            has_voted=vote_results["has_voted"],
            user_votes=vote_results["user_votes"]
        )
    except Exception as e:
        print(f"创建投票卡片失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{vote_card_id}", response_model=VoteCardResponse)
async def get_vote_card(
    vote_card_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取投票卡片详情"""
    try:
        vote_service = VoteService(db)
        # 获取当前用户ID
        user_id = current_user.get("id") if current_user else None
        if not user_id:
            raise HTTPException(status_code=401, detail="用户未认证")
        
        vote_results = vote_service.get_vote_results(vote_card_id, user_id)
        vote_card = vote_results["vote_card"]
        
        # 增加浏览次数
        vote_service.increment_view_count(vote_card_id)
        
        return VoteCardResponse(
            id=vote_card.id,
            user_id=vote_card.user_id,
            title=vote_card.title,
            description=vote_card.description,
            category=vote_card.category,
            tags=vote_card.tags,
            cover_image=vote_card.cover_image,
            vote_type=vote_card.vote_type,
            is_anonymous=vote_card.is_anonymous,
            is_realtime_result=vote_card.is_realtime_result,
            visibility=vote_card.visibility,
            view_count=vote_card.view_count,
            total_votes=vote_card.total_votes,
            discussion_count=vote_card.discussion_count,
            share_count=vote_card.share_count,
            start_time=vote_card.start_time,
            end_time=vote_card.end_time,
            created_at=vote_card.created_at,
            updated_at=vote_card.updated_at,
            vote_options=vote_results["options"],
            has_voted=vote_results["has_voted"],
            user_votes=vote_results["user_votes"]
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/{user_id}", response_model=VoteCardsListResponse)
async def get_user_vote_cards(
    user_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的投票卡片列表"""
    try:
        vote_service = VoteService(db)
        result = vote_service.get_vote_cards_by_user(user_id, page, page_size)
        
        # 为每个卡片添加投票状态
        cards_with_status = []
        current_user_id = current_user.get("id")
        for card in result["cards"]:
            vote_results = vote_service.get_vote_results(card.id, current_user_id)
            card_response = VoteCardResponse(
                id=card.id,
                user_id=card.user_id,
                title=card.title,
                description=card.description,
                category=card.category,
                tags=card.tags,
                cover_image=card.cover_image,
                vote_type=card.vote_type,
                is_anonymous=card.is_anonymous,
                is_realtime_result=card.is_realtime_result,
                visibility=card.visibility,
                view_count=card.view_count,
                total_votes=card.total_votes,
                discussion_count=card.discussion_count,
                share_count=card.share_count,
                start_time=card.start_time,
                end_time=card.end_time,
                created_at=card.created_at,
                updated_at=card.updated_at,
                vote_options=vote_results["options"],
                has_voted=vote_results["has_voted"],
                user_votes=vote_results["user_votes"]
            )
            cards_with_status.append(card_response)
        
        return VoteCardsListResponse(
            cards=cards_with_status,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{vote_card_id}/voted-users")
async def get_voted_users(
    vote_card_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取已投票用户列表"""
    try:
        vote_service = VoteService(db)
        result = vote_service.get_voted_users(vote_card_id, page, page_size)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"[DEBUG] 获取已投票用户列表时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/submit", response_model=VoteSubmitResponse)
async def submit_vote(
    vote_request: VoteSubmitRequest,
    request: Request,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """提交投票"""
    try:
        vote_service = VoteService(db)
        
        # 获取客户端信息
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # 获取当前用户ID
        user_id = current_user.get("id") if current_user else None
        if not user_id:
            raise HTTPException(status_code=401, detail="用户未认证")
        
        result = vote_service.submit_vote(
            user_id,
            vote_request.topic_id,
            vote_request.option_ids,
            ip_address,
            user_agent
        )
        
        return VoteSubmitResponse(
            success=True,
            message="投票成功",
            total_votes=result["total_votes"],
            options=result["options"]
        )
    except ValueError as e:
        print(f"[DEBUG] ValueError in submit_vote: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"[DEBUG] Exception in submit_vote: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{vote_card_id}/cancel")
async def cancel_vote(
    vote_card_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取消用户投票"""
    try:
        # 检查用户是否已认证
        if not current_user:
            raise HTTPException(status_code=401, detail="用户未认证")
        
        # 获取当前用户ID
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="用户未认证")
        
        vote_service = VoteService(db)
        result = vote_service.cancel_user_vote(user_id, vote_card_id)
        
        return VoteSubmitResponse(
            success=result["success"],
            message=result["message"],
            total_votes=result["total_votes"],
            options=result["options"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{vote_card_id}")
async def get_vote_status(
    vote_card_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户投票状态"""
    try:
        vote_service = VoteService(db)
        user_id = current_user.get("id") if current_user else None
        status = vote_service.get_user_vote_status(user_id, vote_card_id)
        
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{vote_card_id}/discussions", response_model=VoteDiscussionResponse)
async def add_vote_discussion(
    vote_card_id: str,
    discussion_data: VoteDiscussionCreate,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """添加投票讨论"""
    try:
        vote_service = VoteService(db)
        
        # 获取投票卡片信息以确定host_id
        vote_card = vote_service.get_vote_card(vote_card_id, include_options=False)
        if not vote_card:
            raise HTTPException(status_code=404, detail="投票卡片不存在")
        
        user_id = current_user.get("id") if current_user else None
        if not user_id:
            raise HTTPException(status_code=401, detail="用户未认证")
        
        discussion = vote_service.add_discussion(
            vote_card_id=vote_card_id,
            participant_id=user_id,
            host_id=vote_card.user_id,
            message=discussion_data.message,
            message_type=discussion_data.message_type,
            is_anonymous=discussion_data.is_anonymous
        )
        
        return VoteDiscussionResponse(**discussion.__dict__)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{vote_card_id}/discussions")
async def get_vote_discussions(
    vote_card_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取投票讨论列表"""
    try:
        vote_service = VoteService(db)
        result = vote_service.get_discussions(vote_card_id, page, page_size)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_vote_cards(
    keyword: str = Query(..., min_length=1),
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """搜索投票卡片"""
    try:
        vote_service = VoteService(db)
        result = vote_service.search_vote_cards(keyword, category, page, page_size)
        
        # 为每个卡片添加投票状态
        cards_with_status = []
        for card in result["cards"]:
            vote_results = vote_service.get_vote_results(card.id, current_user.get("id") if current_user else None)
            card_response = VoteCardResponse(
                id=card.id,
                user_id=card.user_id,
                title=card.title,
                description=card.description,
                category=card.category,
                tags=card.tags,
                cover_image=card.cover_image,
                vote_type=card.vote_type,
                is_anonymous=card.is_anonymous,
                is_realtime_result=card.is_realtime_result,
                visibility=card.visibility,
                view_count=card.view_count,
                total_votes=card.total_votes,
                discussion_count=card.discussion_count,
                share_count=card.share_count,
                start_time=card.start_time,
                end_time=card.end_time,
                created_at=card.created_at,
                updated_at=card.updated_at,
                vote_options=vote_results["options"],
                has_voted=vote_results["has_voted"],
                user_votes=vote_results["user_votes"]
            )
            cards_with_status.append(card_response)
        
        return VoteCardsListResponse(
            cards=cards_with_status,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{vote_card_id}")
async def delete_vote_card(
    vote_card_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除投票卡片（软删除）"""
    try:
        # 检查用户是否已认证
        if not current_user:
            raise HTTPException(status_code=401, detail="用户未认证")
        
        # 获取当前用户ID
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="用户未认证")
        
        vote_service = VoteService(db)
        success = vote_service.delete_vote_card(vote_card_id, user_id)
        
        if success:
            return {"success": True, "message": "投票卡片删除成功"}
        else:
            raise HTTPException(status_code=500, detail="删除投票卡片失败")
            
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
