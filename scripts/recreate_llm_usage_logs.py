"""
根据最新模型格式重建大语言模型使用日志表
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, inspect, Column, String, Text, Integer, Float, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum
from app.config import settings

# 定义最新的枚举类型
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
    CHAT_ANALYSIS = "chat_analysis"
    QUESTION_ANSWERING = "question_answering"
    CONTENT_GENERATION = "content_generation"
    RECOMMENDATION = "recommendation"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    COMPREHENSIVE_ANALYSIS = "comprehensive_analysis"
    CONVERSATION_SUGGESTION = "conversation_suggestion"

def recreate_llm_usage_logs_table():
    """根据最新模型格式重建LLM使用日志表"""
    try:
        # 创建数据库连接
        engine = create_engine(settings.DATABASE_URL)
        
        # 检查表是否已存在
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        print(f"当前数据库: {settings.DATABASE_URL}")
        print(f"现有表: {existing_tables}")
        
        # 使用SQLAlchemy ORM方式定义表
        Base = declarative_base()
        
        class LLMUsageLog(Base):
            """大语言模型调用日志表 - 使用最新模型格式"""
            __tablename__ = "llm_usage_logs"
            
            id = Column(String, primary_key=True, index=True)
            
            # 基本信息
            user_id = Column(String, nullable=True, index=True, comment="用户ID，可为空")
            task_type = Column(SQLEnum(LLMTaskType), nullable=False, comment="任务类型")
            provider = Column(SQLEnum(LLMProvider), nullable=False, comment="服务提供商")
            llm_model_name = Column(String, nullable=False, comment="模型名称")
            
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
            status = Column(String, default="success", comment="调用状态")
            error_message = Column(Text, nullable=True, comment="错误信息")
            
            # 时间戳
            created_at = Column(DateTime(timezone=True), server_default=func.now())
            updated_at = Column(DateTime(timezone=True), nullable=True, server_default=func.now(), onupdate=func.now())
        
        # 如果表已存在，先删除再创建
        if 'llm_usage_logs' in existing_tables:
            print("正在删除旧的llm_usage_logs表...")
            # 先删除所有相关的索引
            with engine.connect() as conn:
                # 检查并删除现有索引
                indexes = inspector.get_indexes('llm_usage_logs')
                for idx in indexes:
                    if not idx['unique']:  # 只删除非唯一索引
                        try:
                            conn.execute(f"DROP INDEX IF EXISTS {idx['name']}")
                            print(f"删除索引 {idx['name']} 成功")
                        except Exception as e:
                            print(f"删除索引 {idx['name']} 时出错: {e}")
            # 删除表
            LLMUsageLog.__table__.drop(engine)
            print("✅ 旧表删除成功")
        
        # 创建新表
        print("正在创建新的llm_usage_logs表...")
        LLMUsageLog.__table__.create(engine)
        print("✅ llm_usage_logs表创建成功")
        
        # 创建索引
        try:
            with engine.connect() as conn:
                conn.execute("CREATE INDEX idx_llm_user_id ON llm_usage_logs(user_id)")
                conn.execute("CREATE INDEX idx_llm_task_type ON llm_usage_logs(task_type)")
                conn.execute("CREATE INDEX idx_llm_created_at ON llm_usage_logs(created_at)")
                conn.execute("CREATE INDEX idx_llm_provider ON llm_usage_logs(provider)")
                conn.execute("CREATE INDEX idx_llm_model_name ON llm_usage_logs(llm_model_name)")
            print("✅ 索引创建成功")
        except Exception as e:
            print(f"⚠️ 索引创建警告: {e}")
        
        # 验证表创建
        inspector = inspect(engine)
        updated_tables = inspector.get_table_names()
        print(f"更新后的表列表: {updated_tables}")
        
        if 'llm_usage_logs' in updated_tables:
            columns = inspector.get_columns('llm_usage_logs')
            print("\nllm_usage_logs表结构:")
            for col in columns:
                print(f"  - {col['name']}: {col['type']}")
        
        print(f"\n🎉 LLM使用日志表重建完成！当前使用的模型: {settings.LLM_MODEL}")
        print("✅ 表结构已更新为最新模型格式")
        print("✅ 包含火山引擎(VOLCENGINE)支持")
        print("✅ 支持最新的任务类型")
        
    except Exception as e:
        print(f"❌ 重建表失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    recreate_llm_usage_logs_table()