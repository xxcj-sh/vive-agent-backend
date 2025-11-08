"""
AI技能路由
管理AI分身技能配置
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.ai_skill import (
    AISkill, AISkillCreate, AISkillUpdate, AISkillResponse,
    UserCardSkill, UserCardSkillCreate, UserCardSkillUpdate,
    UserCardSkillResponse, UserCardSkillListResponse
)
from app.models.user_card_db import UserCard
from app.utils.logger import logger

router = APIRouter()


@router.get("/skills", response_model=List[AISkillResponse])
async def get_ai_skills(
    skill_type: str = None,
    is_active: bool = True,
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
    db: Session = Depends(get_db)
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
