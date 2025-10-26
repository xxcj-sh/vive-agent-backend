"""
用户画像版本控制和历史记录API路由
提供用户画像的历史记录查询、版本对比、版本回滚等功能
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.database import get_db
from app.models.user_profile_history import UserProfileHistory
from app.utils.auth import get_current_user
from app.models.user import User
from app.services.enhanced_user_profile_service import EnhancedUserProfileService

router = APIRouter(prefix="/profiles/history", tags=["用户画像历史记录"])


def get_profile_service(db: Session = Depends(get_db)) -> EnhancedUserProfileService:
    """获取增强用户画像服务实例"""
    return EnhancedUserProfileService(db)


@router.get("/user/{user_id}")
async def get_user_profile_history(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户画像历史记录列表"""
    # 权限检查：用户只能查看自己的历史记录，管理员可以查看所有用户
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="权限不足，只能查看自己的历史记录")
    
    # 查询历史记录
    history_records = db.query(UserProfileHistory).filter(
        UserProfileHistory.user_id == user_id
    ).order_by(UserProfileHistory.created_at.desc()).offset(skip).limit(limit).all()
    
    if not history_records:
        return {
            "user_id": user_id,
            "history": [],
            "total": 0,
            "skip": skip,
            "limit": limit
        }
    
    # 转换响应格式
    history_list = []
    for record in history_records:
        history_list.append({
            "id": record.id,
            "user_id": record.user_id,
            "profile_id": record.profile_id,
            "version": record.version,
            "change_type": record.change_type,
            "change_description": record.change_description,
            "previous_snapshot": record.previous_snapshot,
            "current_snapshot": record.current_snapshot,
            "metadata": record.metadata,
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat()
        })
    
    # 获取总数
    total = db.query(UserProfileHistory).filter(
        UserProfileHistory.user_id == user_id
    ).count()
    
    return {
        "user_id": user_id,
        "history": history_list,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/version/{version_id}")
async def get_version_details(
    version_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定版本的详细信息"""
    # 查询版本记录
    history_record = db.query(UserProfileHistory).filter(
        UserProfileHistory.id == version_id
    ).first()
    
    if not history_record:
        raise HTTPException(status_code=404, detail="版本记录不存在")
    
    # 权限检查
    if current_user.id != history_record.user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="权限不足，只能查看自己的版本记录")
    
    return {
        "id": history_record.id,
        "user_id": history_record.user_id,
        "profile_id": history_record.profile_id,
        "version": history_record.version,
        "change_type": history_record.change_type,
        "change_description": history_record.change_description,
        "previous_snapshot": history_record.previous_snapshot,
        "current_snapshot": history_record.current_snapshot,
        "metadata": history_record.metadata,
        "created_at": history_record.created_at.isoformat(),
        "updated_at": history_record.updated_at.isoformat()
    }


@router.post("/compare-versions")
async def compare_versions(
    version_ids: List[int],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """对比多个版本的差异"""
    if len(version_ids) < 2 or len(version_ids) > 5:
        raise HTTPException(status_code=400, detail="版本数量必须在2-5个之间")
    
    # 查询所有版本记录
    history_records = db.query(UserProfileHistory).filter(
        UserProfileHistory.id.in_(version_ids)
    ).all()
    
    if len(history_records) != len(version_ids):
        raise HTTPException(status_code=404, detail="部分版本记录不存在")
    
    # 权限检查：确保所有版本都属于同一用户
    user_ids = {record.user_id for record in history_records}
    if len(user_ids) > 1:
        raise HTTPException(status_code=400, detail="版本不属于同一用户")
    
    user_id = user_ids.pop()
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="权限不足，只能对比自己的版本")
    
    # 按版本号排序
    history_records.sort(key=lambda x: x.version)
    
    # 构建对比结果
    comparison = {
        "user_id": user_id,
        "versions_compared": len(history_records),
        "comparison_results": []
    }
    
    for i in range(len(history_records) - 1):
        current_record = history_records[i]
        next_record = history_records[i + 1]
        
        comparison_result = {
            "from_version": current_record.version,
            "to_version": next_record.version,
            "change_type": next_record.change_type,
            "change_description": next_record.change_description,
            "timestamp_diff": (next_record.created_at - current_record.created_at).total_seconds(),
            "snapshot_changes": {
                "previous": current_record.current_snapshot,
                "current": next_record.current_snapshot
            }
        }
        
        comparison["comparison_results"].append(comparison_result)
    
    return comparison


@router.post("/rollback/{version_id}")
async def rollback_to_version(
    version_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    profile_service: EnhancedUserProfileService = Depends(get_profile_service)
):
    """回滚到指定版本"""
    # 查询版本记录
    history_record = db.query(UserProfileHistory).filter(
        UserProfileHistory.id == version_id
    ).first()
    
    if not history_record:
        raise HTTPException(status_code=404, detail="版本记录不存在")
    
    # 权限检查
    if current_user.id != history_record.user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="权限不足，只能回滚自己的版本")
    
    # 执行回滚
    result = await profile_service.rollback_to_version(current_user.id, version_id)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/version-stats/{user_id}")
async def get_version_statistics(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户画像版本统计信息"""
    # 权限检查
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="权限不足，只能查看自己的统计信息")
    
    # 查询用户的历史记录统计
    from sqlalchemy import func
    
    stats = db.query(
        func.count(UserProfileHistory.id).label("total_versions"),
        func.min(UserProfileHistory.created_at).label("first_version_date"),
        func.max(UserProfileHistory.created_at).label("last_version_date"),
        func.avg(func.length(UserProfileHistory.change_description)).label("avg_change_length")
    ).filter(UserProfileHistory.user_id == user_id).first()
    
    # 查询各种变更类型的数量
    change_type_stats = db.query(
        UserProfileHistory.change_type,
        func.count(UserProfileHistory.id).label("count")
    ).filter(UserProfileHistory.user_id == user_id).group_by(UserProfileHistory.change_type).all()
    
    # 查询最近的版本
    latest_version = db.query(UserProfileHistory).filter(
        UserProfileHistory.user_id == user_id
    ).order_by(UserProfileHistory.created_at.desc()).first()
    
    return {
        "user_id": user_id,
        "total_versions": stats.total_versions or 0,
        "first_version_date": stats.first_version_date.isoformat() if stats.first_version_date else None,
        "last_version_date": stats.last_version_date.isoformat() if stats.last_version_date else None,
        "latest_version": latest_version.version if latest_version else None,
        "avg_change_length": float(stats.avg_change_length) if stats.avg_change_length else 0,
        "change_type_distribution": {
            change_type: count for change_type, count in change_type_stats
        }
    }