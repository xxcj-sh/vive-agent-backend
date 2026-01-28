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
