"""
标签管理路由
API接口定义
创建时间: 2025-01-28
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.schemas import BaseResponse
from app.services.tag_service import TagService

router = APIRouter()


class TagCreateRequest(BaseModel):
    """创建标签请求"""
    name: str = Field(..., min_length=1, max_length=50, description="标签名称")
    desc: Optional[str] = Field(default="", max_length=255, description="标签描述")
    icon: Optional[str] = Field(default="", max_length=500, description="标签图标URL")
    tag_type: str = Field(default="user_community", description="标签类型")
    max_members: Optional[int] = Field(default=None, ge=1, description="最大成员数")
    is_public: int = Field(default=1, ge=0, le=1, description="是否公开")


class TagUpdateRequest(BaseModel):
    """更新标签请求"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=50, description="标签名称")
    desc: Optional[str] = Field(default=None, max_length=255, description="标签描述")
    icon: Optional[str] = Field(default=None, max_length=500, description="标签图标URL")


class UserTagBindRequest(BaseModel):
    """绑定用户标签请求"""
    user_id: str = Field(..., description="被绑定用户ID")
    tag_id: int = Field(..., description="标签ID")


class TagFilterRequest(BaseModel):
    """标签筛选请求"""
    tag_type: Optional[str] = Query(default=None, description="标签类型")
    user_id: Optional[str] = Query(default=None, description="创建者用户ID")
    is_public: Optional[int] = Query(default=None, ge=0, le=1, description="是否公开")
    page: int = Query(default=1, ge=1, description="页码")
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量")


@router.post("/tags", response_model=BaseResponse)
def create_tag(
    request: TagCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建标签"""
    if not current_user:
        raise HTTPException(status_code=401, detail="用户未认证")
    
    user_id = str(current_user.get("id"))
    tag_service = TagService(db)
    
    result = tag_service.create_tag(
        user_id=user_id,
        name=request.name,
        tag_type=request.tag_type,
        desc=request.desc,
        icon=request.icon,
        max_members=request.max_members,
        is_public=request.is_public
    )
    
    if result["code"] != 0:
        raise HTTPException(status_code=result["code"], detail=result["message"])
    
    return BaseResponse(code=0, message=result["message"], data=result["data"])


@router.get("/tags", response_model=BaseResponse)
def get_tags(
    tag_type: Optional[str] = Query(default=None, description="标签类型"),
    user_id: Optional[str] = Query(default=None, description="创建者用户ID"),
    is_public: Optional[int] = Query(default=None, ge=0, le=1, description="是否公开"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """获取标签列表"""
    tag_service = TagService(db)
    
    result = tag_service.get_tags(
        tag_type=tag_type,
        user_id=user_id,
        page=page,
        page_size=page_size,
        is_public=is_public
    )
    
    return BaseResponse(code=0, message="success", data=result)


@router.get("/tags/my", response_model=BaseResponse)
def get_my_tags(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户创建的标签列表"""
    if not current_user:
        raise HTTPException(status_code=401, detail="用户未认证")
    
    user_id = str(current_user.get("id"))
    tag_service = TagService(db)
    
    result = tag_service.get_user_created_tags(
        user_id=user_id,
        page=page,
        page_size=page_size
    )
    
    return BaseResponse(code=0, message="success", data=result)


@router.get("/tags/{tag_id}", response_model=BaseResponse)
def get_tag_detail(tag_id: int, db: Session = Depends(get_db)):
    """获取标签详情"""
    tag_service = TagService(db)
    tag = tag_service.get_tag(tag_id)
    
    if not tag:
        raise HTTPException(status_code=404, detail="标签不存在")
    
    return BaseResponse(code=0, message="success", data=tag_service._format_tag(tag))


@router.put("/tags/{tag_id}", response_model=BaseResponse)
def update_tag(
    tag_id: int,
    request: TagUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新标签（仅创建者可操作）"""
    if not current_user:
        raise HTTPException(status_code=401, detail="用户未认证")
    
    user_id = str(current_user.get("id"))
    tag_service = TagService(db)
    
    result = tag_service.update_tag(
        tag_id=tag_id,
        user_id=user_id,
        name=request.name,
        desc=request.desc,
        icon=request.icon
    )
    
    if result["code"] != 0:
        raise HTTPException(status_code=result["code"], detail=result["message"])
    
    return BaseResponse(code=0, message=result["message"], data=result["data"])


@router.delete("/tags/{tag_id}", response_model=BaseResponse)
def delete_tag(
    tag_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除标签（仅创建者可操作，软删除）"""
    if not current_user:
        raise HTTPException(status_code=401, detail="用户未认证")
    
    user_id = str(current_user.get("id"))
    tag_service = TagService(db)
    
    result = tag_service.delete_tag(tag_id=tag_id, user_id=user_id)
    
    if result["code"] != 0:
        raise HTTPException(status_code=result["code"], detail=result["message"])
    
    return BaseResponse(code=0, message=result["message"], data=result["data"])


@router.post("/user-tags", response_model=BaseResponse)
def bind_tag_to_user(
    request: UserTagBindRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """给用户绑定标签"""
    if not current_user:
        raise HTTPException(status_code=401, detail="用户未认证")
    
    operator_id = str(current_user.get("id"))
    tag_service = TagService(db)
    
    result = tag_service.bind_tag_to_user(
        user_id=request.user_id,
        tag_id=request.tag_id,
        granted_by=operator_id
    )
    
    if result["code"] != 0:
        raise HTTPException(status_code=result["code"], detail=result["message"])
    
    return BaseResponse(code=0, message=result["message"], data=result["data"])


@router.delete("/user-tags/{user_id}/{tag_id}", response_model=BaseResponse)
def unbind_tag_from_user(
    user_id: str,
    tag_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """解绑用户标签"""
    if not current_user:
        raise HTTPException(status_code=401, detail="用户未认证")
    
    operator_id = str(current_user.get("id"))
    tag_service = TagService(db)
    
    result = tag_service.unbind_tag_from_user(
        user_id=user_id,
        tag_id=tag_id,
        operator_id=operator_id
    )
    
    if result["code"] != 0:
        raise HTTPException(status_code=result["code"], detail=result["message"])
    
    return BaseResponse(code=0, message=result["message"], data=result["data"])


@router.get("/users/{user_id}/tags", response_model=BaseResponse)
def get_user_tags(user_id: str, db: Session = Depends(get_db)):
    """获取用户的标签列表"""
    tag_service = TagService(db)
    
    tags = tag_service.get_user_tags(user_id=user_id)
    
    return BaseResponse(code=0, message="success", data=tags)


@router.get("/users/me/communities", response_model=BaseResponse)
def get_my_communities(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=50, ge=1, le=100, description="每页数量"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户已加入的社群列表"""
    if not current_user:
        raise HTTPException(status_code=401, detail="用户未认证")
    
    user_id = str(current_user.get("id"))
    tag_service = TagService(db)
    
    all_tags = tag_service.get_user_tags(user_id=user_id)
    
    total = len(all_tags)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_items = all_tags[start_idx:end_idx]
    
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    
    return BaseResponse(
        code=0, 
        message="success", 
        data={
            "items": paginated_items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    )


@router.get("/tags/{tag_id}/users", response_model=BaseResponse)
def get_tag_users(
    tag_id: int,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(default=None, description="搜索关键词"),
    db: Session = Depends(get_db)
):
    """获取标签下的用户列表"""
    tag_service = TagService(db)
    
    result = tag_service.get_tag_users(
        tag_id=tag_id,
        page=page,
        page_size=page_size,
        keyword=keyword
    )
    
    if result["code"] != 0:
        raise HTTPException(status_code=result["code"], detail=result["message"])
    
    return BaseResponse(code=0, message=result["message"], data=result["data"])


# ==================== 标签内容推送功能 ====================

class TagContentCreateRequest(BaseModel):
    """创建标签内容请求"""
    title: str = Field(..., min_length=1, max_length=100, description="内容标题")
    content: str = Field(..., description="内容详情")
    content_type: str = Field(..., description="内容类型：card/topic/article/link")
    tag_ids: List[int] = Field(..., description="关联标签ID列表")
    cover_image: Optional[str] = Field(default="", max_length=500, description="封面图URL")
    priority: int = Field(default=0, ge=0, description="推送优先级")


@router.post("/contents", response_model=BaseResponse)
def create_tag_content(
    request: TagContentCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建标签推送内容"""
    if not current_user:
        raise HTTPException(status_code=401, detail="用户未认证")
    
    user_id = str(current_user.get("id"))
    tag_service = TagService(db)
    
    result = tag_service.create_tag_content(
        title=request.title,
        content=request.content,
        content_type=request.content_type,
        tag_ids=request.tag_ids,
        cover_image=request.cover_image,
        priority=request.priority,
        created_by=user_id
    )
    
    if result["code"] != 0:
        raise HTTPException(status_code=result["code"], detail=result["message"])
    
    return BaseResponse(code=0, message=result["message"], data=result["data"])


@router.post("/contents/{content_id}/publish", response_model=BaseResponse)
def publish_tag_content(
    content_id: int,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """发布标签内容"""
    if not current_user:
        raise HTTPException(status_code=401, detail="用户未认证")
    
    user_id = str(current_user.get("id"))
    tag_service = TagService(db)
    
    result = tag_service.publish_tag_content(
        content_id=content_id,
        user_id=user_id
    )
    
    if result["code"] != 0:
        raise HTTPException(status_code=result["code"], detail=result["message"])
    
    return BaseResponse(code=0, message=result["message"], data=result["data"])


@router.get("/tags/{tag_id}/contents", response_model=BaseResponse)
def get_tag_contents(
    tag_id: int,
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    content_type: Optional[str] = Query(default=None, description="内容类型筛选"),
    db: Session = Depends(get_db)
):
    """获取标签的内容列表"""
    tag_service = TagService(db)
    
    result = tag_service.get_tag_contents(
        tag_id=tag_id,
        page=page,
        page_size=page_size,
        content_type=content_type
    )
    
    return BaseResponse(code=0, message="success", data=result)


@router.get("/contents/recommend", response_model=BaseResponse)
def get_recommended_contents(
    tag_ids: Optional[str] = Query(default=None, description="标签ID列表，逗号分隔"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    content_type: Optional[str] = Query(default=None, description="内容类型筛选"),
    db: Session = Depends(get_db)
):
    """根据标签获取推荐内容"""
    tag_service = TagService(db)
    
    if tag_ids:
        ids = [int(tid) for tid in tag_ids.split(",")]
        result = tag_service.get_contents_by_tags(
            tag_ids=ids,
            page=page,
            page_size=page_size,
            content_type=content_type
        )
    else:
        result = {
            "items": [],
            "total": 0,
            "page": page,
            "page_size": page_size,
            "total_pages": 0
        }
    
    return BaseResponse(code=0, message="success", data=result)


@router.get("/contents/re/mycommend", response_model=BaseResponse)
def get_my_recommended_contents(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    content_type: Optional[str] = Query(default=None, description="内容类型筛选"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取根据我的标签推荐的个性化内容"""
    if not current_user:
        raise HTTPException(status_code=401, detail="用户未认证")
    
    user_id = str(current_user.get("id"))
    tag_service = TagService(db)
    
    result = tag_service.get_user_recommended_contents(
        user_id=user_id,
        page=page,
        page_size=page_size,
        content_type=content_type
    )
    
    return BaseResponse(code=0, message="success", data=result)


@router.get("/contents/{content_id}", response_model=BaseResponse)
def get_content_detail(
    content_id: int,
    db: Session = Depends(get_db)
):
    """获取内容详情"""
    tag_service = TagService(db)
    
    content = tag_service.get_content_detail(content_id)
    
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")
    
    return BaseResponse(code=0, message="success", data=tag_service._format_tag_content(content))


class ContentInteractionRequest(BaseModel):
    """内容交互请求"""
    interaction_type: str = Field(..., description="交互类型：view/like/share")


@router.post("/contents/{content_id}/interact", response_model=BaseResponse)
def interact_with_content(
    content_id: int,
    request: ContentInteractionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """内容交互（浏览、点赞、分享）"""
    if not current_user:
        raise HTTPException(status_code=401, detail="用户未认证")
    
    user_id = str(current_user.get("id"))
    tag_service = TagService(db)
    
    result = tag_service.interact_with_content(
        content_id=content_id,
        user_id=user_id,
        interaction_type=request.interaction_type
    )
    
    if result["code"] != 0:
        raise HTTPException(status_code=result["code"], detail=result["message"])
    
    return BaseResponse(code=0, message=result["message"], data=result["data"])
