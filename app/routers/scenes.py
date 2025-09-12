from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any
from app.models.schemas import BaseResponse, SceneConfigResponse, SceneConfig, SceneRole

# 创建不带依赖的路由器
router = APIRouter(prefix="/scenes", tags=["scenes"], dependencies=[])

# 场景配置数据 - 使用与 schemas.py 一致的格式
SCENE_CONFIGS = {
    "activity": SceneConfig(
        key="activity",
        label="活动",
        icon="/images/interest.svg",
        iconActive="/images/interest-active.svg",
        description="寻找活动伙伴",
        roles={
            "seeker": SceneRole(
                key="activity_seeker",
                label="参与者",
                description="寻找活动伙伴"
            ),
            "provider": SceneRole(
                key="activity_provider",
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
    "social": SceneConfig(
        key="social",
        label="社交",
        icon="/images/social.svg",
        iconActive="/images/social-active.svg",
        description="商务社交与职业发展",
        roles={
            "social_business": SceneRole(
                key="social_business",
                label="商务拓展",
                description="寻找商务合作、投资机会"
            ),
            "social_career": SceneRole(
                key="social_career",
                label="职业发展",
                description="寻求职业指导、跳槽机会"
            ),
            "social_interest": SceneRole(
                key="social_interest",
                label="兴趣社交",
                description="基于共同兴趣的社交互动"
            ),
            "social_dating": SceneRole(
                key="social_dating",
                label="社交约会",
                description="寻找恋爱关系和约会对象"
            )
        },
        CardFields=[
            "currentRole",
            "currentCompany",
            "industry",
            "yearsOfExperience",
            "skills",
            "expertiseAreas",
            "socialInterests",
            "valueOfferings",
            "seekingOpportunities",
            "professionalLevel",
            "companySize"
        ],
        tags=[
            "互联网科技",
            "人工智能",
            "金融科技",
            "企业服务",
            "电子商务",
            "教育培训",
            "医疗健康",
            "新能源",
            "区块链",
            "大数据",
            "云计算",
            "物联网",
            "游戏娱乐",
            "广告营销",
            "咨询顾问",
            "创业投资",
            "产品设计",
            "技术开发",
            "运营管理",
            "市场销售"
        ]
    )
}

@router.get("/")
@router.get("")
async def get_scene_configs() -> BaseResponse:
    """
    获取所有场景配置信息
    
    返回住房、活动、社交、恋爱交友等场景的配置数据，包括：
    - 场景基本信息（名称、图标、描述）
    - 角色配置（租客/房东、参与者/组织者、商务拓展/职业发展等）
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

@router.get("/roles")
async def get_roles_display() -> BaseResponse:
    """
    获取所有场景的角色类型显示文案配置
    
    返回格式：{roleType: role_display_string}
    其中 roleType 是角色的 key，role_display_string 是角色的 label
    """
    try:
        roles_display = {}
        
        # 遍历所有场景配置
        for scene_key, scene_config in SCENE_CONFIGS.items():
            # 遍历场景中的角色
            for role_key, scene_role in scene_config.roles.items():
                # 使用角色的 key 作为字典的 key，label 作为显示文案
                roles_display[role_key] = scene_role.label
        
        return BaseResponse(
            code=0,
            message="success",
            data=roles_display
        )
    except Exception as e:
        return BaseResponse(
            code=1500,
            message=f"服务器内部错误: {str(e)}",
            data=None
        )

@router.get("/{scene_key}/roles")
async def get_scene_roles_display(scene_key: str) -> BaseResponse:
    """
    获取指定场景的角色类型显示文案配置
    
    返回格式：{roleType: role_display_string}
    其中 roleType 是角色的 key，role_display_string 是角色的 label
    """
    try:
        if scene_key not in SCENE_CONFIGS:
            raise HTTPException(status_code=404, detail="场景不存在")
        
        roles_display = {}
        scene_config = SCENE_CONFIGS[scene_key]
        
        # 遍历场景中的角色
        for role_key, scene_role in scene_config.roles.items():
            # 使用角色的 key 作为字典的 key，label 作为显示文案
            roles_display[role_key] = scene_role.label
        
        return BaseResponse(
            code=0,
            message="success",
            data=roles_display
        )
    except HTTPException:
        raise
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