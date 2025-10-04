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
    

    
class QuestionAnsweringRequest(LLMRequest):
    """用户提问回答请求"""
    task_type: LLMTaskType = Field(default=LLMTaskType.QUESTION_ANSWERING, description="任务类型")
    question: str = Field(..., description="用户问题")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")
    
class LLMResponse(BaseModel):
    """LLM响应基础模型"""
    success: bool = Field(..., description="是否成功")
    data: Optional[str] = Field(None, description="响应数据")
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
    

    
class QuestionAnsweringResponse(LLMResponse):
    """用户提问回答响应"""
    answer: str = Field(..., description="回答内容")
    confidence: float = Field(..., description="置信度")
    sources: Optional[List[str]] = Field(None, description="信息来源")

class ComprehensiveAnalysisRequest(BaseModel):
    """综合分析请求"""
    user_id: Optional[str] = Field(None, description="用户ID")
    profile_data: Dict[str, Any] = Field(..., description="用户资料数据")
    interests: List[str] = Field(..., description="用户兴趣列表")
    context: Optional[Dict[str, Any]] = Field(None, description="额外上下文信息")
    analysis_types: List[str] = Field(..., description="分析类型列表")

class ComprehensiveAnalysisResponse(LLMResponse):
    """综合分析响应"""
    profile_analysis: Optional[Dict[str, Any]] = Field(None, description="用户资料分析")
    interest_analysis: Optional[Dict[str, Any]] = Field(None, description="兴趣分析")
    overall_insights: List[str] = Field(..., description="综合洞察")
    recommendations: List[str] = Field(..., description="综合建议")



class LLMUsageLogResponse(BaseModel):
    """LLM使用日志响应"""
    id: str = Field(..., description="日志ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    task_type: LLMTaskType = Field(..., description="任务类型")
    provider: LLMProvider = Field(..., description="服务提供商")
    llm_model_name: str = Field(..., description="模型名称")
    total_tokens: int = Field(..., description="总token数")
    prompt_tokens: int = Field(..., description="输入token数")
    completion_tokens: int = Field(..., description="输出token数")
    duration: float = Field(..., description="耗时(秒)")
    status: str = Field(..., description="状态")
    created_at: datetime = Field(..., description="创建时间")
    
    class Config:
        from_attributes = True

class ConversationSuggestionRequest(BaseModel):
    """对话建议请求"""
    userId: Optional[str] = Field(None, description="用户ID")
    cardId: Optional[str] = Field(None, description="卡片ID")
    chatId: str = Field(..., description="聊天ID")
    context: Dict[str, Any] = Field(..., description="上下文信息")
    suggestionType: str = Field(..., description="建议类型")
    maxSuggestions: int = Field(default=3, description="最大建议数量")

class ConversationSuggestionResponse(LLMResponse):
    """对话建议响应"""
    suggestions: List[str] = Field(..., description="建议列表")
    confidence: float = Field(..., description="置信度")
    is_meet_preference: bool = Field(..., description="是否满足卡片主人偏好")
    preference_judgement: Optional[str] = Field(None, description="满足偏好的判断论述")
