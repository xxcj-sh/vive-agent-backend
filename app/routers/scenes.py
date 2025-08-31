from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any
from app.models.schemas import BaseResponse

# 创建不带依赖的路由器
router = APIRouter(prefix="/scenes", tags=["scenes"], dependencies=[])

# 场景配置数据
SCENE_CONFIGS = [
    {
        "key": "housing",
        "label": "住房",
        'iconActive': '/images/house-active.svg',
        "icon": '/images/house.svg',
        "description": "寻找室友或出租房源",
        "roles": [
            {
                "role": "seeker",
                "label": "租客",
                "description": "寻找房源的租客"
            },
            {
                "role": "provider",
                "label": "房东",
                "description": "出租房源的房东"
            }
        ],
        "profileFields": [
            "budget",
            "location",
            "houseType",
            "moveInDate",
            "leaseTerm"
        ],
        "tags": [
            "近地铁",
            "拎包入住",
            "押一付一",
            "精装修",
            "家电齐全",
            "南北通透"
        ]
    },
    {
        "key": "activity",
        "label": "活动",
        "iconActive": "/images/interest-active.svg",
        "icon": "/images/interest.svg",
        "description": "寻找活动伙伴",
        "roles": [
            {
                "role": "seeker",
                "label": "参与者",
                "description": "寻找活动伙伴"
            },
            {
                "role": "provider",
                "label": "组织者",
                "description": "组织活动的组织者"
            }
        ],
        "profileFields": [
            "interests",
            "skillLevel",
            "availableTime",
            "groupSize",
            "budget"
        ],
        "tags": [
            "户外运动",
            "音乐",
            "摄影",
            "美食",
            "阅读",
            "旅行",
            "健身",
            "游戏"
        ]
    },
    {
        "key": "dating",
        "label": "恋爱交友",
        "icon": "/images/icon-dating.svg",
        "iconActive": "/images/icon-dating-active.svg",
        "description": "寻找恋爱对象",
        "roles": [
            {
                "role": "seeker",
                "label": "女生",
                "description": "寻找恋爱对象"
            },
            {
                "role": "provider",
                "label": "男生",
                "description": "寻找恋爱对象"
            }
        ],
        "profileFields": [
            "ageRange",
            "height",
            "education",
            "income",
            "location",
            "interests"
        ],
        "tags": [
            "温柔体贴",
            "幽默风趣",
            "事业稳定",
            "热爱运动",
            "喜欢旅行",
            "美食达人"
        ]
    }
]

@router.get("/")
@router.get("")
async def get_scene_configs():
    """
    获取所有场景配置信息
    
    返回住房、活动、恋爱交友三个场景的配置数据，包括：
    - 场景基本信息（名称、图标、描述）
    - 角色配置（租客/房东、参与者/组织者、寻找对象/被寻找）
    - 个人资料字段配置
    - 场景相关标签
    """
    try:
        return {
            "code": 0,
            "message": "success",
            "data": {
                "scenes": SCENE_CONFIGS
            }
        }
    except Exception as e:
        return {
            "code": 1500,
            "message": f"服务器内部错误: {str(e)}",
            "data": None
        }

@router.get("/{scene_key}")
async def get_scene_config(scene_key: str):
    """
    获取指定场景的配置信息
    """
    try:
        config = None
        for scene in SCENE_CONFIGS:
            if scene.get("key") == scene_key:
                config = scene
                break

        if config is None:
            raise HTTPException(status_code=404, detail="场景不存在")

        return {
            "code": 0,
            "message": "success",
            "data": config
        }
    except HTTPException:
        raise
    except Exception as e:
        return {
            "code": 1500,
            "message": f"服务器内部错误: {str(e)}",
            "data": None
        }