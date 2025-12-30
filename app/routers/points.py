from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import get_db
from app.services.points_service import PointsService
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/points", tags=["积分管理"])


def get_points_service(db: Session = Depends(get_db)) -> PointsService:
    """获取积分服务实例"""
    return PointsService(db)


@router.get("/info", summary="获取用户积分信息")
async def get_user_points_info(
    current_user: User = Depends(get_current_user),
    points_service: PointsService = Depends(get_points_service)
) -> Dict[str, Any]:
    """获取当前用户的积分和等级信息"""
    try:
        return points_service.get_user_points_info(current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取积分信息失败: {str(e)}")


@router.post("/reward/survey", summary="奖励问卷完成")
async def reward_survey_completion(
    current_user: User = Depends(get_current_user),
    points_service: PointsService = Depends(get_points_service)
) -> Dict[str, Any]:
    """用户完成问卷后获得积分奖励"""
    try:
        result = points_service.reward_survey_completion(current_user.id)
        if result['success']:
            return {
                "success": True,
                "message": f"恭喜获得 {result['points_added']} 积分奖励！",
                "data": result
            }
        else:
            return {
                "success": False,
                "message": "奖励发放失败",
                "data": result
            }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"奖励发放失败: {str(e)}")


@router.post("/reward/vote", summary="奖励投票参与")
async def reward_vote_participation(
    current_user: User = Depends(get_current_user),
    points_service: PointsService = Depends(get_points_service)
) -> Dict[str, Any]:
    """用户参与投票后获得积分奖励"""
    try:
        result = points_service.reward_vote_participation(current_user.id)
        if result['success']:
            return {
                "success": True,
                "message": f"恭喜获得 {result['points_added']} 积分投票奖励！",
                "data": result
            }
        else:
            return {
                "success": False,
                "message": "奖励发放失败",
                "data": result
            }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"投票奖励发放失败: {str(e)}")


@router.post("/reward/discussion", summary="奖励讨论参与")
async def reward_discussion_participation(
    current_user: User = Depends(get_current_user),
    points_service: PointsService = Depends(get_points_service)
) -> Dict[str, Any]:
    """用户参与讨论后获得积分奖励"""
    try:
        result = points_service.reward_discussion_participation(current_user.id)
        if result['success']:
            return {
                "success": True,
                "message": f"恭喜获得 {result['points_added']} 积分讨论奖励！",
                "data": result
            }
        else:
            return {
                "success": False,
                "message": "奖励发放失败",
                "data": result
            }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"讨论奖励发放失败: {str(e)}")


@router.post("/consume/create-card/{card_type}", summary="消耗积分创建卡片")
async def consume_points_for_card(
    card_type: str,
    current_user: User = Depends(get_current_user),
    points_service: PointsService = Depends(get_points_service)
) -> Dict[str, Any]:
    """消耗积分创建不同类型的卡片"""
    try:
        result = points_service.consume_create_card(current_user.id, card_type)
        if result['success']:
            return {
                "success": True,
                "message": f"成功消耗 {result['points_consumed']} 积分创建{result['reason'].split('创建')[-1]}！",
                "data": result
            }
        else:
            return {
                "success": False,
                "message": f"积分不足，当前积分：{result['current_points']}，需要积分：{result['required_points']}",
                "data": result
            }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"积分消耗失败: {str(e)}")


@router.get("/check/create-card/{card_type}", summary="检查创建卡片权限")
async def check_create_card_permission(
    card_type: str,
    current_user: User = Depends(get_current_user),
    points_service: PointsService = Depends(get_points_service)
) -> Dict[str, Any]:
    """检查用户是否有足够积分创建指定类型的卡片"""
    try:
        result = points_service.check_create_card_permission(current_user.id, card_type)
        return {
            "success": True,
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"检查权限失败: {str(e)}")


@router.post("/add", summary="增加积分（管理员用）")
async def add_points(
    user_id: str,
    points: int,
    reason: str = "",
    current_user: User = Depends(get_current_user),
    points_service: PointsService = Depends(get_points_service)
) -> Dict[str, Any]:
    """管理员给用户增加积分"""
    # 这里应该添加管理员权限检查
    # if not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="无权限操作")
    
    try:
        result = points_service.add_points(user_id, points, reason)
        return {
            "success": True,
            "message": f"成功给用户增加 {points} 积分",
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"增加积分失败: {str(e)}")


@router.post("/consume", summary="消耗积分（管理员用）")
async def consume_points(
    user_id: str,
    points: int,
    reason: str = "",
    current_user: User = Depends(get_current_user),
    points_service: PointsService = Depends(get_points_service)
) -> Dict[str, Any]:
    """管理员扣除用户积分"""
    # 这里应该添加管理员权限检查
    # if not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="无权限操作")
    
    try:
        result = points_service.consume_points(user_id, points, reason)
        if result['success']:
            return {
                "success": True,
                "message": f"成功扣除用户 {points} 积分",
                "data": result
            }
        else:
            return {
                "success": False,
                "message": f"用户积分不足，当前积分：{result['current_points']}，需要扣除：{result['required_points']}",
                "data": result
            }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"扣除积分失败: {str(e)}")