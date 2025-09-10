"""
大语言模型相关的Pydantic schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from .llm_usage_log import LLMProvider, LLMTaskType

class LLMRequest(BaseModel):
    """LLM请求基础模型"""
    user_id: Optional[str] = Field(None, description="用户ID")
    task_type: LLMTaskType = Field(..., description="任务类型")
    prompt: str = Field(..., description="提示内容")
    llm_config: Optional[Dict[str, Any]] = Field(None, description="模型配置")
    
class ProfileAnalysisRequest(LLMRequest):
    """用户资料分析请求"""
    task_type: LLMTaskType = Field(default=LLMTaskType.PROFILE_ANALYSIS, description="任务类型")
    profile_data: Dict[str, Any] = Field(..., description="用户资料数据")
    card_type: str = Field(..., description="卡片类型")
    
class InterestAnalysisRequest(LLMRequest):
    """用户兴趣分析请求"""
    task_type: LLMTaskType = Field(default=LLMTaskType.INTEREST_ANALYSIS, description="任务类型")
    user_interests: List[str] = Field(..., description="用户兴趣列表")
    context_data: Optional[Dict[str, Any]] = Field(None, description="上下文数据")
    
class ChatAnalysisRequest(LLMRequest):
    """聊天记录分析请求"""
    task_type: LLMTaskType = Field(default=LLMTaskType.CHAT_ANALYSIS, description="任务类型")
    chat_history: List[Dict[str, Any]] = Field(..., description="聊天记录")
    analysis_type: str = Field(..., description="分析类型: sentiment, summary, insights")
    
class QuestionAnsweringRequest(LLMRequest):
    """用户提问回答请求"""
    task_type: LLMTaskType = Field(default=LLMTaskType.QUESTION_ANSWERING, description="任务类型")
    question: str = Field(..., description="用户问题")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")
    
class LLMResponse(BaseModel):
    """LLM响应基础模型"""
    success: bool = Field(..., description="是否成功")
    data: Optional[Dict[str, Any]] = Field(None, description="响应数据")
    usage: Dict[str, int] = Field(..., description="token使用情况")
    duration: float = Field(..., description="处理耗时(秒)")
    
class ProfileAnalysisResponse(LLMResponse):
    """用户资料分析响应"""
    analysis: Dict[str, Any] = Field(..., description="分析结果")
    key_insights: List[str] = Field(..., description="关键洞察")
    recommendations: List[str] = Field(..., description="改进建议")
    
class InterestAnalysisResponse(LLMResponse):
    """用户兴趣分析响应"""
    interests: List[str] = Field(..., description="识别出的兴趣")
    categories: Dict[str, List[str]] = Field(..., description="兴趣分类")
    match_suggestions: List[str] = Field(..., description="匹配建议")
    
class ChatAnalysisResponse(LLMResponse):
    """聊天记录分析响应"""
    sentiment: str = Field(..., description="情感倾向")
    summary: str = Field(..., description="聊天摘要")
    key_topics: List[str] = Field(..., description="主要话题")
    relationship_score: Optional[float] = Field(None, description="关系评分")
    
class QuestionAnsweringResponse(LLMResponse):
    """用户提问回答响应"""
    answer: str = Field(..., description="回答内容")
    confidence: float = Field(..., description="置信度")
    sources: Optional[List[str]] = Field(None, description="信息来源")

class LLMUsageLogResponse(BaseModel):
    """LLM使用日志响应"""
    id: str = Field(..., description="日志ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    task_type: LLMTaskType = Field(..., description="任务类型")
    provider: LLMProvider = Field(..., description="服务提供商")
    model_name: str = Field(..., description="模型名称")
    total_tokens: int = Field(..., description="总token数")
    prompt_tokens: int = Field(..., description="输入token数")
    completion_tokens: int = Field(..., description="输出token数")
    duration: float = Field(..., description="耗时(秒)")
    status: str = Field(..., description="状态")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True