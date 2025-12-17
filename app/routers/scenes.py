from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any
from app.models.schemas import BaseResponse, SceneConfigResponse, SceneConfig, SceneRole

# 创建不带依赖的路由器
router = APIRouter(prefix="/scenes", tags=["scenes"], dependencies=[])

# 场景配置数据 - 使用与 schemas.py 一致的格式
SCENE_CONFIGS = {
    "vote": SceneConfig(
        key="vote",
        label="投票",
        icon="/images/icon-vote.svg",
        iconActive="/images/icon-vote-active.svg",
        description="发起投票，收集意见，做出决策",
        roles={
            "vote_selection": SceneRole(
                key="vote_selection",
                label="选择投票",
                description="在多个选项中进行选择"
            )
        },
        CardFields=[
            "voteTitle",
            "voteDescription",
            "voteOptions",
            "voteType",
            "endTime",
            "allowMultiple",
            "anonymous",
            "targetAudience",
            "votingPurpose",
            "resultVisibility"
        ],
        tags=[
        ]
    ),
    "social": SceneConfig(
        key="social",
        label="社交",
        icon="/images/social.svg",
        iconActive="/images/social-active.svg",
        description="寻找兴趣伙伴，或者生活、事业合伙人",
        roles={
            "social_identity": SceneRole(
                key="social_identity",
                label="身份名片",
                description="更生动地向别人介绍你"
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
        ]
    ),
    "topic": SceneConfig(
        key="topic",
        label="话题",
        icon="/images/icon-ai.svg",
        iconActive="/images/icon-ai.svg",
        description="分享想法，发起讨论，寻找共鸣",
        roles={
            "topic_discussion": SceneRole(
                key="topic_discussion",
                label="话题交流",
                description="了解他人的想法"
            )
        },
        CardFields=[
            "topicTitle",
            "topicContent",
            "topicCategory",
            "tags",
            "targetAudience",
            "discussionGoals",
            "backgroundInfo",
            "keyPoints",
            "callToAction"
        ],
        tags=[        ]
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