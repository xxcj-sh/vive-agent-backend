"""
用户画像路由模块

该模块整合了所有用户画像相关的路由功能，包括：
- 基础用户画像管理
- 用户画像评分系统
- 技能解锁机制
- 评分历史记录
- 排行榜功能
"""

from fastapi import APIRouter

# 从当前目录导入各个子模块
from .user_profile_main import router as main_router
from .user_profile import router as profile_router
from .user_profile_score import router as score_router

# 创建主路由器
router = APIRouter()

# 包含所有用户画像相关的子路由
router.include_router(main_router)
router.include_router(profile_router)
router.include_router(score_router)

# 导出主路由器
__all__ = ["router"]