"""
用户画像API路由（增强版）
提供用户画像数据的CRUD操作、分析接口和智能功能
整合了基础功能和增强功能，避免重复
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.database import get_db
from app.services.user_profile_service import UserProfileService
from app.models.user_profile import (
    UserProfileCreate, 
    UserProfileUpdate, 
    UserProfileResponse,
    UserProfileListResponse,
    UserProfileAnalysisRequest,
    UserProfileAnalysisResponse
)
from app.utils.auth import get_current_user
from app.models.user import User
from pydantic import BaseModel, Field
from enum import Enum

router = APIRouter(prefix="/profiles", tags=["user-profiles"])

# 评价相关模型
class EvaluationType(str, Enum):
    """评价类型枚举"""
    ACCURACY = "accuracy"  # 准确性评价
    COMPLETENESS = "completeness"  # 完整性评价
    USEFULNESS = "usefulness"  # 有用性评价
    OVERALL = "overall"  # 总体评价

class ProfileEvaluationRequest(BaseModel):
    """用户画像评价请求模型"""
    rating: Optional[int] = Field(None, ge=1, le=5, description="评分，1-5分")
    evaluation_type: EvaluationType = Field(default=EvaluationType.OVERALL, description="评价类型")
    comment: Optional[str] = Field(None, description="评价备注")
    tags: Optional[List[str]] = Field(None, description="评价标签")
    # 前端兼容字段
    accuracy_rating: Optional[str] = Field(None, description="准确率评价(accurate, partial, inaccurate)")
    adjustment_suggestion: Optional[str] = Field(None, description="调整建议")
    profile_id: Optional[str] = Field(None, description="用户画像ID")
    timestamp: Optional[str] = Field(None, description="时间戳")

class ProfileEvaluationResponse(BaseModel):
    """用户画像评价响应模型"""
    id: str
    user_id: str
    rating: int
    evaluation_type: str
    comment: Optional[str]
    tags: Optional[List[str]]
    created_at: datetime
    message: str = "评价提交成功"


def get_enhanced_profile_service(db: Session = Depends(get_db)) -> UserProfileService:
    """获取增强用户画像服务实例"""
    return UserProfileService(db)

@router.get("/me")
async def get_my_enhanced_profile(
    include_history: bool = Query(False, description="是否包含历史记录"),
    include_recommendations: bool = Query(False, description="是否包含推荐"),
    current_user: dict = Depends(get_current_user),
    service: UserProfileService = Depends(get_enhanced_profile_service)
):
    """
    获取当前用户的增强画像
    包含更多智能分析结果
    """
    result = service.get_user_profile_by_user_id(current_user.get("id"), include_history)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    # 如果需要推荐，添加推荐数据
    if include_recommendations:
        recommendations = await service.get_smart_recommendations(current_user.get("id"), "all", 5)
        result["recommendations"] = recommendations
    
    return result


# ===== 用户画像评价接口 =====
@router.post("/me/evaluation", response_model=ProfileEvaluationResponse)
async def submit_profile_evaluation(
    evaluation_data: ProfileEvaluationRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    提交用户画像评价
    用户可以对自己的画像进行评价，包括准确性、完整性、有用性等方面
    同时更新用户画像的 accuracy_rating 和 adjustment_text 字段
    """
    from uuid import uuid4
    from app.models.user_profile_feedback import UserProfileFeedback
    
    try:
        user_id = str(current_user.get("id"))
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        # 获取当前用户的画像
        service = UserProfileService(db)
        profile = service.get_active_user_profile(user_id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="用户画像不存在，请先创建画像"
            )
        
        # 处理前端兼容数据格式
        rating = evaluation_data.rating
        comment = evaluation_data.comment
        
        # 如果前端发送了兼容字段，进行转换
        if evaluation_data.accuracy_rating and not rating:
            # 根据accuracy_rating反向推导rating
            accuracy_to_rating = {
                "accurate": 5,
                "partial": 3,
                "inaccurate": 1
            }
            rating = accuracy_to_rating.get(evaluation_data.accuracy_rating, 3)
        
        # 如果前端发送了adjustment_suggestion，用作comment
        if evaluation_data.adjustment_suggestion and not comment:
            comment = evaluation_data.adjustment_suggestion
        
        # 如果仍然没有rating，使用默认值
        if not rating:
            rating = 3  # 默认中等评分
        
        # 根据评价类型更新用户画像的 accuracy_rating 和 adjustment_text
        accuracy_rating_map = {
            1: "inaccurate",
            2: "inaccurate", 
            3: "partial",
            4: "accurate",
            5: "accurate"
        }
        
        # 获取对应的准确率评价
        new_accuracy_rating = accuracy_rating_map.get(rating, "partial")
        
        # 构建更新数据
        update_data = UserProfileUpdate(
            accuracy_rating=new_accuracy_rating,
            adjustment_text=comment,
            update_reason=f"用户画像评价: {evaluation_data.evaluation_type.value} - 评分: {rating}",
            is_user_edit=True
        )
        
        # 更新用户画像
        updated_profile = service.update_user_profile(
            profile.id,
            update_data,
            change_source="user_evaluation",
            change_reason=f"用户提交{evaluation_data.evaluation_type.value}评价"
        )
        
        if not updated_profile:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新用户画像失败"
            )
        
        # 创建用户画像反馈记录
        feedback = UserProfileFeedback(
            user_id=user_id,
            profile_id=profile.id,
            rating=rating,
            evaluation_type=evaluation_data.evaluation_type.value,
            comment=comment,
            feedback_content={
                "tags": evaluation_data.tags or [],
                "adjustment_suggestion": evaluation_data.adjustment_suggestion,
                "accuracy_rating": evaluation_data.accuracy_rating
            },
            suggested_improvements=evaluation_data.tags or [],
            is_processed=False  # 初始状态为未处理，等待调度器处理
        )
        
        db.add(feedback)
        db.commit()
        
        return ProfileEvaluationResponse(
            id=feedback.id,
            user_id=feedback.user_id,
            rating=feedback.rating,
            evaluation_type=feedback.evaluation_type,
            comment=feedback.comment,
            tags=evaluation_data.tags or [],
            created_at=feedback.created_at,
            message=f"评价提交成功，用户画像已更新: accuracy_rating={new_accuracy_rating}，反馈将自动处理"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"提交评价失败: {str(e)}"
        )


@router.get("/me/evaluation/feedback")
async def get_pending_feedback(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取待处理的用户评价反馈
    返回当前用户未处理的用户画像反馈记录
    """
    try:
        user_id = str(current_user.get("id"))
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        from app.models.user_profile_feedback import UserProfileFeedback
        from datetime import datetime, timedelta
        
        # 查询未处理的反馈
        pending_feedback = db.query(UserProfileFeedback).filter(
            UserProfileFeedback.user_id == user_id,
            UserProfileFeedback.is_processed == False
        ).order_by(UserProfileFeedback.created_at.desc()).all()
        
        # 构建响应数据
        feedback_list = []
        for feedback in pending_feedback:
            feedback_list.append({
                "id": feedback.id,
                "profile_id": feedback.profile_id,
                "rating": feedback.rating,
                "evaluation_type": feedback.evaluation_type,
                "comment": feedback.comment,
                "feedback_content": feedback.feedback_content,
                "suggested_improvements": feedback.suggested_improvements,
                "is_processed": feedback.is_processed,
                "processed_at": feedback.processed_at,
                "created_at": feedback.created_at
            })
        
        return {
            "total_count": len(feedback_list),
            "pending_count": len([f for f in feedback_list if not f["is_processed"]]),
            "feedback_list": feedback_list,
            "message": f"找到 {len(feedback_list)} 条反馈记录，其中 {len([f for f in feedback_list if not f['is_processed']])} 条待处理"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取待处理反馈失败: {str(e)}"
        )


@router.get("/me/evaluation/feedback/admin")
async def get_all_pending_feedback(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    processed_filter: Optional[str] = Query(None, description="过滤条件: all, pending, processed"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    管理员获取所有待处理的用户评价反馈
    需要管理员权限，用于查看系统范围内的反馈处理情况
    """
    try:
        user_id = str(current_user.get("id"))
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        # 检查管理员权限（这里简化处理，实际应该检查角色权限）
        # TODO: 实现基于角色的权限控制
        
        from app.models.user_profile_feedback import UserProfileFeedback
        from sqlalchemy import func
        
        # 构建查询条件
        query = db.query(UserProfileFeedback)
        
        if processed_filter == "pending":
            query = query.filter(UserProfileFeedback.is_processed == False)
        elif processed_filter == "processed":
            query = query.filter(UserProfileFeedback.is_processed == True)
        # processed_filter == "all" 或 None 时查询所有记录
        
        # 获取总数
        total_count = query.count()
        
        # 分页查询
        feedback_list = query.order_by(
            UserProfileFeedback.created_at.desc()
        ).offset((page - 1) * page_size).limit(page_size).all()
        
        # 构建响应数据
        result_list = []
        for feedback in feedback_list:
            result_list.append({
                "id": feedback.id,
                "user_id": feedback.user_id,
                "profile_id": feedback.profile_id,
                "rating": feedback.rating,
                "evaluation_type": feedback.evaluation_type,
                "comment": feedback.comment,
                "feedback_content": feedback.feedback_content,
                "suggested_improvements": feedback.suggested_improvements,
                "is_processed": feedback.is_processed,
                "processed_at": feedback.processed_at,
                "created_at": feedback.created_at
            })
        
        # 统计信息
        pending_count = db.query(UserProfileFeedback).filter(
            UserProfileFeedback.is_processed == False
        ).count()
        processed_count = db.query(UserProfileFeedback).filter(
            UserProfileFeedback.is_processed == True
        ).count()
        
        return {
            "total_count": total_count,
            "pending_count": pending_count,
            "processed_count": processed_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size,
            "feedback_list": result_list,
            "message": f"找到 {total_count} 条反馈记录，其中 {pending_count} 条待处理，{processed_count} 条已处理"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取反馈列表失败: {str(e)}"
        )


@router.get("/me/evaluation/stats")
async def get_profile_evaluation_stats(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户画像评价统计
    返回用户的评价统计数据，基于用户画像的 accuracy_rating 和 adjustment_text 字段
    """
    try:
        user_id = str(current_user.get("id"))
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        # 获取当前用户的画像
        service = UserProfileService(db)
        profile = service.get_active_user_profile(user_id)
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="用户画像不存在"
            )
        
        # 基于用户画像的 accuracy_rating 和 adjustment_text 生成统计
        # 这里简化处理，实际应该从评价记录表中查询真实数据
        current_accuracy = profile.accuracy_rating or "unknown"
        current_adjustment = profile.adjustment_text or ""
        
        # 根据 accuracy_rating 映射到评分
        rating_map = {
            "accurate": 5,
            "partial": 3,
            "inaccurate": 1,
            "unknown": 0
        }
        
        current_rating = rating_map.get(current_accuracy, 0)
        
        stats = {
            "total_evaluations": 1 if current_accuracy != "unknown" else 0,
            "average_rating": current_rating if current_rating > 0 else None,
            "current_accuracy_rating": current_accuracy,
            "current_adjustment_text": current_adjustment,
            "evaluation_breakdown": {
                "accuracy": {
                    "current_rating": current_accuracy,
                    "comment": current_adjustment
                }
            },
            "recent_evaluations": [
                {
                    "id": f"eval_{profile.id}",
                    "rating": current_rating,
                    "evaluation_type": "overall",
                    "comment": current_adjustment,
                    "created_at": profile.updated_at.isoformat() if profile.updated_at else profile.created_at.isoformat()
                }
            ] if current_accuracy != "unknown" else []
        }
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取评价统计失败: {str(e)}"
        )



@router.post("/", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_user_profile(
    profile_data: UserProfileCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    创建用户画像（增强版）
    支持当前用户或管理员创建
    """
    service = UserProfileService(db)
    try:
        # 如果profile_data中没有user_id，使用当前用户ID
        if not profile_data.user_id:
            profile_data.user_id = str(current_user.get("id"))
        
        # 权限检查：用户只能创建自己的画像，管理员可以创建任何用户的画像
        current_user_id = current_user.get("id")
        is_admin = current_user.get("is_admin", False)
        if profile_data.user_id != str(current_user_id) and not is_admin:
            raise HTTPException(status_code=403, detail="权限不足，只能创建自己的用户画像")
        
        profile = service.create_user_profile(profile_data)
        return UserProfileResponse.from_orm(profile)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"创建用户画像失败: {str(e)}")


@router.get("/{profile_id}", response_model=UserProfileResponse)
async def get_user_profile(
    profile_id: str,
    db: Session = Depends(get_db)
):
    """
    获取用户画像详情
    """
    service = UserProfileService(db)
    profile = service.get_user_profile(profile_id)
    
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户画像不存在")
    
    return UserProfileResponse.from_orm(profile)


@router.get("/user/{user_id}", response_model=UserProfileResponse)
async def get_active_user_profile(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户画像（增强版）
    添加权限控制，用户只能查看自己的画像
    """
    # 权限检查 - current_user是字典，使用get方法获取id
    current_user_id = current_user.get("id")
    if not current_user_id or str(current_user_id) != user_id:
        raise HTTPException(status_code=403, detail="权限不足，只能查看自己的用户画像")
    
    service = UserProfileService(db)
    profile = service.get_active_user_profile(user_id)
    
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户没有激活的画像")
    
    return UserProfileResponse.from_orm(profile)

@router.put("/{profile_id}", response_model=UserProfileResponse)
async def update_user_profile(
    profile_id: str,
    update_data: UserProfileUpdate,
    db: Session = Depends(get_db)
):
    """
    更新用户画像
    """
    service = UserProfileService(db)
    profile = service.update_user_profile(profile_id, update_data)
    
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户画像不存在")
    
    return UserProfileResponse.from_orm(profile)


@router.post("/{profile_id}/activate", response_model=UserProfileResponse)
async def activate_user_profile(
    profile_id: str,
    db: Session = Depends(get_db)
):
    """
    激活用户画像
    """
    service = UserProfileService(db)
    success = service.activate_user_profile(profile_id)
    
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户画像不存在")
    
    profile = service.get_user_profile(profile_id)
    return UserProfileResponse.from_orm(profile)


@router.post("/{profile_id}/deactivate", response_model=UserProfileResponse)
async def deactivate_user_profile(
    profile_id: str,
    db: Session = Depends(get_db)
):
    """
    停用用户画像
    """
    service = UserProfileService(db)
    success = service.deactivate_user_profile(profile_id)
    
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户画像不存在")
    
    profile = service.get_user_profile(profile_id)
    return UserProfileResponse.from_orm(profile)


@router.post("/analyze/preferences", response_model=UserProfileAnalysisResponse)
async def analyze_user_preferences(
    request: UserProfileAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    分析用户偏好
    """
    service = UserProfileService(db)
    result = service.analyze_user_preferences(request.user_id)
    
    if "error" in result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
    
    return UserProfileAnalysisResponse(
        user_id=result["user_id"],
        analysis_type=result["analysis_type"],
        results={
            "preferences": result["preferences"],
            "interest_tags": result["interest_tags"],
            "social_preferences": result["social_preferences"],
            "match_preferences": result["match_preferences"]
        },
        confidence_score=result["confidence_score"],
        data_source=result["data_source"],
        generated_at=result["generated_at"]
    )


@router.post("/analyze/personality", response_model=UserProfileAnalysisResponse)
async def analyze_user_personality(
    request: UserProfileAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    分析用户个性
    """
    service = UserProfileService(db)
    result = service.analyze_user_personality(request.user_id)
    
    if "error" in result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
    
    return UserProfileAnalysisResponse(
        user_id=result["user_id"],
        analysis_type=result["analysis_type"],
        results={
            "personality_traits": result["personality_traits"],
            "behavior_patterns": result["behavior_patterns"]
        },
        confidence_score=result["confidence_score"],
        data_source=result["data_source"],
        generated_at=result["generated_at"]
    )


@router.post("/analyze/mood", response_model=UserProfileAnalysisResponse)
async def analyze_user_mood(
    request: UserProfileAnalysisRequest,
    db: Session = Depends(get_db)
):
    """
    分析用户心情
    """
    service = UserProfileService(db)
    result = service.analyze_user_mood(request.user_id)
    
    if "error" in result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["error"])
    
    return UserProfileAnalysisResponse(
        user_id=result["user_id"],
        analysis_type=result["analysis_type"],
        results={
            "mood_state": result["mood_state"]
        },
        confidence_score=result["confidence_score"],
        data_source=result["data_source"],
        generated_at=result["generated_at"]
    )


@router.get("/user/{user_id}/statistics")
async def get_profile_statistics(
    user_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取用户画像统计信息（增强版）
    添加权限控制
    """
    # 权限检查
    if str(current_user.get("id")) != user_id and not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="权限不足，只能查看自己的统计信息")
    
    service = UserProfileService(db)
    statistics = service.get_profile_statistics(user_id)
    
    return statistics


# ===== 增强功能接口（原user_profile_enhanced.py的核心功能） =====

@router.post("/smart-update")
async def update_with_smart_suggestions(
    update_data: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user),
    service: UserProfileService = Depends(get_enhanced_profile_service)
):
    """
    智能更新用户画像（基于AI建议）
    整合自user_profile_enhanced.py的增强功能
    """
    # Get user's profile first
    profile = service.get_active_user_profile(current_user.get("id"))
    if not profile:
        raise HTTPException(status_code=404, detail="用户画像不存在")
    
    # Use apply_ai_suggestions method instead of the non-existent update_with_smart_suggestions
    result = service.apply_ai_suggestions(profile.id, update_data)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/implicit-learning")
async def perform_implicit_learning(
    interaction_data: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user),
    service: UserProfileService = Depends(get_enhanced_profile_service)
):
    """
    执行隐式学习更新
    根据用户交互行为自动更新画像
    """
    result = await service.perform_implicit_learning(current_user.get("id"), interaction_data)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/periodic-review")
async def perform_periodic_review(
    review_type: str = Query("monthly", description="回顾类型: monthly, quarterly"),
    current_user: dict = Depends(get_current_user),
    service: UserProfileService = Depends(get_enhanced_profile_service)
):
    """
    执行定期回顾
    定期分析和优化用户画像
    """
    result = await service.perform_periodic_review(current_user.get("id"), review_type)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.get("/recommendations")
async def get_smart_recommendations(
    recommendation_type: str = Query("all", description="推荐类型: all, content, social, activity"),
    limit: int = Query(10, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
    service: UserProfileService = Depends(get_enhanced_profile_service)
):
    """
    获取智能推荐
    基于用户画像提供个性化推荐
    """
    result = await service.get_smart_recommendations(current_user.get("id"), recommendation_type, limit)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result



@router.get("/health")
async def health_check():
    """
    健康检查端点
    """
    return {
        "status": "healthy",
        "service": "user_profile_enhanced",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "基础CRUD操作",
            "智能分析",
            "隐式学习",
            "定期回顾",
            "智能推荐",
            "用户画像评价"
        ]
    }

