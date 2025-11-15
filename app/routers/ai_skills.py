"""
AI技能相关路由
包含通用AI技能管理和咖啡店推荐功能
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import json
from datetime import datetime

from app.database import get_db
from app.models.ai_skill import (
    CoffeeShopRecommendationRequest, 
    CoffeeShopRecommendationResponse,
    AISkill, AISkillCreate, AISkillUpdate, AISkillResponse,
    UserCardSkill, UserCardSkillCreate, UserCardSkillUpdate,
    UserCardSkillResponse, UserCardSkillListResponse
)
from app.models.user_card_db import UserCard
from app.services.coffee_recommendation_service import CoffeeRecommendationService
from app.dependencies import get_current_user
from app.utils.logger import logger

router = APIRouter(prefix="/api/ai-skills", tags=["ai-skills"])


# ===== 通用AI技能管理接口 =====

@router.get("/skills", response_model=List[AISkillResponse])
async def get_ai_skills(
    skill_type: str = None,
    is_active: bool = True,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取AI技能列表"""
    query = db.query(AISkill).filter(AISkill.is_active == is_active)

    if skill_type:
        query = query.filter(AISkill.skill_type == skill_type)

    skills = query.order_by(AISkill.sort_order.asc(), AISkill.created_at.desc()).all()

    return skills


@router.post("/skills", response_model=AISkillResponse)
async def create_ai_skill(
    skill: AISkillCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """创建AI技能（管理员功能）"""
    db_skill = AISkill(**skill.dict())
    db.add(db_skill)
    db.commit()
    db.refresh(db_skill)

    logger.info(f"创建AI技能成功: {db_skill.id}")
    return db_skill


@router.put("/skills/{skill_id}", response_model=AISkillResponse)
async def update_ai_skill(
    skill_id: str,
    skill_update: AISkillUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新AI技能（管理员功能）"""
    db_skill = db.query(AISkill).filter(AISkill.id == skill_id).first()

    if not db_skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI技能不存在"
        )

    update_data = skill_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_skill, field, value)

    db.commit()
    db.refresh(db_skill)

    logger.info(f"更新AI技能成功: {skill_id}")
    return db_skill


@router.get("/cards/{user_card_id}/skills", response_model=UserCardSkillListResponse)
async def get_user_card_skills(
    user_card_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """获取用户卡片的技能配置"""
    # 验证卡片是否存在
    user_card = db.query(UserCard).filter(UserCard.id == user_card_id).first()
    if not user_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户卡片不存在"
        )

    card_skills = db.query(UserCardSkill).filter(
        UserCardSkill.user_card_id == user_card_id
    ).all()

    return UserCardSkillListResponse(
        skills=card_skills,
        total_count=len(card_skills)
    )


@router.post("/cards/{user_card_id}/skills", response_model=UserCardSkillResponse)
async def bind_skill_to_card(
    user_card_id: str,
    skill_binding: UserCardSkillCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """为用户卡片绑定技能"""
    # 验证卡片是否存在
    user_card = db.query(UserCard).filter(UserCard.id == user_card_id).first()
    if not user_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户卡片不存在"
        )

    # 验证技能是否存在
    skill = db.query(AISkill).filter(AISkill.id == skill_binding.skill_id).first()
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI技能不存在"
        )

    # 检查是否已绑定
    existing_binding = db.query(UserCardSkill).filter(
        UserCardSkill.user_card_id == user_card_id,
        UserCardSkill.skill_id == skill_binding.skill_id
    ).first()

    if existing_binding:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="技能已绑定到该卡片"
        )

    # 创建绑定关系
    db_binding = UserCardSkill(
        user_card_id=user_card_id,
        skill_id=skill_binding.skill_id,
        is_enabled=skill_binding.is_enabled,
        skill_config=skill_binding.skill_config
    )

    db.add(db_binding)
    db.commit()
    db.refresh(db_binding)

    logger.info(f"绑定技能成功: card={user_card_id}, skill={skill_binding.skill_id}")
    return db_binding


@router.put("/cards/{user_card_id}/skills/{skill_id}", response_model=UserCardSkillResponse)
async def update_card_skill(
    user_card_id: str,
    skill_id: str,
    skill_update: UserCardSkillUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """更新用户卡片的技能配置"""
    db_binding = db.query(UserCardSkill).filter(
        UserCardSkill.user_card_id == user_card_id,
        UserCardSkill.skill_id == skill_id
    ).first()

    if not db_binding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="技能未绑定到该卡片"
        )

    update_data = skill_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_binding, field, value)

    db.commit()
    db.refresh(db_binding)

    logger.info(f"更新技能配置成功: card={user_card_id}, skill={skill_id}")
    return db_binding


@router.delete("/cards/{user_card_id}/skills/{skill_id}")
async def unbind_skill_from_card(
    user_card_id: str,
    skill_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """解除用户卡片的技能绑定"""
    db_binding = db.query(UserCardSkill).filter(
        UserCardSkill.user_card_id == user_card_id,
        UserCardSkill.skill_id == skill_id
    ).first()

    if not db_binding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="技能未绑定到该卡片"
        )

    db.delete(db_binding)
    db.commit()

    logger.info(f"解除技能绑定成功: card={user_card_id}, skill={skill_id}")
    return {"message": "技能已成功解除绑定"}


# ===== 咖啡店推荐相关接口 =====


@router.post("/coffee-recommendations", response_model=CoffeeShopRecommendationResponse)
async def get_coffee_shop_recommendations(
    request: CoffeeShopRecommendationRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取咖啡店推荐
    
    基于用户画像、地理位置、时间偏好等数据，智能推荐咖啡店
    """
    try:
        service = CoffeeRecommendationService(db)
        return service.get_coffee_shop_recommendations(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推荐服务错误: {str(e)}")


@router.get("/coffee-recommendations/simple")
async def get_simple_coffee_recommendations(
    user_card_id: str = Query(..., description="用户卡片ID"),
    location: str = Query(..., description="目标地点"),
    preferred_time: Optional[str] = Query(None, description="偏好时间"),
    coffee_type: Optional[str] = Query(None, description="咖啡类型偏好"),
    budget: Optional[str] = Query(None, description="预算范围"),
    max_distance: Optional[int] = Query(1000, description="最大距离（米）"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    简化的咖啡店推荐接口
    
    提供简化的参数，快速获取咖啡店推荐
    """
    try:
        # 构建请求对象
        request = CoffeeShopRecommendationRequest(
            user_card_id=user_card_id,
            location=location,
            preferred_time=preferred_time,
            coffee_preferences=[coffee_type] if coffee_type else None,
            budget_range=budget,
            max_distance=max_distance
        )
        
        service = CoffeeRecommendationService(db)
        return service.get_coffee_shop_recommendations(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推荐服务错误: {str(e)}")


@router.get("/coffee-skills/{user_card_id}", response_model=UserCardSkillListResponse)
async def get_user_coffee_skills(
    user_card_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取用户的咖啡店相关技能
    
    返回用户卡片关联的咖啡店推荐技能信息
    """
    try:
        from app.models.ai_skill import UserCardSkill, AISkill
        from sqlalchemy import and_
        from datetime import datetime
        
        # 查询咖啡店相关技能
        coffee_skills = db.query(UserCardSkill, AISkill).join(
            AISkill, UserCardSkill.skill_id == AISkill.id
        ).filter(
            and_(
                UserCardSkill.user_card_id == user_card_id,
                AISkill.skill_type == "coffee_booking",
                UserCardSkill.is_enabled == True,
                AISkill.is_active == True
            )
        ).all()
        
        # 转换响应格式
        skills = []
        for user_skill, ai_skill in coffee_skills:
            skill_response = UserCardSkillResponse(
                id=user_skill.id,
                user_card_id=user_skill.user_card_id,
                skill_id=user_skill.skill_id,
                is_enabled=user_skill.is_enabled,
                skill_config=user_skill.skill_config,
                created_at=user_skill.created_at,
                updated_at=user_skill.updated_at,
                skill=AISkillResponse.from_orm(ai_skill)
            )
            skills.append(skill_response)
        
        return UserCardSkillListResponse(
            skills=skills,
            total_count=len(skills)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取技能信息失败: {str(e)}")


@router.post("/coffee-skills/{user_card_id}/enable")
async def enable_coffee_skill(
    user_card_id: str,
    skill_id: str = Query(..., description="技能ID"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    启用咖啡店推荐技能
    
    为用户卡片启用咖啡店推荐功能
    """
    try:
        from app.models.ai_skill import UserCardSkill
        from sqlalchemy import and_
        from datetime import datetime
        
        # 查找现有技能关联
        user_skill = db.query(UserCardSkill).filter(
            and_(
                UserCardSkill.user_card_id == user_card_id,
                UserCardSkill.skill_id == skill_id
            )
        ).first()
        
        if user_skill:
            user_skill.is_enabled = True
            user_skill.updated_at = datetime.utcnow()
        else:
            # 创建新的技能关联
            user_skill = UserCardSkill(
                user_card_id=user_card_id,
                skill_id=skill_id,
                is_enabled=True,
                skill_config=json.dumps({
                    "auto_recommend": True,
                    "max_distance": 1000,
                    "min_rating": 4.0,
                    "price_range": "all"
                })
            )
            db.add(user_skill)
        
        db.commit()
        return {"message": "咖啡店推荐技能已启用", "success": True}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"启用技能失败: {str(e)}")


@router.get("/coffee-analytics/{user_card_id}")
async def get_coffee_recommendation_analytics(
    user_card_id: str,
    days: Optional[int] = Query(30, description="分析天数"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    获取咖啡店推荐分析数据
    
    分析用户的咖啡店推荐偏好和使用情况
    """
    try:
        # 这里可以添加更复杂的分析逻辑
        # 目前返回基础分析数据
        return {
            "user_card_id": user_card_id,
            "total_recommendations": 0,  # 需要实现推荐记录存储
            "preferred_coffee_types": ["拿铁", "美式"],  # 基于用户画像分析
            "preferred_atmosphere": ["安静", "舒适"],
            "average_budget": "¥30-50",
            "preferred_distance": "500m内",
            "analysis_period_days": days,
            "last_updated": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析数据获取失败: {str(e)}")