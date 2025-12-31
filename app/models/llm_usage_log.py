"""
大语言模型调用日志模型
记录每次LLM API调用的详细信息
"""

from sqlalchemy import Column, String, Text, Integer, Float, DateTime, JSON, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum

class LLMProvider(str, enum.Enum):
    """LLM服务提供商枚举"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    BAIDU = "baidu"
    ALIYUN = "aliyun"
    TENCENT = "tencent"
    CUSTOM = "custom"
    VOLCENGINE = "volcengine"  # 火山引擎

class LLMTaskType(str, enum.Enum):
    """LLM任务类型枚举"""
    PROFILE_ANALYSIS = "profile_analysis"
    INTEREST_ANALYSIS = "interest_analysis"
    QUESTION_ANSWERING = "question_answering"
    CONTENT_GENERATION = "content_generation"
    CONTENT_MODERATION = "content_moderation"
    RECOMMENDATION = "recommendation"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    COMPREHENSIVE_ANALYSIS = "comprehensive_analysis"
    CONVERSATION_SUGGESTION = "conversation_suggestion"
    ACTIVITY_INFO_EXTRACTION = "activity_info_extraction"
    OPINION_SUMMARIZATION = "opinion_summarization"
    CHAT_SUMMARIZATION = "chat_summarization"

class LLMUsageLog(Base):
    """大语言模型调用日志表"""
    __tablename__ = "llm_usage_logs"
    
    id = Column(String(36), primary_key=True, index=True)
    
    # 基本信息
    user_id = Column(String(36), nullable=True, index=True, comment="用户ID，可为空")
    task_type = Column(Enum(LLMTaskType), nullable=False, comment="任务类型")
    provider = Column(Enum(LLMProvider), nullable=False, comment="服务提供商")
    llm_model_name = Column(String(100), nullable=False, comment="模型名称")
    
    # 输入输出统计
    prompt_tokens = Column(Integer, nullable=False, default=0, comment="输入token数")
    completion_tokens = Column(Integer, nullable=False, default=0, comment="输出token数")
    total_tokens = Column(Integer, nullable=False, default=0, comment="总token数")
    
    # 调用内容
    prompt_content = Column(Text, nullable=True, comment="输入提示内容")
    response_content = Column(Text, nullable=True, comment="输出响应内容")
    
    # 性能指标
    request_duration = Column(Float, nullable=False, comment="请求耗时(秒)")
    response_time = Column(Float, nullable=False, comment="响应时间(秒)")
    
    # 请求参数
    request_params = Column(JSON, nullable=True, comment="请求参数(JSON)")
    response_metadata = Column(JSON, nullable=True, comment="响应元数据(JSON)")
    
    # 状态信息
    status = Column(String(20), default="success", comment="调用状态")
    error_message = Column(Text, nullable=True, comment="错误信息")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<LLMUsageLog(id={self.id}, user_id={self.user_id}, task_type={self.task_type}, total_tokens={self.total_tokens})>"