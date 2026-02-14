"""
用户画像评分API路由
提供用户画像评分相关的接口，包括评分查询、更新、历史记录等功能
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.database import get_db
from app.services.user_profile.user_profile_score_service import UserProfileScoreService
from app.models.user_profile_score import (
    UserProfileScore,
    UserProfileSkill,
    ScoreCalculationRequest as ScoreRequest,
    ScoreCalculationResponse as ScoreResponse,
    UserProfileSkillResponse as SkillResponse,
    UserProfileScoreHistoryResponse,
    UserProfileScoreUpdate as UserProfileScoreUpdateRequest
)
from app.utils.auth import get_current_user
from pydantic import BaseModel, Field
from enum import Enum

router = APIRouter(prefix="/profiles/scores", tags=["user-profile-scores"])


class ScoreType(str, Enum):
    """评分类型枚举"""
    ACCURACY = "accuracy"  # 准确性评分
    COMPLETENESS = "completeness"  # 完整性评分
    ACTIVITY = "activity"  # 活跃度评分
    ENGAGEMENT = "engagement"  # 互动度评分
    OVERALL = "overall"  # 综合评分


class SkillUnlockRequest(BaseModel):
    """技能解锁请求模型"""
    skill_id: str = Field(..., description="技能ID")
    score_threshold: Optional[int] = Field(None, description="解锁所需的评分阈值")


class UserProfileScoreSummary(BaseModel):
    """用户画像评分摘要响应模型"""
    user_id: str
    overall_score: float
    accuracy_score: float
    completeness_score: float
    activity_score: float
    engagement_score: float
    total_experience: int
    level: int
    unlocked_skills: List[str]
    next_level_progress: float
    last_updated: datetime
    message: str = "评分查询成功"


def get_score_service(db: Session = Depends(get_db)) -> UserProfileScoreService:
    """获取用户画像评分服务实例"""
    return UserProfileScoreService(db)


@router.get("/me", response_model=UserProfileScoreSummary)
async def get_my_profile_score(
    include_skills: bool = Query(True, description="是否包含已解锁技能"),
    current_user: dict = Depends(get_current_user),
    service: UserProfileScoreService = Depends(get_score_service)
):
    """
    获取当前用户的画像评分
    返回用户的综合评分、各维度评分、经验值、等级和已解锁技能等信息
    """
    user_id = str(current_user.get("id"))
    if not user_id:
        raise HTTPException(status_code=401, detail="用户未认证")
    
    # 获取用户评分信息
    score_info = service.get_user_profile_score(user_id)
    if not score_info:
        # 如果不存在评分记录，创建默认评分
        score_info = service.create_default_score(user_id)
    
    # 获取已解锁技能
    unlocked_skills = []
    if include_skills:
        skills = service.get_user_unlocked_skills(user_id)
        unlocked_skills = [skill.skill_name for skill in skills]
    
    # 计算升级进度
    level_info = service.calculate_level_info(score_info.total_experience)
    
    return UserProfileScoreSummary(
        user_id=score_info.user_id,
        overall_score=score_info.overall_score,
        accuracy_score=score_info.accuracy_score,
        completeness_score=score_info.completeness_score,
        activity_score=score_info.activity_score,
        engagement_score=score_info.engagement_score,
        total_experience=score_info.total_experience,
        level=level_info["current_level"],
        unlocked_skills=unlocked_skills,
        next_level_progress=level_info["progress"],
        last_updated=score_info.updated_at
    )


@router.put("/me/update", response_model=ScoreResponse)
async def update_my_profile_score(
    score_data: UserProfileScoreUpdateRequest,
    current_user: dict = Depends(get_current_user),
    service: UserProfileScoreService = Depends(get_score_service)
):
    """
    更新当前用户的画像评分
    可以更新特定维度的评分，系统会自动计算综合评分和更新历史记录
    """
    user_id = str(current_user.get("id"))
    if not user_id:
        raise HTTPException(status_code=401, detail="用户未认证")
    
    # 验证评分范围
    for score_field in ["accuracy_score", "completeness_score", "activity_score", "engagement_score"]:
        score_value = getattr(score_data, score_field)
        if score_value is not None and (score_value < 0 or score_value > 100):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{score_field} 必须在0-100之间"
            )
    
    # 更新评分
    updated_score = service.update_user_profile_score(
        user_id=user_id,
        score_data=score_data
    )
    
    if not updated_score:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新评分失败"
        )
    
    return ScoreResponse(
        id=updated_score.id,
        user_id=updated_score.user_id,
        accuracy_score=updated_score.accuracy_score,
        completeness_score=updated_score.completeness_score,
        activity_score=updated_score.activity_score,
        engagement_score=updated_score.engagement_score,
        overall_score=updated_score.overall_score,
        total_experience=updated_score.total_experience,
        level=service.calculate_level_info(updated_score.total_experience)["current_level"],
        created_at=updated_score.created_at,
        updated_at=updated_score.updated_at,
        message="评分更新成功"
    )


@router.post("/me/experience", response_model=ScoreResponse)
async def add_experience(
    experience_points: int = Body(..., description="要添加的经验值", ge=1, le=1000),
    reason: str = Body(..., description="获得经验值的原因"),
    current_user: dict = Depends(get_current_user),
    service: UserProfileScoreService = Depends(get_score_service)
):
    """
    为当前用户添加经验值
    经验值达到一定阈值会自动升级，并可能解锁新技能
    """
    user_id = str(current_user.get("id"))
    if not user_id:
        raise HTTPException(status_code=401, detail="用户未认证")
    
    # 添加经验值
    updated_score = service.add_user_experience(
        user_id=user_id,
        experience_points=experience_points,
        reason=reason
    )
    
    if not updated_score:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="添加经验值失败"
        )
    
    # 检查并解锁新技能
    service.check_and_unlock_new_skills(user_id)
    
    return ScoreResponse(
        id=updated_score.id,
        user_id=updated_score.user_id,
        accuracy_score=updated_score.accuracy_score,
        completeness_score=updated_score.completeness_score,
        activity_score=updated_score.activity_score,
        engagement_score=updated_score.engagement_score,
        overall_score=updated_score.overall_score,
        total_experience=updated_score.total_experience,
        level=service.calculate_level_info(updated_score.total_experience)["current_level"],
        created_at=updated_score.created_at,
        updated_at=updated_score.updated_at,
        message=f"成功添加{experience_points}经验值"
    )


@router.get("/me/history", response_model=List[UserProfileScoreHistoryResponse])
async def get_my_score_history(
    limit: int = Query(20, description="返回记录数量限制", ge=1, le=100),
    offset: int = Query(0, description="偏移量", ge=0),
    current_user: dict = Depends(get_current_user),
    service: UserProfileScoreService = Depends(get_score_service)
):
    """
    获取当前用户的评分历史记录
    记录所有评分变化和经验值获取的历史
    """
    user_id = str(current_user.get("id"))
    if not user_id:
        raise HTTPException(status_code=401, detail="用户未认证")
    
    # 获取评分历史
    history_records = service.get_user_score_history(
        user_id=user_id,
        limit=limit,
        offset=offset
    )
    
    # 转换为响应模型
    response = []
    for record in history_records:
        response.append(UserProfileScoreHistoryResponse(
            id=record.id,
            user_id=record.user_id,
            change_type=record.change_type,
            score_changes=record.score_changes,
            experience_change=record.experience_change,
            reason=record.reason,
            created_at=record.created_at,
            previous_level=record.previous_level,
            current_level=record.current_level
        ))
    
    return response


@router.get("/me/skills", response_model=List[SkillResponse])
async def get_my_unlocked_skills(
    include_details: bool = Query(False, description="是否包含技能详细描述"),
    current_user: dict = Depends(get_current_user),
    service: UserProfileScoreService = Depends(get_score_service)
):
    """
    获取当前用户已解锁的技能列表
    """
    user_id = str(current_user.get("id"))
    if not user_id:
        raise HTTPException(status_code=401, detail="用户未认证")
    
    # 获取已解锁技能
    skills = service.get_user_unlocked_skills(user_id)
    
    # 转换为响应模型
    response = []
    for skill in skills:
        skill_data = SkillResponse(
            id=skill.id,
            skill_name=skill.skill_name,
            skill_code=skill.skill_code,
            unlocked_at=skill.unlocked_at,
            level_requirement=skill.level_requirement,
            description=skill.description if include_details else ""
        )
        response.append(skill_data)
    
    return response


@router.post("/me/skills/unlock", response_model=SkillResponse)
async def unlock_skill(
    unlock_request: SkillUnlockRequest,
    current_user: dict = Depends(get_current_user),
    service: UserProfileScoreService = Depends(get_score_service)
):
    """
    手动解锁特定技能
    需要满足技能解锁条件（等级或评分要求）
    """
    user_id = str(current_user.get("id"))
    if not user_id:
        raise HTTPException(status_code=401, detail="用户未认证")
    
    # 尝试解锁技能
    unlocked_skill = service.unlock_skill(
        user_id=user_id,
        skill_id=unlock_request.skill_id,
        score_threshold=unlock_request.score_threshold
    )
    
    if not unlocked_skill:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="技能解锁失败，可能不满足解锁条件"
        )
    
    return SkillResponse(
        id=unlocked_skill.id,
        skill_name=unlocked_skill.skill_name,
        skill_code=unlocked_skill.skill_code,
        unlocked_at=unlocked_skill.unlocked_at,
        level_requirement=unlocked_skill.level_requirement,
        description=unlocked_skill.description,
        message="技能解锁成功"
    )


@router.get("/me/ranking", response_model=Dict[str, Any])
async def get_my_ranking(
    score_type: ScoreType = Query(ScoreType.OVERALL, description="排行榜类型"),
    current_user: dict = Depends(get_current_user),
    service: UserProfileScoreService = Depends(get_score_service)
):
    """
    获取当前用户在特定评分类型的排行榜位置
    返回用户排名和周围用户信息
    """
    user_id = str(current_user.get("id"))
    if not user_id:
        raise HTTPException(status_code=401, detail="用户未认证")
    
    # 获取用户排名信息
    ranking_info = service.get_user_ranking(
        user_id=user_id,
        score_type=score_type.value
    )
    
    if not ranking_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="无法获取排名信息"
        )
    
    return ranking_info


@router.get("/leaderboard", response_model=List[Dict[str, Any]])
async def get_leaderboard(
    score_type: ScoreType = Query(ScoreType.OVERALL, description="排行榜类型"),
    limit: int = Query(50, description="返回数量限制", ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    service: UserProfileScoreService = Depends(get_score_service)
):
    """
    获取评分排行榜
    展示用户在特定评分类型的排名情况
    """
    # 获取排行榜数据
    leaderboard = service.get_leaderboard(
        score_type=score_type.value,
        limit=limit
    )
    
    return leaderboard