"""
用户画像路由集成模块
整合所有用户画像相关路由
"""

from fastapi import APIRouter
from . import user_profile, user_profile_score  # 用户画像相关模块

# 创建主路由器
router = APIRouter()

# 包含所有用户画像相关的子路由
router.include_router(user_profile.router)
router.include_router(user_profile_score.router)

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
            "基础用户画像",
            "评分系统"
        ],
        "note": "用户画像系统已重构到独立目录"
    }