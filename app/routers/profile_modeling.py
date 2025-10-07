"""
用户画像离线建模模块API路由
提供人设真实性验证、内容合规性验证、用户画像分析更新等功能
"""

from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
import logging

from app.dependencies import get_db
from app.services.profile_modeling_service import ProfileModelingService
from app.services.profile_modeling_scheduler import ProfileModelingScheduler
from app.models.user import User
from app.core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/profile-modeling", tags=["用户画像离线建模"])


@router.post("/verify-authenticity/{user_id}", response_model=Dict[str, Any])
async def verify_profile_authenticity(
    user_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    验证用户人设真实性
    
    - **user_id**: 用户ID
    - **background_tasks**: 后台任务
    - **db**: 数据库会话
    - **current_user**: 当前登录用户
    
    返回:
    - success: 是否成功
    - authenticity_score: 真实性评分 (0-100)
    - analysis_result: 分析结果
    - verification_details: 验证详情
    """
    try:
        modeling_service = ProfileModelingService(db)
        
        # 验证用户是否有权限访问此功能
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="您没有权限验证其他用户的人设真实性"
            )
        
        # 执行真实性验证
        result = await modeling_service.verify_profile_authenticity(user_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"人设真实性验证失败: {result.get('error', '未知错误')}"
            )
        
        logger.info(f"用户 {user_id} 人设真实性验证完成，评分: {result['authenticity_score']}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"验证用户 {user_id} 人设真实性时发生错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"人设真实性验证过程中发生错误: {str(e)}"
        )


@router.post("/verify-compliance/{card_id}", response_model=Dict[str, Any])
async def verify_content_compliance(
    card_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    验证卡片内容合规性
    
    - **card_id**: 卡片ID
    - **background_tasks**: 后台任务
    - **db**: 数据库会话
    - **current_user**: 当前登录用户
    
    返回:
    - success: 是否成功
    - is_compliant: 是否合规
    - compliance_score: 合规性评分 (0-100)
    - violations: 违规详情
    - suggestions: 改进建议
    """
    try:
        modeling_service = ProfileModelingService(db)
        
        # 执行合规性验证
        result = await modeling_service.verify_content_compliance(card_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"内容合规性验证失败: {result.get('error', '未知错误')}"
            )
        
        compliance_status = "通过" if result["is_compliant"] else "拒绝"
        logger.info(f"卡片 {card_id} 内容合规性验证完成，状态: {compliance_status}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"验证卡片 {card_id} 内容合规性时发生错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"内容合规性验证过程中发生错误: {str(e)}"
        )


@router.post("/update-profile/{user_id}", response_model=Dict[str, Any])
async def update_user_profile_analysis(
    user_id: int,
    background_tasks: BackgroundTasks,
    include_recent_chats: bool = Query(True, description="是否包含最近聊天记录"),
    include_new_cards: bool = Query(True, description="是否包含新卡片内容"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新用户画像分析
    
    - **user_id**: 用户ID
    - **include_recent_chats**: 是否包含最近聊天记录
    - **include_new_cards**: 是否包含新卡片内容
    - **background_tasks**: 后台任务
    - **db**: 数据库会话
    - **current_user**: 当前登录用户
    
    返回:
    - success: 是否成功
    - confidence_score: 置信度评分 (0-100)
    - updated_fields: 更新的字段
    - analysis_summary: 分析摘要
    """
    try:
        modeling_service = ProfileModelingService(db)
        
        # 验证用户是否有权限访问此功能
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="您没有权限更新其他用户的画像分析"
            )
        
        # 执行画像更新
        result = await modeling_service.update_user_profile_analysis(
            user_id, 
            include_recent_chats=include_recent_chats,
            include_new_cards=include_new_cards
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"用户画像更新失败: {result.get('error', '未知错误')}"
            )
        
        logger.info(f"用户 {user_id} 画像更新完成，置信度: {result['confidence_score']}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新用户 {user_id} 画像时发生错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"用户画像更新过程中发生错误: {str(e)}"
        )


@router.post("/scheduler/start", response_model=Dict[str, Any])
async def start_profile_modeling_scheduler(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    启动用户画像离线建模调度器
    
    - **db**: 数据库会话
    - **current_user**: 当前登录用户（需要管理员权限）
    
    返回:
    - success: 是否成功
    - message: 状态消息
    - scheduler_status: 调度器状态
    """
    try:
        # 验证管理员权限
        if not current_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="只有管理员才能启动调度器"
            )
        
        scheduler = ProfileModelingScheduler(db)
        scheduler.start()
        
        status = scheduler.get_task_status()
        
        logger.info(f"用户画像离线建模调度器已启动，用户: {current_user.id}")
        
        return {
            "success": True,
            "message": "用户画像离线建模调度器已成功启动",
            "scheduler_status": status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动调度器时发生错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"启动调度器失败: {str(e)}"
        )


@router.post("/scheduler/stop", response_model=Dict[str, Any])
async def stop_profile_modeling_scheduler(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    停止用户画像离线建模调度器
    
    - **db**: 数据库会话
    - **current_user**: 当前登录用户（需要管理员权限）
    
    返回:
    - success: 是否成功
    - message: 状态消息
    """
    try:
        # 验证管理员权限
        if not current_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="只有管理员才能停止调度器"
            )
        
        scheduler = ProfileModelingScheduler(db)
        scheduler.stop()
        
        logger.info(f"用户画像离线建模调度器已停止，用户: {current_user.id}")
        
        return {
            "success": True,
            "message": "用户画像离线建模调度器已成功停止"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止调度器时发生错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"停止调度器失败: {str(e)}"
        )


@router.get("/scheduler/status", response_model=Dict[str, Any])
async def get_scheduler_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取调度器状态
    
    - **db**: 数据库会话
    - **current_user**: 当前登录用户（需要管理员权限）
    
    返回:
    - scheduler_running: 调度器是否运行中
    - jobs: 任务列表
    - task_configs: 任务配置
    """
    try:
        # 验证管理员权限
        if not current_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="只有管理员才能查看调度器状态"
            )
        
        scheduler = ProfileModelingScheduler(db)
        status = scheduler.get_task_status()
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取调度器状态时发生错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取调度器状态失败: {str(e)}"
        )


@router.put("/scheduler/config/{task_name}", response_model=Dict[str, Any])
async def update_task_config(
    task_name: str,
    config: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新任务配置
    
    - **task_name**: 任务名称 (authenticity_verification, content_compliance, profile_update)
    - **config**: 配置参数
    - **db**: 数据库会话
    - **current_user**: 当前登录用户（需要管理员权限）
    
    返回:
    - success: 是否成功
    - message: 状态消息
    - updated_config: 更新后的配置
    """
    try:
        # 验证管理员权限
        if not current_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="只有管理员才能更新任务配置"
            )
        
        # 验证任务名称
        valid_tasks = ["authenticity_verification", "content_compliance", "profile_update"]
        if task_name not in valid_tasks:
            raise HTTPException(
                status_code=400,
                detail=f"无效的任务名称。有效名称: {', '.join(valid_tasks)}"
            )
        
        scheduler = ProfileModelingScheduler(db)
        scheduler.update_task_config(task_name, config)
        
        logger.info(f"任务 {task_name} 配置已更新，用户: {current_user.id}")
        
        return {
            "success": True,
            "message": f"任务 {task_name} 配置已成功更新",
            "updated_config": scheduler.task_configs[task_name]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新任务配置时发生错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"更新任务配置失败: {str(e)}"
        )


@router.get("/verification-history/{user_id}", response_model=Dict[str, Any])
async def get_verification_history(
    user_id: int,
    limit: int = Query(20, ge=1, le=100, description="返回记录数量限制"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取用户验证历史记录
    
    - **user_id**: 用户ID
    - **limit**: 返回记录数量限制
    - **db**: 数据库会话
    - **current_user**: 当前登录用户
    
    返回:
    - user_id: 用户ID
    - history: 验证历史记录列表
    - total_count: 总记录数
    """
    try:
        # 验证用户权限
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=403,
                detail="您没有权限查看其他用户的验证历史"
            )
        
        # 这里应该从数据库查询验证历史记录
        # 由于目前还没有验证历史表，这里返回模拟数据
        mock_history = [
            {
                "id": 1,
                "user_id": user_id,
                "verification_type": "authenticity",
                "score": 85,
                "status": "passed",
                "created_at": "2024-01-15T10:30:00Z",
                "details": {
                    "analysis_result": "用户人设真实度较高",
                    "key_factors": ["头像真实", "简介详细", "行为模式正常"]
                }
            },
            {
                "id": 2,
                "user_id": user_id,
                "verification_type": "compliance",
                "score": 92,
                "status": "approved",
                "created_at": "2024-01-14T15:45:00Z",
                "details": {
                    "violations": [],
                    "suggestions": ["内容质量良好"]
                }
            }
        ]
        
        return {
            "user_id": user_id,
            "history": mock_history[:limit],
            "total_count": len(mock_history)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取用户 {user_id} 验证历史时发生错误: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取验证历史失败: {str(e)}"
        )