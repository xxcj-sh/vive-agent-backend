from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any
from app.models.schemas import BaseResponse, SceneConfigResponse, SceneConfig, SceneRole

# 创建不带依赖的路由器
router = APIRouter(prefix="/scenes", tags=["scenes"], dependencies=[])

# 场景配置数据 - 使用与 schemas.py 一致的格式
SCENE_CONFIGS = {
    "housing": SceneConfig(
        key="housing",
        label="住房",
        icon="/images/house.svg",
        description="寻找室友或出租房源",
        roles={
            "seeker": SceneRole(
                key="seeker",
                label="租客",
                description="寻找房源的租客"
            ),
            "provider": SceneRole(
                key="provider",
                label="房东",
                description="出租房源的房东"
            )
        },
        CardFields=["budget", "location", "houseType", "moveInDate", "leaseTerm"],
        tags=[
            "近地铁",
            "拎包入住",
            "押一付一",
            "精装修",
            "家电齐全",
            "南北通透"
        ]
    ),
    "activity": SceneConfig(
        key="activity",
        label="活动",
        icon="/images/interest.svg",
        description="寻找活动伙伴",
        roles={
            "seeker": SceneRole(
                key="seeker",
                label="参与者",
                description="寻找活动伙伴"
            ),
            "provider": SceneRole(
                key="provider",
                label="组织者",
                description="组织活动的组织者"
            )
        },
        CardFields=["interests", "skillLevel", "availableTime", "groupSize", "budget"],
        tags=[
            "户外运动",
            "音乐",
            "摄影",
            "美食",
            "阅读",
            "旅行",
            "健身",
            "游戏"
        ]
    ),
    "dating": SceneConfig(
        key="dating",
        label="恋爱交友",
        icon="/images/icon-dating.svg",
        description="寻找恋爱对象",
        roles={
            "seeker": SceneRole(
                key="seeker",
                label="女生",
                description="寻找恋爱对象"
            ),
            "provider": SceneRole(
                key="provider",
                label="男生",
                description="寻找恋爱对象"
            )
        },
        CardFields=["ageRange", "height", "education", "income", "location", "interests"],
        tags=[
            "温柔体贴",
            "幽默风趣",
            "事业稳定",
            "热爱运动",
            "喜欢旅行",
            "美食达人"
        ]
    )
}

@router.get("/")
@router.get("")
async def get_scene_configs() -> BaseResponse:
    """
    获取所有场景配置信息
    
    返回住房、活动、恋爱交友三个场景的配置数据，包括：
    - 场景基本信息（名称、图标、描述）
    - 角色配置（租客/房东、参与者/组织者、寻找对象/被寻找）
    - 个人资料字段配置
    - 场景相关标签
    """
    try:
        response = SceneConfigResponse(scenes=SCENE_CONFIGS)
        return BaseResponse(
            code=0,
            message="success",
            data=response.model_dump()
        )
    except Exception as e:
        return BaseResponse(
            code=1500,
            message=f"服务器内部错误: {str(e)}",
            data=None
        )

@router.get("/{scene_key}")
async def get_scene_config(scene_key: str) -> BaseResponse:
    """
    获取指定场景的配置信息
    """
    try:
        if scene_key not in SCENE_CONFIGS:
            raise HTTPException(status_code=404, detail="场景不存在")
        
        config = SCENE_CONFIGS[scene_key]
        return BaseResponse(
            code=0,
            message="success",
            data=config.model_dump()
        )
    except HTTPException:
        raise
    except Exception as e:
        return BaseResponse(
            code=1500,
            message=f"服务器内部错误: {str(e)}",
            data=None
        )