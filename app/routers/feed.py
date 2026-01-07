from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.services.feed_service import FeedService

router = APIRouter()

@router.get("/item-cards")
@router.get("/cards")
async def get_feed_item_cards(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=50, description="每页数量"),
    card_type: Optional[str] = Query(None, description="卡片类型: topic, vote, all"),
    category: Optional[str] = Query(None, description="分类筛选"),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    获取统一的卡片流数据
    
    支持获取话题卡片和投票卡片，可以按类型筛选或获取混合内容
    """
    try:
        user_id = str(current_user.get("id")) if current_user else None
        feed_service = FeedService(db)
        
        return feed_service.get_feed_item_cards(
            user_id=user_id,
            page=page,
            page_size=page_size,
            card_type=card_type,
            category=category
        )
        
    except Exception as e:
        print(f"获取卡片流失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取卡片流失败: {str(e)}")



@router.get("/user-cards")
@router.get("/recommendation-user-cards")
async def get_feed_user_cards(
    page: int = Query(1, description="页码"),
    pageSize: int = Query(10, description="每页数量"),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """    
    推荐逻辑：
    1. 根据用户上次访问(VISIT)时间顺序排列，选取最久未访问的若干用户
    2. 剔除最近两周曾经浏览(VIEW)过的用户
    3. 按顺序展示给用户
    
    对于未登录用户，返回随机的5张公开用户卡片
    """
    try:
        feed_service = FeedService(db)
        feed_card_list = []
        if current_user: 
            # 获取用户ID
            if isinstance(current_user, dict):
                user_id = str(current_user.get('id', ''))
            else:
                user_id = str(current_user.id)
            
            # 使用FeedService获取推荐卡片
            result = feed_service.get_feed_user_cards(
                user_id=user_id,
                page=page,
                page_size=pageSize
            )
            feed_card_list = result["cards"]
            # 能返回超过 5 张卡片时，直接使用基于用户关系的 feed 算法
            if len(result["cards"]) >= pageSize :
                return {
                "code": 0,
                "message": "success",
                "data": {
                    "cards": result["cards"],
                    "pagination": {
                        "page": page,
                        "pageSize": pageSize,
                        "total": result["pagination"]["total"],
                        "totalPages": result["pagination"]["totalPages"]
                    },
                    "source": result["source"]
                }
            }
        # 未登录或者无法获得有效推荐的情况，获取 5 张随机的公开用户卡片
        random_cards = feed_service.get_random_public_user_cards(limit=pageSize)  
        random_cards.extend(feed_card_list)
        return {
            "code": 0,
            "message": "success",
            "data": {
                "cards": random_cards,
                "pagination": {
                    "page": 1,
                    "pageSize": 5,
                    "total": len(random_cards),
                    "totalPages": 1
                },
                "source": "random_public_cards_for_unauthenticated"
            }
        }
            
    except Exception as e:
        print(f"获取推荐卡片异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "code": 500,
            "message": f"获取推荐卡片失败: {str(e)}",
            "data": None
        }