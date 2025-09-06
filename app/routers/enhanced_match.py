"""
增强的匹配路由
提供智能匹配推荐和撮合功能的API接口
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from app.models.schemas import BaseResponse
from app.utils.auth import get_current_user
from app.models.user import User
from app.services.enhanced_match_service import EnhancedMatchService
from app.services.match_scheduler import match_scheduler, recommendation_cache
from app.database import get_db

router = APIRouter()

# 请求模型
class RecommendationRequest(BaseModel):
    matchType: str
    maxRecommendations: Optional[int] = 10
    refreshCache: Optional[bool] = False

class BatchGenerationRequest(BaseModel):
    matchType: str
    batchSize: Optional[int] = 100

class SchedulerTaskRequest(BaseModel):
    taskName: str  # daily_generation, hourly_cleanup, statistics_update


@router.get("/recommendations")
async def get_match_recommendations(
    matchType: str = Query(..., description="匹配类型"),
    maxRecommendations: int = Query(10, description="最大推荐数量"),
    refreshCache: bool = Query(False, description="是否刷新缓存"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取智能匹配推荐列表
    
    根据用户资料和偏好，返回兼容性最高的匹配推荐
    """
    try:
        # 获取当前用户ID
        if isinstance(current_user, dict):
            user_id = str(current_user.get('id', ''))
        else:
            user_id = str(current_user.id)
        
        # 检查缓存
        if not refreshCache:
            cached_recommendations = recommendation_cache.get_user_recommendations(user_id, matchType)
            if cached_recommendations:
                return BaseResponse(
                    code=0,
                    message="success",
                    data={
                        "recommendations": cached_recommendations[:maxRecommendations],
                        "total": len(cached_recommendations),
                        "fromCache": True,
                        "matchType": matchType
                    }
                )
        
        # 生成新的推荐
        match_service = EnhancedMatchService(db)
        recommendations = match_service.generate_daily_match_recommendations(
            user_id=user_id,
            match_type=matchType,
            max_recommendations=maxRecommendations
        )
        
        # 缓存推荐结果
        if recommendations:
            recommendation_cache.set_user_recommendations(
                user_id, matchType, recommendations, expire_hours=24
            )
        
        return BaseResponse(
            code=0,
            message="success",
            data={
                "recommendations": recommendations,
                "total": len(recommendations),
                "fromCache": False,
                "matchType": matchType,
                "generatedAt": match_service.db.execute("SELECT datetime('now')").scalar()
            }
        )
        
    except Exception as e:
        print(f"获取匹配推荐异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return BaseResponse(
            code=500,
            message=f"获取匹配推荐失败: {str(e)}",
            data=None
        )


@router.get("/statistics")
async def get_match_statistics(
    matchType: Optional[str] = Query(None, description="匹配类型筛选"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户匹配统计信息
    
    包括匹配率、活跃度、操作历史等统计数据
    """
    try:
        # 获取当前用户ID
        if isinstance(current_user, dict):
            user_id = str(current_user.get('id', ''))
        else:
            user_id = str(current_user.id)
        
        match_service = EnhancedMatchService(db)
        statistics = match_service.get_match_statistics(user_id, matchType)
        
        return BaseResponse(
            code=0,
            message="success",
            data=statistics
        )
        
    except Exception as e:
        print(f"获取匹配统计异常: {str(e)}")
        return BaseResponse(
            code=500,
            message=f"获取匹配统计失败: {str(e)}",
            data=None
        )


@router.post("/batch-generate")
async def batch_generate_recommendations(
    request: BatchGenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    批量生成匹配推荐（管理员功能）
    
    用于离线生成大量用户的匹配推荐
    """
    try:
        match_service = EnhancedMatchService(db)
        
        # 在后台任务中执行批量生成
        def run_batch_generation():
            result = match_service.batch_generate_recommendations(
                match_type=request.matchType,
                batch_size=request.batchSize
            )
            print(f"批量生成完成: {result}")
        
        background_tasks.add_task(run_batch_generation)
        
        return BaseResponse(
            code=0,
            message="批量生成任务已启动",
            data={
                "matchType": request.matchType,
                "batchSize": request.batchSize,
                "status": "started"
            }
        )
        
    except Exception as e:
        print(f"批量生成推荐异常: {str(e)}")
        return BaseResponse(
            code=500,
            message=f"批量生成推荐失败: {str(e)}",
            data=None
        )


@router.get("/scheduler/status")
async def get_scheduler_status():
    """
    获取匹配任务调度器状态
    
    返回调度器运行状态和最近执行时间
    """
    try:
        status = match_scheduler.get_scheduler_status()
        return BaseResponse(
            code=0,
            message="success",
            data=status
        )
        
    except Exception as e:
        return BaseResponse(
            code=500,
            message=f"获取调度器状态失败: {str(e)}",
            data=None
        )


@router.post("/scheduler/trigger")
async def trigger_scheduler_task(
    request: SchedulerTaskRequest,
    background_tasks: BackgroundTasks
):
    """
    手动触发调度器任务（管理员功能）
    
    支持手动执行匹配推荐生成、数据清理等任务
    """
    try:
        # 在后台任务中执行
        def run_task():
            result = match_scheduler.manual_trigger_task(request.taskName)
            print(f"手动任务执行结果: {result}")
        
        background_tasks.add_task(run_task)
        
        return BaseResponse(
            code=0,
            message=f"任务 {request.taskName} 已触发",
            data={
                "taskName": request.taskName,
                "status": "triggered"
            }
        )
        
    except Exception as e:
        return BaseResponse(
            code=500,
            message=f"触发任务失败: {str(e)}",
            data=None
        )


@router.delete("/cache")
async def clear_recommendation_cache(
    matchType: Optional[str] = Query(None, description="匹配类型"),
    current_user: User = Depends(get_current_user)
):
    """
    清除用户匹配推荐缓存
    
    用户可以主动清除缓存以获取最新推荐
    """
    try:
        # 获取当前用户ID
        if isinstance(current_user, dict):
            user_id = str(current_user.get('id', ''))
        else:
            user_id = str(current_user.id)
        
        recommendation_cache.clear_user_recommendations(user_id, matchType)
        
        return BaseResponse(
            code=0,
            message="缓存已清除",
            data={
                "userId": user_id,
                "matchType": matchType or "all"
            }
        )
        
    except Exception as e:
        return BaseResponse(
            code=500,
            message=f"清除缓存失败: {str(e)}",
            data=None
        )


@router.get("/compatibility/{target_user_id}")
async def calculate_compatibility(
    target_user_id: str,
    matchType: str = Query(..., description="匹配类型"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    计算与指定用户的兼容性分数
    
    返回详细的兼容性分析和匹配原因
    """
    try:
        # 获取当前用户ID
        if isinstance(current_user, dict):
            user_id = str(current_user.get('id', ''))
        else:
            user_id = str(current_user.id)
        
        match_service = EnhancedMatchService(db)
        
        # 获取两个用户的资料
        current_user_card = match_service._get_user_card_data(user_id, matchType)
        target_user_card = match_service._get_user_card_data(target_user_id, matchType)
        
        if not current_user_card or not target_user_card:
            return BaseResponse(
                code=404,
                message="用户资料不存在",
                data=None
            )
        
        # 计算兼容性分数
        compatibility_score = match_service.compatibility_calculator.calculate_compatibility_score(
            current_user_card, target_user_card, matchType
        )
        
        # 生成匹配原因
        match_reasons = match_service._generate_match_reasons(
            current_user_card, target_user_card, matchType
        )
        
        return BaseResponse(
            code=0,
            message="success",
            data={
                "targetUserId": target_user_id,
                "matchType": matchType,
                "compatibilityScore": compatibility_score,
                "matchReasons": match_reasons,
                "compatibilityLevel": match_service._get_compatibility_level(compatibility_score)
            }
        )
        
    except Exception as e:
        print(f"计算兼容性异常: {str(e)}")
        return BaseResponse(
            code=500,
            message=f"计算兼容性失败: {str(e)}",
            data=None
        )


# 辅助方法扩展
def _get_compatibility_level(score: float) -> str:
    """根据分数获取兼容性等级"""
    if score >= 80:
        return "非常匹配"
    elif score >= 60:
        return "较为匹配"
    elif score >= 40:
        return "一般匹配"
    else:
        return "匹配度较低"

# 将方法添加到EnhancedMatchService类中
EnhancedMatchService._get_compatibility_level = _get_compatibility_level