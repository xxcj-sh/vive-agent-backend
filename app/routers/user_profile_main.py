"""
用户画像路由集成模块
整合所有用户画像相关路由
"""

from fastapi import APIRouter
from app.routers import (
    user_profile,  # 已包含增强功能
    user_profile_learning,
    user_profile_history,
    user_profile_review
)

# 创建主路由器
router = APIRouter()

# 包含所有用户画像相关的子路由
# user_profile现在包含了基础功能和增强功能
router.include_router(user_profile.router)
router.include_router(user_profile_learning.router)
router.include_router(user_profile_history.router)
router.include_router(user_profile_review.router)

# 健康检查端点
@router.get("/health")
async def health_check():
    """用户画像系统健康检查"""
    from datetime import datetime
    return {
        "status": "healthy",
        "service": "user_profile_system",
        "timestamp": datetime.now().isoformat(),
        "available_modules": [
            "基础用户画像（已整合增强功能）",
            "智能学习",
            "历史记录",
            "定期回顾"
        ],
        "note": "user_profile_enhanced功能已合并到user_profile，避免重复"
    }