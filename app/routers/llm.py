"""
大语言模型API路由
提供LLM相关的RESTful API接口
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.database import get_db
from app.services.auth import auth_service
from app.services.llm_service import LLMService
from app.models.llm_schemas import (
    ProfileAnalysisRequest, InterestAnalysisRequest,
    ChatAnalysisRequest, QuestionAnsweringRequest,
    LLMUsageLogResponse
)
from app.models.llm_usage_log import LLMTaskType, LLMProvider

router = APIRouter(prefix="/llm", tags=["大语言模型"])

@router.post("/analyze-profile")
async def analyze_user_profile(
    request: ProfileAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_service.get_current_user)
):
    """
    分析用户资料
    
    对用户资料进行深入分析，提供个性化洞察和建议
    """
    service = LLMService(db)
    
    # 如果request中没有user_id，使用当前登录用户
    if not request.user_id:
        request.user_id = current_user["id"]
    
    response = await service.analyze_user_profile(
        user_id=request.user_id,
        profile_data=request.profile_data,
        card_type=request.card_type,
        provider=LLMProvider.OPENAI,  # 可以从前端指定
        model_name="gpt-3.5-turbo"
    )
    
    if not response.success:
        raise HTTPException(status_code=500, detail="分析失败")
    
    return {
        "code": 0,
        "message": "success",
        "data": {
            "analysis": response.analysis,
            "key_insights": response.key_insights,
            "recommendations": response.recommendations,
            "usage": response.usage,
            "duration": response.duration
        }
    }

@router.post("/analyze-interests")
async def analyze_user_interests(
    request: InterestAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_service.get_current_user)
):
    """
    分析用户兴趣
    
    分析用户的兴趣爱好，提供兴趣分类和匹配建议
    """
    service = LLMService(db)
    
    if not request.user_id:
        request.user_id = current_user["id"]
    
    response = await service.analyze_user_interests(
        user_id=request.user_id,
        user_interests=request.user_interests,
        context_data=request.context_data,
        provider=LLMProvider.OPENAI,
        model_name="gpt-3.5-turbo"
    )
    
    if not response.success:
        raise HTTPException(status_code=500, detail="分析失败")
    
    return {
        "code": 0,
        "message": "success",
        "data": {
            "interests": response.interests,
            "categories": response.categories,
            "match_suggestions": response.match_suggestions,
            "usage": response.usage,
            "duration": response.duration
        }
    }

@router.post("/analyze-chat")
async def analyze_chat_history(
    request: ChatAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_service.get_current_user)
):
    """
    分析聊天记录
    
    分析用户聊天记录，提供情感分析、内容摘要和关系洞察
    """
    service = LLMService(db)
    
    if not request.user_id:
        request.user_id = current_user["id"]
    
    response = await service.analyze_chat_history(
        user_id=request.user_id,
        chat_history=request.chat_history,
        analysis_type=request.analysis_type,
        provider=LLMProvider.OPENAI,
        model_name="gpt-3.5-turbo"
    )
    
    if not response.success:
        raise HTTPException(status_code=500, detail="分析失败")
    
    return {
        "code": 0,
        "message": "success",
        "data": {
            "sentiment": response.sentiment,
            "summary": response.summary,
            "key_topics": response.key_topics,
            "relationship_score": response.relationship_score,
            "usage": response.usage,
            "duration": response.duration
        }
    }

@router.post("/ask")
async def answer_user_question(
    request: QuestionAnsweringRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_service.get_current_user)
):
    """
    回答用户问题
    
    基于用户资料和上下文信息，智能回答用户的问题
    """
    service = LLMService(db)
    
    if not request.user_id:
        request.user_id = current_user["id"]
    
    response = await service.answer_user_question(
        user_id=request.user_id,
        question=request.question,
        context=request.context,
        provider=LLMProvider.OPENAI,
        model_name="gpt-3.5-turbo"
    )
    
    if not response.success:
        raise HTTPException(status_code=500, detail="回答失败")
    
    return {
        "code": 0,
        "message": "success",
        "data": {
            "answer": response.answer,
            "confidence": response.confidence,
            "sources": response.sources,
            "usage": response.usage,
            "duration": response.duration
        }
    }

@router.get("/usage-logs")
async def get_usage_logs(
    user_id: Optional[str] = Query(None, description="用户ID过滤"),
    task_type: Optional[LLMTaskType] = Query(None, description="任务类型过滤"),
    provider: Optional[LLMProvider] = Query(None, description="提供商过滤"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_service.get_current_user)
):
    """
    获取LLM使用日志
    
    查询用户的LLM API调用记录，包括耗时、token使用等信息
    """
    from sqlalchemy import desc
    
    query = db.query(LLMUsageLog)
    
    # 管理员可以查看所有日志，普通用户只能查看自己的日志
    if current_user.get("role") != "admin":
        query = query.filter(LLMUsageLog.user_id == current_user["id"])
    elif user_id:
        query = query.filter(LLMUsageLog.user_id == user_id)
    
    if task_type:
        query = query.filter(LLMUsageLog.task_type == task_type)
    
    if provider:
        query = query.filter(LLMUsageLog.provider == provider)
    
    logs = query.order_by(desc(LLMUsageLog.created_at)).offset(offset).limit(limit).all()
    
    return {
        "code": 0,
        "message": "success",
        "data": {
            "logs": [LLMUsageLogResponse.from_orm(log) for log in logs],
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": query.count()
            }
        }
    }

@router.get("/usage-stats")
async def get_usage_stats(
    user_id: Optional[str] = Query(None, description="用户ID过滤"),
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_service.get_current_user)
):
    """
    获取LLM使用统计
    
    获取用户LLM API调用的统计数据，包括总token数、调用次数等
    """
    from sqlalchemy import func, and_
    from datetime import datetime, timedelta
    
    # 管理员可以查看所有统计，普通用户只能查看自己的统计
    target_user_id = user_id if current_user.get("role") == "admin" else current_user["id"]
    
    # 计算日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # 基础查询
    query = db.query(LLMUsageLog).filter(
        and_(
            LLMUsageLog.user_id == target_user_id,
            LLMUsageLog.created_at >= start_date,
            LLMUsageLog.created_at <= end_date
        )
    )
    
    # 统计信息
    total_calls = query.count()
    total_tokens = db.query(func.sum(LLMUsageLog.total_tokens)).filter(
        and_(
            LLMUsageLog.user_id == target_user_id,
            LLMUsageLog.created_at >= start_date,
            LLMUsageLog.created_at <= end_date
        )
    ).scalar() or 0
    
    total_cost = total_tokens * 0.001  # 假设每1000 tokens $0.001
    
    # 按任务类型统计
    task_stats = db.query(
        LLMUsageLog.task_type,
        func.count(LLMUsageLog.id).label('count'),
        func.sum(LLMUsageLog.total_tokens).label('tokens')
    ).filter(
        and_(
            LLMUsageLog.user_id == target_user_id,
            LLMUsageLog.created_at >= start_date,
            LLMUsageLog.created_at <= end_date
        )
    ).group_by(LLMUsageLog.task_type).all()
    
    # 按提供商统计
    provider_stats = db.query(
        LLMUsageLog.provider,
        func.count(LLMUsageLog.id).label('count'),
        func.sum(LLMUsageLog.total_tokens).label('tokens')
    ).filter(
        and_(
            LLMUsageLog.user_id == target_user_id,
            LLMUsageLog.created_at >= start_date,
            LLMUsageLog.created_at <= end_date
        )
    ).group_by(LLMUsageLog.provider).all()
    
    return {
        "code": 0,
        "message": "success",
        "data": {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "summary": {
                "total_calls": total_calls,
                "total_tokens": total_tokens,
                "total_cost": total_cost,
                "avg_tokens_per_call": total_tokens / total_calls if total_calls > 0 else 0
            },
            "task_stats": [
                {
                    "task_type": stat.task_type,
                    "count": stat.count,
                    "tokens": stat.tokens,
                    "percentage": (stat.count / total_calls * 100) if total_calls > 0 else 0
                }
                for stat in task_stats
            ],
            "provider_stats": [
                {
                    "provider": stat.provider,
                    "count": stat.count,
                    "tokens": stat.tokens,
                    "percentage": (stat.count / total_calls * 100) if total_calls > 0 else 0
                }
                for stat in provider_stats
            ]
        }
    }