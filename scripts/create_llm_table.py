#!/usr/bin/env python3
"""
创建大语言模型使用日志表
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, inspect, Column, String, Text, Integer, Float, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings
import enum

# 定义枚举
class LLMProvider(str, enum.Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    BAIDU = "baidu"
    ALIYUN = "aliyun"
    TENCENT = "tencent"
    CUSTOM = "custom"

class LLMTaskType(str, enum.Enum):
    PROFILE_ANALYSIS = "profile_analysis"
    INTEREST_ANALYSIS = "interest_analysis"
    CHAT_ANALYSIS = "chat_analysis"
    QUESTION_ANSWERING = "question_answering"
    CONTENT_GENERATION = "content_generation"
    RECOMMENDATION = "recommendation"
    SENTIMENT_ANALYSIS = "sentiment_analysis"

def create_llm_table():
    """创建LLM使用日志表"""
    try:
        # 创建数据库连接
        engine = create_engine(settings.DATABASE_URL)
        
        # 检查表是否已存在
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        print(f"当前数据库: {settings.DATABASE_URL}")
        print(f"现有表: {existing_tables}")
        
        # 使用SQLAlchemy ORM方式创建表
        Base = declarative_base()
        
        class LLMUsageLog(Base):
            __tablename__ = 'llm_usage_logs'
            
            id = Column(String, primary_key=True)
            user_id = Column(String)
            task_type = Column(String, nullable=False)
            provider = Column(String, nullable=False)
            model_name = Column(String, nullable=False)
            prompt_tokens = Column(Integer, default=0, nullable=False)
            completion_tokens = Column(Integer, default=0, nullable=False)
            total_tokens = Column(Integer, default=0, nullable=False)
            prompt_content = Column(Text)
            response_content = Column(Text)
            request_duration = Column(Float, nullable=False)
            response_time = Column(Float, nullable=False)
            request_params = Column(Text)
            response_metadata = Column(Text)
            status = Column(String, default='success')
            error_message = Column(Text)
            created_at = Column(DateTime, default=func.now())
            updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
        
        # 直接创建表
        if 'llm_usage_logs' not in existing_tables:
            print("正在创建llm_usage_logs表...")
            LLMUsageLog.__table__.create(engine)
            print("✅ llm_usage_logs表创建成功")
            
            # 创建索引
            try:
                with engine.connect() as conn:
                    conn.execute("CREATE INDEX idx_llm_user_id ON llm_usage_logs(user_id)")
                    conn.execute("CREATE INDEX idx_llm_task_type ON llm_usage_logs(task_type)")
                    conn.execute("CREATE INDEX idx_llm_created_at ON llm_usage_logs(created_at)")
                print("✅ 索引创建成功")
            except Exception as e:
                print(f"⚠️ 索引创建警告: {e}")
                
        else:
            print("ℹ️ llm_usage_logs表已存在，跳过创建")
        
        # 验证表创建
        inspector = inspect(engine)
        updated_tables = inspector.get_table_names()
        print(f"更新后的表列表: {updated_tables}")
        
        if 'llm_usage_logs' in updated_tables:
            columns = inspector.get_columns('llm_usage_logs')
            print("\nllm_usage_logs表结构:")
            for col in columns:
                print(f"  - {col['name']}: {col['type']}")
        
        print("\n🎉 LLM表初始化完成！")
        
    except Exception as e:
        print(f"❌ 初始化失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_llm_table()