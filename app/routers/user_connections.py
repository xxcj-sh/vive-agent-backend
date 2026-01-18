from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from app.utils.db_config import get_db
from app.dependencies import get_current_user
from app.models.user_connection import (
    UserConnectionCreate,
    UserConnectionUpdate,
    UserConnectionResponse,
    UserConnectionWithUserInfoResponse,
    ConnectionType,
    ConnectionStatus
)
from app.services.user_connection_service import UserConnectionService
from app.models.schemas import BaseResponse
from datetime import datetime, timedelta

router = APIRouter(tags=["user-connections"])

@router.post("", response_model=BaseResponse, status_code=201)
async def create_connection(
    request: Request,
    connection_data: UserConnectionCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建用户连接请求
    
    Args:
        request: 请求对象
        connection_data: 连接请求数据
        current_user: 当前用户信息
        db: 数据库会话
        
    Returns:
        创建结果
    """
    try:
        # 创建连接请求
        connection = UserConnectionService.create_connection(
            db=db,
            from_user_id=current_user["id"],
            connection_data=connection_data
        )
        
        # 构建响应
        return BaseResponse(
            code=0,
            message="success",
            data={
                "id": connection.id,
                "status": connection.status,
                "created_at": connection.created_at
            }
        )
    except HTTPException as e:
        return BaseResponse(
            code=e.status_code,
            message=e.detail,
            data={}
        )
    except Exception as e:
        return BaseResponse(
            code=1000,
            message=f"创建连接请求失败: {str(e)}",
            data={}
        )

@router.put("/{connection_id}", response_model=BaseResponse)
async def update_connection_status(
    connection_id: str,
    update_data: UserConnectionUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    更新连接状态（接受/拒绝/拉黑）
    
    Args:
        connection_id: 连接ID
        update_data: 更新数据
        current_user: 当前用户信息
        db: 数据库会话
        
    Returns:
        更新结果
    """
    try:
        # 更新连接状态
        connection = UserConnectionService.update_connection_status(
            db=db,
            connection_id=connection_id,
            user_id=current_user["id"],
            update_data=update_data
        )
        
        # 构建响应
        return BaseResponse(
            code=0,
            message="success",
            data={
                "id": connection.id,
                "status": connection.status,
                "updated_at": connection.updated_at
            }
        )
    except HTTPException as e:
        return BaseResponse(
            code=e.status_code,
            message=e.detail,
            data={}
        )
    except Exception as e:
        return BaseResponse(
            code=1000,
            message=f"更新连接状态失败: {str(e)}",
            data={}
        )

@router.get("", response_model=BaseResponse)
async def get_user_connections(
    connection_type: Optional[ConnectionType] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户的连接列表
    
    Args:
        connection_type: 连接类型过滤
        current_user: 当前用户信息
        db: 数据库会话
        
    Returns:
        连接列表
    """
    try:
        # 获取连接列表
        connections = UserConnectionService.get_user_connections(
            db=db,
            user_id=current_user["id"],
            connection_type=connection_type,
            as_addressee=False
        )
        
        # 构建带有用户信息的响应数据
        result_data = []
        for connection in connections:
            connection_with_info = UserConnectionService.get_connection_with_user_info(
                db=db,
                connection=connection,
                current_user_id=current_user["id"]
            )
            result_data.append(connection_with_info)
        
        # 构建响应
        return BaseResponse(
            code=0,
            message="success",
            data={
                "connections": result_data,
                "total": len(result_data)
            }
        )
    except Exception as e:
        return BaseResponse(
            code=1000,
            message=f"获取连接列表失败: {str(e)}",
            data={}
        )

@router.post("/record-visit/{to_user_id}", response_model=BaseResponse)
async def record_user_visit(
    to_user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    记录用户访问行为（访问他人主页）
    
    Args:
        to_user_id: 被访问用户的ID
        current_user: 当前用户信息
        db: 数据库会话
        
    Returns:
        记录结果
    """
    try:
        # 记录访问行为
        connection = UserConnectionService.record_visit(
            db=db,
            from_user_id=current_user["id"],
            to_user_id=to_user_id
        )
        
        if connection:
            return BaseResponse(
                code=0,
                message="访问记录成功",
                data={
                    "id": connection.id,
                    "connection_type": connection.connection_type,
                    "updated_at": connection.updated_at
                }
            )
        else:
            return BaseResponse(
                code=0,
                message="访问记录成功（无需创建新记录）",
                data={}
            )
            
    except Exception as e:
        return BaseResponse(
            code=1000,
            message=f"记录访问失败: {str(e)}",
            data={}
        )

@router.post("/record-view/{to_user_id}", response_model=BaseResponse)
async def record_user_view(
    to_user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    记录用户浏览行为（在Index页面浏览用户卡片）
    
    Args:
        to_user_id: 被浏览用户的ID
        current_user: 当前用户信息
        db: 数据库会话
        
    Returns:
        记录结果
    """
    try:
        # 记录浏览行为
        connection = UserConnectionService.record_view(
            db=db,
            from_user_id=current_user["id"],
            to_user_id=to_user_id
        )
        
        if connection:
            return BaseResponse(
                code=0,
                message="浏览记录成功",
                data={
                    "id": connection.id,
                    "connection_type": connection.connection_type,
                    "updated_at": connection.updated_at
                }
            )
        else:
            return BaseResponse(
                code=0,
                message="浏览记录成功（无需创建新记录）",
                data={}
            )
            
    except Exception as e:
        return BaseResponse(
            code=1000,
            message=f"记录浏览失败: {str(e)}",
            data={}
        )

@router.delete("/{connection_id}", status_code=204)
async def delete_connection(
    connection_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除连接关系
    
    Args:
        connection_id: 连接ID
        current_user: 当前用户信息
        db: 数据库会话
    """
    try:
        # 删除连接
        success = UserConnectionService.delete_connection(
            db=db,
            connection_id=connection_id,
            user_id=current_user["id"]
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="删除连接失败"
            )
            
        return None  # 204 No Content不应返回响应体
        
    except HTTPException:
        raise  # 重新抛出HTTPException
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"删除连接失败: {str(e)}"
        )

@router.get("/check/{target_user_id}", response_model=BaseResponse)
async def check_connection(
    target_user_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    检查与目标用户的连接状态
    
    Args:
        target_user_id: 目标用户ID
        current_user: 当前用户信息
        db: 数据库会话
        
    Returns:
        连接状态信息
    """
    try:
        # 检查连接
        connection = UserConnectionService.check_connection(
            db=db,
            user_id=current_user["id"],
            target_user_id=target_user_id
        )
        
        # 构建响应
        if connection:
            return BaseResponse(
                code=0,
                message="success",
                data={
                    "has_connection": True,
                    "connection_id": connection.id,
                    "status": connection.status,
                    "connection_type": connection.connection_type,
                    "is_requester": connection.from_user_id == current_user["id"]
                }
            )
        else:
            return BaseResponse(
                code=0,
                message="success",
                data={
                    "has_connection": False
                }
            )
    except Exception as e:
        return BaseResponse(
            code=1000,
            message=f"检查连接状态失败: {str(e)}",
            data={}
        )
